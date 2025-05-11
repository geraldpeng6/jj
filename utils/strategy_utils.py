#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具模块

提供策略相关的功能，包括获取策略列表、策略详情、创建/更新/删除策略等
"""

import os
import json
import logging
import requests
import sys
from typing import Dict, Optional, Any, List, Tuple, Union

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

            # 保存策略列表到文件
            save_strategy_list_to_file(strategy_list, strategy_group)

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

            # 更新策略列表文件中的策略详情
            update_strategy_in_list(strategy_detail)

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


def create_strategy(strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    创建新策略

    Args:
        strategy_data: 策略数据，包含策略名称、配置等

    Returns:
        Optional[Dict[str, Any]]: 创建结果，包含策略ID等信息，创建失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    url = f"{BASE_URL}/trader-service/strategy/create"
    headers = get_headers()

    # 确保包含用户ID
    if isinstance(strategy_data, dict):
        strategy_data['user_id'] = user_id

    try:
        response = requests.post(url, json=strategy_data, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get('code') == 1 and data.get('msg') == 'ok':
            result = data.get('data', {})
            logger.info(f"创建策略成功，策略ID: {result.get('strategy_id')}")
            return result
        else:
            logger.error(f"创建策略失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败")
        return None
    except Exception as e:
        logger.error(f"创建策略时发生未知错误")
        return None


def update_strategy(strategy_id: str, strategy_data: Dict[str, Any]) -> requests.Response:
    """
    更新策略

    Args:
        strategy_id: 策略ID
        strategy_data: 策略数据，包含策略名称、配置等

    Returns:
        requests.Response: 更新请求的响应对象
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 首先获取现有策略详情，确保所有必需字段都存在
    existing_strategy = get_strategy_detail(strategy_id, "user")
    if not existing_strategy:
        logger.error(f"更新策略失败: 找不到策略ID {strategy_id}")
        return None

    # 构建完整的策略数据，确保包含所有必需字段
    complete_strategy_data = {
        "strategy_name": existing_strategy.get("strategy_name", ""),
        "indicator": existing_strategy.get("indicator", ""),
        "choose_stock": existing_strategy.get("choose_stock", ""),
        "timing": existing_strategy.get("timing", ""),
        "control_risk": existing_strategy.get("control_risk", ""),
        "strategy_id": strategy_id,
        "user_id": user_id
    }

    # 用新数据更新完整数据
    if isinstance(strategy_data, dict):
        for key, value in strategy_data.items():
            if key in complete_strategy_data and value is not None:
                complete_strategy_data[key] = value

    # 构建URL和请求参数
    url = f"{BASE_URL}/trader-service/strategy/user-strategy"
    params = {"user_id": user_id}
    headers = get_headers()

    try:
        # 使用PUT请求
        response = requests.put(url, params=params, json=complete_strategy_data, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 1 and result.get('msg') == 'ok':
            logger.info(f"更新策略成功，策略ID: {strategy_id}")
        else:
            logger.error(f"更新策略失败")

        # 返回完整的响应对象
        return response

    except Exception as e:
        logger.error(f"更新策略时发生错误")
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


def copy_strategy_from_library(library_strategy_id: str, strategy_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    从策略库复制策略到用户的策略列表

    Args:
        library_strategy_id: 策略库中的策略ID
        strategy_name: 新策略的名称，如果不提供则使用原策略名称

    Returns:
        Optional[Dict[str, Any]]: 复制结果，包含新策略ID等信息，复制失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    url = f"{BASE_URL}/trader-service/strategy/copy-from-library"
    headers = get_headers()

    data = {
        "user_id": user_id,
        "library_strategy_id": library_strategy_id
    }

    if strategy_name:
        data["strategy_name"] = strategy_name

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        result = response.json()

        if result.get('code') == 1 and result.get('msg') == 'ok':
            copy_result = result.get('data', {})
            logger.info(f"从策略库复制策略成功，新策略ID: {copy_result.get('strategy_id')}")
            return copy_result
        else:
            logger.error(f"从策略库复制策略失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败")
        return None
    except Exception as e:
        logger.error(f"从策略库复制策略时发生未知错误")
        return None


def save_strategy_list_to_file(strategy_list: List[Dict[str, Any]], strategy_group: str = "library") -> None:
    """
    将策略列表保存到策略列表文件中

    Args:
        strategy_list: 策略列表
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"library"
    """
    if not strategy_list:
        logger.warning("策略列表为空，无法保存")
        return

    # 保存到文件
    file_path = 'data/strategy/strategy_list.json'

    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 检查文件是否已存在
    existing_strategies = {}
    if os.path.exists(file_path):
        try:
            # 读取现有文件
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)

            # 如果现有数据不是列表，则创建新列表
            if not isinstance(existing_data, list):
                existing_data = []

            # 创建ID到策略的映射
            for strategy in existing_data:
                strategy_id = strategy.get('strategy_id')
                if strategy_id:
                    # 如果策略组相同或者现有策略没有策略组标识，则更新
                    if strategy.get('strategy_group') == strategy_group or 'strategy_group' not in strategy:
                        existing_strategies[strategy_id] = strategy

            # 查找相同ID的策略索引
            strategy_id_indices = {}
            for i, s in enumerate(existing_data):
                strategy_id = s.get('strategy_id')
                if strategy_id:
                    if strategy_id not in strategy_id_indices:
                        strategy_id_indices[strategy_id] = []
                    strategy_id_indices[strategy_id].append(i)

            # 删除重复的策略（保留最新的一个）
            for strategy_id, indices in strategy_id_indices.items():
                if len(indices) > 1:
                    # 从后往前删除，以避免索引变化
                    for i in sorted(indices[:-1], reverse=True):
                        del existing_data[i]

            # 更新策略列表
            for strategy in strategy_list:
                strategy_id = strategy.get('strategy_id')
                found = False

                # 查找并更新现有策略
                for i, s in enumerate(existing_data):
                    if s.get('strategy_id') == strategy_id:
                        # 保留现有的详情字段
                        for field in ['indicator', 'control_risk', 'timing', 'choose_stock']:
                            if field in s and field not in strategy:
                                strategy[field] = s[field]
                        # 替换现有策略
                        existing_data[i] = strategy
                        found = True
                        break

                if not found:
                    # 添加新策略
                    existing_data.append(strategy)

            # 保存更新后的数据，确保中文字符以可读形式存储
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            logger.info(f"策略列表已更新到文件: {file_path}")

        except Exception as e:
            logger.error(f"保存策略列表到文件时出错: {e}")
            # 如果读取现有文件出错，则直接覆盖，确保中文字符以可读形式存储
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_list, f, indent=2, ensure_ascii=False)
    else:
        # 文件不存在，直接写入，确保中文字符以可读形式存储
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(strategy_list, f, indent=2, ensure_ascii=False)
        logger.info(f"策略列表已保存到文件: {file_path}")


