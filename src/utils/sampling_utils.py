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

请记住，你的建议仅供参考，实际交易中应进行充分测试并考虑风险。""",

    "technical_analysis": """你是一位专业的技术分析师，擅长各种技术指标和图表形态的分析。
在进行技术分析时，请注意以下几点：
1. 综合多种技术指标进行分析，避免单一指标决策
2. 关注指标之间的相互验证或背离情况
3. 考虑不同时间周期的信号一致性
4. 结合成交量分析价格走势
5. 识别关键支撑位和阻力位
6. 分析趋势强度和持续性
7. 提供明确的交易信号和建议
8. 讨论技术分析的局限性和风险

请提供客观、详细的分析，并解释各指标的计算方法和信号含义。""",

    "fundamental_analysis": """你是一位专业的基本面分析师，擅长财务分析和公司估值。
在进行基本面分析时，请注意以下几点：
1. 全面分析公司财务报表和关键指标
2. 评估公司的竞争优势和行业地位
3. 分析公司的增长潜力和盈利能力
4. 考虑宏观经济因素对公司的影响
5. 使用多种估值方法评估公司价值
6. 比较历史估值和行业平均水平
7. 识别潜在的风险因素和催化剂
8. 提供明确的投资建议和目标价

请提供深入、客观的分析，并引用相关数据支持你的观点。""",

    "market_analysis": """你是一位专业的市场分析师，擅长宏观经济和市场趋势分析。
在进行市场分析时，请注意以下几点：
1. 分析关键经济指标和政策走向
2. 评估不同资产类别的相对吸引力
3. 识别市场情绪和投资者心理状态
4. 考虑地缘政治因素和全球市场联动
5. 分析行业轮动和主题投资机会
6. 评估市场估值水平和风险溢价
7. 提供明确的市场展望和投资策略
8. 讨论潜在的风险因素和不确定性

请提供全面、客观的分析，并考虑多种可能的市场情景。""",

    "portfolio_management": """你是一位专业的投资组合管理专家，擅长资产配置和风险管理。
在进行投资组合管理时，请注意以下几点：
1. 根据投资目标和风险偏好进行资产配置
2. 考虑资产间的相关性和分散化效果
3. 评估投资组合的风险收益特征
4. 设计适当的再平衡策略和触发条件
5. 分析投资组合在不同市场环境下的表现
6. 提供具体的风险管理措施和工具
7. 评估投资组合的绩效归因和改进方向
8. 考虑税务、流动性等实际约束因素

请提供实用、全面的建议，并解释各项决策的理论依据和实施方法。""",

    "backtest_analysis": """你是一位专业的量化策略回测分析专家，擅长评估交易策略的绩效和风险特征。
在分析回测结果时，请注意以下几点：
1. 全面评估策略的收益指标和风险指标
2. 分析策略在不同市场环境下的表现
3. 评估策略的稳健性和一致性
4. 识别潜在的过拟合风险
5. 分析交易统计数据和行为特征
6. 与基准和其他策略进行比较
7. 提供具体的优化方向和改进建议
8. 讨论实盘应用的注意事项和调整

请提供详细、客观的分析，并解释各项指标的含义和重要性。"""
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
    ),

    "technical_analysis": ModelPreferences(
        hints=[{"name": "claude-3-sonnet"}],  # 建议使用Claude 3 Sonnet模型
        intelligencePriority=0.7,  # 较高模型能力要求
        speedPriority=0.5,         # 中等速度要求
        costPriority=0.4           # 中等成本优先级
    ),

    "fundamental_analysis": ModelPreferences(
        hints=[{"name": "claude-3-opus"}],  # 建议使用Claude 3 Opus模型
        intelligencePriority=0.9,  # 高度优先考虑模型能力
        speedPriority=0.2,         # 低速度要求
        costPriority=0.2           # 低成本优先级
    ),

    "market_analysis": ModelPreferences(
        hints=[{"name": "claude-3-opus"}],  # 建议使用Claude 3 Opus模型
        intelligencePriority=0.8,  # 较高模型能力要求
        speedPriority=0.3,         # 较低速度要求
        costPriority=0.3           # 较低成本优先级
    ),

    "portfolio_management": ModelPreferences(
        hints=[{"name": "claude-3-sonnet"}],  # 建议使用Claude 3 Sonnet模型
        intelligencePriority=0.7,  # 较高模型能力要求
        speedPriority=0.4,         # 中等速度要求
        costPriority=0.4           # 中等成本优先级
    ),

    "backtest_analysis": ModelPreferences(
        hints=[{"name": "claude-3-sonnet"}],  # 建议使用Claude 3 Sonnet模型
        intelligencePriority=0.8,  # 较高模型能力要求
        speedPriority=0.4,         # 中等速度要求
        costPriority=0.3           # 较低成本优先级
    )
}
