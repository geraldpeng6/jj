#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具模块

提供策略相关的功能，包括获取策略列表、策略详情、更新/删除策略等，所有策略在远程管理，不进行本地存储
"""

import json
import logging
import requests
from typing import Dict, Optional, Any, List

from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_utils')

# API基础URL
BASE_URL = "https://api.yueniusz.com"


def get_strategy_list(strategy_group: str = "user") -> Optional[List[Dict[str, Any]]]:
    """
    获取策略列表，可以是用户策略列表或策略库列表

    Args:
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"user"

    Returns:
        Optional[List[Dict[str, Any]]]: 策略列表，每个策略包含strategy_id、strategy_name等字段，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 根据策略组类型选择不同的URL
    if strategy_group == "library":
        url = f"{BASE_URL}/trader-service/strategy/strategy-library-list"
        log_prefix = "策略库"
    else:
        url = f"{BASE_URL}/trader-service/strategy/user-strategy-list"
        log_prefix = "用户策略"

    params = {"user_id": user_id}
    headers = get_headers()

    # 添加禁用压缩响应的头部
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 1 and data.get('msg') == 'ok':
            strategy_list = data.get('data', {}).get('strategy_list', [])

            # 为每个策略添加策略组标识
            for strategy in strategy_list:
                strategy['strategy_group'] = strategy_group
                # 为缺失的字段添加默认值None
                for field in ['indicator', 'control_risk', 'timing', 'choose_stock']:
                    if field not in strategy:
                        strategy[field] = None

            logger.info(f"获取{log_prefix}列表成功，共 {len(strategy_list)} 个策略")
            return strategy_list
        else:
            logger.error(f"获取{log_prefix}列表失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败")
        return None
    except Exception as e:
        logger.error(f"获取{log_prefix}列表时发生未知错误")
        return None


def get_strategy_detail(strategy_id: str, strategy_group: str = "library") -> Optional[Dict[str, Any]]:
    """
    获取策略详情，可以是用户策略详情或策略库策略详情

    Args:
        strategy_id: 策略ID
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"library"

    Returns:
        Optional[Dict[str, Any]]: 策略详情，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 根据策略组类型选择不同的URL
    if strategy_group == "user":
        url = f"{BASE_URL}/trader-service/strategy/user-strategy"
        log_prefix = "用户策略"
    else:
        url = f"{BASE_URL}/trader-service/strategy/strategy-library"
        log_prefix = "策略库"

    params = {
        "user_id": user_id,
        "strategy_id": strategy_id
    }
    headers = get_headers()

    # 添加禁用压缩响应的头部
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 1 and data.get('msg') == 'ok':
            strategy_detail = data.get('data', {})

            # 添加策略组标识和策略ID
            strategy_detail['strategy_group'] = strategy_group
            if 'strategy_id' not in strategy_detail:
                strategy_detail['strategy_id'] = strategy_id

            logger.info(f"获取{log_prefix}详情成功，策略ID: {strategy_id}")
            return strategy_detail
        else:
            logger.error(f"获取{log_prefix}详情失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败")
        return None
    except Exception as e:
        logger.error(f"获取{log_prefix}详情时发生未知错误")
        return None








def delete_strategy(strategy_id: str) -> requests.Response:
    """
    删除策略

    Args:
        strategy_id: 策略ID

    Returns:
        requests.Response: 删除请求的响应对象
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 构建URL和请求参数
    url = f"{BASE_URL}/trader-service/strategy/user-strategy"
    params = {"user_id": user_id}
    headers = get_headers()

    # 添加禁用压缩响应的头部
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应

    data = {
        "user_id": user_id,
        "strategy_id": strategy_id
    }

    try:
        # 使用DELETE请求
        response = requests.delete(url, params=params, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 1 and result.get('msg') == 'ok':
            logger.info(f"删除策略成功，策略ID: {strategy_id}")
        else:
            logger.error(f"删除策略失败")

        # 返回完整的响应对象
        return response

    except Exception as e:
        logger.error(f"删除策略时发生错误")
        return None






