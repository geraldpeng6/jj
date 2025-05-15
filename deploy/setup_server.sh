#!/bin/bash

# MCP项目一键配置脚本
# 用于在Ubuntu服务器上自动配置和部署MCP项目
# 使用方法: sudo bash setup_server.sh [选项]

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

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    print_error "请以root权限运行此脚本: sudo bash $0"
    exit 1
fi

# 默认配置
SERVER_IP=$(hostname -I | awk '{print $1}')
SERVER_DOMAIN=""
SERVER_PORT=80
USE_SSL=false
SSL_EMAIL=""
PROJECT_DIR=$(pwd)
USERNAME=$(logname)
USERGROUP=$(id -gn $USERNAME)

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --domain)
            SERVER_DOMAIN="$2"
            shift
            shift
            ;;
        --ip)
            SERVER_IP="$2"
            shift
            shift
            ;;
        --port)
            SERVER_PORT="$2"
            shift
            shift
            ;;
        --ssl)
            USE_SSL=true
            shift
            ;;
        --ssl-email)
            SSL_EMAIL="$2"
            shift
            shift
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift
            shift
            ;;
        --help)
            echo "用法: sudo bash $0 [选项]"
            echo "选项:"
            echo "  --domain DOMAIN      服务器域名 (如果有)"
            echo "  --ip IP              服务器IP地址 (默认: 自动检测)"
            echo "  --port PORT          HTTP端口 (默认: 80)"
            echo "  --ssl                启用SSL/HTTPS"
            echo "  --ssl-email EMAIL    用于Let's Encrypt的邮箱地址"
            echo "  --project-dir DIR    项目目录 (默认: 当前目录)"
            echo "  --help               显示此帮助信息"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 如果没有指定域名，使用IP地址
if [ -z "$SERVER_DOMAIN" ]; then
    SERVER_HOST=$SERVER_IP
else
    SERVER_HOST=$SERVER_DOMAIN
fi

# 如果启用SSL但没有指定域名，报错
if [ "$USE_SSL" = true ] && [ -z "$SERVER_DOMAIN" ]; then
    print_error "启用SSL需要指定域名，请使用 --domain 选项"
    exit 1
fi

# 如果启用SSL但没有指定邮箱，报错
if [ "$USE_SSL" = true ] && [ -z "$SSL_EMAIL" ]; then
    print_error "启用SSL需要指定邮箱地址，请使用 --ssl-email 选项"
    exit 1
fi

# 显示配置信息
print_message "配置信息:"
echo "服务器主机: $SERVER_HOST"
echo "HTTP端口: $SERVER_PORT"
echo "启用SSL: $USE_SSL"
if [ "$USE_SSL" = true ]; then
    echo "SSL邮箱: $SSL_EMAIL"
fi
echo "项目目录: $PROJECT_DIR"
echo "用户: $USERNAME"
echo "用户组: $USERGROUP"

# 确认继续
read -p "是否继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_message "已取消"
    exit 0
fi

# 更新系统并安装依赖
print_message "更新系统并安装依赖..."
apt update
apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx curl

# 如果启用SSL，安装certbot
if [ "$USE_SSL" = true ]; then
    print_message "安装certbot..."
    apt install -y certbot python3-certbot-nginx
fi

# 确保项目目录存在
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 导航到项目目录
cd "$PROJECT_DIR"

# 确保deploy目录存在
if [ ! -d "deploy" ]; then
    print_error "deploy目录不存在，请确保您在项目根目录运行此脚本"
    exit 1
fi

# 创建虚拟环境
print_message "创建虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_success "虚拟环境创建成功"
else
    print_warning "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境并安装依赖
print_message "安装依赖..."
source .venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_warning "requirements.txt不存在，跳过安装项目依赖"
fi
pip install gunicorn uvicorn

# 创建环境配置文件
print_message "创建环境配置文件..."
if [ -f "deploy/.env.example" ]; then
    cp deploy/.env.example deploy/.env

    # 设置服务器URL和SSE配置
    if [ "$USE_SSL" = true ]; then
        sed -i "s|MCP_SERVER_HOST=.*|MCP_SERVER_HOST=$SERVER_HOST|g" deploy/.env
        sed -i "s|MCP_SERVER_PORT=.*|MCP_SERVER_PORT=443|g" deploy/.env
        sed -i "s|MCP_SERVER_PROTOCOL=.*|MCP_SERVER_PROTOCOL=https|g" deploy/.env
    else
        sed -i "s|MCP_SERVER_HOST=.*|MCP_SERVER_HOST=$SERVER_HOST|g" deploy/.env
        sed -i "s|MCP_SERVER_PORT=.*|MCP_SERVER_PORT=$SERVER_PORT|g" deploy/.env
        sed -i "s|MCP_SERVER_PROTOCOL=.*|MCP_SERVER_PROTOCOL=http|g" deploy/.env
    fi

    # 确保SSE模式配置正确
    if grep -q "HTTP_ACCEPT_HEADER" deploy/.env; then
        sed -i "s|HTTP_ACCEPT_HEADER=.*|HTTP_ACCEPT_HEADER=\"text/event-stream, application/json\"|g" deploy/.env
    else
        echo "HTTP_ACCEPT_HEADER=\"text/event-stream, application/json\"" >> deploy/.env
    fi

    if grep -q "HTTP_CONTENT_TYPE" deploy/.env; then
        sed -i "s|HTTP_CONTENT_TYPE=.*|HTTP_CONTENT_TYPE=\"text/event-stream\"|g" deploy/.env
    else
        echo "HTTP_CONTENT_TYPE=\"text/event-stream\"" >> deploy/.env
    fi

    if grep -q "MCP_TRANSPORT" deploy/.env; then
        sed -i "s|MCP_TRANSPORT=.*|MCP_TRANSPORT=streamable-http|g" deploy/.env
    else
        echo "MCP_TRANSPORT=streamable-http" >> deploy/.env
    fi

    if grep -q "MCP_STATELESS" deploy/.env; then
        sed -i "s|MCP_STATELESS=.*|MCP_STATELESS=true|g" deploy/.env
    else
        echo "MCP_STATELESS=true" >> deploy/.env
    fi

    print_success "环境配置文件创建成功"
