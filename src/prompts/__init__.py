#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示模块初始化文件

导入并注册所有提示模板
"""

import logging
from mcp.server.fastmcp import FastMCP

# 获取日志记录器
logger = logging.getLogger('quant_mcp.prompts')

def register_all_prompts(mcp: FastMCP):
    """
    注册所有提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 导入提示模块
    from src.prompts.kline_prompts import register_prompts as register_kline_prompts
    from src.prompts.strategy_prompts import register_prompts as register_strategy_prompts
    from src.prompts.market_prompts import register_prompts as register_market_prompts
    from src.prompts.technical_prompts import register_prompts as register_technical_prompts
    from src.prompts.fundamental_prompts import register_prompts as register_fundamental_prompts
    from src.prompts.portfolio_prompts import register_prompts as register_portfolio_prompts
    from src.prompts.backtest_prompts import register_prompts as register_backtest_prompts

    # 注册K线数据提示模板
    logger.info("注册K线数据提示模板")
    register_kline_prompts(mcp)

    # 注册交易策略提示模板
    logger.info("注册交易策略提示模板")
    register_strategy_prompts(mcp)

    # 注册市场分析提示模板
    logger.info("注册市场分析提示模板")
    register_market_prompts(mcp)

    # 注册技术分析提示模板
    logger.info("注册技术分析提示模板")
    register_technical_prompts(mcp)

    # 注册基本面分析提示模板
    logger.info("注册基本面分析提示模板")
    register_fundamental_prompts(mcp)

    # 注册投资组合管理提示模板
    logger.info("注册投资组合管理提示模板")
    register_portfolio_prompts(mcp)

    # 注册回测分析提示模板
    logger.info("注册回测分析提示模板")
    register_backtest_prompts(mcp)
