#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票符号工具模块

提供股票符号相关的功能，包括获取股票符号详细信息
"""

import json
import logging
import requests
import sys
from typing import Dict, Optional, Any

from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 获取日志记录器
logger = logging.getLogger('quant_mcp.symbol_utils')

# API基础URL
BASE_URL = "https://api.yueniusz.com"


def get_symbol_info(full_name: str) -> Optional[Dict[str, Any]]:
    """
    获取股票符号详细信息

    Args:
        full_name: 完整的股票代码，例如 "600000.XSHG"

    Returns:
        Optional[Dict[str, Any]]: 股票符号详细信息，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    if not full_name:
        error_msg = "错误: 股票代码不能为空"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    url = f"{BASE_URL}/trader-service/symbols"
    params = {
        "full_name": full_name,
        "user_id": user_id
    }

    headers = get_headers()
    logger.debug(f"发送GET请求到: {url}")
    logger.debug(f"请求参数: {params}")
    logger.debug(f"请求头: {headers}")

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        logger.debug(f"收到响应: {data}")

        if data.get('code') == 1 and data.get('msg') == 'ok':
            symbol_info = data.get('data', {})
            logger.info(f"获取股票信息成功，股票代码: {symbol_info.get('symbol')}")
            return symbol_info
        else:
            logger.error(f"获取股票信息失败: {data}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取股票信息时发生未知错误: {e}")
        return None
