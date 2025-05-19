#!/bin/bash

# 安装和配置Nginx脚本
# 此脚本用于安装Nginx并配置为提供HTML图表文件服务

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录（脚本假设在项目根目录运行）
PROJECT_DIR=$(pwd)
CHARTS_DIR="${PROJECT_DIR}/data/charts"

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help                显示此帮助信息"
    echo "  -d, --charts-dir DIR      指定图表目录路径 (默认: ${CHARTS_DIR})"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置配置Nginx"
    echo "  $0 -d /path/to/charts     # 指定图表目录路径"
    exit 0
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -d|--charts-dir)
            CHARTS_DIR="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            show_help
            ;;
    esac
done

# 检查是否以root权限运行
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}错误: 此脚本需要root权限运行${NC}"
        echo -e "${YELLOW}请使用 sudo 运行此脚本${NC}"
        exit 1
    fi
}

# 检查并安装Nginx
install_nginx() {
    echo -e "${YELLOW}检查Nginx是否已安装...${NC}"
    
    if command -v nginx > /dev/null; then
        echo -e "${GREEN}Nginx已安装!${NC}"
    else
        echo -e "${YELLOW}Nginx未安装，正在安装...${NC}"
        
        # 检测操作系统类型
        if [ -f /etc/debian_version ]; then
            # Debian/Ubuntu
            apt-get update
            apt-get install -y nginx
        elif [ -f /etc/redhat-release ]; then
            # CentOS/RHEL/Amazon Linux
            yum install -y nginx
        elif [ -f /etc/os-release ]; then
            # 检查是否为macOS
            if [[ "$(uname)" == "Darwin" ]]; then
                # macOS
                if command -v brew > /dev/null; then
                    brew install nginx
                else
                    echo -e "${RED}错误: 请先安装Homebrew${NC}"
                    echo -e "${YELLOW}可以使用以下命令安装Homebrew:${NC}"
                    echo -e "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                    exit 1
                fi
            else
                echo -e "${RED}错误: 不支持的操作系统${NC}"
                exit 1
            fi
        else
            echo -e "${RED}错误: 不支持的操作系统${NC}"
            exit 1
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Nginx安装成功!${NC}"
        else
            echo -e "${RED}错误: Nginx安装失败${NC}"
            exit 1
        fi
    fi
}

# 创建Nginx配置文件
create_nginx_config() {
    echo -e "${YELLOW}创建Nginx配置文件...${NC}"
    
    # 确保图表目录存在
    if [ ! -d "$CHARTS_DIR" ]; then
        echo -e "${YELLOW}图表目录不存在，正在创建...${NC}"
        mkdir -p "$CHARTS_DIR"
    fi
    
    # 获取绝对路径
    CHARTS_DIR_ABS=$(realpath "$CHARTS_DIR")
    echo -e "${YELLOW}图表目录绝对路径: ${CHARTS_DIR_ABS}${NC}"
    
    # 检测操作系统类型
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        NGINX_CONF="/usr/local/etc/nginx/servers/quant_charts.conf"
        NGINX_CONF_DIR="/usr/local/etc/nginx/servers"
        
        # 确保配置目录存在
        mkdir -p "$NGINX_CONF_DIR"
    else
        # Linux
        NGINX_CONF="/etc/nginx/conf.d/quant_charts.conf"
        NGINX_CONF_DIR="/etc/nginx/conf.d"
        
        # 确保配置目录存在
        mkdir -p "$NGINX_CONF_DIR"
    fi
    
    # 创建Nginx配置文件
    cat > "$NGINX_CONF" << EOF
# 量化交易图表服务器配置
# 此配置文件由install_nginx.sh脚本自动生成

server {
    listen 80;
    server_name _;  # 匹配所有域名
    
    # 访问日志和错误日志
    access_log /var/log/nginx/quant_charts_access.log;
    error_log /var/log/nginx/quant_charts_error.log;
    
    # 图表文件目录
    location / {
        root $CHARTS_DIR_ABS;
        
        # 只允许访问HTML文件
        location ~* \.(html)$ {
            # 添加CORS头，允许所有来源访问
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
            
            # 设置缓存控制
            add_header Cache-Control "no-cache, must-revalidate";
            
            # 设置内容类型
            add_header Content-Type "text/html; charset=utf-8";
        }
        
        # 禁止访问非HTML文件
        location ~* \.((?!html).)*$ {
            deny all;
            return 403;
        }
        
        # 禁止目录列表
        autoindex off;
        
        # 默认文件（如果有的话）
        index index.html;
    }
    
    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        return 404;
    }
}
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx配置文件创建成功: ${NGINX_CONF}${NC}"
    else
        echo -e "${RED}错误: Nginx配置文件创建失败${NC}"
        exit 1
    fi
}

