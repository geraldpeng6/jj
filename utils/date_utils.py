#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日期时间工具模块

提供处理日期时间的辅助函数，包括北京时间转换和日期验证
"""

import logging
import datetime
import calendar
from typing import Optional, Tuple, Union
from datetime import datetime, timedelta, timezone
import re

# 获取日志记录器
logger = logging.getLogger('quant_mcp.date_utils')

# 北京时区 (UTC+8)
BEIJING_TIMEZONE = timezone(timedelta(hours=8))

def get_beijing_now() -> datetime:
    """
    获取北京时间的当前时间

    Returns:
        datetime: 北京时间的当前时间
    """
    # 获取UTC时间
    utc_now = datetime.now(timezone.utc)
    # 转换为北京时间
    beijing_now = utc_now.astimezone(BEIJING_TIMEZONE)
    # 返回没有时区信息的datetime对象，与原代码保持一致
    return beijing_now.replace(tzinfo=None)

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    解析日期字符串，支持多种格式，并验证日期有效性

    Args:
        date_str: 日期字符串，支持格式：YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD

    Returns:
        Optional[datetime]: 解析后的datetime对象，如果日期无效则返回None
    """
    if not date_str:
        return None
        
    # 尝试标准化日期字符串格式（处理不同的分隔符）
    normalized_date = re.sub(r'[./-]', '-', date_str.strip())
    
    # 尝试解析日期
    try:
        dt = datetime.strptime(normalized_date, "%Y-%m-%d")
        
        # 验证日期是否有效（例如处理2月29日在非闰年的情况）
        year, month, day = dt.year, dt.month, dt.day
        
        # 检查月份和日期是否有效
        if month < 1 or month > 12:
            logger.warning(f"无效的月份: {month} in {date_str}")
            return None
            
        # 获取该月的最大天数
        _, max_day = calendar.monthrange(year, month)
        if day < 1 or day > max_day:
            logger.warning(f"无效的日期: {year}-{month}-{day} (该月最大天数为 {max_day})")
            return None
            
        return dt
    except ValueError as e:
        logger.warning(f"解析日期字符串 '{date_str}' 失败: {e}")
        return None

def validate_date_range(start_date_str: Optional[str], end_date_str: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    验证日期范围的有效性，如果日期无效则尝试修复或返回None

    Args:
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串

    Returns:
        Tuple[Optional[str], Optional[str]]: 验证后的开始日期和结束日期字符串，格式为YYYY-MM-DD
    """
    # 获取当前北京时间
    beijing_now = get_beijing_now()
    
    # 设置默认值
    default_start_date = (beijing_now - timedelta(days=365)).strftime("%Y-%m-%d")
    default_end_date = beijing_now.strftime("%Y-%m-%d")
    
    # 解析开始日期
    start_date = None
    if start_date_str:
        start_date = parse_date_string(start_date_str)
        if not start_date:
            logger.warning(f"无效的开始日期 '{start_date_str}'，使用默认值: {default_start_date}")
            start_date_str = default_start_date
        else:
            # 格式化为标准格式
            start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date_str = default_start_date
    
    # 解析结束日期
    end_date = None
    if end_date_str:
        end_date = parse_date_string(end_date_str)
        if not end_date:
            logger.warning(f"无效的结束日期 '{end_date_str}'，使用默认值: {default_end_date}")
            end_date_str = default_end_date
        else:
            # 格式化为标准格式
            end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date_str = default_end_date
    
    # 验证日期顺序
    if start_date and end_date and start_date > end_date:
        logger.warning(f"开始日期 {start_date_str} 晚于结束日期 {end_date_str}，交换顺序")
        return end_date_str, start_date_str
    
    return start_date_str, end_date_str

def timestamp_to_beijing_time(timestamp_ms: int) -> datetime:
    """
    将毫秒时间戳转换为北京时间

    Args:
        timestamp_ms: 毫秒时间戳

    Returns:
        datetime: 北京时间的datetime对象
    """
    # 转换为UTC时间
    utc_time = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
    # 转换为北京时间
    beijing_time = utc_time.astimezone(BEIJING_TIMEZONE)
    # 返回没有时区信息的datetime对象
    return beijing_time.replace(tzinfo=None) 