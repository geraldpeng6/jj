#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试HTML文件是否可访问
echo -e "${YELLOW}测试HTML文件是否可访问...${NC}"

# 生成测试HTML文件
TEST_URL=$(python -c "
import sys
sys.path.append('.')
from utils.html_server import get_html_url
import os
test_path = os.path.abspath('data/charts/test.html')
if os.path.exists(test_path):
    url = get_html_url(test_path)
    print(url)
else:
    print('测试文件不存在，正在创建...')
    from utils.html_server import generate_test_html
    url = generate_test_html()
    print(url)
")

if [ -n "$TEST_URL" ]; then
    echo -e "${GREEN}测试HTML文件URL: $TEST_URL${NC}"
    echo -e "${YELLOW}尝试使用curl访问测试HTML文件...${NC}"
    curl -s -I "$TEST_URL" | head -n 1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}测试HTML文件可以成功访问!${NC}"
        echo -e "${YELLOW}尝试获取完整内容...${NC}"
        curl -s "$TEST_URL" | head -n 10
    else
        echo -e "${RED}无法访问测试HTML文件，请检查Nginx配置。${NC}"
    fi
else
    echo -e "${RED}无法获取测试HTML文件URL。${NC}"
fi
