#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
采样路由模块

提供自定义采样路由，用于处理不同类型的采样请求
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from mcp.server.fastmcp import FastMCP
from mcp.types import SamplingMessage, ModelPreferences, TextContent

# 获取日志记录器
logger = logging.getLogger('quant_mcp.sampling_routes')

# 采样处理器类型
SamplingHandler = Callable[[List[SamplingMessage], Optional[str]], Awaitable[Dict[str, Any]]]

# 采样处理器注册表
sampling_handlers: List[SamplingHandler] = []

def register_sampling_handler(handler: SamplingHandler):
    """
    注册采样处理器
    
    Args:
        handler: 采样处理器函数
    """
    sampling_handlers.append(handler)
    logger.info(f"已注册采样处理器: {handler.__name__}")

async def handle_kline_sampling(messages: List[SamplingMessage], system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    处理K线数据相关的采样请求
    
    Args:
        messages: 消息列表
        system_prompt: 系统提示词
        
    Returns:
        采样配置或None
    """
    # 检查消息内容是否与K线数据相关
    is_kline_related = False
    for message in messages:
        if message.role == "user" and isinstance(message.content, TextContent):
            text = message.content.text.lower()
            if any(keyword in text for keyword in ["k线", "kline", "蜡烛图", "candlestick", "股票", "stock", "技术分析", "technical analysis"]):
                is_kline_related = True
                break
    
    if not is_kline_related:
        # 不是K线数据相关的请求，返回None让其他处理器处理
        return None
    
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
    
    # 返回采样配置
    return {
        "messages": [m.model_dump() for m in messages],  # 转换为字典
        "systemPrompt": custom_system_prompt,
        "modelPreferences": model_preferences.model_dump(),
        "temperature": 0.3,        # 较低温度，保持回答一致性
        "maxTokens": 2000,         # 足够长的回复
        "includeContext": "thisServer"  # 包含当前服务器的上下文
    }

async def handle_strategy_sampling(messages: List[SamplingMessage], system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    处理交易策略相关的采样请求
    
    Args:
        messages: 消息列表
        system_prompt: 系统提示词
        
    Returns:
        采样配置或None
    """
    # 检查消息内容是否与交易策略相关
    is_strategy_related = False
    for message in messages:
        if message.role == "user" and isinstance(message.content, TextContent):
            text = message.content.text.lower()
            if any(keyword in text for keyword in ["策略", "strategy", "交易系统", "trading system", "回测", "backtest", "优化", "optimize"]):
                is_strategy_related = True
                break
    
    if not is_strategy_related:
        # 不是交易策略相关的请求，返回None让其他处理器处理
        return None
    
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
    
    # 返回采样配置
    return {
        "messages": [m.model_dump() for m in messages],  # 转换为字典
        "systemPrompt": custom_system_prompt,
        "modelPreferences": model_preferences.model_dump(),
        "temperature": 0.2,        # 低温度，保持回答一致性和准确性
        "maxTokens": 3000,         # 较长的回复，以便详细解释
        "includeContext": "thisServer"  # 包含当前服务器的上下文
    }

async def handle_sampling_request(request: Request) -> Response:
    """
    处理采样请求的自定义路由处理函数
    
    Args:
        request: HTTP请求
        
    Returns:
        HTTP响应
    """
    try:
        # 解析请求体
        body = await request.json()
        
        # 提取消息和系统提示词
        messages_data = body.get("messages", [])
        system_prompt = body.get("systemPrompt")
        
        # 转换为SamplingMessage对象
        messages = []
        for msg_data in messages_data:
            try:
                # 创建SamplingMessage对象
                if msg_data.get("content", {}).get("type") == "text":
                    content = TextContent(
                        type="text",
                        text=msg_data.get("content", {}).get("text", "")
                    )
                    message = SamplingMessage(
                        role=msg_data.get("role", "user"),
                        content=content
                    )
                    messages.append(message)
                else:
                    # 暂不支持其他类型的内容
                    logger.warning(f"不支持的消息内容类型: {msg_data.get('content', {}).get('type')}")
            except Exception as e:
                logger.error(f"解析消息时发生错误: {e}")
        
        # 如果没有消息，返回错误
        if not messages:
            return JSONResponse(
                {"error": "No valid messages found in request"},
                status_code=400
            )
        
        # 尝试所有采样处理器
        for handler in sampling_handlers:
            try:
                result = await handler(messages, system_prompt)
                if result is not None:
                    # 找到匹配的处理器，返回结果
                    return JSONResponse(result)
            except Exception as e:
                logger.error(f"采样处理器 {handler.__name__} 发生错误: {e}")
        
        # 如果没有处理器处理请求，返回默认配置
        default_config = {
            "messages": [m.model_dump() for m in messages],
            "systemPrompt": system_prompt,
            "temperature": 0.7,
            "maxTokens": 1000,
            "includeContext": "thisServer"
        }
        
        return JSONResponse(default_config)
    
    except Exception as e:
        logger.error(f"处理采样请求时发生错误: {e}")
        return JSONResponse(
            {"error": f"Error processing sampling request: {str(e)}"},
            status_code=500
        )

def register_sampling_routes(mcp: FastMCP):
    """
    注册采样路由到MCP服务器
    
    Args:
        mcp: MCP服务器实例
    """
    # 注册采样处理器
    register_sampling_handler(handle_kline_sampling)
    register_sampling_handler(handle_strategy_sampling)
    
    # 注册自定义路由
    @mcp.custom_route("/sampling", methods=["POST"])
    async def sampling_route(request: Request) -> Response:
        """采样路由"""
        return await handle_sampling_request(request)
    
    logger.info("已注册采样路由: /sampling")
