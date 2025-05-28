#!/bin/bash

# EC2部署脚本
# 此脚本用于在EC2实例上部署MCP服务器

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

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help                显示此帮助信息"
    echo "  -t, --transport TRANSPORT 指定传输协议 (stdio, sse, streamable-http) (默认: sse)"
    echo "  -H, --host HOST           指定主机地址 (默认: 0.0.0.0)"
    echo "  -p, --port PORT           指定端口号 (默认: 8000)"
    echo "  --html-port PORT          指定HTML服务器端口号 (默认: 8081)"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置部署 (SSE, 0.0.0.0:8000)"
    echo "  $0 -t streamable-http     # 使用Streamable HTTP传输协议部署"
    echo "  $0 -p 9000 --html-port 9001   # 在端口9000上部署MCP服务器，在端口9001上部署HTML服务器"
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

# 安装系统依赖
install_system_deps() {
    echo -e "${YELLOW}安装系统依赖...${NC}"
    
    # 更新包列表
    sudo apt-get update
    
    # 安装Python和pip
    sudo apt-get install -y python3 python3-pip python3-venv
    
    # 安装Nginx
    sudo apt-get install -y nginx
    
    # 安装其他依赖
    sudo apt-get install -y curl git
    
    echo -e "${GREEN}系统依赖安装完成!${NC}"
}

# 设置虚拟环境
setup_venv() {
    echo -e "${YELLOW}设置Python虚拟环境...${NC}"
    
    # 创建虚拟环境
    python3 -m venv .venv
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 安装依赖
    pip install -r requirements.txt
    
    echo -e "${GREEN}Python虚拟环境设置完成!${NC}"
}

# 修复MCP库绑定问题
fix_mcp_binding() {
    echo -e "${YELLOW}直接修改MCP库文件修复绑定问题...${NC}"
    
    # 获取虚拟环境路径
    VENV_PATH=".venv"
    MCP_PATH=$(find $VENV_PATH -path "*/site-packages/mcp" -type d | head -n 1)
    
    if [ -z "$MCP_PATH" ]; then
        echo -e "${RED}未找到MCP库路径!${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}找到MCP库路径: $MCP_PATH${NC}"
    
    # 修改SSE服务器文件
    SSE_FILE=$(find $MCP_PATH -name "sse.py" -type f | head -n 1)
    if [ -n "$SSE_FILE" ]; then
        echo -e "${YELLOW}修改SSE服务器文件: $SSE_FILE${NC}"
        
        # 备份原始文件
        cp $SSE_FILE ${SSE_FILE}.bak
        
        # 修改host绑定
        sed -i 's/host="127.0.0.1"/host="0.0.0.0"/g' $SSE_FILE
        sed -i 's/host = "127.0.0.1"/host = "0.0.0.0"/g' $SSE_FILE
        sed -i 's/host: str = "127.0.0.1"/host: str = "0.0.0.0"/g' $SSE_FILE
        
        echo -e "${GREEN}SSE服务器文件已修改!${NC}"
    else
        echo -e "${YELLOW}未找到SSE服务器文件!${NC}"
    fi
    
    # 修改HTTP服务器文件
    HTTP_FILE=$(find $MCP_PATH -name "http.py" -type f | head -n 1)
    if [ -n "$HTTP_FILE" ]; then
        echo -e "${YELLOW}修改HTTP服务器文件: $HTTP_FILE${NC}"
        
        # 备份原始文件
        cp $HTTP_FILE ${HTTP_FILE}.bak
        
        # 修改host绑定
        sed -i 's/host="127.0.0.1"/host="0.0.0.0"/g' $HTTP_FILE
        sed -i 's/host = "127.0.0.1"/host = "0.0.0.0"/g' $HTTP_FILE
        sed -i 's/host: str = "127.0.0.1"/host: str = "0.0.0.0"/g' $HTTP_FILE
        
        echo -e "${GREEN}HTTP服务器文件已修改!${NC}"
    else
        echo -e "${YELLOW}未找到HTTP服务器文件!${NC}"
    fi
    
    # 修改fastmcp文件
    FASTMCP_FILE=$(find $MCP_PATH -name "fastmcp.py" -type f | head -n 1)
    if [ -n "$FASTMCP_FILE" ]; then
        echo -e "${YELLOW}修改FastMCP文件: $FASTMCP_FILE${NC}"
        
        # 备份原始文件
        cp $FASTMCP_FILE ${FASTMCP_FILE}.bak
        
        # 修改host绑定
        sed -i 's/host="127.0.0.1"/host="0.0.0.0"/g' $FASTMCP_FILE
        sed -i 's/host = "127.0.0.1"/host = "0.0.0.0"/g' $FASTMCP_FILE
        sed -i 's/host: str = "127.0.0.1"/host: str = "0.0.0.0"/g' $FASTMCP_FILE
        
        echo -e "${GREEN}FastMCP文件已修改!${NC}"
    else
        echo -e "${YELLOW}未找到FastMCP文件!${NC}"
    fi
    
    # 尝试修复uvicorn配置
    for UVICORN_FILE in $(find $VENV_PATH -path "*/uvicorn" -name "*.py" | grep -E "config|server"); do
        if [ -n "$UVICORN_FILE" ]; then
            echo -e "${YELLOW}修改Uvicorn文件: $UVICORN_FILE${NC}"
            
            # 备份原始文件
            cp $UVICORN_FILE ${UVICORN_FILE}.bak
            
            # 修改host绑定
            sed -i 's/host="127.0.0.1"/host="0.0.0.0"/g' $UVICORN_FILE
            sed -i 's/host = "127.0.0.1"/host = "0.0.0.0"/g' $UVICORN_FILE
            sed -i 's/host: str = "127.0.0.1"/host: str = "0.0.0.0"/g' $UVICORN_FILE
        fi
    done
    
    echo -e "${GREEN}MCP库文件修改完成!${NC}"
}

