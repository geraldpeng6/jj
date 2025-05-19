#!/bin/bash

# 停止EC2模式测试环境

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止模拟EC2元数据服务
if [ -f "mock_ec2/mock_pid.txt" ]; then
    MOCK_PID=$(cat mock_ec2/mock_pid.txt)
    echo -e "${YELLOW}停止模拟EC2元数据服务 (PID: $MOCK_PID)...${NC}"
    kill $MOCK_PID 2>/dev/null || true
    rm mock_ec2/mock_pid.txt
fi

# 停止MCP服务器
if [ -f "mock_ec2/mcp_pid.txt" ]; then
    MCP_PID=$(cat mock_ec2/mcp_pid.txt)
    echo -e "${YELLOW}停止MCP服务器 (PID: $MCP_PID)...${NC}"
    kill $MCP_PID 2>/dev/null || true
    rm mock_ec2/mcp_pid.txt
fi

# 删除Nginx配置
echo -e "${YELLOW}删除Nginx配置...${NC}"
sudo rm -f /opt/homebrew/etc/nginx/servers/mcp_html_server.conf
brew services reload nginx

# 删除HTML服务器配置
echo -e "${YELLOW}删除HTML服务器配置...${NC}"
rm -f data/config/html_server.json

echo -e "${GREEN}EC2模式测试环境已停止!${NC}"
