#!/bin/bash

# 修复文件权限脚本
# 此脚本用于修复图表目录的文件权限

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

echo -e "${YELLOW}开始修复文件权限...${NC}"

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
echo -e "${YELLOW}设置目录权限...${NC}"
chown -R "$NGINX_USER":"$NGINX_USER" "$CHARTS_DIR_ABS"
chmod -R 755 "$CHARTS_DIR_ABS"

echo -e "${GREEN}目录权限已设置:${NC}"
ls -la "$CHARTS_DIR_ABS"

# 创建测试文件
echo -e "${YELLOW}创建测试HTML文件...${NC}"
TEST_FILE="${CHARTS_DIR_ABS}/test_permissions.html"

cat > "$TEST_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>权限测试</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>文件权限测试成功!</h1>
    <p>如果您看到此页面，说明文件权限已正确设置。</p>
    <p>生成时间: $(date)</p>
</body>
</html>
EOF

# 设置测试文件权限
chown "$NGINX_USER":"$NGINX_USER" "$TEST_FILE"
chmod 644 "$TEST_FILE"

echo -e "${GREEN}测试文件已创建: ${TEST_FILE}${NC}"
echo -e "${GREEN}测试文件权限:${NC}"
ls -la "$TEST_FILE"

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

echo -e "${GREEN}权限修复完成!${NC}"
echo -e "${GREEN}服务器IP地址: ${SERVER_IP}${NC}"
echo -e "${GREEN}测试URL: http://${SERVER_IP}/test_permissions.html${NC}"
echo -e "${GREEN}请在浏览器中访问测试URL，验证权限是否正确设置${NC}"
