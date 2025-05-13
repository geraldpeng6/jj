#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HiTrader策略生成提示模块

提供自动生成HiTrader交易策略代码的MCP提示模板
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

# 导入采样工具
from src.utils.sampling_utils import request_sampling, SYSTEM_PROMPTS, MODEL_PREFERENCES

# 获取日志记录器
logger = logging.getLogger('quant_mcp.hitrader_strategy_prompts')

# 添加HiTrader策略分析的系统提示词
SYSTEM_PROMPTS["hitrader_strategy"] = """你是一位专业的量化交易策略开发专家，擅长使用HiTrader框架设计、实现和优化交易策略。
在生成HiTrader策略代码时，请注意以下几点：

1. HiTrader策略通常包含四个主要函数：
   - indicators(context): 计算技术指标
   - choose_stock(context): 选择交易标的
   - timing(context): 实现交易信号和执行交易
   - control_risk(context): 实现风险控制逻辑

2. 常用的技术指标函数包括：
   - SMA(period): 简单移动平均线
   - EMA(period): 指数移动平均线
   - MACD(fast_period, slow_period, signal_period): MACD指标
   - RSI(period): 相对强弱指数
   - BOLL(period, std_dev): 布林带
   - KDJ(period): KDJ随机指标
   - ATR(period): 平均真实波幅

3. 交易信号通常基于：
   - 均线交叉（如金叉、死叉）
   - 指标背离
   - 突破（价格突破、指标突破）
   - 形态识别
   - 波动率变化

4. 风险控制方法包括：
   - 止损设置（固定止损、跟踪止损、ATR止损）
   - 仓位管理（固定仓位、动态仓位）
   - 分散投资
   - 盈亏比控制

5. 代码应该清晰、简洁，并包含详细的中文注释。

请根据用户的需求生成完整、可执行的HiTrader策略代码。"""

# 添加HiTrader策略分析的模型偏好
MODEL_PREFERENCES["hitrader_strategy"] = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_tokens": 2000
}

