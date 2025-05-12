#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
采样工具模块

提供MCP采样相关的工具函数，用于在工具和提示模板中请求LLM采样
"""

import logging
from typing import Dict, Any, List, Optional, Union
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    SamplingMessage,
    TextContent,
    ModelPreferences,
    CreateMessageRequest,
    CreateMessageResult
)

# 获取日志记录器
logger = logging.getLogger('quant_mcp.sampling_utils')

async def request_sampling(
    mcp: FastMCP,
    messages: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    model_preferences: Optional[ModelPreferences] = None,
    include_context: str = "thisServer",
    max_tokens: int = 1000,
    temperature: Optional[float] = None,
    stop_sequences: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    请求LLM采样，获取模型回复

    Args:
        mcp: MCP服务器实例
        messages: 消息列表，每个消息包含role和content
        system_prompt: 系统提示词，可选
        model_preferences: 模型偏好设置，可选
        include_context: 包含上下文的范围，可选值为"none"、"thisServer"、"allServers"，默认为"thisServer"
        max_tokens: 最大生成令牌数，默认为1000
        temperature: 采样温度，可选，默认由客户端决定
        stop_sequences: 停止序列列表，可选

    Returns:
        Optional[Dict[str, Any]]: 采样结果，如果采样失败则返回None
    """
    try:
        # 构建采样消息
        sampling_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # 如果content是字符串，转换为TextContent对象
            if isinstance(content, str):
                content = TextContent(type="text", text=content)

            # 添加到消息列表
            sampling_messages.append(SamplingMessage(role=role, content=content))

        # 构建采样请求
        request = CreateMessageRequest(
            messages=sampling_messages,
            systemPrompt=system_prompt,
            includeContext=include_context,
            maxTokens=max_tokens
        )

        # 添加可选参数
        if model_preferences:
            request.modelPreferences = model_preferences

        if temperature is not None:
            request.temperature = temperature

        if stop_sequences:
            request.stopSequences = stop_sequences

        # 发送采样请求
        logger.info(f"发送采样请求: {request}")
        response = await mcp.sampling_create_message(request)

        # 处理响应
        if response and hasattr(response, "content"):
            # 提取文本内容
            if hasattr(response.content, "text"):
                logger.info(f"采样成功，模型: {response.model}")
                return {
                    "model": response.model,
                    "role": response.role,
                    "content": response.content.text,
                    "stop_reason": getattr(response, "stopReason", None)
                }
            else:
                logger.warning("采样响应不包含文本内容")
                return None
        else:
            logger.warning("采样响应无效")
            return None

    except Exception as e:
        logger.error(f"采样请求失败: {e}")
        return None

# 为不同类型的分析创建预设的系统提示词
SYSTEM_PROMPTS = {
    "kline_analysis": """你是一位专业的量化交易分析师，擅长技术分析和K线图解读。
在分析K线数据时，请注意以下几点：
1. 关注价格趋势、成交量和关键支撑/阻力位
2. 识别常见的K线形态，如头肩顶、双底、旗形等
3. 分析技术指标，如MACD、RSI、布林带等
4. 提供客观的市场观点，同时考虑多种可能性
5. 清晰说明你的分析依据和推理过程
6. 使用专业术语，但确保解释清晰
7. 在适当情况下使用图表或可视化辅助说明

请记住，你的分析仅供参考，不构成投资建议。""",

    "strategy_analysis": """你是一位专业的量化交易策略开发专家，擅长设计、实现和优化交易策略。
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
}

# 为不同类型的分析创建预设的模型偏好
MODEL_PREFERENCES = {
    "kline_analysis": ModelPreferences(
        hints=[{"name": "claude-3-sonnet"}],  # 建议使用Claude 3 Sonnet模型
        intelligencePriority=0.8,  # 优先考虑模型能力
        speedPriority=0.4,         # 中等速度要求
        costPriority=0.3           # 较低成本优先级
    ),

    "strategy_analysis": ModelPreferences(
        hints=[{"name": "claude-3-opus"}],  # 建议使用Claude 3 Opus模型
        intelligencePriority=0.9,  # 高度优先考虑模型能力
        speedPriority=0.3,         # 较低速度要求
        costPriority=0.2           # 低成本优先级
    )
}
