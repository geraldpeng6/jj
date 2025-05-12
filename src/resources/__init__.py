#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
资源模块初始化文件

导入并注册所有资源
"""

from mcp.server.fastmcp import FastMCP

def register_all_resources(mcp: FastMCP):
    """
    注册所有资源到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 导入资源模块
    from src.resources.kline_resources import register_resources as register_kline_resources
    from src.resources.symbol_resources import register_resources as register_symbol_resources

    # 注册K线数据资源
    register_kline_resources(mcp)

    # 注册股票代码资源
    register_symbol_resources(mcp)
