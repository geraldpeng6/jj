#!/bin/bash

# EC2模式测试脚本
# 此脚本用于在本地macOS环境中模拟EC2环境进行测试

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认参数
TRANSPORT="sse"  # 默认使用SSE传输协议
HOST="0.0.0.0"
PORT=8000
HTML_PORT=8081
MOCK_IP="123.45.67.89"  # 模拟的EC2公网IP

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help                显示此帮助信息"
    echo "  -t, --transport TRANSPORT 指定传输协议 (stdio, sse, streamable-http) (默认: sse)"
    echo "  -H, --host HOST           指定主机地址 (默认: 0.0.0.0)"
    echo "  -p, --port PORT           指定端口号 (默认: 8000)"
    echo "  --html-port PORT          指定HTML服务器端口号 (默认: 8081)"
    echo "  --mock-ip IP              指定模拟的EC2公网IP (默认: 123.45.67.89)"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置测试"
    echo "  $0 --mock-ip 11.22.33.44  # 使用指定的模拟IP测试"
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
        --html-port)
            HTML_PORT="$2"
            shift 2
            ;;
        --mock-ip)
            MOCK_IP="$2"
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

# 检查Nginx是否已安装
check_nginx() {
    echo -e "${YELLOW}检查Nginx是否已安装...${NC}"
    
    if ! command -v nginx &> /dev/null; then
        echo -e "${RED}错误: Nginx未安装，请先安装Nginx${NC}"
        echo -e "${YELLOW}可以使用Homebrew安装: brew install nginx${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Nginx已安装!${NC}"
}