# 检查Nginx配置是否有效
check_nginx_config() {
    echo -e "${YELLOW}检查Nginx配置是否有效...${NC}"
    
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx配置有效!${NC}"
    else
        echo -e "${RED}错误: Nginx配置无效${NC}"
        exit 1
    fi
}

# 重启Nginx服务
restart_nginx() {
    echo -e "${YELLOW}重启Nginx服务...${NC}"
    
    # 检测操作系统类型
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        if command -v brew > /dev/null; then
            brew services restart nginx
        else
            nginx -s stop
            nginx
        fi
    else
        # Linux
        # 检测系统使用的服务管理器
        if command -v systemctl > /dev/null; then
            # systemd
            systemctl restart nginx
        elif command -v service > /dev/null; then
            # SysVinit
            service nginx restart
        else
            # 直接使用nginx命令
            nginx -s reload
        fi
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Nginx服务重启成功!${NC}"
    else
        echo -e "${RED}错误: Nginx服务重启失败${NC}"
        exit 1
    fi
}

# 设置目录权限
set_permissions() {
    echo -e "${YELLOW}设置目录权限...${NC}"
    
    # 确保Nginx用户可以访问图表目录
    # 通常Nginx用户是www-data(Debian/Ubuntu)或nginx(CentOS/RHEL)
    
    # 检测操作系统类型
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        chmod -R 755 "$CHARTS_DIR_ABS"
    else
        # Linux
        # 检测Nginx用户
        NGINX_USER=$(grep -E "^user" /etc/nginx/nginx.conf | awk '{print $2}' | tr -d ';')
        
        if [ -z "$NGINX_USER" ]; then
            # 如果未在配置中找到，尝试使用默认值
            if [ -f /etc/debian_version ]; then
                NGINX_USER="www-data"
            else
                NGINX_USER="nginx"
            fi
        fi
        
        echo -e "${YELLOW}Nginx运行用户: ${NGINX_USER}${NC}"
        
        # 设置目录权限
        chown -R "$NGINX_USER":"$NGINX_USER" "$CHARTS_DIR_ABS"
        chmod -R 755 "$CHARTS_DIR_ABS"
    fi
    
    echo -e "${GREEN}目录权限设置完成!${NC}"
}

# 测试配置
test_config() {
    echo -e "${YELLOW}测试Nginx配置...${NC}"
    
    # 获取服务器IP地址
    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        SERVER_IP=$(ipconfig getifaddr en0)
        if [ -z "$SERVER_IP" ]; then
            SERVER_IP=$(ipconfig getifaddr en1)
        fi
    else
        # Linux
        SERVER_IP=$(hostname -I | awk '{print $1}')
    fi
    
    echo -e "${GREEN}服务器IP地址: ${SERVER_IP}${NC}"
    echo -e "${GREEN}测试URL: http://${SERVER_IP}/${NC}"
    
    # 创建测试HTML文件
    TEST_FILE="${CHARTS_DIR_ABS}/test.html"
    
    cat > "$TEST_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Nginx配置测试</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Nginx配置测试成功!</h1>
    <p>如果您看到此页面，说明Nginx已成功配置为提供HTML文件。</p>
    <p>生成时间: $(date)</p>
</body>
</html>
EOF
    
    # 设置测试文件权限
    chmod 644 "$TEST_FILE"
    
    echo -e "${GREEN}测试文件已创建: ${TEST_FILE}${NC}"
    echo -e "${GREEN}请在浏览器中访问 http://${SERVER_IP}/test.html 测试配置${NC}"
}

# 主函数
main() {
    echo -e "${YELLOW}开始配置Nginx服务器...${NC}"
    
    # 检查root权限
    check_root
    
    # 安装Nginx
    install_nginx
    
    # 创建Nginx配置
    create_nginx_config
    
    # 设置目录权限
    set_permissions
    
    # 检查配置
    check_nginx_config
    
    # 重启Nginx
    restart_nginx
    
    # 测试配置
    test_config
    
    echo -e "${GREEN}Nginx配置完成!${NC}"
    echo -e "${GREEN}现在您可以通过 http://服务器IP/文件名.html 访问图表文件${NC}"
}

# 执行主函数
main