# 配置HTML服务器
setup_html_server() {
    echo -e "${YELLOW}配置HTML服务器...${NC}"
    
    # 创建配置目录
    mkdir -p data/config
    
    # 设置/home/ubuntu目录权限
    sudo chmod 755 /home/ubuntu
    echo -e "${GREEN}/home/ubuntu目录权限已设置为755${NC}"
    
    # 创建HTML服务器配置文件
    if [ ! -f "data/config/html_server.json" ]; then
        cat > data/config/html_server.json << EOF
{
    "server_port": $HTML_PORT,
    "server_host": "0.0.0.0",
    "charts_dir": "data/charts",
    "use_ec2_metadata": true,
    "use_public_ip": true
}
EOF
        echo -e "${GREEN}HTML服务器配置文件已创建!${NC}"
    else
        echo -e "${YELLOW}HTML服务器配置文件已存在，正在更新...${NC}"
        # 更新现有配置文件
        mv data/config/html_server.json data/config/html_server.json.bak
        cat > data/config/html_server.json << EOF
{
    "server_port": $HTML_PORT,
    "server_host": "0.0.0.0", 
    "charts_dir": "data/charts",
    "use_ec2_metadata": true,
    "use_public_ip": true
}
EOF
        echo -e "${GREEN}HTML服务器配置文件已更新!${NC}"
    fi
    
    # 设置环境变量
    export MCP_ENV="production"
    
    # 确保charts目录存在
    mkdir -p data/charts
    chmod -R 755 data/charts
    
    # 生成测试HTML文件
    python -c "
import sys
sys.path.append('.')
from utils.html_server import generate_test_html
url = generate_test_html()
print(f'测试HTML文件已生成，URL: {url}')
"
    
    # 创建HTML服务器systemd服务
    sudo bash -c "cat > /etc/systemd/system/html-server.service << EOF
[Unit]
Description=HTML Server
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=MCP_ENV=production
ExecStart=$(pwd)/.venv/bin/python -m utils.html_server
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF"
    
    # 重新加载systemd配置
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable html-server.service
    
    echo -e "${GREEN}HTML服务器配置完成!${NC}"
}

# 配置Nginx
setup_nginx() {
    echo -e "${YELLOW}配置Nginx...${NC}"
    
    # 创建Nginx配置文件
    sudo bash -c "cat > /etc/nginx/sites-available/quant_mcp << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$HTML_PORT;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }

    location /charts/ {
        alias $(pwd)/data/charts/;
        autoindex on;
    }
}
EOF"

    # 创建符号链接到sites-enabled
    sudo ln -sf /etc/nginx/sites-available/quant_mcp /etc/nginx/sites-enabled/quant_mcp
    
    # 测试Nginx配置
    echo -e "${YELLOW}测试Nginx配置...${NC}"
    sudo nginx -t
    
    # 设置环境变量
    export MCP_ENV="production"
    
    # 使用Python脚本生成Nginx配置（可选）
    python -c "
import sys
sys.path.append('.')
try:
    from utils.html_server import setup_nginx
    success, message = setup_nginx()
    print(message)
except Exception as e:
    print(f'Python配置脚本遇到错误: {e}')
"
    
    echo -e "${GREEN}Nginx配置完成!${NC}"
}

