#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
采样模块初始化文件

导入并注册所有采样配置
"""

from mcp.server.fastmcp import FastMCP

def register_all_sampling(mcp: FastMCP):
    """
    注册所有采样配置到MCP服务器
    
    Args:
        mcp: MCP服务器实例
    """
    # 导入采样模块
    from src.sampling.kline_sampling import register_sampling as register_kline_sampling
    from src.sampling.strategy_sampling import register_sampling as register_strategy_sampling
    
    # 注册K线数据采样配置
    register_kline_sampling(mcp)
    
    # 注册交易策略采样配置
    register_strategy_sampling(mcp)
