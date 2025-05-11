#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API客户端模块

提供与yueniusz API交互的功能
"""

import json
import logging
import requests
import time
import datetime
from typing import Dict, Any, Optional, List, Union

from utils.auth_utils import get_headers, get_auth_info

# 获取日志记录器
logger = logging.getLogger('quant_mcp.api_client')

# API基础URL
BASE_URL = "https://api.yueniusz.com"


def convert_date_to_timestamp(date_str: Optional[str], default_days_ago: int = 0) -> int:
    """
    将日期字符串转换为时间戳

    Args:
        date_str: 日期字符串，格式为YYYY-MM-DD
        default_days_ago: 如果date_str为None，则使用当前日期减去指定天数

    Returns:
        int: 时间戳（毫秒）
    """
    if date_str is None:
        # 使用当前日期减去指定天数
        date = datetime.datetime.now() - datetime.timedelta(days=default_days_ago)
        return int(date.timestamp() * 1000)
    else:
        # 如果是日期字符串，转换为时间戳
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            return int(date.timestamp() * 1000)
        except ValueError:
            raise ValueError(f"无效的日期格式: {date_str}，应为YYYY-MM-DD")


def get_kline_data_from_api(
    symbol: str, 
    exchange: str, 
    resolution: str = "1D",
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None,
    fq: str = "post", 
    fq_date: Optional[str] = None,
    category: str = "stock", 
    skip_paused: bool = False
) -> Dict[str, Any]:
    """
    从API获取K线数据

    Args:
        symbol: 股票代码，例如 "600000"
        exchange: 交易所代码，例如 "XSHG"
        resolution: 时间周期，例如 "1D"（日线）, "1"（1分钟）
        from_date: 开始日期，格式为YYYY-MM-DD，默认为30天前
        to_date: 结束日期，格式为YYYY-MM-DD，默认为当前日期
        fq: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
        fq_date: 复权基准日期，格式为YYYY-MM-DD，默认为当前日期
        category: 品种类别，默认为 "stock"（股票）
        skip_paused: 是否跳过停牌日期，默认为 False

    Returns:
        Dict[str, Any]: API响应数据
    """
    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        raise ValueError("无法获取认证信息")

    # 处理日期参数
    from_date_ts = convert_date_to_timestamp(from_date, default_days_ago=30)
    to_date_ts = convert_date_to_timestamp(to_date)
    fq_date_ts = convert_date_to_timestamp(fq_date)

    # 构建请求参数
    params = {
        "category": category,
        "exchange": exchange,
        "symbol": symbol,
        "resolution": resolution,
        "from_date": from_date_ts,
        "to_date": to_date_ts,
        "fq_date": fq_date_ts,
        "fq": fq,
        "skip_paused": str(skip_paused).lower(),
        "user_id": user_id
    }

    url = f"{BASE_URL}/trader-service/history"
    headers = get_headers()

    logger.debug(f"发送GET请求到: {url}")
    logger.debug(f"请求参数: {params}")
    logger.debug(f"请求头: {headers}")

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        logger.debug(f"收到响应: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        raise
