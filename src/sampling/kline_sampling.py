#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据采样模块

提供K线数据分析相关的MCP采样配置
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    SamplingMessage,
    TextContent,
    ModelPreferences,
    CreateMessageRequest,
    EmbeddedResource,
    TextResourceContents
)

# 导入采样工具
from src.utils.sampling_utils import request_sampling, SYSTEM_PROMPTS, MODEL_PREFERENCES

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_sampling')

def register_sampling(mcp: FastMCP):
    """
    注册K线数据相关的采样配置到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    logger.info("注册K线数据采样配置")

    # 注册K线分析采样处理函数
    async def analyze_kline_with_sampling(
        symbol: str,
        exchange: str,
        resolution: str,
        analysis_type: str = "all"
    ) -> Optional[Dict[str, Any]]:
        """
        使用采样分析K线数据

        Args:
            symbol: 股票代码
            exchange: 交易所代码
            resolution: 时间周期
            analysis_type: 分析类型

        Returns:
            Optional[Dict[str, Any]]: 采样结果
        """
        try:
            # 构建资源URI
            resource_uri = f"kline://{exchange}/{symbol}/{resolution}"

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": f"请分析 {symbol} 在 {exchange} 交易所的 {resolution} K线数据。"
                    f"我需要{'全面' if analysis_type == 'all' else analysis_type}分析，"
                    f"包括{'趋势分析、形态分析和指标分析' if analysis_type == 'all' else analysis_type}。"
                    f"分析应包括：\n"
                    f"1. 价格趋势和关键支撑/阻力位\n"
                    f"2. 成交量分析\n"
                    f"3. 主要技术指标（如MACD、RSI等）\n"
                    f"4. 形态识别（如头肩顶、双底等）\n"
                    f"5. 总体市场观点和可能的交易机会"
                },
                {
                    "role": "user",
                    "content": EmbeddedResource(
                        type="resource",
                        resource=TextResourceContents(
                            uri=resource_uri,
                            mimeType="text/csv",
                            text=""  # 添加必需的text字段
                        )
                    )
                }
            ]

            # 请求采样
            return await request_sampling(
                mcp=mcp,
                messages=messages,
                system_prompt=SYSTEM_PROMPTS["kline_analysis"],
                model_preferences=MODEL_PREFERENCES["kline_analysis"],
                include_context="thisServer",
                max_tokens=2000
            )
        except Exception as e:
            logger.error(f"K线数据采样失败: {e}")
            return None

    # 注册股票比较采样处理函数
    async def compare_stocks_with_sampling(
        symbols: str,
        exchange: str,
        resolution: str,
        comparison_period: str = "3m"
    ) -> Optional[Dict[str, Any]]:
        """
        使用采样比较多只股票

        Args:
            symbols: 股票代码列表，用逗号分隔
            exchange: 交易所代码
            resolution: 时间周期
            comparison_period: 比较周期

        Returns:
            Optional[Dict[str, Any]]: 采样结果
        """
        try:
            # 解析股票代码列表
            symbol_list = symbols.split(",")
            symbols_text = ", ".join(symbol_list)

            # 构建基本消息
            messages = [
                {
                    "role": "user",
                    "content": f"请比较以下股票在{comparison_period}期间的表现：{symbols_text}。\n\n"
                    f"比较应包括：\n"
                    f"1. 价格走势对比\n"
                    f"2. 相对强弱分析\n"
                    f"3. 波动性比较\n"
                    f"4. 成交量对比\n"
                    f"5. 相关性分析\n"
                    f"6. 总体评估和投资建议"
                }
            ]

            # 为每个股票添加资源消息
            for symbol in symbol_list:
                symbol = symbol.strip()
                resource_uri = f"kline://{exchange}/{symbol}/{resolution}"

                messages.append({
                    "role": "user",
                    "content": EmbeddedResource(
                        type="resource",
                        resource=TextResourceContents(
                            uri=resource_uri,
                            mimeType="text/csv",
                            text=""  # 添加必需的text字段
                        )
                    )
                })

            # 请求采样
            return await request_sampling(
                mcp=mcp,
                messages=messages,
                system_prompt=SYSTEM_PROMPTS["kline_analysis"],
                model_preferences=MODEL_PREFERENCES["kline_analysis"],
                include_context="thisServer",
                max_tokens=3000
            )
        except Exception as e:
            logger.error(f"股票比较采样失败: {e}")
            return None

    # 将采样处理函数添加到MCP服务器的上下文中
    # 这些函数可以在工具和提示模板中使用
    setattr(mcp, 'analyze_kline_with_sampling', analyze_kline_with_sampling)
    setattr(mcp, 'compare_stocks_with_sampling', compare_stocks_with_sampling)

    logger.info("K线数据采样配置已注册")


