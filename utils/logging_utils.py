#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块

提供日志设置和配置功能，按功能组织日志文件
"""

import os
import logging
import time
import sys
from logging.handlers import RotatingFileHandler


def configure_root_logger(log_level=logging.INFO, log_dir='data/logs'):
    """
    配置根日志记录器，确保所有模块的日志都能正确输出到文件

    Args:
        log_level: 日志级别，默认为INFO
        log_dir: 日志根目录，默认为'data/logs'

    Returns:
        logging.Logger: 配置好的根日志记录器
    """
    # 确保日志根目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 如果已经有处理器，先移除所有处理器
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    # 创建日志文件路径
    log_file = os.path.join(log_dir, 'root.log')
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    root_logger.addHandler(file_handler)
    
    # 配置一个控制台处理器，让日志也输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def setup_logging(logger_name, log_level=logging.INFO, log_dir='data/logs', max_bytes=10485760, backup_count=5):
    """
    设置日志记录器，按功能组织日志文件

    Args:
        logger_name: 日志记录器名称，例如 'quant_mcp.backtest_tools'
        log_level: 日志级别，默认为INFO
        log_dir: 日志根目录，默认为'data/logs'
        max_bytes: 单个日志文件最大字节数，默认为10MB
        backup_count: 备份文件数量，默认为5

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志根目录存在
    os.makedirs(log_dir, exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # 如果已经有处理器，清除所有处理器
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # 解析logger_name，提取功能模块名称
    # 例如从 'quant_mcp.backtest_tools' 提取 'backtest'
    parts = logger_name.split('.')
    
    # 确定日志文件所属的功能模块
    feature = "general"  # 默认为通用日志
    
    if len(parts) > 1:
        # 检查是否有功能标识
        if 'backtest' in parts[-1]:
            feature = "backtest"
        elif 'kline' in parts[-1]:
            feature = "kline"
        elif 'strategy' in parts[-1]:
            feature = "strategy"
        elif 'market' in parts[-1]:
            feature = "market"
        elif 'symbol' in parts[-1]:
            feature = "symbol"
        elif 'chart' in parts[-1]:
            feature = "chart"
        elif 'auth' in parts[-1]:
            feature = "auth"
        elif 'server' in parts[-1]:
            feature = "server"
        elif 'html_server' in parts[-1]:
            feature = "html"
        elif 'prompt' in parts[-1]:
            feature = "prompt"
        else:
            # 使用最后一个部分作为功能名称
            feature = parts[-1]
    
    # 确保功能日志目录存在
    feature_log_dir = os.path.join(log_dir, feature)
    os.makedirs(feature_log_dir, exist_ok=True)
    
    # 创建以日期命名的日志文件名
    today = time.strftime("%Y%m%d")
    log_filename = f"{feature}_{today}.log"
    log_file = os.path.join(feature_log_dir, log_filename)

    # 创建日志处理器，使用RotatingFileHandler进行日志轮转
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )

    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # 添加处理器到记录器
    logger.addHandler(file_handler)

    # 防止日志重复输出
    logger.propagate = False

    return logger