# 检查端口连接
check_connections() {
    echo -e "${YELLOW}检查服务连接情况...${NC}"
    
    # 获取公网IP
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || curl -s icanhazip.com)
    
    # 查看端口绑定
    echo -e "${YELLOW}查看MCP进程:${NC}"
    pgrep -f "python.*server.py" | xargs -I{} ps -p {} -o pid,cmd
    
    echo -e "${YELLOW}MCP服务器绑定地址:${NC}"
    sudo ss -tuln | grep $PORT
    
    echo -e "${YELLOW}HTML服务器绑定地址:${NC}"
    sudo ss -tuln | grep $HTML_PORT
    
    # 检查MCP服务连接
    echo -e "${YELLOW}检查MCP服务内部连接...${NC}"
    curl -v "http://127.0.0.1:$PORT/sse" 2>&1 | grep "< HTTP"
    
    # 检查HTML服务连接
    echo -e "${YELLOW}检查HTML服务内部连接...${NC}"
    curl -v "http://127.0.0.1:$HTML_PORT" 2>&1 | grep "< HTTP"
    
    # 输出iptables防火墙规则
    echo -e "${YELLOW}当前iptables规则:${NC}"
    sudo iptables -L INPUT | grep -E "(ACCEPT|$PORT|$HTML_PORT|80)"
    
    # 检查服务器上的监听进程
    echo -e "${YELLOW}检查端口监听:${NC}"
    sudo netstat -tulpn | grep -E "($PORT|$HTML_PORT)"
    
    # 提供调试信息
    echo -e "${YELLOW}如果外部连接失败，请尝试:${NC}"
    echo -e "1. ${GREEN}检查EC2安全组是否开放端口 $PORT 和 $HTML_PORT${NC}"
    echo -e "2. ${GREEN}检查服务器防火墙: sudo ufw status${NC}"
    echo -e "3. ${GREEN}测试连接: curl -v http://$PUBLIC_IP:$PORT/sse${NC}"
    echo -e "4. ${GREEN}手动启动MCP服务 (临时测试): ${NC}"
    echo -e "   ${GREEN}cd $(pwd) && source .venv/bin/activate && python server.py --transport sse --host 0.0.0.0 --port $PORT${NC}"
}

# 创建systemd服务
create_systemd_service() {
    echo -e "${YELLOW}创建systemd服务...${NC}"
    
    # 获取当前目录
    CURRENT_DIR=$(pwd)
    
    # 创建MCP服务文件
    sudo bash -c "cat > /etc/systemd/system/mcp.service << EOF
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$CURRENT_DIR
Environment=MCP_ENV=production
Environment=MCP_SERVER_HOST=0.0.0.0
Environment=MCP_SSE_HOST=0.0.0.0
Environment=MCP_HTTP_HOST=0.0.0.0
Environment=MCP_BIND=0.0.0.0
Environment=UVICORN_HOST=0.0.0.0
Environment=STARLETTE_HOST=0.0.0.0
Environment=HOST=0.0.0.0
ExecStart=/bin/bash -c 'cd $CURRENT_DIR && source .venv/bin/activate && python server.py --transport $TRANSPORT --host 0.0.0.0 --port $PORT --bind 0.0.0.0'
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF"
    
    # 重新加载systemd配置
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable mcp.service
    
    echo -e "${GREEN}systemd服务创建完成!${NC}"
    
    # 手动测试服务器
    echo -e "${YELLOW}执行手动测试...${NC}"
    cd $CURRENT_DIR
    source .venv/bin/activate
    python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
try:
    s.bind(('0.0.0.0', $PORT))
    print('端口 $PORT 可绑定，可用')
    s.close()
except Exception as e:
    print(f'端口 $PORT 测试失败: {e}')

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', $PORT))
    print('端口 $PORT 已被占用 (连接成功)')
    s.close()
except:
    print('端口 $PORT 未被占用 (连接失败)')
"
}