# 创建模拟EC2元数据服务
create_mock_ec2_metadata() {
    echo -e "${YELLOW}创建模拟EC2元数据服务...${NC}"
    
    # 创建临时目录
    mkdir -p mock_ec2
    
    # 创建模拟EC2元数据服务的Python脚本
    cat > mock_ec2/mock_metadata_service.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟EC2元数据服务

此脚本模拟EC2元数据服务，返回指定的公网IP
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# 模拟的EC2公网IP
MOCK_IP = "$MOCK_IP"

class MetadataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/latest/meta-data/public-ipv4":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(MOCK_IP.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        # 禁止输出HTTP请求日志
        pass

def run(server_class=HTTPServer, handler_class=MetadataHandler, port=80):
    server_address = ("127.0.0.1", port)
    httpd = server_class(server_address, handler_class)
    print(f"模拟EC2元数据服务已启动，监听端口: {port}")
    print(f"模拟的EC2公网IP: {MOCK_IP}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("模拟EC2元数据服务已停止")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8169  # 默认端口
    run(port=port)
EOF
    
    # 使脚本可执行
    chmod +x mock_ec2/mock_metadata_service.py
    
    echo -e "${GREEN}模拟EC2元数据服务已创建!${NC}"
}

# 配置HTML服务器
setup_html_server() {
    echo -e "${YELLOW}配置HTML服务器...${NC}"
    
    # 创建配置目录
    mkdir -p data/config
    
    # 创建HTML服务器配置文件
    cat > data/config/html_server.json << EOF
{
    "server_host": "$MOCK_IP",
    "server_port": $HTML_PORT,
    "charts_dir": "data/charts",
    "use_ec2_metadata": false,
    "use_public_ip": false
}
EOF
    
    echo -e "${GREEN}HTML服务器配置文件已创建!${NC}"
}

# 启动模拟EC2元数据服务
start_mock_ec2_metadata() {
    echo -e "${YELLOW}启动模拟EC2元数据服务...${NC}"
    
    # 启动模拟EC2元数据服务
    python mock_ec2/mock_metadata_service.py 8169 &
    MOCK_PID=$!
    
    # 等待服务启动
    sleep 1
    
    echo -e "${GREEN}模拟EC2元数据服务已启动，PID: $MOCK_PID${NC}"
    
    # 保存PID到文件
    echo $MOCK_PID > mock_ec2/mock_pid.txt
}

# 生成测试HTML文件
generate_test_html() {
    echo -e "${YELLOW}生成测试HTML文件...${NC}"
    
    # 设置环境变量
    export MCP_ENV="production"
    export MCP_SERVER_HOST="$MOCK_IP"
    
    # 生成测试HTML文件
    python -c "
import sys
sys.path.append('.')
from utils.html_server import generate_test_html
url = generate_test_html()
print(f'测试HTML文件已生成，URL: {url}')
"
    
    echo -e "${GREEN}测试HTML文件已生成!${NC}"
}

# 配置本地Nginx
setup_local_nginx() {
    echo -e "${YELLOW}配置本地Nginx...${NC}"
    
    # 获取charts目录的绝对路径
    CHARTS_DIR=$(pwd)/data/charts
    
    # 创建Nginx配置文件
    cat > mcp_html_server.conf << EOF
# MCP HTML服务器配置
server {
    listen $HTML_PORT;
    server_name localhost;
    
    # 允许跨域访问
    add_header 'Access-Control-Allow-Origin' '*';
    add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';

    # 禁止访问隐藏文件
    location ~ /\\. {
        deny all;
    }

    # 静态文件服务
    location /charts/ {
        alias $CHARTS_DIR/;

        # 只允许访问HTML文件
        location ~* \\.(html)$ {
            add_header Content-Type text/html;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            # 允许跨域访问
            add_header 'Access-Control-Allow-Origin' '*';
            add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
        }

        # 禁止目录列表
        autoindex off;

        # 禁止访问其他类型的文件
        location ~* \\.(php|py|js|json|txt|log|ini|conf)$ {
            deny all;
        }
    }

    # 默认页面 - 生成一个测试页面
    location = / {
        return 200 '<html><head><title>MCP HTML服务器</title></head><body><h1>MCP HTML服务器</h1><p>服务器运行正常</p><p>当前时间: <span id="time"></span></p><script>document.getElementById("time").textContent = new Date().toLocaleString();</script></body></html>';
        add_header Content-Type text/html;
    }
}
EOF
    
    # 复制配置文件到Nginx配置目录
    sudo cp mcp_html_server.conf /opt/homebrew/etc/nginx/servers/
    
    # 测试Nginx配置
    nginx -t
    
    # 重新加载Nginx
    brew services reload nginx
    
    echo -e "${GREEN}本地Nginx已配置!${NC}"
}

# 启动MCP服务器
start_mcp_server() {
    echo -e "${YELLOW}启动MCP服务器...${NC}"
    
    # 设置环境变量
    export MCP_ENV="production"
    export MCP_SERVER_HOST="$MOCK_IP"
    
    # 启动MCP服务器
    python server.py --transport $TRANSPORT --host $HOST --port $PORT &
    MCP_PID=$!
    
    # 保存PID到文件
    echo $MCP_PID > mock_ec2/mcp_pid.txt
    
    echo -e "${GREEN}MCP服务器已启动，PID: $MCP_PID${NC}"
}

# 显示测试信息
show_test_info() {
    echo -e "${GREEN}EC2模式测试环境已启动!${NC}"
    echo -e "${GREEN}模拟的EC2公网IP: $MOCK_IP${NC}"
    echo -e "${GREEN}MCP服务器地址: http://$HOST:$PORT${NC}"
    if [ "$TRANSPORT" == "sse" ]; then
        echo -e "${GREEN}MCP服务器SSE端点: http://$HOST:$PORT/sse${NC}"
    elif [ "$TRANSPORT" == "streamable-http" ]; then
        echo -e "${GREEN}MCP服务器HTTP端点: http://$HOST:$PORT/mcp${NC}"
    fi
    echo -e "${GREEN}HTML服务器地址: http://localhost:$HTML_PORT${NC}"
    echo -e "${GREEN}测试HTML页面: http://localhost:$HTML_PORT/charts/test.html${NC}"
    echo -e "${YELLOW}注意: 在浏览器中访问时，服务器主机地址会显示为 $MOCK_IP${NC}"
    echo -e "${YELLOW}要停止测试环境，请运行: ./stop_ec2_test.sh${NC}"
}

# 创建停止脚本
create_stop_script() {
    echo -e "${YELLOW}创建停止脚本...${NC}"
    
    # 创建停止脚本
    cat > stop_ec2_test.sh << EOF
#!/bin/bash

# 停止EC2模式测试环境

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止模拟EC2元数据服务
if [ -f "mock_ec2/mock_pid.txt" ]; then
    MOCK_PID=\$(cat mock_ec2/mock_pid.txt)
    echo -e "\${YELLOW}停止模拟EC2元数据服务 (PID: \$MOCK_PID)...\${NC}"
    kill \$MOCK_PID 2>/dev/null || true
    rm mock_ec2/mock_pid.txt
fi

# 停止MCP服务器
if [ -f "mock_ec2/mcp_pid.txt" ]; then
    MCP_PID=\$(cat mock_ec2/mcp_pid.txt)
    echo -e "\${YELLOW}停止MCP服务器 (PID: \$MCP_PID)...\${NC}"
    kill \$MCP_PID 2>/dev/null || true
    rm mock_ec2/mcp_pid.txt
fi

# 删除Nginx配置
echo -e "\${YELLOW}删除Nginx配置...\${NC}"
sudo rm -f /opt/homebrew/etc/nginx/servers/mcp_html_server.conf
brew services reload nginx

# 删除HTML服务器配置
echo -e "\${YELLOW}删除HTML服务器配置...\${NC}"
rm -f data/config/html_server.json

echo -e "\${GREEN}EC2模式测试环境已停止!\${NC}"
EOF
    
    # 使脚本可执行
    chmod +x stop_ec2_test.sh
    
    echo -e "${GREEN}停止脚本已创建!${NC}"
}

# 主函数
main() {
    echo -e "${YELLOW}开始在本地macOS环境中模拟EC2环境进行测试...${NC}"
    
    # 检查Nginx
    check_nginx
    
    # 创建模拟EC2元数据服务
    create_mock_ec2_metadata
    
    # 配置HTML服务器
    setup_html_server
    
    # 启动模拟EC2元数据服务
    start_mock_ec2_metadata
    
    # 生成测试HTML文件
    generate_test_html
    
    # 配置本地Nginx
    setup_local_nginx
    
    # 启动MCP服务器
    start_mcp_server
    
    # 创建停止脚本
    create_stop_script
    
    # 显示测试信息
    show_test_info
}

# 执行主函数
main
