#!/bin/bash

# MCP SSE模式一键部署脚本
# 用于在服务器上部署MCP应用，并确保SSE模式正确配置

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
STATIC_DIR="${MCP_DIR}/data/charts"
NGINX_CONF="/etc/nginx/sites-available/mcp"
NGINX_ENABLED="/etc/nginx/sites-enabled/mcp"
SYSTEMD_SERVICE="/etc/systemd/system/mcp.service"
SERVER_NAME="localhost"  # 默认服务器名称，应该改为实际域名或IP
USE_SSL=false
SSL_CERT=""
SSL_KEY=""

# 解析命令行参数
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
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --host HOST            绑定的主机地址 (默认: 0.0.0.0)"
            echo "  --port PORT            绑定的端口 (默认: 8000)"
            echo "  --workers WORKERS      Gunicorn工作进程数 (默认: 2)"
            echo "  --server-name NAME     Nginx服务器名称 (默认: localhost)"
            echo "  --ssl                  启用SSL"
            echo "  --ssl-cert CERT        SSL证书路径"
            echo "  --ssl-key KEY          SSL密钥路径"
            echo "  --help                 显示此帮助信息"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 检查必要的命令
print_message "检查必要的命令..."
check_command python3
check_command pip3
check_command nginx

# 创建必要的目录
print_message "创建必要的目录..."
mkdir -p "${STATIC_DIR}"
mkdir -p "logs"
mkdir -p "data/logs"
mkdir -p "data/klines"
mkdir -p "data/charts"
mkdir -p "data/temp"
mkdir -p "data/config"
mkdir -p "data/backtest"
mkdir -p "data/templates"

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
pip install gunicorn uvicorn

# 创建或更新.env文件
print_message "配置环境变量..."
cat > ".env" << EOF
# MCP服务器配置
MCP_SERVER_HOST=${SERVER_NAME}
MCP_SERVER_PORT=${PORT}
MCP_SERVER_PROTOCOL=$([ "$USE_SSL" = true ] && echo "https" || echo "http")

# MCP服务配置
MCP_HOST=${HOST}
MCP_PORT=${PORT}
MCP_WORKERS=${WORKERS}

# 传输协议配置 - SSE模式
MCP_TRANSPORT=streamable-http
MCP_STATELESS=true

# 静态文件配置
STATIC_DIR=data/charts

# HTTP头部配置 - 确保支持SSE模式
HTTP_ACCEPT_HEADER="text/event-stream, application/json"

# 响应类型配置 - 确保服务器返回正确的Content-Type
HTTP_CONTENT_TYPE="text/event-stream"
EOF

print_success "环境变量配置完成"

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

    # MCP API - 配置SSE支持
    location /mcp {
        proxy_pass http://${HOST}:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # SSE配置
        proxy_set_header Accept "text/event-stream, application/json";
        proxy_cache off;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
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

    # MCP API - 配置SSE支持
    location /mcp {
        proxy_pass http://${HOST}:${PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # SSE配置
        proxy_set_header Accept "text/event-stream, application/json";
        proxy_cache off;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
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

# 创建systemd服务文件
print_message "创建systemd服务文件..."
cat > "${MCP_DIR}/deploy/mcp.service" << EOF
[Unit]
Description=MCP Service
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=${MCP_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HTTP_ACCEPT_HEADER=text/event-stream, application/json"
Environment="HTTP_CONTENT_TYPE=text/event-stream"
Environment="MCP_TRANSPORT=streamable-http"
Environment="MCP_STATELESS=true"
ExecStart=${VENV_DIR}/bin/python server.py --transport streamable-http --host ${HOST} --port ${PORT} --stateless
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
EOF

print_success "systemd服务文件创建成功: ${MCP_DIR}/deploy/mcp.service"

# 测试HTTP头部配置
print_message "测试HTTP头部配置..."
if command -v python &> /dev/null; then
    if [ -f "deploy/test_headers.py" ]; then
        python deploy/test_headers.py --host localhost --port ${PORT}
        if [ $? -eq 0 ]; then
            print_success "HTTP头部测试成功"
        else
            print_warning "HTTP头部测试失败，请检查配置"
        fi
    else
        print_warning "未找到test_headers.py，跳过HTTP头部测试"
    fi
else
    print_warning "未找到Python，跳过HTTP头部测试"
fi

print_message "部署准备完成！"
print_message "请以root权限运行以下命令完成部署:"
echo "sudo cp ${MCP_DIR}/deploy/nginx.conf ${NGINX_CONF}"
echo "sudo ln -sf ${NGINX_CONF} ${NGINX_ENABLED}"
echo "sudo cp ${MCP_DIR}/deploy/mcp.service ${SYSTEMD_SERVICE}"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable mcp"
echo "sudo systemctl start mcp"
echo "sudo systemctl restart nginx"

print_success "部署脚本执行完成"
