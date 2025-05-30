#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图表工具模块

提供图表相关的工具函数，包括生成图表路径和检查已存在的回测结果
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime

from utils.html_server import get_server_host, get_html_url

# 获取日志记录器
logger = logging.getLogger('quant_mcp.chart_utils')

# 回测结果目录
DATA_DIR = 'data'
BACKTEST_DIR = os.path.join(DATA_DIR, 'backtest')
CHARTS_DIR = os.path.join(DATA_DIR, 'charts')

# 确保目录存在
os.makedirs(BACKTEST_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)


def generate_chart_path(strategy_id: str, symbol: str, exchange: str, timestamp: str) -> str:
    """
    生成图表路径

    Args:
        strategy_id: 策略ID
        symbol: 股票代码
        exchange: 交易所代码
        timestamp: 时间戳

    Returns:
        str: 图表路径
    """
    file_name = f"backtest_{strategy_id}_{symbol}_{exchange}_{timestamp}.html"
    file_path = os.path.join(CHARTS_DIR, file_name)
    
    # 动态获取服务器主机地址
    server_host = get_server_host()
    
    # 使用get_html_url生成完整URL
    url = get_html_url(file_path)
    
    return url


def check_existing_backtest(
    strategy_id: str, 
    start_date: Optional[str], 
    end_date: Optional[str],
    choose_stock: Optional[str]
) -> Optional[str]:
    """
    检查是否存在相同参数的回测结果

    Args:
        strategy_id: 策略ID
        start_date: 回测开始日期
        end_date: 回测结束日期
        choose_stock: 自定义标的代码

    Returns:
        Optional[str]: 找到的回测结果信息，如果不存在则返回None
    """
    # 这个函数原来依赖于任务管理器，现在简化为始终返回None
    # 在未来版本中，可以实现一个更简单的文件系统扫描方法来查找相似的回测结果
    return None 