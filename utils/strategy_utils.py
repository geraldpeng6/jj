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


def get_strategy_detail(strategy_id: str) -> Optional[Dict[str, Any]]:
    """
    获取策略详情，自动检查用户策略和策略库

    Args:
        strategy_id: 策略ID

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

    # 检查顺序：先检查用户策略，再检查策略库
    groups_to_check = ["user", "library"]
    
    # 存储结果
    results = {}
    
    # 遍历每个需要检查的组
    for group in groups_to_check:
        # 根据策略组类型选择不同的URL
        if group == "user":
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
            
            # 添加详细的响应日志，仅在调试模式下启用
            logger.debug(f"响应数据: {json.dumps(data, ensure_ascii=False)}")

            if data.get('code') == 1 and data.get('msg') == 'ok':
                strategy_detail = data.get('data', {})
                
                # 先检查数据是否为空
                if not strategy_detail:
                    logger.warning(f"在{log_prefix}中找到策略ID {strategy_id}，但返回了空数据")
                    results[group] = None
                    continue
                
                # 记录找到的详情字段
                logger.debug(f"在{log_prefix}中找到策略字段: {list(strategy_detail.keys())}")
                
                # 验证响应是否包含必要字段并且字段值不为空
                if 'strategy_name' not in strategy_detail or not strategy_detail.get('strategy_name'):
                    logger.warning(f"在{log_prefix}中找到策略ID {strategy_id}，但响应缺少策略名称或名称为空")
                    # 检查完整响应中是否可能有其他位置包含策略名称
                    if isinstance(data, dict) and isinstance(data.get('data'), dict):
                        logger.debug(f"响应data字段内容: {json.dumps(data.get('data'), ensure_ascii=False)}")
                    results[group] = None
                    continue
                
                # 添加策略组标识和策略ID
                strategy_detail['strategy_group'] = group
                if 'strategy_id' not in strategy_detail:
                    strategy_detail['strategy_id'] = strategy_id

                logger.info(f"获取{log_prefix}详情成功，策略ID: {strategy_id}")
                results[group] = strategy_detail
            else:
                logger.warning(f"在{log_prefix}中未找到策略，策略ID: {strategy_id}，响应状态: {data.get('code')}, 消息: {data.get('msg')}")
                results[group] = None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            results[group] = None
        except json.JSONDecodeError as e:
            logger.error(f"解析响应JSON失败: {e}")
            results[group] = None
        except Exception as e:
            logger.error(f"获取{log_prefix}详情时发生未知错误: {e}")
            results[group] = None
    
    # 优先返回更完整的结果
    if results.get("user") and 'strategy_name' in results["user"]:
        return results["user"]
    elif results.get("library") and 'strategy_name' in results["library"]:
        return results["library"]
    
    # 如果所有组都检查完毕仍未找到有效结果，则返回None
    logger.error(f"获取策略详情失败，在所有组中未找到有效策略，策略ID: {strategy_id}")
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


def create_user_strategy(strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    创建用户策略

    Args:
        strategy_data: 策略数据，包含strategy_name, indicator, choose_stock, timing, control_risk等字段

    Returns:
        Optional[Dict[str, Any]]: 创建结果，包含strategy_id字段，创建失败时返回None
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
    
    # 确保请求数据包含user_id
    strategy_data["user_id"] = user_id
    
    # 确保有策略名称
    if "strategy_name" not in strategy_data or not strategy_data["strategy_name"]:
        strategy_data["strategy_name"] = "未命名策略"
    
    # 添加禁用压缩响应的头部
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应

    try:
        # 使用POST请求创建策略
        response = requests.post(url, params=params, json=strategy_data, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 1 and result.get('msg') == 'ok':
            logger.info(f"创建策略成功: {strategy_data.get('strategy_name')}")
            # 返回创建结果，包含strategy_id
            return result.get('data', {})
        else:
            logger.error(f"创建策略失败: {result.get('msg', '未知错误')}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"创建策略请求失败: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析创建策略响应JSON失败: {e}")
        return None
    except Exception as e:
        logger.error(f"创建策略时发生未知错误: {e}")
        return None


def update_user_strategy(strategy_data: Dict[str, Any]) -> bool:
    """
    更新用户策略，包含预检查确保策略存在

    Args:
        strategy_data: 策略数据，必须包含strategy_id字段

    Returns:
        bool: 更新是否成功
    """
    # 加载认证配置
    if not load_auth_config():
        return False

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return False
    
    # 检查必要参数
    if "strategy_id" not in strategy_data or not strategy_data["strategy_id"]:
        logger.error("错误: 更新策略时缺少strategy_id")
        return False
    
    strategy_id = strategy_data["strategy_id"]
    
    # 先检查策略是否存在
    existing_strategy = get_strategy_detail(strategy_id)
    if not existing_strategy:
        logger.error(f"错误: 策略ID {strategy_id} 不存在，无法更新")
        return False
    
    # 如果不是用户策略，无法更新
    if existing_strategy.get("strategy_group") != "user":
        logger.error(f"错误: 策略ID {strategy_id} 不是用户策略，无法更新")
        return False

    # 构建URL和请求参数
    url = f"{BASE_URL}/trader-service/strategy/user-strategy"
    params = {"user_id": user_id}
    headers = get_headers()
    
    # 确保请求数据包含user_id
    strategy_data["user_id"] = user_id
    
    # 添加禁用压缩响应的头部
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应

    try:
        # 使用PUT请求更新策略
        response = requests.put(url, params=params, json=strategy_data, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 1 and result.get('msg') == 'ok':
            logger.info(f"更新策略成功，策略ID: {strategy_id}")
            return True
        else:
            logger.error(f"更新策略失败: {result.get('msg', '未知错误')}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"更新策略请求失败: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"解析更新策略响应JSON失败: {e}")
        return False
    except Exception as e:
        logger.error(f"更新策略时发生未知错误: {e}")
        return False






