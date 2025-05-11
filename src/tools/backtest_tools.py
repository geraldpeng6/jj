#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测工具模块

提供回测相关的MCP工具
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from utils.backtest_utils import run_backtest, format_choose_stock

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_tools')


async def run_strategy_backtest(
    strategy_id: str,
    listen_time: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    indicator: Optional[str] = None,
    control_risk: Optional[str] = None,
    timing: Optional[str] = None,
    choose_stock: Optional[str] = None
) -> str:
    """
    运行策略回测

    Args:
        strategy_id: 策略ID
        listen_time: 监听时间（秒），默认30秒
        start_date: 回测开始日期，格式为 "YYYY-MM-DD"，可选，默认为一年前
        end_date: 回测结束日期，格式为 "YYYY-MM-DD"，可选，默认为今天
        indicator: 自定义指标代码，可选
        control_risk: 自定义风控代码，可选
        timing: 自定义择时代码，可选
        choose_stock: 自定义标的代码或股票代码，可选

    Returns:
        str: 回测结果信息，或错误信息
    """
    try:
        # 检查策略ID
        if not strategy_id:
            return "错误: 策略ID不能为空"

        # 运行回测
        result = run_backtest(
            strategy_id=strategy_id,
            listen_time=listen_time,
            start_date=start_date,
            end_date=end_date,
            indicator=indicator,
            control_risk=control_risk,
            timing=timing,
            choose_stock=choose_stock
        )

        # 格式化输出
        if result['success']:
            result_str = f"回测成功完成！\n\n"
            result_str += f"策略: {result['strategy_name']} (ID: {result['strategy_id']})\n"
            result_str += f"接收到 {result['position_count']} 条position数据\n"
            result_str += f"数据已保存到: {result['file_path']}\n"

            if result.get('chart_path'):
                result_str += f"\n回测结果图表已生成并在浏览器中打开: {result['chart_path']}"
            else:
                result_str += "\n未生成回测结果图表"

            return result_str
        else:
            return f"回测失败: {result.get('error', '未知错误')}"

    except Exception as e:
        logger.error(f"运行回测时发生错误: {e}")
        return f"运行回测时发生错误: {e}"


async def backtest_with_stock(
    strategy_id: str,
    stock_code: str,
    listen_time: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    使用指定股票进行回测

    Args:
        strategy_id: 策略ID
        stock_code: 股票代码，例如 "600000.XSHG" 或多个股票 "600000.XSHG&000001.XSHE"
        listen_time: 监听时间（秒），默认30秒
        start_date: 回测开始日期，格式为 "YYYY-MM-DD"，可选，默认为一年前
        end_date: 回测结束日期，格式为 "YYYY-MM-DD"，可选，默认为今天

    Returns:
        str: 回测结果信息，或错误信息
    """
    try:
        # 检查策略ID和股票代码
        if not strategy_id:
            return "错误: 策略ID不能为空"

        if not stock_code:
            return "错误: 股票代码不能为空"

        # 格式化股票代码为choose_stock函数
        choose_stock = format_choose_stock(stock_code)

        # 运行回测
        result = run_backtest(
            strategy_id=strategy_id,
            listen_time=listen_time,
            start_date=start_date,
            end_date=end_date,
            choose_stock=choose_stock
        )

        # 格式化输出
        if result['success']:
            result_str = f"使用股票 {stock_code} 回测成功完成！\n\n"
            result_str += f"策略: {result['strategy_name']} (ID: {result['strategy_id']})\n"
            result_str += f"接收到 {result['position_count']} 条position数据\n"
            result_str += f"数据已保存到: {result['file_path']}\n"

            if result.get('chart_path'):
                result_str += f"\n回测结果图表已生成并在浏览器中打开: {result['chart_path']}"
            else:
                result_str += "\n未生成回测结果图表"

            return result_str
        else:
            return f"回测失败: {result.get('error', '未知错误')}"

    except Exception as e:
        logger.error(f"运行回测时发生错误: {e}")
        return f"运行回测时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册回测相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册运行策略回测工具
    mcp.tool()(run_strategy_backtest)

    # 注册使用指定股票进行回测工具
    mcp.tool()(backtest_with_stock)
