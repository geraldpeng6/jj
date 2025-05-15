#!/bin/bash

# SSE模式配置脚本
# 用于配置MCP服务器的SSE模式，确保数据传输正确

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
MCP_DIR="$(pwd)"
ENV_FILE="${MCP_DIR}/.env"
HOST="0.0.0.0"
PORT="8000"

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
        --env-file)
            ENV_FILE="$2"
            shift
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --host HOST            绑定的主机地址 (默认: 0.0.0.0)"
            echo "  --port PORT            绑定的端口 (默认: 8000)"
            echo "  --env-file FILE        环境变量文件路径 (默认: .env)"
            echo "  --help                 显示此帮助信息"
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 检查环境变量文件
if [ -f "${ENV_FILE}" ]; then
    print_message "加载环境变量文件: ${ENV_FILE}"
    source "${ENV_FILE}"
else
    print_warning "环境变量文件不存在: ${ENV_FILE}"
    print_warning "将创建新的环境变量文件"
    
    # 创建环境变量文件
    cat > "${ENV_FILE}" << EOF
# MCP服务器配置
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8000
MCP_SERVER_PROTOCOL=http

# MCP服务配置
MCP_HOST=${HOST}
MCP_PORT=${PORT}
MCP_WORKERS=2

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
    
    print_success "已创建环境变量文件: ${ENV_FILE}"
fi

# 确保必要的目录存在
print_message "检查必要的目录..."
mkdir -p data/logs
mkdir -p data/klines
mkdir -p data/charts
mkdir -p data/temp
mkdir -p data/config
mkdir -p data/backtest
mkdir -p data/templates

print_success "目录检查完成"

# 检查Python虚拟环境
if [ -d ".venv" ]; then
    print_message "激活Python虚拟环境..."
    source .venv/bin/activate
else
    print_warning "Python虚拟环境不存在，尝试创建..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    print_success "Python虚拟环境创建完成"
fi

# 设置环境变量
export MCP_SERVER_HOST="${MCP_SERVER_HOST:-localhost}"
export MCP_SERVER_PORT="${MCP_SERVER_PORT:-80}"
export MCP_SERVER_PROTOCOL="${MCP_SERVER_PROTOCOL:-http}"
export HTTP_ACCEPT_HEADER="${HTTP_ACCEPT_HEADER:-text/event-stream, application/json}"
export HTTP_CONTENT_TYPE="${HTTP_CONTENT_TYPE:-text/event-stream}"

# 获取传输协议配置
TRANSPORT="${MCP_TRANSPORT:-streamable-http}"
STATELESS="${MCP_STATELESS:-true}"

print_message "配置信息:"
print_message "主机: ${HOST}"
print_message "端口: ${PORT}"
print_message "传输协议: ${TRANSPORT}"
print_message "无状态模式: ${STATELESS}"
print_message "HTTP接受头: ${HTTP_ACCEPT_HEADER}"
print_message "HTTP内容类型: ${HTTP_CONTENT_TYPE}"

# 测试HTTP头部配置
print_message "测试HTTP头部配置..."
if command -v python &> /dev/null; then
    python deploy/test_headers.py --host localhost --port ${PORT}
    if [ $? -eq 0 ]; then
        print_success "HTTP头部测试成功"
    else
        print_warning "HTTP头部测试失败，请检查配置"
    fi
else
    print_warning "未找到Python，跳过HTTP头部测试"
fi

print_success "SSE模式配置完成"
print_message "现在可以使用以下命令启动MCP服务器:"
print_message "python server.py --transport ${TRANSPORT} --host ${HOST} --port ${PORT} $([ "${STATELESS}" == "true" ] && echo "--stateless")"