else
    print_warning "deploy/.env.example不存在，跳过创建环境配置文件"
fi

# 修改静态文件服务模块
print_message "修改静态文件服务模块..."
if [ -f "utils/static_server.py" ]; then
    # 备份原文件
    cp utils/static_server.py utils/static_server.py.bak

    # 修改URL生成逻辑
    sed -i 's|url = f"file://{os.path.abspath(file_path)}"|server_url = get_server_url()\nurl = f"{server_url}/static/{rel_path}"|g' utils/static_server.py

    print_success "静态文件服务模块修改成功"
else
    print_warning "utils/static_server.py不存在，跳过修改静态文件服务模块"
fi

# 创建必要的目录
print_message "创建必要的目录..."
mkdir -p data/charts/klines data/charts/backtests logs
chown -R $USERNAME:$USERGROUP data logs

# 创建Nginx配置文件
print_message "创建Nginx配置文件..."
cat > /etc/nginx/sites-available/mcp << EOF
server {
    listen $SERVER_PORT;
    server_name $SERVER_HOST;

    client_max_body_size 100M;

    # MCP API - 配置SSE支持
    location /mcp {
        proxy_pass http://127.0.0.1:8000;
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
        alias $PROJECT_DIR/data/charts/;
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

# 启用Nginx配置
ln -sf /etc/nginx/sites-available/mcp /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
print_success "Nginx配置成功"

# 如果启用SSL，配置SSL
if [ "$USE_SSL" = true ]; then
    print_message "配置SSL..."
    certbot --nginx -d $SERVER_DOMAIN --non-interactive --agree-tos -m $SSL_EMAIL
    print_success "SSL配置成功"
fi

# 创建systemd服务文件
print_message "创建systemd服务文件..."
cat > /etc/systemd/system/mcp.service << EOF
[Unit]
Description=MCP Service
After=network.target

[Service]
User=$USERNAME
Group=$USERGROUP
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="HTTP_ACCEPT_HEADER=text/event-stream, application/json"
Environment="HTTP_CONTENT_TYPE=text/event-stream"
Environment="MCP_TRANSPORT=streamable-http"
Environment="MCP_STATELESS=true"
ExecStart=$PROJECT_DIR/.venv/bin/python server.py --transport streamable-http --host 0.0.0.0 --port 8000 --stateless
Restart=always
RestartSec=5
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
systemctl daemon-reload
systemctl enable mcp
systemctl start mcp
print_success "MCP服务启动成功"

# 配置防火墙
print_message "配置防火墙..."
if command -v ufw > /dev/null; then
    ufw allow $SERVER_PORT/tcp
    if [ "$USE_SSL" = true ]; then
        ufw allow 443/tcp
    fi
    ufw allow 22/tcp  # SSH

    # 如果防火墙未启用，启用它
    if ! ufw status | grep -q "Status: active"; then
        print_warning "防火墙未启用，正在启用..."
        echo "y" | ufw enable
    fi

    print_success "防火墙配置成功"
else
    print_warning "未找到ufw，跳过防火墙配置"
fi

# 显示配置信息
print_success "MCP项目配置完成！"
echo
echo "服务器信息:"
echo "============================================"
echo "MCP API URL: http$([ "$USE_SSL" = true ] && echo "s")://$SERVER_HOST/mcp"
echo "静态文件URL: http$([ "$USE_SSL" = true ] && echo "s")://$SERVER_HOST/static/"
echo "健康检查URL: http$([ "$USE_SSL" = true ] && echo "s")://$SERVER_HOST/health"
echo
echo "VSCode配置:"
echo "============================================"
echo '{
    "mcpServers": {
        "量化交易助手": {
            "url": "http'"$([ "$USE_SSL" = true ] && echo "s")"'://'$SERVER_HOST'/mcp",
            "transportType": "streamable_http"
        }
    }
}'
echo
echo "服务管理命令:"
echo "============================================"
echo "查看服务状态: sudo systemctl status mcp"
echo "重启服务: sudo systemctl restart mcp"
echo "停止服务: sudo systemctl stop mcp"
echo "查看日志: sudo journalctl -u mcp.service"
echo
echo "测试命令:"
echo "============================================"
echo "测试MCP服务: curl http://localhost:8000/health"
echo "测试Nginx代理: curl http$([ "$USE_SSL" = true ] && echo "s")://$SERVER_HOST/health"
echo "测试K线图生成: cd $PROJECT_DIR && source .venv/bin/activate && python -c \"from src.tools.kline_tools import get_kline_data; import asyncio; result = asyncio.run(get_kline_data('600000', 'XSHG', http_mode=True)); print(result)\""
