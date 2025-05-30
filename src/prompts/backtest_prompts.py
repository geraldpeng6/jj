#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测分析提示模块

提供回测分析相关的MCP提示模板，包括回测结果分析、策略优化等
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage, TextContent

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_prompts')

def register_prompts(mcp: FastMCP):
    """
    注册回测分析相关的提示模板到MCP服务器

    Args:
        mcp: MCP服务器实例
    """

    # 注册回测分析提示处理函数
    @mcp.prompt(
        name="analyze_backtest",
        description="分析策略回测结果并提供见解"
    )
    async def analyze_backtest(
        strategy_name: str = Field(description="策略名称"),
        backtest_period: str = Field(default="1y", description="回测周期 [默认值: 1y] [建议: 3m, 6m, 1y, 3y, 5y]"),
        metrics_focus: str = Field(default="all", description="指标重点 [默认值: all] [建议: returns, risk, drawdown, trades, all]"),
        comparison: str = Field(default="benchmark", description="比较基准 [默认值: benchmark] [建议: benchmark, strategy, none]")
    ) -> List[PromptMessage]:
        """
        分析策略回测结果并提供见解
        
        Args:
            strategy_name: 策略名称
            backtest_period: 回测周期
            metrics_focus: 指标重点
            comparison: 比较基准
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 回测周期映射
        period_map = {
            "3m": "近3个月",
            "6m": "近6个月",
            "1y": "近1年",
            "3y": "近3年",
            "5y": "近5年"
        }
        
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请分析{strategy_name}策略在{period_map.get(backtest_period, '近1年')}的回测结果，"
                    f"{'重点关注所有主要指标' if metrics_focus == 'all' else f'重点关注{metrics_focus}指标'}，"
                    f"{'与基准进行比较' if comparison == 'benchmark' else '与其他策略进行比较' if comparison == 'strategy' else '不进行比较'}。\n\n"
                    f"分析应包括：\n"
                    f"1. 总体绩效评估（收益率、风险调整收益等）\n"
                    f"2. 风险指标分析（波动率、最大回撤、下行风险等）\n"
                    f"3. 交易统计分析（胜率、盈亏比、平均持仓时间等）\n"
                    f"4. 不同市场环境下的表现\n"
                    f"5. 策略的优势和局限性\n"
                    f"6. 潜在的过拟合风险评估\n"
                    f"7. 策略改进和优化建议\n"
                    f"8. 实盘应用的注意事项\n\n"
                    f"请提供详细的分析，并解释各项指标的含义和重要性。\n\n"
                    f"请注意：由于数据资源已被移除，您将需要使用其他数据源或提供数据进行分析。"
                )
            )
        ]

        return messages

    # 注册策略优化建议提示处理函数
    @mcp.prompt(
        name="optimize_backtest",
        description="基于回测结果提供策略优化建议"
    )
    async def optimize_backtest(
        strategy_name: str = Field(description="策略名称"),
        optimization_goal: str = Field(description="优化目标 [建议: returns, sharpe, drawdown, stability, execution]"),
        constraints: str = Field(default="none", description="优化约束 [默认值: none] [建议: complexity, parameters, risk, cost, none]"),
        market_focus: str = Field(default="all", description="市场环境重点 [默认值: all] [建议: bull, bear, volatile, all]")
    ) -> List[PromptMessage]:
        """
        基于回测结果提供策略优化建议
        
        Args:
            strategy_name: 策略名称
            optimization_goal: 优化目标
            constraints: 优化约束
            market_focus: 市场环境重点
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 优化目标映射
        goal_map = {
            "returns": "收益率",
            "sharpe": "夏普比率",
            "drawdown": "最大回撤",
            "stability": "稳定性",
            "execution": "执行效率"
        }
        
        # 优化约束映射
        constraint_map = {
            "complexity": "复杂度限制",
            "parameters": "参数数量限制",
            "risk": "风险限制",
            "cost": "成本限制",
            "none": "无特殊约束"
        }
        
        # 市场环境映射
        market_map = {
            "bull": "牛市",
            "bear": "熊市",
            "volatile": "波动市",
            "all": "所有市场环境"
        }
        
        # 构建提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请基于{strategy_name}策略的回测结果，提供优化建议，"
                    f"优化目标是提高{goal_map.get(optimization_goal, '收益率')}，"
                    f"优化约束是{constraint_map.get(constraints, '无特殊约束')}，"
                    f"重点关注在{market_map.get(market_focus, '所有市场环境')}下的表现。\n\n"
                    f"优化建议应包括：\n"
                    f"1. 当前策略在目标指标上的不足分析\n"
                    f"2. 参数优化建议（范围、步长、敏感性等）\n"
                    f"3. 入场和出场条件的改进建议\n"
                    f"4. 过滤条件和确认信号的增强\n"
                    f"5. 仓位管理和风险控制的优化\n"
                    f"6. 针对特定市场环境的适应性调整\n"
                    f"7. 可能的策略变体或组合策略\n"
                    f"8. 优化后预期效果和潜在风险\n\n"
                    f"请提供具体、可操作的优化建议，并解释每项建议的理论依据和预期效果。\n\n"
                    f"请注意：由于数据资源已被移除，您将需要使用其他数据源或提供数据进行分析。"
                )
            )
        ]

        return messages

    # 注册回测比较提示处理函数
    @mcp.prompt(
        name="compare_backtests",
        description="比较多个策略的回测结果"
    )
    async def compare_backtests(
        strategy_names: str = Field(description="策略名称列表，用逗号分隔"),
        comparison_period: str = Field(default="1y", description="比较周期 [默认值: 1y] [建议: 3m, 6m, 1y, 3y, 5y]"),
        comparison_focus: str = Field(default="comprehensive", description="比较重点 [默认值: comprehensive] [建议: returns, risk, consistency, comprehensive]"),
        include_benchmark: bool = Field(default=True, description="是否包含基准 [默认值: true]")
    ) -> List[PromptMessage]:
        """
        比较多个策略的回测结果
        
        Args:
            strategy_names: 策略名称列表，用逗号分隔
            comparison_period: 比较周期
            comparison_focus: 比较重点
            include_benchmark: 是否包含基准
            
        Returns:
            List[PromptMessage]: 提示消息列表
        """
        # 解析策略名称列表
        strategy_list = strategy_names.split(",")
        strategy_list = [s.strip() for s in strategy_list]
        
        # 比较周期映射
        period_map = {
            "3m": "近3个月",
            "6m": "近6个月",
            "1y": "近1年",
            "3y": "近3年",
            "5y": "近5年"
        }
        
        # 比较重点映射
        focus_map = {
            "returns": "收益指标",
            "risk": "风险指标",
            "consistency": "一致性和稳定性",
            "comprehensive": "综合表现"
        }
        
        # 构建提示消息
        strategies_text = ", ".join(strategy_list)
        
        # 创建基本提示消息
        messages = [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"请比较以下策略在{period_map.get(comparison_period, '近1年')}的回测结果：{strategies_text}，"
                    f"重点分析{focus_map.get(comparison_focus, '综合表现')}，"
                    f"{'包含基准比较' if include_benchmark else '不包含基准比较'}。\n\n"
                    f"比较分析应包括：\n"
                    f"1. 关键绩效指标的对比（年化收益率、夏普比率、最大回撤等）\n"
                    f"2. 不同市场环境下的相对表现\n"
                    f"3. 风险特征的比较\n"
                    f"4. 交易行为和效率的对比\n"
                    f"5. 各策略的优势和劣势分析\n"
                    f"6. 策略相关性和多策略组合可行性\n"
                    f"7. 适合不同投资目标的策略推荐\n"
                    f"8. 整体评价和排名\n\n"
                    f"请提供详细的比较分析，并使用图表和数据说明各项比较结果。\n\n"
                    f"请注意：由于数据资源已被移除，您将需要使用其他数据源或提供数据进行分析。"
                )
            )
        ]

        return messages
