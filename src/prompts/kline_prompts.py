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
    # 不再使用add_prompt方法，而是直接使用prompt装饰器
    # 这样可以避免'Prompt'对象没有'render'属性的错误

    # 注册K线分析提示处理函数
    @mcp.prompt("analyze_kline")
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

    # 注册股票比较提示处理函数
    @mcp.prompt("compare_stocks")
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


