#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测历史记录工具模块

提供回测历史记录相关的功能，包括获取策略回测历史记录
"""

import json
import logging
import requests
from typing import Dict, Optional, Any, List
from datetime import datetime

from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_history_utils')

# API基础URL
BASE_URL = "https://api.yueniusz.com"


def get_strategy_backtest_history(strategy_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    获取策略回测历史记录列表

    Args:
        strategy_id: 策略ID

    Returns:
        Optional[List[Dict[str, Any]]]: 策略回测历史记录列表，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 构建URL
    url = f"{BASE_URL}/trader-service/strategy/back-test/strategy-history-list"
    
    # 构建参数
    params = {
        "strategy_id": strategy_id,
        "user_id": user_id
    }
    
    # 获取请求头
    headers = get_headers()

    try:
        # 发送请求
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()

        if data.get('code') == 1 and data.get('msg') == 'ok':
            # 获取历史记录列表
            history_list = data.get('data', {}).get('history_strategy_info', [])
            logger.info(f"获取策略回测历史记录成功，策略ID: {strategy_id}，共 {len(history_list)} 条记录")
            return history_list
        else:
            logger.error(f"获取策略回测历史记录失败，策略ID: {strategy_id}，错误信息: {data.get('msg')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取策略回测历史记录时发生未知错误: {str(e)}")
        return None


def get_backtest_history_detail(history_strategy_id: str) -> Optional[Dict[str, Any]]:
    """
    获取回测历史记录详情

    Args:
        history_strategy_id: 历史策略ID

    Returns:
        Optional[Dict[str, Any]]: 回测历史记录详情，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 构建URL
    url = f"{BASE_URL}/trader-service/strategy/back-test/strategy-history"
    
    # 构建参数
    params = {
        "history_strategy_id": history_strategy_id,
        "user_id": user_id
    }
    
    # 获取请求头
    headers = get_headers()

    try:
        # 发送请求
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()

        if data.get('code') == 1 and data.get('msg') == 'ok':
            # 获取历史记录详情
            history_detail = data.get('data', {})
            logger.info(f"获取回测历史记录详情成功，历史策略ID: {history_strategy_id}")
            return history_detail
        else:
            logger.error(f"获取回测历史记录详情失败，历史策略ID: {history_strategy_id}，错误信息: {data.get('msg')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取回测历史记录详情时发生未知错误: {str(e)}")
        return None


def format_backtest_history(history_list: List[Dict[str, Any]]) -> str:
    """
    格式化回测历史记录列表

    Args:
        history_list: 回测历史记录列表

    Returns:
        str: 格式化后的回测历史记录信息
    """
    if not history_list:
        return "没有找到回测历史记录"

    # 格式化输出
    result_str = f"策略回测历史记录，共 {len(history_list)} 条记录\n\n"

    # 显示历史记录列表
    for i, history in enumerate(history_list, 1):
        start_time = datetime.fromtimestamp(history.get('start', 0) / 1000).strftime('%Y-%m-%d') if history.get('start') else '未知'
        end_time = datetime.fromtimestamp(history.get('end', 0) / 1000).strftime('%Y-%m-%d') if history.get('end') else '未知'
        create_time = datetime.fromtimestamp(history.get('create_time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if history.get('create_time') else '未知'
        
        result_str += f"{i}. 历史记录ID: {history.get('history_strategy_id')}\n"
        result_str += f"   策略ID: {history.get('strategy_id')}\n"
        result_str += f"   收益率: {history.get('profit')}\n"
        result_str += f"   年化收益: {history.get('annual_profit')}\n"
        result_str += f"   最大回撤: {history.get('drawdown')}\n"
        result_str += f"   是否适合: {'是' if history.get('is_suitable') else '否'}\n"
        result_str += f"   回测区间: {start_time} 至 {end_time}\n"
        result_str += f"   创建时间: {create_time}\n"
        if history.get('remark'):
            result_str += f"   备注: {history.get('remark')}\n"
        result_str += "\n"

    return result_str 