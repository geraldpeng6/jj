#!/bin/bash

# MCP SSE模式一键部署脚本
# 用于快速部署MCP并配置SSE模式

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

# 默认配置
HOST="0.0.0.0"
PORT="8000"
SERVER_NAME="localhost"
USE_SSL=false

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
        --server-name)
            SERVER_NAME="$2"
            shift
            shift
            ;;
        --ssl)
            USE_SSL=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --host HOST            绑定的主机地址 (默认: 0.0.0.0)"
            echo "  --port PORT            绑定的端口 (默认: 8000)"
            echo "  --server-name NAME     服务器名称 (默认: localhost)"
            echo "  --ssl                  启用SSL"
            echo "  --help                 显示此帮助信息"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 显示配置信息
print_message "配置信息:"
echo "主机: $HOST"
echo "端口: $PORT"
echo "服务器名称: $SERVER_NAME"
echo "启用SSL: $USE_SSL"

# 确认继续
read -p "是否继续? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_message "已取消"
    exit 0
fi

# 步骤1: 配置SSE模式
print_message "步骤1: 配置SSE模式..."
./configure_sse.sh --host $HOST --port $PORT
print_success "SSE模式配置完成"

# 步骤2: 部署MCP
print_message "步骤2: 部署MCP..."
./deploy/deploy_sse.sh --host $HOST --port $PORT --server-name $SERVER_NAME $([ "$USE_SSL" = true ] && echo "--ssl")
print_success "MCP部署完成"

# 步骤3: 测试SSE配置
print_message "步骤3: 测试SSE配置..."
python test_sse.py --host localhost --port $PORT
print_success "SSE配置测试完成"

print_success "MCP SSE模式部署完成！"
print_message "现在可以使用以下命令启动MCP服务器:"
print_message "python server.py --transport streamable-http --host $HOST --port $PORT --stateless"
print_message "或者使用systemd服务:"
print_message "sudo systemctl start mcp"
