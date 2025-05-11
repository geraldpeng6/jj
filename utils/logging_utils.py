#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志工具模块

提供日志设置和配置功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(logger_name, log_level=logging.INFO, log_dir='data/logs', max_bytes=10485760, backup_count=5):
    """
    设置日志记录器

    Args:
        logger_name: 日志记录器名称
        log_level: 日志级别，默认为INFO
        log_dir: 日志目录，默认为'data/logs'
        max_bytes: 单个日志文件最大字节数，默认为10MB
        backup_count: 备份文件数量，默认为5

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)

    # 创建日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # 如果已经有处理器，不再添加
    if logger.handlers:
        return logger

    # 创建日志处理器，使用RotatingFileHandler进行日志轮转
    log_file = os.path.join(log_dir, f'{logger_name.split(".")[-1]}.log')
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