# 配置防火墙
configure_firewall() {
    echo -e "${YELLOW}配置防火墙规则...${NC}"
    
    # 检查ufw状态
    if command -v ufw &> /dev/null; then
        echo -e "${YELLOW}配置UFW防火墙...${NC}"
        
        # 允许SSH端口
        sudo ufw allow ssh
        
        # 允许MCP端口
        sudo ufw allow $PORT/tcp
        
        # 允许HTML服务器端口
        sudo ufw allow $HTML_PORT/tcp
        
        # 允许HTTP端口
        sudo ufw allow 80/tcp
        
        # 如果防火墙未启用，则启用它
        if ! sudo ufw status | grep -q "Status: active"; then
            echo -e "${YELLOW}启用UFW防火墙...${NC}"
            echo "y" | sudo ufw enable
        fi
        
        echo -e "${GREEN}UFW防火墙配置完成!${NC}"
    elif command -v iptables &> /dev/null; then
        echo -e "${YELLOW}配置iptables防火墙...${NC}"
        
        # 允许SSH端口
        sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
        
        # 允许MCP端口
        sudo iptables -A INPUT -p tcp --dport $PORT -j ACCEPT
        
        # 允许HTML服务器端口
        sudo iptables -A INPUT -p tcp --dport $HTML_PORT -j ACCEPT
        
        # 允许HTTP端口
        sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
        
        # 保存规则
        if command -v netfilter-persistent &> /dev/null; then
            sudo netfilter-persistent save
            echo -e "${GREEN}已保存iptables规则!${NC}"
        else
            echo -e "${YELLOW}未找到netfilter-persistent，规则可能不会在重启后保留${NC}"
            echo -e "${YELLOW}请考虑安装: sudo apt-get install iptables-persistent${NC}"
        fi
        
        echo -e "${GREEN}iptables防火墙配置完成!${NC}"
    else
        echo -e "${YELLOW}未找到支持的防火墙工具，跳过防火墙配置${NC}"
    fi
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    
    # 确保charts目录权限正确
    chmod -R 755 data/charts
    
    # 启动Nginx
    sudo systemctl restart nginx || echo -e "${YELLOW}Nginx启动失败，尝试修复配置...${NC}"
    
    # 如果Nginx启动失败，尝试修复
    if ! systemctl is-active --quiet nginx; then
        echo -e "${YELLOW}尝试修复Nginx配置...${NC}"
        # 删除默认配置
        sudo rm -f /etc/nginx/sites-enabled/default
        # 重启Nginx
        sudo systemctl restart nginx
    fi
    
    # 启动HTML服务器
    sudo systemctl start html-server.service
    
    # 启动MCP服务
    sudo systemctl restart mcp.service
    
    # 等待服务启动完成
    echo -e "${YELLOW}等待服务启动完成...${NC}"
    sleep 3
    
    # 检查服务状态
    echo -e "${YELLOW}Nginx状态:${NC}"
    sudo systemctl status nginx --no-pager
    
    echo -e "${YELLOW}HTML服务器状态:${NC}"
    sudo systemctl status html-server.service --no-pager
    
    echo -e "${YELLOW}MCP服务状态:${NC}"
    sudo systemctl status mcp.service --no-pager
    
    # 检查网络连接
    echo -e "${YELLOW}检查网络连接...${NC}"
    echo -e "${YELLOW}MCP服务器绑定地址:${NC}"
    sudo ss -tuln | grep $PORT
    
    echo -e "${YELLOW}HTML服务器绑定地址:${NC}"
    sudo ss -tuln | grep $HTML_PORT
    
    echo -e "${GREEN}服务已启动!${NC}"
}

# 显示服务信息
show_service_info() {
    echo -e "${YELLOW}获取服务信息...${NC}"
    
    # 尝试从多个IP查询服务获取公网IP
    echo -e "${YELLOW}正在从外部服务获取公网IP...${NC}"
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || curl -s icanhazip.com)
    
    # 如果外部服务失败，尝试EC2元数据
    if [ -z "$PUBLIC_IP" ]; then
        echo -e "${YELLOW}外部服务获取IP失败，尝试EC2元数据...${NC}"
        PUBLIC_IP=$(curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/public-ipv4)
    fi
    
    # 如果仍然失败，使用本地IP
    if [ -z "$PUBLIC_IP" ]; then
        echo -e "${YELLOW}无法获取公网IP，使用本地IP...${NC}"
        PUBLIC_IP=$(hostname -I | awk '{print $1}')
    fi
    
    echo -e "${GREEN}部署完成!${NC}"
    echo -e "${GREEN}检测到的公网IP: $PUBLIC_IP${NC}"
    echo -e "${GREEN}MCP服务器地址: http://$PUBLIC_IP:$PORT${NC}"
    if [ "$TRANSPORT" == "sse" ]; then
        echo -e "${GREEN}MCP服务器SSE端点: http://$PUBLIC_IP:$PORT/sse${NC}"
    elif [ "$TRANSPORT" == "streamable-http" ]; then
        echo -e "${GREEN}MCP服务器HTTP端点: http://$PUBLIC_IP:$PORT/mcp${NC}"
    fi
    echo -e "${GREEN}HTML服务器地址: http://$PUBLIC_IP:$HTML_PORT${NC}"
    echo -e "${GREEN}测试HTML页面: http://$PUBLIC_IP:$HTML_PORT/charts/test.html${NC}"
    echo -e "${GREEN}Nginx HTTP服务: http://$PUBLIC_IP/${NC}"
}

# 主函数
main() {
    echo -e "${YELLOW}开始在EC2实例上部署MCP服务器...${NC}"
    
    # 安装系统依赖
    install_system_deps
    
    # 设置虚拟环境
    setup_venv
    
    # 修复MCP库绑定问题
    fix_mcp_binding
    
    # 配置HTML服务器
    setup_html_server
    
    # 配置Nginx
    setup_nginx
    
    # 创建systemd服务
    create_systemd_service
    
    # 配置防火墙
    configure_firewall
    
    # 启动服务
    start_services
    
    # 检查连接
    check_connections
    
    # 显示服务信息
    show_service_info
}

# 执行主函数
main
