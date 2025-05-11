#!/bin/bash

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始设置量化交易助手环境...${NC}"

# 检查是否安装了uv
if ! command -v uv &> /dev/null
then
    echo -e "${YELLOW}未检测到uv，正在安装...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # 添加uv到PATH
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# 创建虚拟环境
echo -e "${YELLOW}创建虚拟环境...${NC}"
uv venv .venv

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# 安装依赖
echo -e "${YELLOW}安装依赖...${NC}"
uv pip install -r requirements.txt

echo -e "${GREEN}环境设置完成！${NC}"
echo -e "${YELLOW}使用方法:${NC}"
echo -e "1. 激活环境: ${GREEN}source .venv/bin/activate${NC}"
echo -e "2. 运行服务器: ${GREEN}python server.py${NC}"
