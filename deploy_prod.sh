#!/bin/bash
# 量化交易助手MCP服务器生产环境部署脚本
# 使用Gunicorn作为WSGI服务器

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
ENV_FILE=".env"
USE_VENV=true
VENV_PATH=".venv"
INSTALL_DEPS=true
LOG_DIR="logs"
PID_FILE="mcp_server.pid"
DAEMON_MODE=false

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo "命令:"
    echo "  start                     启动服务器"
    echo "  stop                      停止服务器"
    echo "  restart                   重启服务器"
    echo "  status                    查看服务器状态"
    echo ""
    echo "选项:"
    echo "  -h, --help                显示帮助信息"
    echo "  -p, --port PORT           设置HTTP服务器端口 (默认: 8000)"
    echo "  --host HOST               设置HTTP服务器主机地址 (默认: 0.0.0.0)"
    echo "  --env-file FILE           指定环境变量文件 (默认: .env)"
    echo "  --no-venv                 不使用虚拟环境"
    echo "  --venv-path PATH          指定虚拟环境路径 (默认: .venv)"
    echo "  --no-deps                 不安装依赖"
    echo "  --log-dir DIR             指定日志目录 (默认: logs)"
    echo "  --pid-file FILE           指定PID文件 (默认: mcp_server.pid)"
    echo "  --daemon                  以守护进程模式运行"
    echo ""
}

# 解析命令行参数
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|status)
            COMMAND="$1"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
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
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --pid-file)
            PID_FILE="$2"
            shift 2
            ;;
        --daemon)
            DAEMON_MODE=true
            shift
            ;;
        *)
            error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查是否提供了命令
if [ -z "$COMMAND" ]; then
    error "未提供命令"
    show_help
    exit 1
fi

# 检查必要的命令
check_command python3
check_command pip3

# 创建日志目录
mkdir -p $LOG_DIR

# 设置环境变量
export GUNICORN_BIND="${HOST}:${PORT}"
export GUNICORN_ACCESS_LOG="${LOG_DIR}/access.log"
export GUNICORN_ERROR_LOG="${LOG_DIR}/error.log"
export GUNICORN_PID="${PID_FILE}"

if [ "$DAEMON_MODE" = true ]; then
    export GUNICORN_DAEMON="true"
else
    export GUNICORN_DAEMON="false"
fi

# 启动服务器
start_server() {
    info "启动MCP服务器..."
    
    # 创建并激活虚拟环境
    if [ "$USE_VENV" = true ]; then
        if [ ! -d "$VENV_PATH" ]; then
            info "创建虚拟环境: $VENV_PATH"
            python3 -m venv $VENV_PATH
        fi
        
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
    
    # 启动Gunicorn
    info "启动Gunicorn，监听地址: ${HOST}:${PORT}"
    gunicorn -c gunicorn_config.py "server:create_server(stateless_http=True).streamable_http_app()"
    
    if [ $? -ne 0 ]; then
        error "服务器启动失败"
        exit 1
    fi
    
    info "服务器已启动"
}

# 停止服务器
stop_server() {
    info "停止MCP服务器..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            kill $PID
            info "已发送停止信号到进程 $PID"
            sleep 2
            
            if ps -p $PID > /dev/null; then
                warn "进程未响应，尝试强制终止..."
                kill -9 $PID
                sleep 1
            fi
            
            if ! ps -p $PID > /dev/null; then
                info "服务器已停止"
                rm -f $PID_FILE
            else
                error "无法停止服务器"
                exit 1
            fi
        else
            warn "PID文件存在，但进程不存在"
            rm -f $PID_FILE
        fi
    else
        warn "PID文件不存在，服务器可能未运行"
    fi
}

# 重启服务器
restart_server() {
    info "重启MCP服务器..."
    stop_server
    start_server
}

# 查看服务器状态
server_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null; then
            info "服务器正在运行，PID: $PID"
            info "监听地址: ${HOST}:${PORT}"
        else
            warn "PID文件存在，但进程不存在"
        fi
    else
        warn "服务器未运行"
    fi
}

# 执行命令
case $COMMAND in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        server_status
        ;;
esac
