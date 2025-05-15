#!/bin/bash
# 量化交易助手MCP服务器部署脚本
# 用于在云服务器上部署MCP服务器

# 显示彩色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 默认配置
PORT=8000
HOST="0.0.0.0"
TRANSPORT="streamable-http"
STATELESS=true
ENV_FILE=".env"
USE_VENV=true
VENV_PATH=".venv"
INSTALL_DEPS=true

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help                显示帮助信息"
    echo "  -t, --transport TRANSPORT 传输协议: stdio或streamable-http (默认: streamable-http)"
    echo "  -p, --port PORT           设置HTTP服务器端口 (默认: 8000)"
    echo "  --host HOST               设置HTTP服务器主机地址 (默认: 0.0.0.0)"
    echo "  --stateless               使用无状态HTTP模式 (推荐用于云服务器部署)"
    echo "  --env-file FILE           指定环境变量文件 (默认: .env)"
    echo "  --no-venv                 不使用虚拟环境"
    echo "  --venv-path PATH          指定虚拟环境路径 (默认: .venv)"
    echo "  --no-deps                 不安装依赖"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--transport)
            TRANSPORT="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --stateless)
            STATELESS=true
            shift
            ;;
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --venv-path)
            VENV_PATH="$2"
            shift 2
            ;;
        --no-deps)
            INSTALL_DEPS=false
            shift
            ;;
        *)
            error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必要的命令
check_command python3
check_command pip3

# 创建并激活虚拟环境
if [ "$USE_VENV" = true ]; then
    info "创建虚拟环境: $VENV_PATH"
    python3 -m venv $VENV_PATH

    info "激活虚拟环境"
    source $VENV_PATH/bin/activate

    # 检查是否成功激活
    if [ -z "$VIRTUAL_ENV" ]; then
        error "虚拟环境激活失败"
        exit 1
    fi

    info "已激活虚拟环境: $VIRTUAL_ENV"
fi

# 安装依赖
if [ "$INSTALL_DEPS" = true ]; then
    info "安装依赖"
    pip3 install -r requirements.txt

    if [ $? -ne 0 ]; then
        error "依赖安装失败"
        exit 1
    fi

    info "依赖安装成功"
fi

# 检查环境变量文件
if [ -f "$ENV_FILE" ]; then
    info "加载环境变量: $ENV_FILE"
    set -a
    source $ENV_FILE
    set +a
else
    warn "环境变量文件不存在: $ENV_FILE"
fi

# 构建启动命令
CMD="python3 server.py --transport $TRANSPORT --host $HOST --port $PORT"

if [ "$STATELESS" = true ]; then
    CMD="$CMD --stateless"
    info "使用无状态HTTP模式 (推荐用于云服务器部署)"
fi

# 准备启动MCP服务器

# 启动MCP服务器
info "启动MCP服务器: $CMD"
info "服务器将在 $HOST:$PORT 上监听"
eval $CMD
