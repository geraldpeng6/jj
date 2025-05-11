#!/bin/bash

# 使用 uv 更新依赖的脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo -e "${RED}错误: uv 未安装，请先运行 ./scripts/setup_uv.sh${NC}"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo -e "${RED}错误: 虚拟环境不存在，请先运行 ./scripts/setup_uv.sh${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# 使用 uv 更新依赖
echo -e "${YELLOW}更新依赖...${NC}"
uv pip install --upgrade -r requirements.txt

echo -e "${GREEN}依赖更新完成!${NC}"
