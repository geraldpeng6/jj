#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略采样模块

提供交易策略相关的MCP采样配置
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    SamplingMessage,
    TextContent,
    ModelPreferences,
    CreateMessageRequest,
    EmbeddedResource
)

# 导入采样工具
from src.utils.sampling_utils import request_sampling, SYSTEM_PROMPTS, MODEL_PREFERENCES

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_sampling')

def register_sampling(mcp: FastMCP):
    """
    注册交易策略相关的采样配置到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    logger.info("注册交易策略采样配置")

    # 注册创建策略采样处理函数
    async def create_strategy_with_sampling(
        strategy_type: str,
        timeframe: str,
        risk_level: str
    ) -> Optional[Dict[str, Any]]:
        """
        使用采样创建交易策略

        Args:
            strategy_type: 策略类型
            timeframe: 交易时间框架
            risk_level: 风险水平

        Returns:
            Optional[Dict[str, Any]]: 采样结果
        """
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": f"请为我创建一个{strategy_type}类型的交易策略，适用于{timeframe}交易，风险水平为{risk_level}。\n\n"
                    f"策略应包括以下内容：\n"
                    f"1. 策略概述和理论基础\n"
                    f"2. 入场条件和信号\n"
                    f"3. 出场条件和信号\n"
                    f"4. 仓位管理和风险控制\n"
                    f"5. 关键参数和指标\n"
                    f"6. 回测方法和评估标准\n"
                    f"7. 策略优缺点分析\n"
                    f"8. 实现代码框架或伪代码\n\n"
                    f"请尽可能详细地描述策略，并提供具体的技术指标和参数。"
                }
            ]

            # 请求采样
            return await request_sampling(
                mcp=mcp,
                messages=messages,
                system_prompt=SYSTEM_PROMPTS["strategy_analysis"],
                model_preferences=MODEL_PREFERENCES["strategy_analysis"],
                include_context="thisServer",
                max_tokens=3000
            )
        except Exception as e:
            logger.error(f"创建策略采样失败: {e}")
            return None

    # 注册优化策略采样处理函数
    async def optimize_strategy_with_sampling(
        strategy_description: str,
        optimization_goal: str,
        market_condition: str = "normal"
    ) -> Optional[Dict[str, Any]]:
        """
        使用采样优化交易策略

        Args:
            strategy_description: 现有策略的描述
            optimization_goal: 优化目标
            market_condition: 市场环境

        Returns:
            Optional[Dict[str, Any]]: 采样结果
        """
        try:
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": f"请帮我优化以下交易策略，优化目标是{optimization_goal}，考虑{market_condition}市场环境：\n\n"
                    f"{strategy_description}\n\n"
                    f"优化建议应包括：\n"
                    f"1. 现有策略的问题分析\n"
                    f"2. 针对{optimization_goal}的具体优化方案\n"
                    f"3. 参数调整建议\n"
                    f"4. 额外的过滤条件或规则\n"
                    f"5. 风险管理改进\n"
                    f"6. 预期效果和潜在风险\n"
                    f"7. 优化后的策略框架或伪代码\n\n"
                    f"请提供详细的优化建议，并解释每项改进的理由和预期效果。"
                }
            ]

            # 请求采样
            return await request_sampling(
                mcp=mcp,
                messages=messages,
                system_prompt=SYSTEM_PROMPTS["strategy_analysis"],
                model_preferences=MODEL_PREFERENCES["strategy_analysis"],
                include_context="thisServer",
                max_tokens=3000
            )
        except Exception as e:
            logger.error(f"优化策略采样失败: {e}")
            return None

    # 将采样处理函数添加到MCP服务器的上下文中
    # 这些函数可以在工具和提示模板中使用
    setattr(mcp, 'create_strategy_with_sampling', create_strategy_with_sampling)
    setattr(mcp, 'optimize_strategy_with_sampling', optimize_strategy_with_sampling)

    logger.info("交易策略采样配置已注册")


