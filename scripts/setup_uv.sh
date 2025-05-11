#!/bin/bash

# 设置 uv 和虚拟环境的脚本
# 此脚本会安装 uv 并创建一个虚拟环境

# 确保 scripts 目录存在
mkdir -p scripts

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始设置 uv 和虚拟环境...${NC}"

# 检查 uv 是否已安装
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv 未安装，正在安装...${NC}"
    
    # 安装 uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # 添加 uv 到 PATH
    if [[ ":$PATH:" != *":$HOME/.cargo/bin:"* ]]; then
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
    
    echo -e "${GREEN}uv 安装完成!${NC}"
else
    echo -e "${GREEN}uv 已安装!${NC}"
fi

# 创建虚拟环境
echo -e "${YELLOW}创建虚拟环境...${NC}"
uv venv .venv

# 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# 使用 uv 安装依赖
echo -e "${YELLOW}安装依赖...${NC}"
uv pip install -r requirements.txt

echo -e "${GREEN}设置完成!${NC}"
echo -e "${YELLOW}使用以下命令激活虚拟环境:${NC}"
echo -e "${GREEN}source .venv/bin/activate${NC}"

# 创建一个便捷的运行脚本
cat > scripts/run.sh << 'EOF'
#!/bin/bash

# 激活虚拟环境
source .venv/bin/activate

# 运行服务器
python server.py $@
EOF

# 使脚本可执行
chmod +x scripts/run.sh

echo -e "${YELLOW}创建了运行脚本: ${GREEN}scripts/run.sh${NC}"
echo -e "${YELLOW}使用以下命令运行服务器:${NC}"
echo -e "${GREEN}./scripts/run.sh${NC}"
