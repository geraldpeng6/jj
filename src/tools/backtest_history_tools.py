#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测历史记录工具模块

提供回测历史记录相关的MCP工具
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from utils.backtest_history_utils import (
    get_strategy_backtest_history,
    get_backtest_history_detail,
    format_backtest_history
)
from utils.strategy_utils import get_strategy_detail

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_history_tools')


async def get_strategy_history_list(strategy_id: str) -> str:
    """
    获取策略回测历史记录列表

    Args:
        strategy_id: 策略ID

    Returns:
        str: 格式化的策略回测历史记录信息，或错误信息
    """
    try:
        # 首先获取策略详情，确保策略存在
        strategy = get_strategy_detail(strategy_id)
        if not strategy:
            return f"获取策略回测历史记录失败: 找不到策略ID {strategy_id}"

        strategy_name = strategy.get('strategy_name', '未命名策略')

        # 获取策略回测历史记录
        history_list = get_strategy_backtest_history(strategy_id)
        if history_list is None:
            return f"获取策略回测历史记录失败: 策略ID {strategy_id} ({strategy_name})"

        # 格式化回测历史记录
        result_str = f"策略 '{strategy_name}' 的回测历史记录\n\n"
        if history_list:
            result_str += format_backtest_history(history_list)
        else:
            result_str += "该策略没有回测历史记录"

        return result_str

    except Exception as e:
        logger.error(f"获取策略回测历史记录时发生错误: {e}")
        return f"获取策略回测历史记录时发生错误: {e}"


async def get_history_detail(history_strategy_id: str, strategy_id: Optional[str] = None) -> str:
    """
    获取回测历史记录详情

    Args:
        history_strategy_id: 历史策略ID
        strategy_id: 策略ID，可选，如果提供则会显示策略名称

    Returns:
        str: 格式化的回测历史记录详情信息，或错误信息
    """
    try:
        # 如果提供了策略ID，获取策略详情
        strategy_name = "未知策略"
        if strategy_id:
            strategy = get_strategy_detail(strategy_id)
            if strategy:
                strategy_name = strategy.get('strategy_name', '未命名策略')

        # 获取回测历史记录详情
        history_detail = get_backtest_history_detail(history_strategy_id)
        if history_detail is None:
            return f"获取回测历史记录详情失败: 历史策略ID {history_strategy_id}"

        # 格式化历史记录详情
        result_str = f"回测历史记录详情 - 历史策略ID: {history_strategy_id}\n\n"
        
        if strategy_id:
            result_str += f"策略名称: {strategy_name}\n"
            result_str += f"策略ID: {strategy_id}\n\n"
        
        # 添加历史记录详情
        # 这里根据实际API返回的数据结构调整字段显示
        # 简单示例，实际应根据API返回数据结构调整
        for key, value in history_detail.items():
            if key == 'history_strategy_id' or key == 'strategy_id':
                continue  # 已经显示过了
            result_str += f"{key}: {value}\n"

        return result_str

    except Exception as e:
        logger.error(f"获取回测历史记录详情时发生错误: {e}")
        return f"获取回测历史记录详情时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册工具
    mcp.add_tool(get_strategy_history_list)
    mcp.add_tool(get_history_detail) 