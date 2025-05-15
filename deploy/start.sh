#!/bin/bash

# MCP启动脚本
# 用于在服务器上启动MCP服务

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
VENV_DIR="${MCP_DIR}/.venv"
HOST="0.0.0.0"
PORT="8000"
ENV_FILE="${MCP_DIR}/deploy/.env"

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
            echo "  --env-file FILE        环境变量文件路径 (默认: deploy/.env)"
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

    # 如果环境变量文件中有设置，则使用环境变量中的值
    if [ ! -z "${MCP_HOST}" ]; then
        HOST="${MCP_HOST}"
    fi

    if [ ! -z "${MCP_PORT}" ]; then
        PORT="${MCP_PORT}"
    fi
else
    print_warning "环境变量文件不存在: ${ENV_FILE}"
    print_warning "使用默认配置"
fi

# 激活虚拟环境
if [ -d "${VENV_DIR}" ]; then
    print_message "激活Python虚拟环境..."
    source "${VENV_DIR}/bin/activate"
else
    print_error "Python虚拟环境不存在: ${VENV_DIR}"
    print_error "请先运行 deploy.sh 脚本创建虚拟环境"
    exit 1
fi

# 启动MCP服务
print_message "启动MCP服务..."
print_message "主机: ${HOST}"
print_message "端口: ${PORT}"

# 设置环境变量
export MCP_SERVER_HOST="${MCP_SERVER_HOST:-localhost}"
export MCP_SERVER_PORT="${MCP_SERVER_PORT:-80}"
export MCP_SERVER_PROTOCOL="${MCP_SERVER_PROTOCOL:-http}"
export HTTP_ACCEPT_HEADER="${HTTP_ACCEPT_HEADER:-application/json, text/event-stream}"

# 获取传输协议配置
TRANSPORT="${MCP_TRANSPORT:-streamable-http}"
STATELESS="${MCP_STATELESS:-true}"

print_message "传输协议: ${TRANSPORT}"
print_message "无状态模式: ${STATELESS}"
print_message "HTTP接受头: ${HTTP_ACCEPT_HEADER}"

# 启动服务
python server.py --transport "${TRANSPORT}" --host "${HOST}" --port "${PORT}" $([ "${STATELESS}" == "true" ] && echo "--stateless")

print_success "MCP服务已启动"
