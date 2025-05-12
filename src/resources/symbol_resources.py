#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票代码资源模块

提供股票代码相关的MCP资源
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, ResourceContents

from utils.symbol_utils import search_symbols, get_symbol_info

# 获取日志记录器
logger = logging.getLogger('quant_mcp.symbol_resources')

def register_resources(mcp: FastMCP):
    """
    注册股票代码相关的资源到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 添加股票列表资源
    mcp.add_resource(Resource(
        uri="symbol://list",
        name="股票列表",
        description="A股所有股票列表",
        mimeType="application/json"
    ))

    # 注册资源模板 - 使用不同的方式注册模板
    # 不使用add_resource，而是直接在resource装饰器中处理

    # 注册股票列表资源处理函数
    @mcp.resource("symbol://list")
    async def get_stock_list() -> str:
        """获取股票列表"""
        try:
            # 获取股票列表 (使用搜索功能获取常见股票)
            stock_list = search_symbols("上证50", exchange="XSHG")
            if stock_list is None:
                return "获取股票列表失败"

            # 转换为JSON
            return json.dumps(stock_list, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取股票列表时发生错误: {e}")
            return f"获取股票列表时发生错误: {e}"

    # 注册股票信息资源处理函数
    @mcp.resource("symbol://info/{symbol}")
    async def get_stock_info(symbol: str) -> str:
        """获取股票信息"""
        try:
            # 获取股票信息
            stock_info = get_symbol_info(f"{symbol}.XSHG")
            if stock_info is None:
                # 尝试上交所失败，再尝试深交所
                stock_info = get_symbol_info(f"{symbol}.XSHE")
                if stock_info is None:
                    return f"获取股票 {symbol} 的信息失败"

            # 转换为JSON
            return json.dumps(stock_info, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取股票信息时发生错误: {e}")
            return f"获取股票信息时发生错误: {e}"


