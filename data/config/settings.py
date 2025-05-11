#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
全局设置
包含项目的全局配置参数
"""

import os
import json
import logging
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 配置目录
CONFIG_DIR = ROOT_DIR / 'config'

# 数据目录
DATA_DIR = ROOT_DIR / 'data'

# 日志目录
LOG_DIR = ROOT_DIR / 'logs'

# 临时文件目录
TEMP_DIR = ROOT_DIR / 'temp'

# 图表输出目录
CHARTS_DIR = ROOT_DIR / 'charts'

# 模板目录
TEMPLATES_DIR = ROOT_DIR / 'templates'

# API基础URL
BASE_URL = "https://api.yueniusz.com"

# 确保目录存在
for directory in [LOG_DIR, TEMP_DIR, CHARTS_DIR]:
    directory.mkdir(exist_ok=True)

# 日志配置
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOG_DIR / 'quant_mcp.log'

# 认证信息
TOKEN = None
USER_ID = None

def load_auth_config():
    """
    从配置文件加载认证信息

    Returns:
        bool: 加载是否成功
    """
    global TOKEN, USER_ID

    # 检查配置文件是否存在
    config_file = CONFIG_DIR / 'auth.json'
    if not config_file.exists():
        error_msg = f"错误: 登录配置文件 {config_file} 不存在，请先创建配置文件"
        logging.error(error_msg)
        return False

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            TOKEN = config.get('token')
            USER_ID = config.get('user_id')

        if not TOKEN or not USER_ID:
            error_msg = "错误: 配置文件中缺少token或user_id"
            logging.error(error_msg)
            return False

        return True
    except Exception as e:
        error_msg = f"错误: 读取配置文件失败: {e}"
        logging.error(error_msg)
        return False

# 加载认证配置
load_auth_config()
