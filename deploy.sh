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

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    $PYTHON -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误: 无法创建虚拟环境。请确保已安装venv模块。"
        exit 1
    fi
fi

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "错误: 无法找到虚拟环境激活脚本。"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip install -U pip
pip install pandas numpy requests paho-mqtt socks jinja2 pytz

# 检查utils/date_utils.py是否存在
if [ ! -f "utils/date_utils.py" ]; then
    echo "警告: 未找到utils/date_utils.py文件，日期处理可能不正确。"
fi

# 显示部署信息
echo ""
echo "========== 部署完成 =========="
echo "您可以运行以下命令测试系统:"
echo "$PYTHON test_kline.py"
echo ""
echo "请确保已正确配置您的API密钥和认证信息。"

# 保持虚拟环境激活
exec $SHELL 