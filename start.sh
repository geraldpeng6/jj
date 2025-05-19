#!/bin/bash

# 一键启动MCP服务器
# 此脚本会自动检查环境，安装依赖，并启动MCP服务器

# 默认参数
TRANSPORT="sse"  # 默认使用SSE传输协议
HOST="0.0.0.0"
PORT=8000

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help                显示此帮助信息"
    echo "  -t, --transport TRANSPORT 指定传输协议 (stdio, sse, streamable-http) (默认: sse)"
    echo "  -H, --host HOST           指定主机地址 (默认: 0.0.0.0)"
    echo "  -p, --port PORT           指定端口号 (默认: 8000)"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置启动 (SSE, 0.0.0.0:8000)"
    echo "  $0 -t stdio               # 使用STDIO传输协议启动"
    echo "  $0 -t streamable-http     # 使用Streamable HTTP传输协议启动"
    echo "  $0 -H 127.0.0.1 -p 9000   # 在127.0.0.1:9000上启动"
    exit 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -t|--transport)
            TRANSPORT="$2"
            shift 2
            ;;
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            show_help
            ;;
    esac
done

# 检查传输协议是否有效
if [[ "$TRANSPORT" != "stdio" && "$TRANSPORT" != "sse" && "$TRANSPORT" != "streamable-http" ]]; then
    echo -e "${RED}错误: 无效的传输协议 '$TRANSPORT'${NC}"
    echo -e "${YELLOW}有效的传输协议: stdio, sse, streamable-http${NC}"
    exit 1
fi

# 检查是否在项目根目录
if [ ! -f "server.py" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 uv 是否已安装
setup_uv() {
    echo -e "${YELLOW}检查 uv 是否已安装...${NC}"

    if ! command -v uv &> /dev/null; then
        echo -e "${YELLOW}uv 未安装，正在安装...${NC}"

        # 安装 uv
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # 添加 uv 到 PATH
        if [[ ":$PATH:" != *":$HOME/.cargo/bin:"* ]]; then
            export PATH="$HOME/.cargo/bin:$PATH"
        fi

        echo -e "${GREEN}uv 安装完成!${NC}"
    else
        echo -e "${GREEN}uv 已安装!${NC}"
    fi
}

# 设置虚拟环境
setup_venv() {
    echo -e "${YELLOW}检查虚拟环境...${NC}"

    # 检查虚拟环境是否存在
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
        uv venv .venv
    else
        echo -e "${GREEN}虚拟环境已存在!${NC}"
    fi

    # 激活虚拟环境
    echo -e "${YELLOW}激活虚拟环境...${NC}"
    source .venv/bin/activate

    # 检查依赖是否已安装
    echo -e "${YELLOW}检查依赖...${NC}"
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}安装依赖...${NC}"
        uv pip install -r requirements.txt
    else
        echo -e "${YELLOW}未找到 requirements.txt，尝试安装基本依赖...${NC}"
        uv pip install mcp
    fi

    echo -e "${GREEN}环境设置完成!${NC}"
}

# 主函数
main() {
    echo -e "${YELLOW}准备启动MCP服务器，使用 $TRANSPORT 传输协议...${NC}"

    # 设置环境
    setup_uv
    setup_venv

    # 确保必要的目录存在
    mkdir -p data/logs data/klines data/charts data/temp data/config data/backtest data/templates

    # 根据传输协议选择不同的启动方式
    if [ "$TRANSPORT" == "stdio" ]; then
        echo -e "${GREEN}启动MCP服务器，使用STDIO传输协议${NC}"
        python server.py --transport stdio
    elif [ "$TRANSPORT" == "sse" ]; then
        echo -e "${GREEN}启动MCP服务器，使用SSE传输协议，地址: http://$HOST:$PORT/sse${NC}"
        python server.py --transport sse --host "$HOST" --port "$PORT"
    elif [ "$TRANSPORT" == "streamable-http" ]; then
        echo -e "${GREEN}启动MCP服务器，使用Streamable HTTP传输协议，地址: http://$HOST:$PORT/mcp${NC}"
        python server.py --transport streamable-http --host "$HOST" --port "$PORT"
    fi
}

# 执行主函数
main
