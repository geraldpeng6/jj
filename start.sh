#!/bin/bash

# 一键启动MCP服务器
# 此脚本会自动检查环境，安装依赖，并启动MCP服务器

# 默认参数
TRANSPORT="sse"  # 默认使用SSE传输协议
HOST="0.0.0.0"
PORT=8000
SETUP_NGINX=false  # 默认不配置Nginx
SERVER_MODE=false  # 默认不启用服务器模式
SERVER_HOST=""     # 服务器主机地址，默认为空（自动检测）
SERVER_PORT=80     # 服务器端口，默认为80
NGINX_USER="www-data"  # Nginx用户，Ubuntu默认为www-data，CentOS默认为nginx

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
    echo "  -n, --nginx               配置Nginx服务器"
    echo "  -s, --server-mode         启用服务器模式"
    echo "  --server-host HOST        指定服务器主机地址 (默认: 自动检测)"
    echo "  --server-port PORT        指定服务器端口 (默认: 80)"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置启动 (SSE, 0.0.0.0:8000)"
    echo "  $0 -t stdio               # 使用STDIO传输协议启动"
    echo "  $0 -t streamable-http     # 使用Streamable HTTP传输协议启动"
    echo "  $0 -H 127.0.0.1 -p 9000   # 在127.0.0.1:9000上启动"
    echo "  $0 -n                     # 配置Nginx服务器并启动"
    echo "  $0 -s                     # 启用服务器模式并启动"
    echo "  $0 -n -s --server-host example.com --server-port 443  # 完整配置"
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
        -n|--nginx)
            SETUP_NGINX=true
            shift
            ;;
        -s|--server-mode)
            SERVER_MODE=true
            shift
            ;;
        --server-host)
            SERVER_HOST="$2"
            shift 2
            ;;
        --server-port)
            SERVER_PORT="$2"
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

