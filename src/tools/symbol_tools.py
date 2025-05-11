#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票符号工具模块

提供股票符号相关的MCP工具
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from utils.symbol_utils import get_symbol_info

# 获取日志记录器
logger = logging.getLogger('quant_mcp.symbol_tools')


async def get_stock_info(full_name: str) -> str:
    """
    获取股票详细信息

    Args:
        full_name: 完整的股票代码，例如 "600000.XSHG"

    Returns:
        str: 格式化的股票信息，或错误信息
    """
    try:
        # 从utils模块获取股票信息
        symbol_info = get_symbol_info(full_name)

        if not symbol_info:
            return f"获取股票信息失败: {full_name}"

        # 格式化输出
        result_str = f"股票信息 - {full_name}\n\n"

        # 添加基本信息
        result_str += "基本信息:\n"
        result_str += f"- 代码: {symbol_info.get('symbol', '-')}\n"
        result_str += f"- 交易所: {symbol_info.get('exchange', '-')}\n"
        result_str += f"- 名称: {symbol_info.get('name', symbol_info.get('description', '-'))}\n"
        result_str += f"- 类型: {symbol_info.get('type', '-')}\n"

        # 添加交易信息
        result_str += "\n交易信息:\n"
        result_str += f"- 状态: {symbol_info.get('data_status', '-')}\n"
        result_str += f"- 上市日期: {symbol_info.get('start_date', '-')}\n"
        result_str += f"- 最后日期: {symbol_info.get('end_date', '-')}\n"

        # 添加价格信息
        result_str += "\n价格信息:\n"
        result_str += f"- 最小变动价位: {symbol_info.get('minmov', '-')}\n"
        result_str += f"- 价格精度: {symbol_info.get('pricescale', '-')}\n"

        # 添加交易时段信息
        if symbol_info.get('session'):
            result_str += f"\n交易时段: {symbol_info.get('session', '-')}\n"

        # 添加时区信息
        if symbol_info.get('timezone'):
            result_str += f"时区: {symbol_info.get('timezone', '-')}\n"

        # 添加支持的分辨率
        if symbol_info.get('supported_resolutions'):
            resolutions = symbol_info.get('supported_resolutions', [])
            if isinstance(resolutions, list) and resolutions:
                result_str += f"支持的时间周期: {', '.join(resolutions)}\n"

        # 添加描述信息
        if symbol_info.get('description'):
            result_str += f"\n描述: {symbol_info.get('description', '-')}\n"

        if symbol_info.get('volume_precision') is not None:
            result_str += f"\n成交量精度: {symbol_info.get('volume_precision', '-')}\n"

        return result_str

    except Exception as e:
        logger.error(f"获取股票信息时发生错误: {e}")
        return f"获取股票信息时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册股票符号相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册获取股票信息工具
    mcp.tool()(get_stock_info)
