#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具模块

提供策略相关的MCP工具，仅支持查询和删除操作，所有策略在远程管理，不进行本地存储
"""

import json
import logging
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from utils.strategy_utils import (
    get_strategy_list,
    get_strategy_detail,
    delete_strategy
)

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_tools')


async def list_strategies(strategy_group: str = "library") -> str:
    """
    获取策略列表

    Args:
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"library"

    Returns:
        str: 格式化的策略列表信息，或错误信息
    """
    try:
        # 从utils模块获取策略列表
        strategy_list = get_strategy_list(strategy_group)

        if not strategy_list:
            return f"获取{'策略库' if strategy_group == 'library' else '用户策略'}列表失败"

        # 格式化输出
        result_str = f"{'策略库' if strategy_group == 'library' else '用户策略'}列表，共 {len(strategy_list)} 个策略\n\n"

        # 显示策略列表
        for i, strategy in enumerate(strategy_list, 1):
            result_str += f"{i}. {strategy.get('strategy_name', '未命名策略')}\n"
            result_str += f"   ID: {strategy.get('strategy_id', '无ID')}\n"
            if strategy.get('strategy_desc'):
                if isinstance(strategy.get('strategy_desc'), list):
                    result_str += f"   描述: {', '.join(strategy.get('strategy_desc'))}\n"
                else:
                    result_str += f"   描述: {strategy.get('strategy_desc')}\n"
            result_str += "\n"

        return result_str

    except Exception as e:
        logger.error(f"获取策略列表时发生错误: {e}")
        return f"获取策略列表时发生错误: {e}"


async def get_strategy(strategy_id: str) -> str:
    """
    获取策略详情，自动检查用户策略和策略库

    Args:
        strategy_id: 策略ID

    Returns:
        str: 格式化的策略详情信息，或错误信息
    """
    try:
        # 从utils模块获取策略详情，自动检查两个库
        strategy_detail = get_strategy_detail(strategy_id)

        if not strategy_detail:
            return f"获取策略详情失败，策略ID: {strategy_id}，该策略在用户策略和策略库中均未找到"

        # 获取策略组类型
        strategy_group = strategy_detail.get('strategy_group', '未知')

        # 格式化输出
        result_str = f"策略详情 - {strategy_detail.get('strategy_name', '未命名策略')}\n\n"

        # 添加基本信息
        result_str += "基本信息:\n"
        result_str += f"- ID: {strategy_detail.get('strategy_id', '无ID')}\n"
        result_str += f"- 名称: {strategy_detail.get('strategy_name', '未命名策略')}\n"
        result_str += f"- 类型: {'策略库策略' if strategy_group == 'library' else '用户策略'}\n"

        # 添加描述信息
        if strategy_detail.get('strategy_desc'):
            if isinstance(strategy_detail.get('strategy_desc'), list):
                result_str += f"- 描述: {', '.join(strategy_detail.get('strategy_desc'))}\n"
            else:
                result_str += f"- 描述: {strategy_detail.get('strategy_desc')}\n"

        # 添加策略代码信息
        result_str += "\n策略代码:\n"

        # 选股代码
        if strategy_detail.get('choose_stock'):
            result_str += "\n选股代码:\n```python\n"
            result_str += strategy_detail.get('choose_stock', '')
            result_str += "\n```\n"

        # 指标代码
        if strategy_detail.get('indicator'):
            result_str += "\n指标代码:\n```python\n"
            result_str += strategy_detail.get('indicator', '')
            result_str += "\n```\n"

        # 择时代码
        if strategy_detail.get('timing'):
            result_str += "\n择时代码:\n```python\n"
            result_str += strategy_detail.get('timing', '')
            result_str += "\n```\n"

        # 风控代码
        if strategy_detail.get('control_risk'):
            result_str += "\n风控代码:\n```python\n"
            result_str += strategy_detail.get('control_risk', '')
            result_str += "\n```\n"

        return result_str

    except Exception as e:
        logger.error(f"获取策略详情时发生错误: {e}")
        return f"获取策略详情时发生错误: {e}"


async def delete_user_strategy(strategy_id: str) -> str:
    """
    删除用户策略

    Args:
        strategy_id: 策略ID

    Returns:
        str: 删除结果信息，或错误信息
    """
    try:
        # 首先获取策略详情，确保策略存在
        strategy_detail = get_strategy_detail(strategy_id)
        if not strategy_detail:
            return f"删除策略失败: 找不到策略ID {strategy_id}"

        # 检查策略是否为用户策略
        if strategy_detail.get("strategy_group") != "user":
            return f"删除策略失败: 策略ID {strategy_id} 不是用户策略，无法删除"

        strategy_name = strategy_detail.get("strategy_name", "未命名策略")

        # 从utils模块删除策略
        response = delete_strategy(strategy_id)

        if not response:
            return f"删除策略失败: 策略ID {strategy_id}"

        # 解析响应
        try:
            result = response.json()
            if result.get('code') != 1 or result.get('msg') != 'ok':
                return f"删除策略失败: 策略ID {strategy_id}, 服务器返回: {result.get('msg', '未知错误')}"
        except Exception:
            return f"删除策略失败: 无法解析响应"

        # 格式化输出
        result_str = f"成功删除策略: {strategy_name}\n\n"
        result_str += f"策略ID: {strategy_id}\n"
        result_str += f"\n响应状态码: {response.status_code}\n"
        result_str += f"响应内容: {response.text}\n"

        return result_str

    except Exception as e:
        logger.error(f"删除策略时发生错误: {e}")
        return f"删除策略时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册策略相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册策略列表工具
    mcp.tool()(list_strategies)

    # 注册获取策略详情工具
    mcp.tool()(get_strategy)

    # 注册删除策略工具
    mcp.tool()(delete_user_strategy)
