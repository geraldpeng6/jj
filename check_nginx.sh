#!/bin/bash

# 检查Nginx状态和配置脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}检查Nginx状态和配置...${NC}"

# 检查Nginx是否安装
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}Nginx未安装${NC}"
    exit 1
fi

echo -e "${GREEN}Nginx已安装${NC}"

# 检查Nginx是否运行
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx正在运行${NC}"
else
    echo -e "${RED}Nginx未运行${NC}"
    echo -e "${YELLOW}尝试启动Nginx...${NC}"
    sudo systemctl start nginx
    if systemctl is-active --quiet nginx; then
        echo -e "${GREEN}Nginx已成功启动${NC}"
    else
        echo -e "${RED}无法启动Nginx${NC}"
        exit 1
    fi
fi

# 检查Nginx配置
echo -e "${YELLOW}检查Nginx配置...${NC}"
nginx -t

# 检查Nginx配置文件
NGINX_CONF="/etc/nginx/conf.d/quant_charts.conf"
if [ -f "$NGINX_CONF" ]; then
    echo -e "${GREEN}Nginx配置文件存在: ${NGINX_CONF}${NC}"
    echo -e "${YELLOW}配置文件内容:${NC}"
    cat "$NGINX_CONF"
else
    echo -e "${RED}Nginx配置文件不存在: ${NGINX_CONF}${NC}"
fi

# 检查项目目录
PROJECT_DIR=$(pwd)
CHARTS_DIR="${PROJECT_DIR}/data/charts"

if [ -d "$CHARTS_DIR" ]; then
    echo -e "${GREEN}图表目录存在: ${CHARTS_DIR}${NC}"
    echo -e "${YELLOW}图表目录内容:${NC}"
    ls -la "$CHARTS_DIR"
else
    echo -e "${RED}图表目录不存在: ${CHARTS_DIR}${NC}"
fi

# 检查Nginx日志
echo -e "${YELLOW}检查Nginx错误日志...${NC}"
if [ -f "/var/log/nginx/quant_charts_error.log" ]; then
    tail -n 20 /var/log/nginx/quant_charts_error.log
else
    echo -e "${RED}Nginx错误日志文件不存在${NC}"
fi

echo -e "${YELLOW}检查Nginx访问日志...${NC}"
if [ -f "/var/log/nginx/quant_charts_access.log" ]; then
    tail -n 20 /var/log/nginx/quant_charts_access.log
else
    echo -e "${RED}Nginx访问日志文件不存在${NC}"
fi

# 获取服务器IP地址
SERVER_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
fi

echo -e "${GREEN}服务器IP地址: ${SERVER_IP}${NC}"

# 创建测试文件
echo -e "${YELLOW}创建测试HTML文件...${NC}"
TEST_FILE="${CHARTS_DIR}/test_$(date +%Y%m%d_%H%M%S).html"
mkdir -p "$CHARTS_DIR"

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
chmod 644 "$TEST_FILE"

echo -e "${GREEN}测试文件已创建: ${TEST_FILE}${NC}"
echo -e "${GREEN}测试URL: http://${SERVER_IP}/$(basename "$TEST_FILE")${NC}"
echo -e "${GREEN}请在浏览器中访问测试URL，验证配置是否成功${NC}"
