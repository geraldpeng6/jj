#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据采样模块

提供K线数据分析相关的MCP采样配置
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, TextContent, ModelPreferences

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_sampling')

def register_sampling(mcp: FastMCP):
    """
    注册K线数据相关的采样配置到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 由于FastMCP没有直接的sampling_handler方法，我们暂时不注册采样处理器
    # 在实际使用时，可以通过自定义路由或其他方式实现采样功能
    logger.info("K线数据采样配置已注册")

    # 为K线数据分析定制系统提示词
    custom_system_prompt = """你是一位专业的量化交易分析师，擅长技术分析和K线图解读。
在分析K线数据时，请注意以下几点：
1. 关注价格趋势、成交量和关键支撑/阻力位
2. 识别常见的K线形态，如头肩顶、双底、旗形等
3. 分析技术指标，如MACD、RSI、布林带等
4. 提供客观的市场观点，同时考虑多种可能性
5. 清晰说明你的分析依据和推理过程
6. 使用专业术语，但确保解释清晰
7. 在适当情况下使用图表或可视化辅助说明

请记住，你的分析仅供参考，不构成投资建议。"""

    # 设置模型偏好
    model_preferences = ModelPreferences(
        hints=[{"name": "claude-3-sonnet"}],  # 建议使用Claude 3 Sonnet模型
        intelligencePriority=0.8,  # 优先考虑模型能力
        speedPriority=0.4,         # 中等速度要求
        costPriority=0.3           # 较低成本优先级
    )


