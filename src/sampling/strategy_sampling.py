#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略采样模块

提供交易策略相关的MCP采样配置
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, TextContent, ModelPreferences

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_sampling')

def register_sampling(mcp: FastMCP):
    """
    注册交易策略相关的采样配置到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 由于FastMCP没有直接的sampling_handler方法，我们暂时不注册采样处理器
    # 在实际使用时，可以通过自定义路由或其他方式实现采样功能
    logger.info("交易策略采样配置已注册")

    # 为交易策略分析定制系统提示词
    custom_system_prompt = """你是一位专业的量化交易策略开发专家，擅长设计、实现和优化交易策略。
在讨论交易策略时，请注意以下几点：
1. 清晰描述策略的逻辑和规则
2. 考虑入场和出场条件的明确性和可测试性
3. 讨论仓位管理和风险控制方法
4. 分析策略的优势和局限性
5. 考虑不同市场环境下的表现
6. 提供具体的参数和指标建议
7. 在适当情况下提供伪代码或实现思路
8. 讨论策略的回测方法和评估标准

请记住，你的建议仅供参考，实际交易中应进行充分测试并考虑风险。"""

    # 设置模型偏好
    model_preferences = ModelPreferences(
        hints=[{"name": "claude-3-opus"}],  # 建议使用Claude 3 Opus模型
        intelligencePriority=0.9,  # 高度优先考虑模型能力
        speedPriority=0.3,         # 较低速度要求
        costPriority=0.2           # 低成本优先级
    )


