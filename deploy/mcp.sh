#!/bin/bash

# MCP管理脚本
# 用于部署、配置和启动MCP服务

# 确保脚本在出错时退出
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 默认配置
MCP_DIR="$(pwd)"
VENV_DIR="${MCP_DIR}/.venv"
HOST="0.0.0.0"
PORT="8000"
WORKERS=2
TRANSPORT="streamable-http"
MOUNT_PATH="/"
STATIC_DIR="${MCP_DIR}/data/charts"
NGINX_CONF="/etc/nginx/sites-available/mcp"
NGINX_ENABLED="/etc/nginx/sites-enabled/mcp"
SYSTEMD_SERVICE="/etc/systemd/system/mcp.service"
SERVER_NAME="localhost"  # 默认服务器名称，应该改为实际域名或IP
USE_SSL=false
SSL_CERT=""
SSL_KEY=""
ENV_FILE="${MCP_DIR}/deploy/.env"
STATELESS=true

# 显示帮助信息
show_help() {
    echo "用法: $0 [命令] [选项]"
    echo ""
    echo "命令:"
    echo "  setup       设置环境并安装依赖"
    echo "  deploy      部署MCP服务（创建配置文件）"
    echo "  install     安装MCP服务到系统（需要root权限）"
    echo "  start       启动MCP服务"
    echo "  stop        停止MCP服务"
    echo "  restart     重启MCP服务"
    echo "  status      查看MCP服务状态"
    echo "  help        显示此帮助信息"
    echo ""
    echo "选项:"
    echo "  --host HOST            绑定的主机地址 (默认: 0.0.0.0)"
    echo "  --port PORT            绑定的端口 (默认: 8000)"
    echo "  --transport TRANSPORT  传输协议 (默认: streamable-http) [可选: stdio, streamable-http, sse]"
    echo "  --mount-path PATH      SSE服务器挂载路径 (默认: /)"
    echo "  --workers WORKERS      Gunicorn工作进程数 (默认: 2)"
    echo "  --server-name NAME     Nginx服务器名称 (默认: localhost)"
    echo "  --ssl                  启用SSL"
    echo "  --ssl-cert CERT        SSL证书路径"
    echo "  --ssl-key KEY          SSL密钥路径"
    echo "  --env-file FILE        环境变量文件路径 (默认: deploy/.env)"
    echo "  --no-stateless         不使用无状态HTTP模式"
    echo ""
    echo "示例:"
    echo "  $0 setup               设置环境并安装依赖"
    echo "  $0 deploy --ssl --ssl-cert /path/to/cert --ssl-key /path/to/key"
    echo "  $0 start --transport sse --mount-path /mcp"
    echo "  $0 start --env-file .env.prod"
}

# 解析命令行参数
parse_args() {
    # 首先解析命令
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi

    COMMAND="$1"
    shift

    # 然后解析选项
    while [[ $# -gt 0 ]]; do
        key="$1"
        case $key in
            --host)
                HOST="$2"
                shift
                shift
                ;;
            --port)
                PORT="$2"
                shift
                shift
                ;;
            --transport)
                TRANSPORT="$2"
                shift
                shift
                ;;
            --mount-path)
                MOUNT_PATH="$2"
                shift
                shift
                ;;
            --workers)
                WORKERS="$2"
                shift
                shift
                ;;
            --server-name)
                SERVER_NAME="$2"
                shift
                shift
                ;;
            --ssl)
                USE_SSL=true
                shift
                ;;
            --ssl-cert)
                SSL_CERT="$2"
                shift
                shift
                ;;
            --ssl-key)
                SSL_KEY="$2"
                shift
                shift
                ;;
            --env-file)
                ENV_FILE="$2"
                shift
                shift
                ;;
            --no-stateless)
                STATELESS=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                exit 1
                ;;
        esac
    done
}

# 加载环境变量
load_env() {
    if [ -f "${ENV_FILE}" ]; then
        print_message "加载环境变量文件: ${ENV_FILE}"
        source "${ENV_FILE}"
        
        # 如果环境变量文件中有设置，则使用环境变量中的值
        if [ ! -z "${MCP_HOST}" ]; then
            HOST="${MCP_HOST}"
        fi
        
        if [ ! -z "${MCP_PORT}" ]; then
            PORT="${MCP_PORT}"
        fi
        
        if [ ! -z "${MCP_TRANSPORT}" ]; then
            TRANSPORT="${MCP_TRANSPORT}"
        fi
        
        if [ ! -z "${MCP_MOUNT_PATH}" ]; then
            MOUNT_PATH="${MCP_MOUNT_PATH}"
        fi

        if [ ! -z "${MCP_STATELESS}" ]; then
            STATELESS="${MCP_STATELESS}"
        fi
    else
        print_warning "环境变量文件不存在: ${ENV_FILE}"
        print_warning "使用默认配置"
    fi
}