def register_prompts(mcp: FastMCP):
    """
    注册HiTrader策略生成相关的提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """

    # 注册生成HiTrader策略代码提示处理函数
    @mcp.prompt(
        name="generate_hitrader_strategy",
        description="生成HiTrader交易策略代码"
    )
    async def generate_hitrader_strategy(
        strategy_type: str = Field(description="策略类型 [建议: trend_following, mean_reversion, breakout, momentum, dual_ma, macd, rsi, kdj, boll]"),
        timeframe: str = Field(description="交易时间框架 [默认值: daily] [建议: daily, weekly, 60min, 30min, 15min]"),
        risk_level: str = Field(description="风险水平 [默认值: medium] [建议: low, medium, high]"),
        stock_selection: str = Field(default="single", description="选股方式 [默认值: single] [建议: single, multiple, index, sector]"),
        specific_stocks: str = Field(default="600000.XSHG", description="指定股票代码，多个股票用&分隔 [默认值: 600000.XSHG] [建议: 600000.XSHG, 000001.XSHE&600519.XSHG]"),
        indicators_required: str = Field(default="all", description="需要的技术指标 [默认值: all] [建议: ma, macd, rsi, kdj, boll, all]"),
        position_sizing: str = Field(default="fixed", description="仓位管理方式 [默认值: fixed] [建议: fixed, dynamic, risk_based]"),
        stop_loss: str = Field(default="fixed", description="止损方式 [默认值: fixed] [建议: fixed, trailing, atr, none]")
    ) -> List[PromptMessage]:
        """
        生成HiTrader交易策略代码
        
        Args:
            strategy_type: 策略类型
            timeframe: 交易时间框架
            risk_level: 风险水平
            stock_selection: 选股方式
            specific_stocks: 指定股票代码
            indicators_required: 需要的技术指标
            position_sizing: 仓位管理方式
            stop_loss: 止损方式
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 策略类型映射
        strategy_map = {
            "trend_following": "趋势跟踪",
            "mean_reversion": "均值回归",
            "breakout": "突破",
            "momentum": "动量",
            "dual_ma": "双均线",
            "macd": "MACD",
            "rsi": "RSI",
            "kdj": "KDJ",
            "boll": "布林带"
        }
        
        # 时间周期映射
        timeframe_map = {
            "daily": "日线",
            "weekly": "周线",
            "60min": "60分钟线",
            "30min": "30分钟线",
            "15min": "15分钟线"
        }
        
        # 风险水平映射
        risk_map = {
            "low": "低风险",
            "medium": "中等风险",
            "high": "高风险"
        }
        
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请为我生成一个完整的HiTrader交易策略代码，具体要求如下：\n\n"
                    f"1. 策略类型：{strategy_map.get(strategy_type, strategy_type)}\n"
                    f"2. 交易周期：{timeframe_map.get(timeframe, timeframe)}\n"
                    f"3. 风险水平：{risk_map.get(risk_level, risk_level)}\n"
                    f"4. 选股方式：{stock_selection}\n"
                    f"5. 交易标的：{specific_stocks}\n"
                    f"6. 技术指标：{indicators_required}\n"
                    f"7. 仓位管理：{position_sizing}\n"
                    f"8. 止损方式：{stop_loss}\n\n"
                    f"请生成完整的HiTrader策略代码，包括indicators、choose_stock、timing和control_risk四个函数，并确保代码可以直接在HiTrader平台上运行。\n\n"
                    f"代码应包含详细的中文注释，解释每个函数的作用和关键逻辑。特别是交易信号的生成逻辑和风险控制的实现方式。\n\n"
                    f"如果策略类型是均线类，请使用适当的均线参数；如果是指标类策略，请使用相应的指标参数和信号生成逻辑。"
                )
            )
        ]

        return messages

    # 注册优化HiTrader策略代码提示处理函数
    @mcp.prompt(
        name="optimize_hitrader_strategy",
        description="优化现有的HiTrader交易策略代码"
    )
    async def optimize_hitrader_strategy(
        strategy_code: str = Field(description="现有的HiTrader策略代码"),
        optimization_goal: str = Field(description="优化目标 [建议: returns, drawdown, sharpe, stability, execution]"),
        market_condition: str = Field(default="normal", description="市场环境 [默认值: normal] [建议: bull, bear, volatile, normal]"),
        specific_improvements: str = Field(default="all", description="具体改进方向 [默认值: all] [建议: indicators, entry_exit, risk_control, parameters, all]")
    ) -> List[PromptMessage]:
        """
        优化现有的HiTrader交易策略代码
        
        Args:
            strategy_code: 现有的HiTrader策略代码
            optimization_goal: 优化目标
            market_condition: 市场环境
            specific_improvements: 具体改进方向
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 优化目标映射
        goal_map = {
            "returns": "提高收益率",
            "drawdown": "减少回撤",
            "sharpe": "提高夏普比率",
            "stability": "增强稳定性",
            "execution": "改进执行效率"
        }
        
        # 市场环境映射
        market_map = {
            "bull": "牛市",
            "bear": "熊市",
            "volatile": "波动市",
            "normal": "常态市"
        }
        
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请帮我优化以下HiTrader交易策略代码，优化目标是{goal_map.get(optimization_goal, optimization_goal)}，"
                    f"考虑{market_map.get(market_condition, market_condition)}环境，"
                    f"重点改进{'所有方面' if specific_improvements == 'all' else specific_improvements}：\n\n"
                    f"```python\n{strategy_code}\n```\n\n"
                    f"优化建议应包括：\n"
                    f"1. 现有策略的问题分析\n"
                    f"2. 针对{goal_map.get(optimization_goal, optimization_goal)}的具体优化方案\n"
                    f"3. 参数调整建议\n"
                    f"4. 额外的过滤条件或规则\n"
                    f"5. 风险管理改进\n"
                    f"6. 预期效果和潜在风险\n\n"
                    f"请提供完整的优化后代码，包括详细的中文注释，解释每处修改的目的和预期效果。"
                )
            )
        ]

        return messages

    # 注册生成回测代码提示处理函数
    @mcp.prompt(
        name="generate_backtest_code",
        description="生成HiTrader策略的回测代码"
    )
    async def generate_backtest_code(
        strategy_code: str = Field(description="HiTrader策略代码"),
        start_date: str = Field(default="2022-01-01", description="回测开始日期 [默认值: 2022-01-01]"),
        end_date: str = Field(default="2023-01-01", description="回测结束日期 [默认值: 2023-01-01]"),
        benchmark: str = Field(default="000300.XSHG", description="基准指数 [默认值: 000300.XSHG] [建议: 000300.XSHG, 000905.XSHG, 000001.XSHG]"),
        initial_capital: float = Field(default=1000000.0, description="初始资金 [默认值: 1000000.0]")
    ) -> List[PromptMessage]:
        """
        生成HiTrader策略的回测代码
        
        Args:
            strategy_code: HiTrader策略代码
            start_date: 回测开始日期
            end_date: 回测结束日期
            benchmark: 基准指数
            initial_capital: 初始资金
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请为以下HiTrader策略生成回测代码：\n\n"
                    f"```python\n{strategy_code}\n```\n\n"
                    f"回测参数：\n"
                    f"1. 回测开始日期：{start_date}\n"
                    f"2. 回测结束日期：{end_date}\n"
                    f"3. 基准指数：{benchmark}\n"
                    f"4. 初始资金：{initial_capital}元\n\n"
                    f"请生成完整的回测代码，包括回测参数设置、回测执行和结果分析。代码应包含详细的中文注释，解释关键步骤和参数设置。"
                )
            )
        ]

        return messages

    # 将采样处理函数添加到MCP服务器的上下文中
    async def generate_hitrader_strategy_with_sampling(
        strategy_type: str,
        timeframe: str,
        risk_level: str,
        stock_selection: str = "single",
        specific_stocks: str = "600000.XSHG",
        indicators_required: str = "all",
        position_sizing: str = "fixed",
        stop_loss: str = "fixed"
    ) -> Optional[Dict[str, Any]]:
        """
        使用采样生成HiTrader策略代码

        Args:
            strategy_type: 策略类型
            timeframe: 交易时间框架
            risk_level: 风险水平
            stock_selection: 选股方式
            specific_stocks: 指定股票代码
            indicators_required: 需要的技术指标
            position_sizing: 仓位管理方式
            stop_loss: 止损方式

        Returns:
            Optional[Dict[str, Any]]: 采样结果
        """
        try:
            # 策略类型映射
            strategy_map = {
                "trend_following": "趋势跟踪",
                "mean_reversion": "均值回归",
                "breakout": "突破",
                "momentum": "动量",
                "dual_ma": "双均线",
                "macd": "MACD",
                "rsi": "RSI",
                "kdj": "KDJ",
                "boll": "布林带"
            }
            
            # 时间周期映射
            timeframe_map = {
                "daily": "日线",
                "weekly": "周线",
                "60min": "60分钟线",
                "30min": "30分钟线",
                "15min": "15分钟线"
            }
            
            # 风险水平映射
            risk_map = {
                "low": "低风险",
                "medium": "中等风险",
                "high": "高风险"
            }
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": f"请为我生成一个完整的HiTrader交易策略代码，具体要求如下：\n\n"
                    f"1. 策略类型：{strategy_map.get(strategy_type, strategy_type)}\n"
                    f"2. 交易周期：{timeframe_map.get(timeframe, timeframe)}\n"
                    f"3. 风险水平：{risk_map.get(risk_level, risk_level)}\n"
                    f"4. 选股方式：{stock_selection}\n"
                    f"5. 交易标的：{specific_stocks}\n"
                    f"6. 技术指标：{indicators_required}\n"
                    f"7. 仓位管理：{position_sizing}\n"
                    f"8. 止损方式：{stop_loss}\n\n"
                    f"请生成完整的HiTrader策略代码，包括indicators、choose_stock、timing和control_risk四个函数，并确保代码可以直接在HiTrader平台上运行。\n\n"
                    f"代码应包含详细的中文注释，解释每个函数的作用和关键逻辑。特别是交易信号的生成逻辑和风险控制的实现方式。\n\n"
                    f"如果策略类型是均线类，请使用适当的均线参数；如果是指标类策略，请使用相应的指标参数和信号生成逻辑。"
                }
            ]

            # 请求采样
            return await request_sampling(
                mcp=mcp,
                messages=messages,
                system_prompt=SYSTEM_PROMPTS["hitrader_strategy"],
                model_preferences=MODEL_PREFERENCES["hitrader_strategy"],
                include_context="thisServer",
                max_tokens=2000
            )
        except Exception as e:
            logger.error(f"生成HiTrader策略代码采样失败: {e}")
            return None

    # 将采样处理函数添加到MCP服务器的上下文中
    setattr(mcp, 'generate_hitrader_strategy_with_sampling', generate_hitrader_strategy_with_sampling)

    logger.info("HiTrader策略生成提示模板已注册")
