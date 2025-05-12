#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据提示模块

提供K线数据分析相关的MCP提示模板
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent, GetPromptResult

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_prompts')

def register_prompts(mcp: FastMCP):
    """
    注册K线数据相关的提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 定义K线分析提示处理函数
    async def get_analyze_kline_prompt(symbol: str, exchange: str, resolution: str, analysis_type: str = "all") -> GetPromptResult:
        """获取K线分析提示模板"""
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请分析 {symbol} 在 {exchange} 交易所的 {resolution} K线数据。"
                    f"我需要{'全面' if analysis_type == 'all' else analysis_type}分析，"
                    f"包括{'趋势分析、形态分析和指标分析' if analysis_type == 'all' else analysis_type}。"
                    f"请使用资源 kline://{exchange}/{symbol}/{resolution} 获取K线数据。"
                    f"分析应包括：\n"
                    f"1. 价格趋势和关键支撑/阻力位\n"
                    f"2. 成交量分析\n"
                    f"3. 主要技术指标（如MACD、RSI等）\n"
                    f"4. 形态识别（如头肩顶、双底等）\n"
                    f"5. 总体市场观点和可能的交易机会"
                )
            )
        ]

        return GetPromptResult(messages=messages)

    # 定义股票比较提示处理函数
    async def get_compare_stocks_prompt(symbols: str, exchange: str, resolution: str, comparison_period: str = "3m") -> GetPromptResult:
        """获取股票比较提示模板"""
        # 解析股票代码列表
        symbol_list = symbols.split(",")

        # 构建提示消息
        symbols_text = ", ".join(symbol_list)
        resources_text = "\n".join([f"- kline://{exchange}/{symbol.strip()}/{resolution}" for symbol in symbol_list])

        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请比较以下股票在{comparison_period}期间的表现：{symbols_text}。\n\n"
                    f"使用以下资源获取K线数据：\n{resources_text}\n\n"
                    f"比较应包括：\n"
                    f"1. 价格走势对比\n"
                    f"2. 相对强弱分析\n"
                    f"3. 波动性比较\n"
                    f"4. 成交量对比\n"
                    f"5. 相关性分析\n"
                    f"6. 总体评估和投资建议"
                )
            )
        ]

        return GetPromptResult(messages=messages)

    # 注册带有元数据的提示模板
    try:
        # 为K线分析提示添加元数据
        analyze_kline_metadata = Prompt(
            name="analyze_kline",
            description="分析股票K线数据",
            arguments=[
                PromptArgument(
                    name="symbol",
                    description="股票代码 [默认值: AAPL] [建议: AAPL, MSFT, GOOG, AMZN, BABA, 600519, 000001]",
                    required=True
                ),
                PromptArgument(
                    name="exchange",
                    description="交易所 [默认值: US] [建议: US, HK, SH, SZ, binance, okex]",
                    required=True
                ),
                PromptArgument(
                    name="resolution",
                    description="K线周期 [默认值: D] [建议: D, 240, 60, 30, 15, 5, 1]",
                    required=True
                ),
                PromptArgument(
                    name="analysis_type",
                    description="分析类型 [默认值: all] [建议: all, 趋势分析, 形态分析, 指标分析, 支撑阻力, 成交量分析]",
                    required=False
                )
            ]
        )

        # 为股票比较提示添加元数据
        compare_stocks_metadata = Prompt(
            name="compare_stocks",
            description="比较多只股票的表现",
            arguments=[
                PromptArgument(
                    name="symbols",
                    description="股票代码列表（用逗号分隔） [默认值: AAPL,MSFT,GOOG] [建议: AAPL,MSFT,GOOG, BABA,JD,PDD, 600519,000858,002304]",
                    required=True
                ),
                PromptArgument(
                    name="exchange",
                    description="交易所 [默认值: US] [建议: US, HK, SH, SZ]",
                    required=True
                ),
                PromptArgument(
                    name="resolution",
                    description="K线周期 [默认值: D] [建议: D, W, M]",
                    required=True
                ),
                PromptArgument(
                    name="comparison_period",
                    description="比较周期 [默认值: 3m] [建议: 1m, 3m, 6m, 1y, 3y, 5y, ytd]",
                    required=False
                )
            ]
        )

        # 注册带有元数据的提示模板
        mcp.register_prompt_with_metadata("analyze_kline", get_analyze_kline_prompt, analyze_kline_metadata)
        mcp.register_prompt_with_metadata("compare_stocks", get_compare_stocks_prompt, compare_stocks_metadata)
        logger.info("成功注册K线数据提示模板")
    except Exception as e:
        logger.error(f"注册K线数据提示模板时发生错误: {e}")