# 设置环境并安装依赖
setup_env() {
    print_message "检查必要的命令..."
    check_command python3
    check_command pip3

    # 创建必要的目录
    print_message "创建必要的目录..."
    mkdir -p "${STATIC_DIR}"
    mkdir -p "${MCP_DIR}/data/logs"
    mkdir -p "${MCP_DIR}/data/klines"
    mkdir -p "${MCP_DIR}/data/temp"
    mkdir -p "${MCP_DIR}/data/config"
    mkdir -p "${MCP_DIR}/data/backtest"
    mkdir -p "${MCP_DIR}/data/templates"
    mkdir -p "logs"

    # 设置Python虚拟环境
    if [ ! -d "${VENV_DIR}" ]; then
        print_message "创建Python虚拟环境..."
        python3 -m venv "${VENV_DIR}"
        print_success "Python虚拟环境创建成功"
    fi

    # 激活虚拟环境并安装依赖
    print_message "安装依赖..."
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "环境设置完成"
}

# 部署MCP服务（创建配置文件）
deploy_service() {
    print_message "部署MCP服务..."
    
    # 检查Nginx是否安装
    if command -v nginx &> /dev/null; then
        # 创建Nginx配置文件
        print_message "创建Nginx配置文件..."
        if [ "$USE_SSL" = true ]; then
            if [ -z "$SSL_CERT" ] || [ -z "$SSL_KEY" ]; then
                print_error "启用SSL时必须提供证书和密钥路径"
                exit 1
            fi
            
            # 创建带SSL的Nginx配置
            cat > "${MCP_DIR}/deploy/nginx.conf" << EOF
server {
    listen 80;
    server_name ${SERVER_NAME};
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name ${SERVER_NAME};

    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_KEY};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    client_max_body_size 100M;

    # MCP API
    location /mcp {
        proxy_pass http://${HOST}:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # 静态文件
    location /static/ {
        alias ${STATIC_DIR}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # 健康检查
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF
        else
            # 创建不带SSL的Nginx配置
            cat > "${MCP_DIR}/deploy/nginx.conf" << EOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    client_max_body_size 100M;

    # MCP API
    location /mcp {
        proxy_pass http://${HOST}:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # 静态文件
    location /static/ {
        alias ${STATIC_DIR}/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # 健康检查
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF
        fi

        print_success "Nginx配置文件创建成功: ${MCP_DIR}/deploy/nginx.conf"
    else
        print_warning "Nginx未安装，跳过Nginx配置创建"
    fi

    # 创建systemd服务文件
    print_message "创建systemd服务文件..."
    
    # 根据传输协议构建启动命令
    if [ "${TRANSPORT}" == "sse" ]; then
        START_CMD="${VENV_DIR}/bin/python server.py --transport sse --host ${HOST} --port ${PORT} --mount-path ${MOUNT_PATH}"
    else
        START_CMD="${VENV_DIR}/bin/python server.py --transport ${TRANSPORT} --host ${HOST} --port ${PORT}"
    fi
    
    # 添加stateless参数
    if [ "${STATELESS}" = true ]; then
        START_CMD="${START_CMD} --stateless"
    fi
    
    cat > "${MCP_DIR}/deploy/mcp.service" << EOF
[Unit]
Description=MCP Service
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=${MCP_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${START_CMD}
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
EOF

    print_success "systemd服务文件创建成功: ${MCP_DIR}/deploy/mcp.service"
    
    print_message "部署准备完成！"
    print_message "请运行 '$0 install' 以安装服务（需要root权限）"
}

# 安装MCP服务到系统
install_service() {
    print_message "安装MCP服务到系统..."
    
    # 检查是否有root权限
    if [ "$(id -u)" != "0" ]; then
        print_error "安装服务需要root权限，请使用sudo运行此命令"
        exit 1
    fi
    
    # 安装Nginx配置
    if [ -f "${MCP_DIR}/deploy/nginx.conf" ]; then
        print_message "安装Nginx配置..."
        cp "${MCP_DIR}/deploy/nginx.conf" "${NGINX_CONF}"
        ln -sf "${NGINX_CONF}" "${NGINX_ENABLED}"
        systemctl restart nginx
        print_success "Nginx配置安装成功"
    else
        print_warning "Nginx配置文件不存在，跳过Nginx配置安装"
    fi
    
    # 安装systemd服务
    if [ -f "${MCP_DIR}/deploy/mcp.service" ]; then
        print_message "安装systemd服务..."
        cp "${MCP_DIR}/deploy/mcp.service" "${SYSTEMD_SERVICE}"
        systemctl daemon-reload
        systemctl enable mcp
        print_success "systemd服务安装成功"
    else
        print_error "systemd服务文件不存在，请先运行 '$0 deploy'"
        exit 1
    fi
    
    print_success "MCP服务安装完成"
    print_message "可以使用 '$0 start' 启动服务"
}

# 启动MCP服务
start_service() {
    print_message "启动MCP服务..."
    print_message "主机: ${HOST}"
    print_message "端口: ${PORT}"
    print_message "传输协议: ${TRANSPORT}"
    
    if [ "${TRANSPORT}" == "sse" ]; then
        print_message "SSE挂载路径: ${MOUNT_PATH}"
    fi
    
    # 检查是否已安装为systemd服务
    if [ -f "${SYSTEMD_SERVICE}" ] && command -v systemctl &> /dev/null; then
        print_message "使用systemd启动服务..."
        systemctl start mcp
        print_success "MCP服务已启动"
    else
        # 激活虚拟环境
        if [ -d "${VENV_DIR}" ]; then
            print_message "激活Python虚拟环境..."
            source "${VENV_DIR}/bin/activate"
        else
            print_error "Python虚拟环境不存在: ${VENV_DIR}"
            print_error "请先运行 '$0 setup' 创建虚拟环境"
            exit 1
        fi
        
        # 设置环境变量
        export MCP_SERVER_HOST="${MCP_SERVER_HOST:-localhost}"
        export MCP_SERVER_PORT="${MCP_SERVER_PORT:-80}"
        export MCP_SERVER_PROTOCOL="${MCP_SERVER_PROTOCOL:-http}"
        
        # 启动服务
        print_message "直接启动MCP服务..."
        
        # 构建启动命令
        if [ "${TRANSPORT}" == "sse" ]; then
            CMD="python server.py --transport sse --host ${HOST} --port ${PORT} --mount-path ${MOUNT_PATH}"
        else
            CMD="python server.py --transport ${TRANSPORT} --host ${HOST} --port ${PORT}"
        fi
        
        # 添加stateless参数
        if [ "${STATELESS}" = true ]; then
            CMD="${CMD} --stateless"
        fi
        
        # 执行命令
        print_message "执行: ${CMD}"
        ${CMD}
    fi
}

# 停止MCP服务
stop_service() {
    print_message "停止MCP服务..."
    
    # 检查是否已安装为systemd服务
    if [ -f "${SYSTEMD_SERVICE}" ] && command -v systemctl &> /dev/null; then
        systemctl stop mcp
        print_success "MCP服务已停止"
    else
        print_warning "MCP服务未安装为systemd服务，尝试查找并终止进程..."
        
        # 查找并终止MCP进程
        PID=$(ps aux | grep "python server.py" | grep -v grep | awk '{print $2}')
        if [ -n "${PID}" ]; then
            kill ${PID}
            print_success "MCP服务已停止 (PID: ${PID})"
        else
            print_warning "未找到运行中的MCP服务进程"
        fi
    fi
}

# 重启MCP服务
restart_service() {
    print_message "重启MCP服务..."
    
    # 检查是否已安装为systemd服务
    if [ -f "${SYSTEMD_SERVICE}" ] && command -v systemctl &> /dev/null; then
        systemctl restart mcp
        print_success "MCP服务已重启"
    else
        stop_service
        start_service
    fi
}

# 查看MCP服务状态
status_service() {
    print_message "查看MCP服务状态..."
    
    # 检查是否已安装为systemd服务
    if [ -f "${SYSTEMD_SERVICE}" ] && command -v systemctl &> /dev/null; then
        systemctl status mcp
    else
        # 查找MCP进程
        PID=$(ps aux | grep "python server.py" | grep -v grep | awk '{print $2}')
        if [ -n "${PID}" ]; then
            print_success "MCP服务正在运行 (PID: ${PID})"
            ps -p ${PID} -o pid,ppid,cmd,%cpu,%mem,etime
        else
            print_warning "MCP服务未运行"
        fi
    fi
}

# 主函数
main() {
    parse_args "$@"
    load_env
    
    case "${COMMAND}" in
        setup)
            setup_env
            ;;
        deploy)
            deploy_service
            ;;
        install)
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            status_service
            ;;
        help)
            show_help
            ;;
        *)
            print_error "未知命令: ${COMMAND}"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
