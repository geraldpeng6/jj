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
    echo "  -r, --restart             仅重启服务，不执行完整部署"
    echo "  -c, --clean               清理端口和进程，不执行部署"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置部署 (SSE, 0.0.0.0:8000)"
    echo "  $0 -t streamable-http     # 使用Streamable HTTP传输协议部署"
    echo "  $0 -p 9000 --html-port 9001   # 在端口9000上部署MCP服务器，在端口9001上部署HTML服务器"
    echo "  $0 -r                     # 仅重启所有服务"
    echo "  $0 -c                     # 仅清理端口和进程"
    exit 0
}

# 解析命令行参数
RESTART_ONLY=false
CLEAN_ONLY=false
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
        -r|--restart)
            RESTART_ONLY=true
            shift
            ;;
        -c|--clean)
            CLEAN_ONLY=true
            shift
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

    # HTML服务直接转发
    location / {
        proxy_pass http://127.0.0.1:$HTML_PORT;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }

    # 静态文件目录
    location /charts/ {
        alias $(pwd)/data/charts/;
        autoindex on;
    }
    
    # MCP SSE服务反向代理
    location /mcp/ {
        proxy_pass http://127.0.0.1:$PORT/;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
    }
    
    # MCP SSE endpoint
    location /sse {
        proxy_pass http://127.0.0.1:$PORT/sse;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        chunked_transfer_encoding off;
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

# 检查并清理端口
check_and_clean_ports() {
    echo -e "${YELLOW}检查端口占用情况...${NC}"
    
    # 检查MCP端口
    if sudo ss -tuln | grep ":$PORT " > /dev/null; then
        echo -e "${RED}端口 $PORT 已被占用，尝试释放...${NC}"
        
        # 查找占用端口的进程
        PID=$(sudo lsof -t -i:$PORT)
        if [ -n "$PID" ]; then
            echo -e "${YELLOW}找到占用端口 $PORT 的进程: $PID${NC}"
            echo -e "${YELLOW}进程详情:${NC}"
            ps -p $PID -o pid,user,cmd
            
            # 尝试停止服务
            echo -e "${YELLOW}尝试停止MCP服务...${NC}"
            sudo systemctl stop mcp.service
            sleep 2
            
            # 如果进程仍然存在，强制终止
            if kill -0 $PID 2>/dev/null; then
                echo -e "${YELLOW}服务仍在运行，强制终止进程...${NC}"
                sudo kill -9 $PID
                sleep 1
            fi
        else
            # 如果lsof找不到进程，尝试使用netstat
            PID=$(sudo netstat -tulpn | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
            if [ -n "$PID" ]; then
                echo -e "${YELLOW}找到占用端口 $PORT 的进程: $PID${NC}"
                sudo kill -9 $PID
                sleep 1
            else
                echo -e "${RED}无法找到占用端口 $PORT 的进程，请手动检查${NC}"
                echo -e "${YELLOW}尝试使用以下命令手动终止:${NC}"
                echo -e "${YELLOW}sudo fuser -k $PORT/tcp${NC}"
                sudo fuser -k $PORT/tcp
                sleep 2
            fi
        fi
    else
        echo -e "${GREEN}端口 $PORT 未被占用，可以使用${NC}"
    fi
    
    # 检查HTML端口
    if sudo ss -tuln | grep ":$HTML_PORT " > /dev/null; then
        echo -e "${RED}端口 $HTML_PORT 已被占用，尝试释放...${NC}"
        
        # 尝试停止HTML服务
        echo -e "${YELLOW}尝试停止HTML服务...${NC}"
        sudo systemctl stop html-server.service
        sleep 2
        
        # 如果进程仍然存在，强制终止
        PID=$(sudo lsof -t -i:$HTML_PORT)
        if [ -n "$PID" ]; then
            echo -e "${YELLOW}强制终止进程...${NC}"
            sudo kill -9 $PID
            sleep 1
        else
            echo -e "${YELLOW}使用fuser强制释放端口...${NC}"
            sudo fuser -k $HTML_PORT/tcp
            sleep 2
        fi
    else
        echo -e "${GREEN}端口 $HTML_PORT 未被占用，可以使用${NC}"
    fi
    
    # 再次检查端口
    echo -e "${YELLOW}再次检查端口状态...${NC}"
    if sudo ss -tuln | grep -E ":($PORT|$HTML_PORT) " > /dev/null; then
        echo -e "${RED}端口仍然被占用，请手动检查并释放端口${NC}"
        return 1
    else
        echo -e "${GREEN}所有端口已释放，可以继续部署${NC}"
        return 0
    fi
}

# 创建systemd服务
create_systemd_service() {
    echo -e "${YELLOW}创建systemd服务...${NC}"
    
    # 获取当前目录
    CURRENT_DIR=$(pwd)
    
    # 创建启动脚本
    cat > $CURRENT_DIR/start_mcp.sh << EOF
#!/bin/bash
export MCP_SERVER_HOST=0.0.0.0
export MCP_SSE_HOST=0.0.0.0
export MCP_HTTP_HOST=0.0.0.0
export PYTHONPATH=$CURRENT_DIR
export UVICORN_HOST=0.0.0.0
export HOST=0.0.0.0

cd $CURRENT_DIR
source .venv/bin/activate
echo "启动MCP服务器: $TRANSPORT $HOST $PORT"
exec python server.py --transport $TRANSPORT --host 0.0.0.0 --port $PORT
EOF

    # 给启动脚本添加执行权限
    chmod +x $CURRENT_DIR/start_mcp.sh
    
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
Environment=UVICORN_HOST=0.0.0.0
Environment=HOST=0.0.0.0
ExecStart=$CURRENT_DIR/start_mcp.sh
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

# 检查Nginx代理配置
check_nginx_proxy() {
    echo -e "${YELLOW}检查Nginx反向代理配置...${NC}"
    
    # 获取公网IP
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || curl -s icanhazip.com)
    
    # 检查Nginx配置
    echo -e "${YELLOW}Nginx配置状态:${NC}"
    sudo nginx -t
    
    # 检查Nginx服务状态
    echo -e "${YELLOW}Nginx服务状态:${NC}"
    sudo systemctl status nginx --no-pager
    
    # 测试Nginx代理连接
    echo -e "${YELLOW}测试Nginx代理连接...${NC}"
    echo -e "${YELLOW}HTML服务测试:${NC}"
    curl -s -I "http://localhost/" | head -n 1
    
    echo -e "${YELLOW}MCP服务测试:${NC}"
    curl -s -I "http://localhost/mcp/" | head -n 1
    
    # 提供测试命令
    echo -e "${GREEN}要测试外部访问，请在其他机器上运行:${NC}"
    echo -e "${GREEN}curl -v http://$PUBLIC_IP/sse${NC}"
    
    # 检查端口监听情况
    echo -e "${YELLOW}端口监听情况:${NC}"
    sudo ss -tuln | grep -E "(80|$PORT|$HTML_PORT)"
    
    echo -e "${GREEN}Nginx反向代理检查完成!${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    
    # 先检查并清理端口
    check_and_clean_ports || {
        echo -e "${RED}无法释放所需端口，部署终止${NC}"
        exit 1
    }
    
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
    
    # 直接访问MCP服务器（可能只能从本地访问）
    echo -e "${YELLOW}MCP服务器直接地址 (仅限本地访问): http://127.0.0.1:$PORT${NC}"
    echo -e "${YELLOW}MCP服务器SSE直接端点 (仅限本地访问): http://127.0.0.1:$PORT/sse${NC}"
    
    # 通过Nginx反向代理访问MCP服务器
    echo -e "${GREEN}MCP服务器地址 (通过Nginx反向代理): http://$PUBLIC_IP/mcp/${NC}"
    echo -e "${GREEN}MCP服务器SSE端点 (通过Nginx反向代理): http://$PUBLIC_IP/sse${NC}"
    
    # HTML服务器
    echo -e "${GREEN}HTML服务器地址: http://$PUBLIC_IP:$HTML_PORT${NC}"
    echo -e "${GREEN}HTML服务器地址 (通过Nginx): http://$PUBLIC_IP/${NC}"
    echo -e "${GREEN}测试HTML页面: http://$PUBLIC_IP/charts/test.html${NC}"
    
    echo -e "${YELLOW}注意: 如果直接访问MCP服务失败，请使用Nginx反向代理地址${NC}"
    echo -e "${YELLOW}推荐使用: http://$PUBLIC_IP/sse 作为MCP服务的SSE端点${NC}"
}

# 重启服务
restart_services() {
    echo -e "${YELLOW}重启所有服务...${NC}"
    
    # 停止服务
    echo -e "${YELLOW}停止服务...${NC}"
    sudo systemctl stop mcp.service html-server.service nginx
    
    # 等待服务停止
    sleep 2
    
    # 检查是否有残留进程
    if pgrep -f "python.*server.py" > /dev/null; then
        echo -e "${YELLOW}发现残留的MCP服务进程，正在终止...${NC}"
        sudo pkill -f "python.*server.py"
    fi
    
    if pgrep -f "python.*html_server" > /dev/null; then
        echo -e "${YELLOW}发现残留的HTML服务进程，正在终止...${NC}"
        sudo pkill -f "python.*html_server"
    fi
    
    # 检查并清理端口
    check_and_clean_ports
    
    # 启动服务
    echo -e "${YELLOW}启动服务...${NC}"
    sudo systemctl start nginx
    sudo systemctl start html-server.service
    sudo systemctl start mcp.service
    
    # 检查服务状态
    echo -e "${YELLOW}Nginx状态:${NC}"
    sudo systemctl status nginx --no-pager
    
    echo -e "${YELLOW}HTML服务器状态:${NC}"
    sudo systemctl status html-server.service --no-pager
    
    echo -e "${YELLOW}MCP服务状态:${NC}"
    sudo systemctl status mcp.service --no-pager
    
    # 检查端口
    echo -e "${YELLOW}检查端口...${NC}"
    sudo ss -tuln | grep -E "(80|$PORT|$HTML_PORT)"
    
    echo -e "${GREEN}服务已重启!${NC}"
}

# 清理端口和进程
clean_all() {
    echo -e "${YELLOW}清理端口和进程...${NC}"
    
    # 停止服务
    echo -e "${YELLOW}停止所有服务...${NC}"
    sudo systemctl stop mcp.service html-server.service nginx
    
    # 等待服务停止
    sleep 2
    
    # 终止所有相关进程
    echo -e "${YELLOW}终止所有相关进程...${NC}"
    sudo pkill -f "python.*server.py" || true
    sudo pkill -f "python.*html_server" || true
    
    # 检查并清理端口
    check_and_clean_ports
    
    echo -e "${GREEN}清理完成!${NC}"
    
    # 显示当前进程状态
    echo -e "${YELLOW}当前进程状态:${NC}"
    ps aux | grep -E "python.*server.py|python.*html_server" | grep -v grep
    
    # 显示当前端口状态
    echo -e "${YELLOW}当前端口状态:${NC}"
    sudo ss -tuln | grep -E "(80|$PORT|$HTML_PORT)"
}

# 主函数
main() {
    echo -e "${YELLOW}开始在EC2实例上部署MCP服务器...${NC}"
    
    # 如果只是清理
    if [ "$CLEAN_ONLY" = true ]; then
        clean_all
        exit 0
    fi
    
    # 如果只是重启服务
    if [ "$RESTART_ONLY" = true ]; then
        restart_services
        check_nginx_proxy
        show_service_info
        exit 0
    fi
    
    # 安装系统依赖
    install_system_deps
    
    # 设置虚拟环境
    setup_venv
    
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
    
    # 检查Nginx代理
    check_nginx_proxy
    
    # 显示服务信息
    show_service_info
}

# 执行主函数
main
