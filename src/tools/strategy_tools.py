#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具模块

提供策略相关的MCP工具
"""

import json
import logging
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from utils.strategy_utils import (
    get_strategy_list,
    get_strategy_detail,
    create_strategy,
    update_strategy,
    delete_strategy,
    copy_strategy_from_library
)

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_tools')


async def list_strategies(strategy_group: str = "user") -> str:
    """
    获取策略列表

    Args:
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"user"

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


async def get_strategy(strategy_id: str, strategy_group: str = "user") -> str:
    """
    获取策略详情

    Args:
        strategy_id: 策略ID
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"user"

    Returns:
        str: 格式化的策略详情信息，或错误信息
    """
    try:
        # 从utils模块获取策略详情
        strategy_detail = get_strategy_detail(strategy_id, strategy_group)

        if not strategy_detail:
            return f"获取策略详情失败，策略ID: {strategy_id}"

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


async def create_new_strategy(
    strategy_name: str,
    choose_stock: str,
    indicator: str,
    timing: str,
    control_risk: str,
    strategy_desc: Optional[str] = None
) -> str:
    """
    创建新策略

    Args:
        strategy_name: 策略名称
        choose_stock: 选股代码
        indicator: 指标代码
        timing: 择时代码
        control_risk: 风控代码
        strategy_desc: 策略描述，可选

    Returns:
        str: 创建结果信息，或错误信息
    """
    try:
        # 构建策略数据
        strategy_data = {
            "strategy_name": strategy_name,
            "choose_stock": choose_stock,
            "indicator": indicator,
            "timing": timing,
            "control_risk": control_risk
        }

        # 添加策略描述（如果提供）
        if strategy_desc:
            strategy_data["strategy_desc"] = [strategy_desc]

        # 从utils模块创建策略
        result = create_strategy(strategy_data)

        if not result:
            return f"创建策略失败: {strategy_name}"

        # 格式化输出
        result_str = f"成功创建策略: {strategy_name}\n\n"
        result_str += f"策略ID: {result.get('strategy_id', '无ID')}\n"

        # 获取新创建的策略详情
        strategy_detail = get_strategy_detail(result.get('strategy_id'), "user")
        if strategy_detail:
            result_str += "\n策略已保存到用户策略列表中。\n"
            result_str += f"可以使用 get_strategy 工具查看详情: get_strategy(strategy_id='{result.get('strategy_id')}', strategy_group='user')"

        return result_str

    except Exception as e:
        logger.error(f"创建策略时发生错误: {e}")
        return f"创建策略时发生错误: {e}"


