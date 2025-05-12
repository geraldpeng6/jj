#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示模块初始化文件

导入并注册所有提示模板
"""

from mcp.server.fastmcp import FastMCP

def register_all_prompts(mcp: FastMCP):
    """
    注册所有提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 导入提示模块
    from src.prompts.kline_prompts import register_prompts as register_kline_prompts
    from src.prompts.strategy_prompts import register_prompts as register_strategy_prompts

    # 注册K线数据提示模板
    register_kline_prompts(mcp)

    # 注册交易策略提示模板
    register_strategy_prompts(mcp)