def update_strategy_in_list(strategy_detail: Dict[str, Any], file_path: str = 'data/strategy/strategy_list.json') -> bool:
    """
    更新策略列表文件中特定策略的详情

    Args:
        strategy_detail: 策略详情
        file_path: 策略列表文件路径

    Returns:
        bool: 更新是否成功
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 获取策略ID和策略组
    strategy_id = strategy_detail.get('strategy_id')
    strategy_group = strategy_detail.get('strategy_group', 'library')

    if not strategy_id:
        # 尝试从策略名称中获取ID
        strategy_name = strategy_detail.get('strategy_name')
        if strategy_name:
            # 查找具有相同名称的策略
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        strategy_list = json.load(f)

                    for strategy in strategy_list:
                        if strategy.get('strategy_name') == strategy_name and strategy.get('strategy_group') == strategy_group:
                            strategy_id = strategy.get('strategy_id')
                            strategy_detail['strategy_id'] = strategy_id
                            break
                except Exception as e:
                    logger.error(f"查找策略ID时出错: {e}")

        if not strategy_id:
            logger.error("策略详情中缺少策略ID，无法更新")
            return False

    # 读取现有策略库列表
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                strategy_list = json.load(f)

            # 查找并更新策略
            updated = False
            # 查找相同ID的策略索引
            same_id_indices = []
            for i, strategy in enumerate(strategy_list):
                if strategy.get('strategy_id') == strategy_id:
                    same_id_indices.append(i)

            # 如果找到多个相同ID的策略，删除除了与当前策略组匹配的之外的所有策略
            if len(same_id_indices) > 1:
                # 从后往前删除，以避免索引变化
                for i in sorted(same_id_indices, reverse=True):
                    if strategy_list[i].get('strategy_group') != strategy_group:
                        del strategy_list[i]

            # 再次查找并更新策略
            for i, strategy in enumerate(strategy_list):
                if strategy.get('strategy_id') == strategy_id and (strategy.get('strategy_group') == strategy_group or 'strategy_group' not in strategy):
                    # 保留原有的基本信息
                    strategy_name = strategy.get('strategy_name')
                    strategy_desc = strategy.get('strategy_desc')

                    # 更新策略详情
                    strategy_list[i] = strategy_detail

                    # 恢复基本信息（如果新详情中没有）
                    if strategy_name and 'strategy_name' not in strategy_detail:
                        strategy_list[i]['strategy_name'] = strategy_name
                    if strategy_desc and 'strategy_desc' not in strategy_detail:
                        strategy_list[i]['strategy_desc'] = strategy_desc

                    updated = True
                    break

            if not updated:
                logger.warning(f"未在策略列表中找到策略ID: {strategy_id}，将添加为新策略")
                strategy_list.append(strategy_detail)

            # 保存更新后的策略列表，确保中文字符以可读形式存储
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_list, f, indent=2, ensure_ascii=False)

            logger.info(f"已更新策略列表中的策略详情，策略ID: {strategy_id}")
            return True

        except Exception as e:
            logger.error(f"更新策略列表文件时出错: {e}")
            return False
    else:
        logger.error(f"策略列表文件不存在: {file_path}")
        # 创建新文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([strategy_detail], f, indent=2, ensure_ascii=False)
        logger.info(f"已创建策略列表文件并添加策略，策略ID: {strategy_id}")
        return True