# 检测服务器环境
detect_server() {
    echo -e "${YELLOW}检测服务器环境...${NC}"

    # 如果没有指定服务器主机，尝试自动检测
    if [ -z "$SERVER_HOST" ]; then
        # 尝试获取公网IP
        PUBLIC_IP=$(curl -s https://api.ipify.org || curl -s https://ifconfig.me || curl -s https://icanhazip.com)

        if [ -n "$PUBLIC_IP" ]; then
            SERVER_HOST="$PUBLIC_IP"
            echo -e "${GREEN}检测到公网IP: $SERVER_HOST${NC}"
        else
            # 如果无法获取公网IP，尝试获取本地IP
            LOCAL_IP=$(hostname -I | awk '{print $1}')
            if [ -n "$LOCAL_IP" ]; then
                SERVER_HOST="$LOCAL_IP"
                echo -e "${YELLOW}无法获取公网IP，使用本地IP: $SERVER_HOST${NC}"
            else
                SERVER_HOST="localhost"
                echo -e "${YELLOW}无法获取IP地址，使用默认值: $SERVER_HOST${NC}"
            fi
        fi
    fi

    # 检测操作系统类型
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        echo -e "${GREEN}检测到操作系统: $OS${NC}"

        # 根据操作系统设置Nginx用户
        if [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
            NGINX_USER="nginx"
        elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
            NGINX_USER="www-data"
        fi
    else
        echo -e "${YELLOW}无法检测操作系统类型，使用默认Nginx用户: $NGINX_USER${NC}"
    fi
}

# 配置服务器模式
setup_server_mode() {
    echo -e "${YELLOW}配置服务器模式...${NC}"

    # 创建服务器配置文件
    SERVER_CONFIG_FILE="data/config/server.json"

    # 检查是否已存在配置文件
    if [ -f "$SERVER_CONFIG_FILE" ]; then
        echo -e "${YELLOW}服务器配置文件已存在，将被覆盖...${NC}"
    fi

    # 创建配置文件
    cat > "$SERVER_CONFIG_FILE" << EOF
{
  "enabled": true,
  "host": "$SERVER_HOST",
  "port": $SERVER_PORT,
  "base_url": "",
  "charts_dir": "data/charts",
  "use_https": false
}
EOF

    echo -e "${GREEN}服务器配置文件已创建: $SERVER_CONFIG_FILE${NC}"
    echo -e "${GREEN}服务器地址: http://$SERVER_HOST:$SERVER_PORT${NC}"
}

# 配置Nginx
setup_nginx() {
    echo -e "${YELLOW}配置Nginx...${NC}"

    # 检查Nginx是否已安装
    if ! command -v nginx &> /dev/null; then
        echo -e "${RED}Nginx未安装，请先安装Nginx${NC}"
        echo -e "${YELLOW}可以使用以下命令安装Nginx:${NC}"
        echo -e "${YELLOW}Ubuntu/Debian: sudo apt update && sudo apt install -y nginx${NC}"
        echo -e "${YELLOW}CentOS/RHEL: sudo yum install -y epel-release && sudo yum install -y nginx${NC}"
        return 1
    fi

    # 获取当前目录的绝对路径
    CURRENT_DIR=$(pwd)
    CHARTS_DIR="$CURRENT_DIR/data/charts"

    # 创建Nginx配置文件
    NGINX_CONFIG_FILE="data/config/nginx.conf"

    # 生成Nginx配置
    cat > "$NGINX_CONFIG_FILE" << EOF
# Nginx配置文件 - 为量化交易助手提供HTML文件服务
# 将此文件放置在 /etc/nginx/conf.d/ 目录下，然后重启Nginx

server {
    listen $SERVER_PORT;
    server_name _;  # 匹配所有域名

    # 日志配置
    access_log /var/log/nginx/quant_mcp_access.log;
    error_log /var/log/nginx/quant_mcp_error.log;

    # 只允许访问HTML文件
    location / {
        root $CHARTS_DIR;

        # 只允许访问HTML文件
        location ~* \\.html$ {
            # 设置MIME类型
            types {
                text/html html;
            }

            # 添加安全头
            add_header X-Content-Type-Options "nosniff";
            add_header X-XSS-Protection "1; mode=block";
            add_header X-Frame-Options "SAMEORIGIN";

            # 禁用目录列表
            autoindex off;
        }

        # 拒绝访问其他文件
        location ~ \\. {
            deny all;
        }

        # 禁用目录列表
        autoindex off;

        # 默认返回403
        return 403;
    }
}
EOF

    echo -e "${GREEN}Nginx配置文件已生成: $NGINX_CONFIG_FILE${NC}"

    # 尝试复制配置文件到Nginx目录
    if [ -d "/etc/nginx/conf.d" ]; then
        echo -e "${YELLOW}尝试复制配置文件到Nginx目录...${NC}"
        if sudo cp "$NGINX_CONFIG_FILE" /etc/nginx/conf.d/quant_mcp.conf; then
            echo -e "${GREEN}配置文件已复制到: /etc/nginx/conf.d/quant_mcp.conf${NC}"

            # 设置charts目录权限
            echo -e "${YELLOW}设置charts目录权限...${NC}"
            sudo chown -R $NGINX_USER:$NGINX_USER "$CHARTS_DIR"
            sudo chmod -R 755 "$CHARTS_DIR"

            # 测试Nginx配置
            echo -e "${YELLOW}测试Nginx配置...${NC}"
            if sudo nginx -t; then
                echo -e "${GREEN}Nginx配置测试通过${NC}"

                # 重启Nginx
                echo -e "${YELLOW}重启Nginx...${NC}"
                if sudo systemctl restart nginx; then
                    echo -e "${GREEN}Nginx已重启${NC}"
                else
                    echo -e "${RED}Nginx重启失败${NC}"
                    return 1
                fi
            else
                echo -e "${RED}Nginx配置测试失败${NC}"
                return 1
            fi
        else
            echo -e "${RED}无法复制配置文件到Nginx目录，可能需要sudo权限${NC}"
            echo -e "${YELLOW}请手动复制配置文件:${NC}"
            echo -e "${YELLOW}sudo cp $NGINX_CONFIG_FILE /etc/nginx/conf.d/quant_mcp.conf${NC}"
            echo -e "${YELLOW}sudo chown -R $NGINX_USER:$NGINX_USER $CHARTS_DIR${NC}"
            echo -e "${YELLOW}sudo chmod -R 755 $CHARTS_DIR${NC}"
            echo -e "${YELLOW}sudo nginx -t && sudo systemctl restart nginx${NC}"
            return 1
        fi
    else
        echo -e "${RED}找不到Nginx配置目录: /etc/nginx/conf.d${NC}"
        echo -e "${YELLOW}请手动复制配置文件到适当的Nginx配置目录${NC}"
        return 1
    fi

    echo -e "${GREEN}Nginx配置完成!${NC}"
    return 0
}

# 主函数
main() {
    echo -e "${YELLOW}准备启动MCP服务器，使用 $TRANSPORT 传输协议...${NC}"

    # 设置环境
    setup_uv
    setup_venv

    # 确保必要的目录存在
    mkdir -p data/logs data/klines data/charts data/temp data/config data/backtest data/templates

    # 如果启用了服务器模式，配置服务器
    if [ "$SERVER_MODE" = true ]; then
        # 检测服务器环境
        detect_server

        # 配置服务器模式
        setup_server_mode

        echo -e "${GREEN}服务器模式已启用，HTML文件将通过 http://$SERVER_HOST:$SERVER_PORT 访问${NC}"
    fi

    # 如果需要配置Nginx，执行配置
    if [ "$SETUP_NGINX" = true ]; then
        # 如果没有启用服务器模式，先检测服务器环境
        if [ "$SERVER_MODE" != true ]; then
            detect_server
        fi

        # 配置Nginx
        setup_nginx
    fi

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

    # 如果启用了服务器模式，显示访问信息
    if [ "$SERVER_MODE" = true ]; then
        echo -e "${GREEN}HTML文件可通过以下地址访问: http://$SERVER_HOST:$SERVER_PORT/文件名.html${NC}"
    fi
}

# 执行主函数
main
