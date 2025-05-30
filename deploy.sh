#!/bin/bash

# 部署脚本 - 设置环境并安装依赖

echo "========== 开始部署量化交易系统 =========="

# 创建目录结构（如果不存在）
mkdir -p data/klines
mkdir -p data/charts
mkdir -p data/backtest
mkdir -p data/templates
mkdir -p data/config
mkdir -p logs

# 检查Python环境
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo "错误: 未找到Python。请安装Python 3.6或更高版本。"
    exit 1
fi

echo "使用Python: $($PYTHON --version)"

# 检查requirements.txt文件是否存在
if [ ! -f "requirements.txt" ]; then
    echo "错误: 未找到requirements.txt文件。"
    exit 1
fi

# 检查并创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    $PYTHON -m venv .venv
    if [ $? -ne 0 ]; then
        echo "错误: 无法创建虚拟环境。请确保已安装venv模块。"
        exit 1
    fi
fi

# 设置虚拟环境路径
if [ -d ".venv/bin" ]; then
    VENV_PATH=".venv/bin"
elif [ -d ".venv/Scripts" ]; then
    VENV_PATH=".venv/Scripts"
else
    echo "错误: 无法找到虚拟环境bin目录。"
    exit 1
fi

# 首先确保pip可用
echo "确保pip可用..."
$PYTHON -m ensurepip --upgrade || echo "尝试使用系统pip..."

# 使用Python执行pip命令安装依赖
echo "安装依赖..."
"$VENV_PATH/python" -m pip install --upgrade pip || $PYTHON -m pip install --upgrade pip
echo "从requirements.txt安装依赖项..."
"$VENV_PATH/python" -m pip install -r requirements.txt || $PYTHON -m pip install -r requirements.txt

# 检查安装结果
if [ $? -ne 0 ]; then
    echo "警告: 安装依赖时出现错误，请检查requirements.txt文件内容。"
else
    echo "依赖安装完成。"
fi

# 检查utils/date_utils.py是否存在
if [ ! -f "utils/date_utils.py" ]; then
    echo "警告: 未找到utils/date_utils.py文件，日期处理可能不正确。"
fi

# 显示部署信息
echo ""
echo "========== 部署完成 =========="
echo "您可以使用以下命令启动系统:"
echo ""
echo "1. 标准启动:"
echo "   source $VENV_PATH/activate && $PYTHON server.py"
echo ""
echo "2. 使用SSE传输协议启动(推荐):"
echo "   source $VENV_PATH/activate && $PYTHON server.py --transport sse"
echo ""
echo "提示: SSE传输协议更适合Web环境，提供更稳定的连接。"
echo "请确保已正确配置您的API密钥和认证信息。"

# 直接结束脚本
exit 0 