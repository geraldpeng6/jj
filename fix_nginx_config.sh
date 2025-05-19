#!/bin/bash

# 修复Nginx配置脚本
# 此脚本用于修复Nginx配置，解决HTML文件404问题

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 此脚本需要root权限运行${NC}"
    echo -e "${YELLOW}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

echo -e "${YELLOW}开始修复Nginx配置...${NC}"

# 项目根目录（脚本假设在项目根目录运行）
PROJECT_DIR=$(pwd)
CHARTS_DIR="${PROJECT_DIR}/data/charts"

# 确保图表目录存在
if [ ! -d "$CHARTS_DIR" ]; then
    echo -e "${YELLOW}图表目录不存在，正在创建...${NC}"
    mkdir -p "$CHARTS_DIR"
fi

# 获取绝对路径
CHARTS_DIR_ABS=$(realpath "$CHARTS_DIR")
echo -e "${YELLOW}图表目录绝对路径: ${CHARTS_DIR_ABS}${NC}"

# 检查Nginx配置文件
NGINX_CONF="/etc/nginx/conf.d/quant_charts.conf"
if [ ! -f "$NGINX_CONF" ]; then
    echo -e "${YELLOW}Nginx配置文件不存在，正在创建...${NC}"
    
    # 创建Nginx配置文件
    cat > "$NGINX_CONF" << EOF
# 量化交易图表服务器配置
# 此配置文件由fix_nginx_config.sh脚本自动生成

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
else
    echo -e "${YELLOW}Nginx配置文件已存在，正在更新...${NC}"
    
    # 备份原配置文件
    cp "$NGINX_CONF" "${NGINX_CONF}.bak"
    
    # 更新配置文件
    cat > "$NGINX_CONF" << EOF
# 量化交易图表服务器配置
# 此配置文件由fix_nginx_config.sh脚本自动生成

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
fi

# 检查Nginx配置是否有效
echo -e "${YELLOW}检查Nginx配置是否有效...${NC}"
nginx -t

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Nginx配置有效!${NC}"
else
    echo -e "${RED}错误: Nginx配置无效${NC}"
    exit 1
fi

# 创建测试HTML文件
echo -e "${YELLOW}创建测试HTML文件...${NC}"
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

# 设置文件权限
echo -e "${YELLOW}设置文件权限...${NC}"

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

# 重启Nginx服务
echo -e "${YELLOW}重启Nginx服务...${NC}"
systemctl restart nginx

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Nginx服务重启成功!${NC}"
else
    echo -e "${RED}错误: Nginx服务重启失败${NC}"
    exit 1
fi

# 获取服务器IP地址
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
fi

echo -e "${GREEN}配置完成!${NC}"
echo -e "${GREEN}服务器IP地址: ${SERVER_IP}${NC}"
echo -e "${GREEN}测试URL: http://${SERVER_IP}/test.html${NC}"
echo -e "${GREEN}请在浏览器中访问测试URL，验证配置是否成功${NC}"

# 检查日志文件
echo -e "${YELLOW}检查Nginx错误日志...${NC}"
tail -n 20 /var/log/nginx/quant_charts_error.log

echo -e "${YELLOW}检查Nginx访问日志...${NC}"
tail -n 20 /var/log/nginx/quant_charts_access.log

# 显示图表目录内容
echo -e "${YELLOW}图表目录内容:${NC}"
ls -la "$CHARTS_DIR_ABS"
