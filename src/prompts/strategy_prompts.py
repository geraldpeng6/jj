#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略提示模块

提供交易策略相关的MCP提示模板
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent, GetPromptResult

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_prompts')

def register_prompts(mcp: FastMCP):
    """
    注册交易策略相关的提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 不再使用add_prompt方法，而是直接使用prompt装饰器
    # 这样可以避免'Prompt'对象没有'render'属性的错误

    # 注册创建策略提示处理函数
    @mcp.prompt("create_strategy")
    async def get_create_strategy_prompt(strategy_type: str, timeframe: str, risk_level: str) -> GetPromptResult:
        """获取创建策略提示模板"""
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请为我创建一个{strategy_type}类型的交易策略，适用于{timeframe}交易，风险水平为{risk_level}。\n\n"
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
                )
            )
        ]

        return GetPromptResult(messages=messages)

    # 注册优化策略提示处理函数
    @mcp.prompt("optimize_strategy")
    async def get_optimize_strategy_prompt(strategy_description: str, optimization_goal: str) -> GetPromptResult:
        """获取优化策略提示模板"""
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请帮我优化以下交易策略，优化目标是{optimization_goal}：\n\n"
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
                )
            )
        ]

        return GetPromptResult(messages=messages)


