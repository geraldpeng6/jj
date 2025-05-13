#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HiTrader工具模块

提供HiTrader策略代码生成和回测相关的工具函数
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# 导入工具函数
from utils.backtest_utils import run_backtest, format_choose_stock
from utils.strategy_utils import get_strategy_detail

# 获取日志记录器
logger = logging.getLogger('quant_mcp.hitrader_tools')

async def generate_hitrader_strategy(
    strategy_type: str,
    timeframe: str,
    risk_level: str,
    stock_selection: str = "single",
    specific_stocks: str = "600000.XSHG",
    indicators_required: str = "all",
    position_sizing: str = "fixed",
    stop_loss: str = "fixed"
) -> str:
    """
    生成HiTrader策略代码并保存为文件

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
        str: 生成的策略代码或错误信息
    """
    try:
        # 获取MCP服务器实例
        from server import mcp

        # 检查是否注册了采样函数
        if not hasattr(mcp, 'generate_hitrader_strategy_with_sampling'):
            return "错误: HiTrader策略生成采样函数未注册"

        # 使用采样生成策略代码
        result = await mcp.generate_hitrader_strategy_with_sampling(
            strategy_type=strategy_type,
            timeframe=timeframe,
            risk_level=risk_level,
            stock_selection=stock_selection,
            specific_stocks=specific_stocks,
            indicators_required=indicators_required,
            position_sizing=position_sizing,
            stop_loss=stop_loss
        )

        if not result or 'content' not in result:
            return "生成策略代码失败，请检查参数后重试"

        # 提取生成的代码
        generated_code = result['content']

        # 创建策略文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name = f"{strategy_type}_{timeframe}_{risk_level}_{timestamp}"
        file_name = f"{strategy_name}.py"
        
        # 确保目录存在
        strategy_dir = os.path.join("data", "strategy")
        os.makedirs(strategy_dir, exist_ok=True)
        
        # 保存策略代码到文件
        file_path = os.path.join(strategy_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(generated_code)
        
        # 返回结果
        return f"HiTrader策略代码已生成并保存到: {file_path}\n\n```python\n{generated_code}\n```"

    except Exception as e:
        logger.error(f"生成HiTrader策略代码时发生错误: {e}")
        return f"生成HiTrader策略代码时发生错误: {e}"


async def backtest_hitrader_strategy(
    strategy_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    specific_stocks: Optional[str] = None
) -> str:
    """
    回测HiTrader策略

    Args:
        strategy_code: HiTrader策略代码
        start_date: 回测开始日期，格式为 "YYYY-MM-DD"，可选
        end_date: 回测结束日期，格式为 "YYYY-MM-DD"，可选
        specific_stocks: 指定股票代码，可选，如果提供则覆盖策略中的选股函数

    Returns:
        str: 回测结果信息，或错误信息
    """
    try:
        # 创建临时策略文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name = f"temp_strategy_{timestamp}"
        file_name = f"{strategy_name}.py"
        
        # 确保目录存在
        strategy_dir = os.path.join("data", "strategy")
        os.makedirs(strategy_dir, exist_ok=True)
        
        # 保存策略代码到文件
        file_path = os.path.join(strategy_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(strategy_code)
        
        # 提取策略组件
        indicator_code = None
        timing_code = None
        control_risk_code = None
        choose_stock_code = None
        
        # 简单解析策略代码提取各个函数
        lines = strategy_code.split('\n')
        current_function = None
        function_code = []
        
        for line in lines:
            if line.startswith('def indicators(context):'):
                if current_function and function_code:
                    if current_function == 'indicators':
                        indicator_code = '\n'.join(function_code)
                    elif current_function == 'choose_stock':
                        choose_stock_code = '\n'.join(function_code)
                    elif current_function == 'timing':
                        timing_code = '\n'.join(function_code)
                    elif current_function == 'control_risk':
                        control_risk_code = '\n'.join(function_code)
                current_function = 'indicators'
                function_code = [line]
            elif line.startswith('def choose_stock(context):'):
                if current_function and function_code:
                    if current_function == 'indicators':
                        indicator_code = '\n'.join(function_code)
                    elif current_function == 'choose_stock':
                        choose_stock_code = '\n'.join(function_code)
                    elif current_function == 'timing':
                        timing_code = '\n'.join(function_code)
                    elif current_function == 'control_risk':
                        control_risk_code = '\n'.join(function_code)
                current_function = 'choose_stock'
                function_code = [line]
            elif line.startswith('def timing(context):'):
                if current_function and function_code:
                    if current_function == 'indicators':
                        indicator_code = '\n'.join(function_code)
                    elif current_function == 'choose_stock':
                        choose_stock_code = '\n'.join(function_code)
                    elif current_function == 'timing':
                        timing_code = '\n'.join(function_code)
                    elif current_function == 'control_risk':
                        control_risk_code = '\n'.join(function_code)
                current_function = 'timing'
                function_code = [line]
            elif line.startswith('def control_risk(context):'):
                if current_function and function_code:
                    if current_function == 'indicators':
                        indicator_code = '\n'.join(function_code)
                    elif current_function == 'choose_stock':
                        choose_stock_code = '\n'.join(function_code)
                    elif current_function == 'timing':
                        timing_code = '\n'.join(function_code)
                    elif current_function == 'control_risk':
                        control_risk_code = '\n'.join(function_code)
                current_function = 'control_risk'
                function_code = [line]
            else:
                if current_function:
                    function_code.append(line)
        
        # 处理最后一个函数
        if current_function and function_code:
            if current_function == 'indicators':
                indicator_code = '\n'.join(function_code)
            elif current_function == 'choose_stock':
                choose_stock_code = '\n'.join(function_code)
            elif current_function == 'timing':
                timing_code = '\n'.join(function_code)
            elif current_function == 'control_risk':
                control_risk_code = '\n'.join(function_code)
        
        # 如果提供了specific_stocks，则覆盖choose_stock函数
        if specific_stocks:
            choose_stock_code = format_choose_stock(specific_stocks)
        
        # 使用双均线策略作为基础策略ID
        base_strategy_id = "1"  # 双均线策略ID
        
        # 运行回测
        from src.tools.backtest_tools import run_strategy_backtest
        
        result = await run_strategy_backtest(
            strategy_id=base_strategy_id,
            listen_time=30,
            start_date=start_date,
            end_date=end_date,
            indicator=indicator_code,
            control_risk=control_risk_code,
            timing=timing_code,
            choose_stock=choose_stock_code
        )
        
        # 删除临时策略文件
        try:
            os.remove(file_path)
        except:
            pass
        
        return result

    except Exception as e:
        logger.error(f"回测HiTrader策略时发生错误: {e}")
        return f"回测HiTrader策略时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册HiTrader相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册生成HiTrader策略工具
    mcp.tool()(generate_hitrader_strategy)
    
    # 注册回测HiTrader策略工具
    mcp.tool()(backtest_hitrader_strategy)
    
    logger.info("HiTrader工具已注册")