async def update_existing_strategy(
    strategy_id: str,
    strategy_name: Optional[str] = None,
    choose_stock: Optional[str] = None,
    indicator: Optional[str] = None,
    timing: Optional[str] = None,
    control_risk: Optional[str] = None,
    strategy_desc: Optional[str] = None
) -> str:
    """
    更新现有策略

    注意：API要求所有字段（strategy_name, choose_stock, indicator, timing, control_risk, strategy_id, user_id）
    都必须在请求中提供。如果某些字段未提供，将使用策略的现有值。

    Args:
        strategy_id: 策略ID（必需）
        strategy_name: 策略名称，如果不提供则使用现有值
        choose_stock: 选股代码，如果不提供则使用现有值
        indicator: 指标代码，如果不提供则使用现有值
        timing: 择时代码，如果不提供则使用现有值
        control_risk: 风控代码，如果不提供则使用现有值
        strategy_desc: 策略描述，如果不提供则使用现有值

    Returns:
        str: 更新结果信息，或错误信息
    """
    try:
        # 首先获取现有策略详情
        existing_strategy = get_strategy_detail(strategy_id, "user")
        if not existing_strategy:
            return f"更新策略失败: 找不到策略ID {strategy_id}"

        # 构建更新数据，只包含用户提供的字段
        strategy_data = {}

        # 如果用户提供了新值，则使用新值；否则，utils/strategy_utils.py中的update_strategy函数会使用现有值
        if strategy_name is not None:
            strategy_data["strategy_name"] = strategy_name

        if choose_stock is not None:
            strategy_data["choose_stock"] = choose_stock

        if indicator is not None:
            strategy_data["indicator"] = indicator

        if timing is not None:
            strategy_data["timing"] = timing

        if control_risk is not None:
            strategy_data["control_risk"] = control_risk

        if strategy_desc is not None:
            strategy_data["strategy_desc"] = [strategy_desc]

        # 从utils模块更新策略
        response = update_strategy(strategy_id, strategy_data)

        if not response:
            return f"更新策略失败: 策略ID {strategy_id}"

        # 解析响应
        try:
            result = response.json()
            if result.get('code') != 1 or result.get('msg') != 'ok':
                return f"更新策略失败: 策略ID {strategy_id}, 服务器返回: {result.get('msg', '未知错误')}"
        except Exception:
            return f"更新策略失败: 无法解析响应"

        # 格式化输出
        result_str = f"成功更新策略: {strategy_data.get('strategy_name')}\n\n"
        result_str += f"策略ID: {strategy_id}\n"
        result_str += f"\n响应状态码: {response.status_code}\n"
        result_str += f"响应内容: {response.text}\n"

        # 获取更新后的策略详情
        updated_strategy = get_strategy_detail(strategy_id, "user")
        if updated_strategy:
            result_str += "\n策略已更新。\n"
            result_str += f"可以使用 get_strategy 工具查看详情: get_strategy(strategy_id='{strategy_id}', strategy_group='user')"

        return result_str

    except Exception as e:
        logger.error(f"更新策略时发生错误: {e}")
        return f"更新策略时发生错误: {e}"


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
        strategy_detail = get_strategy_detail(strategy_id, "user")
        if not strategy_detail:
            return f"删除策略失败: 找不到策略ID {strategy_id}"

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


async def copy_library_strategy(library_strategy_id: str, new_strategy_name: Optional[str] = None) -> str:
    """
    从策略库复制策略到用户策略列表

    Args:
        library_strategy_id: 策略库中的策略ID
        new_strategy_name: 新策略的名称，可选，如果不提供则使用原策略名称

    Returns:
        str: 复制结果信息，或错误信息
    """
    try:
        # 首先获取策略库中的策略详情，确保策略存在
        library_strategy = get_strategy_detail(library_strategy_id, "library")
        if not library_strategy:
            return f"复制策略失败: 找不到策略库中的策略ID {library_strategy_id}"

        original_name = library_strategy.get("strategy_name", "未命名策略")

        # 从utils模块复制策略
        result = copy_strategy_from_library(library_strategy_id, new_strategy_name)

        if not result:
            return f"复制策略失败: 策略ID {library_strategy_id}"

        new_strategy_id = result.get("strategy_id")

        # 格式化输出
        if new_strategy_name:
            result_str = f"成功将策略库中的策略 '{original_name}' 复制为用户策略 '{new_strategy_name}'\n\n"
        else:
            result_str = f"成功将策略库中的策略 '{original_name}' 复制到用户策略列表\n\n"

        result_str += f"新策略ID: {new_strategy_id}\n"

        # 获取新复制的策略详情
        new_strategy = get_strategy_detail(new_strategy_id, "user")
        if new_strategy:
            result_str += "\n策略已复制到用户策略列表中。\n"
            result_str += f"可以使用 get_strategy 工具查看详情: get_strategy(strategy_id='{new_strategy_id}', strategy_group='user')"

        return result_str

    except Exception as e:
        logger.error(f"复制策略时发生错误: {e}")
        return f"复制策略时发生错误: {e}"


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

    # 注册创建策略工具
    mcp.tool()(create_new_strategy)

    # 注册更新策略工具
    mcp.tool()(update_existing_strategy)

    # 注册删除策略工具
    mcp.tool()(delete_user_strategy)

    # 注册复制策略工具
    mcp.tool()(copy_library_strategy)
