#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测工具模块

提供回测相关的MCP工具
"""

import logging
import os
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from mcp.server.fastmcp import FastMCP

from utils.backtest_utils import run_backtest, format_choose_stock
from utils.date_utils import get_beijing_now, validate_date_range
from utils.html_server import get_server_host, get_html_url
from utils.chart_utils import generate_chart_path, check_existing_backtest

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_tools')

# 存储正在运行的回测任务
RUNNING_BACKTESTS = {}

# 回测结果目录
DATA_DIR = 'data'
BACKTEST_DIR = os.path.join(DATA_DIR, 'backtest')
CHARTS_DIR = os.path.join(DATA_DIR, 'charts')

# 确保目录存在
os.makedirs(BACKTEST_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)


async def run_strategy_backtest(
    strategy_id: str,
    listen_time: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    indicator: Optional[str] = None,
    control_risk: Optional[str] = None,
    timing: Optional[str] = None,
    choose_stock: Optional[str] = None,
    check_existing: bool = False
) -> str:
    """
    运行策略回测

    Args:
        strategy_id: 策略ID
        listen_time: 监听和处理时间（秒），默认30秒
        start_date: 回测开始日期，格式为 "YYYY-MM-DD"，可选，默认为一年前
        end_date: 回测结束日期，格式为 "YYYY-MM-DD"，可选，默认为今天
        indicator: 自定义指标代码，可选
        control_risk: 自定义风控代码，可选
        timing: 自定义择时代码，可选
        choose_stock: 自定义标的代码，可以是以下几种形式：
                     1. 完整的choose_stock函数代码，以"def choose_stock(context):"开头
                     2. 单个股票代码，如"600000.XSHG"
                     3. 多个股票代码，如"600000.XSHG&000001.XSHE"，用"&"符号分隔多个股票代码
        check_existing: 是否检查已存在的回测结果，默认为False

    Returns:
        str: 回测结果信息，或错误信息
    """
    # 验证并修复日期
    start_date, end_date = validate_date_range(start_date, end_date)
    
    # 创建回测任务ID
    beijing_now = get_beijing_now()
    timestamp = beijing_now.strftime('%Y%m%d_%H%M%S')
    task_id = f"{strategy_id}_{start_date}_{end_date}_{timestamp}"
    
    # 获取当前北京日期
    current_date = beijing_now.strftime('%Y-%m-%d')
    
    # 检查是否请求了未来日期
    if end_date and end_date > current_date:
        logger.info(f"请求的回测结束日期 {end_date} 在未来，实际数据可能只到当前日期 {current_date}")
    
    # 初始化预期的图表路径列表
    expected_chart_paths = []
    stock_codes = []
    
    # 解析股票代码和交易所
    if choose_stock and not choose_stock.strip().startswith("def choose_stock"):
        # 判断是否包含多个股票代码
        if "&" in choose_stock:
            # 多个股票代码
            stock_codes = choose_stock.split("&")
            logger.info(f"检测到多个股票代码: {stock_codes}")
            
            # 为每个股票代码生成预期图表路径
            for stock_code in stock_codes:
                if "." in stock_code:
                    parts = stock_code.split('.')
                    if len(parts) == 2:
                        symbol = parts[0]
                        exchange = parts[1]
                        chart_path = generate_chart_path(strategy_id, symbol, exchange, timestamp)
                        if chart_path:
                            expected_chart_paths.append((stock_code, chart_path))
        else:
            # 单个股票代码
            stock_codes = [choose_stock]
            if "." in choose_stock:
                parts = choose_stock.split('.')
                if len(parts) == 2:
                    symbol = parts[0]
                    exchange = parts[1]
                    chart_path = generate_chart_path(strategy_id, symbol, exchange, timestamp)
                    if chart_path:
                        expected_chart_paths.append((choose_stock, chart_path))
    
    # 如果check_existing为True，则检查是否有相同参数的回测结果
    if check_existing:
        existing_result = check_existing_backtest(strategy_id, start_date, end_date, choose_stock)
        if existing_result:
            return f"找到已存在的回测结果:\n\n{existing_result}"
    
    try:
        # 检查策略ID
        if not strategy_id:
            return "错误: 策略ID不能为空"

        # 获取策略名称 - 同时尝试从用户策略和策略库中获取
        # 在函数内部导入，避免循环导入问题
        from utils.strategy_utils import get_strategy_detail
        strategy_name = None
        
        # 首先尝试从用户策略库获取
        user_strategy = get_strategy_detail(strategy_id, "user")
        if user_strategy:
            # 优先使用用户策略的名称
            strategy_name = user_strategy.get('name') or user_strategy.get('strategy_name')
            if strategy_name:
                logger.info(f"从用户策略库获取到策略名称: {strategy_name}")
            else:
                logger.info(f"用户策略存在但没有名称，尝试从策略库获取")
            strategy_data = user_strategy
        
        # 如果没有从用户策略获取到名称，尝试从策略库获取
        if not strategy_name:
            # 尝试从系统策略库获取
            library_strategy = get_strategy_detail(strategy_id, "library")
            if library_strategy:
                strategy_name = library_strategy.get('name') or library_strategy.get('strategy_name')
                logger.info(f"从系统策略库获取到策略名称: {strategy_name}")
                # 如果之前没有获取到策略数据，使用库策略数据
                if not strategy_data:
                    strategy_data = library_strategy
            
        # 如果仍然没有获取到策略数据，说明两处都没有找到
        if not strategy_data:
            error_msg = f"未找到策略: {strategy_id}"
            logger.error(error_msg)
            return error_msg
        
        # 如果名称仍为空，使用默认名称
        if not strategy_name:
            strategy_name = "未命名策略"
            logger.warning(f"无法获取策略名称，使用默认名称: {strategy_name}")

        # 处理choose_stock参数
        stock_info = ""
        if choose_stock:
            # 判断是否已经是完整的choose_stock函数
            if choose_stock.strip().startswith("def choose_stock(context):"):
                # 已经是完整的函数代码，直接使用
                stock_info = choose_stock.strip()
                logger.info("使用提供的choose_stock函数代码进行回测")
            else:
                # 不是函数代码，将其格式化为choose_stock函数
                stock_info = choose_stock
                try:
                    # 验证股票代码格式
                    if '.' not in choose_stock and not choose_stock.strip().startswith("def"):
                        logger.info(f"股票代码 {choose_stock} 不包含交易所后缀，将尝试自动添加")
                    
                    choose_stock = format_choose_stock(choose_stock)
                    logger.info(f"使用指定股票 {stock_info} 进行回测")
                except Exception as e:
                    error_msg = f"处理股票代码失败: {str(e)}"
                    logger.error(error_msg)
                    return error_msg

        # 准备策略代码数据
        strategy_code = {}
        if indicator:
            strategy_code['indicator'] = indicator
        if control_risk:
            strategy_code['control_risk'] = control_risk
        if timing:
            strategy_code['timing'] = timing
        if choose_stock:
            strategy_code['choose_stock'] = choose_stock

        # 直接运行回测，不使用任务队列
        logger.info(f"开始运行回测，策略: {strategy_name} (ID: {strategy_id})，监听时间: {listen_time}秒")
        
        # 导入run_backtest函数
        from utils.backtest_utils import run_backtest
        
        # 直接运行回测
        result = run_backtest(
            strategy_id=strategy_id,
            listen_time=listen_time,
            start_date=start_date,
            end_date=end_date,
            indicator=indicator,
            control_risk=control_risk,
            timing=timing,
            choose_stock=choose_stock,
            timestamp=timestamp
        )
        
        # 检查回测结果
        if result.get('success'):
            chart_path = result.get('chart_path')
            position_count = result.get('position_count', 0)
            
            if chart_path:
                return f"回测完成！\n\n" \
                       f"策略: {strategy_name} (ID: {strategy_id})\n" \
                       f"接收到 {position_count} 条position数据\n" \
                       f"回测结果图表链接: {chart_path}"
            else:
                return f"回测完成，但未生成图表！\n\n" \
                       f"策略: {strategy_name} (ID: {strategy_id})\n" \
                       f"接收到 {position_count} 条position数据"
        else:
            error_msg = result.get('error', '未知错误')
            return f"回测执行失败！\n\n" \
                   f"策略: {strategy_name} (ID: {strategy_id})\n" \
                   f"错误信息: {error_msg}"

    except Exception as e:
        logger.error(f"运行回测时发生错误: {e}")
        return f"运行回测时发生错误: {e}"


def list_backtests(
    limit: int = 10,
    filter_status: Optional[str] = None
) -> str:
    """
    列出回测任务

    Args:
        limit: 返回的任务数量限制，默认为10
        filter_status: 过滤的状态，可选，如"成功"、"失败"、"运行中"等

    Returns:
        str: 回测任务列表
    """
    # 简化版本 - 只扫描CHARTS_DIR目录中的文件
    try:
        chart_files = []
        for filename in os.listdir(CHARTS_DIR):
            if filename.startswith("backtest_") and filename.endswith(".html"):
                # 提取信息
                parts = filename[9:-5].split('_')  # 去掉"backtest_"和".html"
                if len(parts) >= 4:
                    strategy_id = parts[0]
                    symbol = parts[1]
                    exchange = parts[2]
                    timestamp = parts[3]
                    
                    chart_path = get_html_url(os.path.join(CHARTS_DIR, filename))
                    
                    chart_files.append({
                        'strategy_id': strategy_id,
                        'symbol': f"{symbol}.{exchange}",
                        'timestamp': timestamp,
                        'chart_path': chart_path,
                        'file_time': os.path.getmtime(os.path.join(CHARTS_DIR, filename))
                    })
        
        # 按文件修改时间排序（降序）
        chart_files.sort(key=lambda x: x['file_time'], reverse=True)
        
        # 限制返回数量
        chart_files = chart_files[:limit]
        
        if not chart_files:
            return "未找到任何回测结果"
        
        # 生成结果列表
        result_str = f"回测结果列表 (共{len(chart_files)}个):\n\n"
        for i, info in enumerate(chart_files, 1):
            # 格式化时间戳为可读时间
            try:
                timestamp = info['timestamp']
                if len(timestamp) >= 8:  # 至少包含YYYYMMDD
                    year = timestamp[:4]
                    month = timestamp[4:6]
                    day = timestamp[6:8]
                    time_str = f"{year}-{month}-{day}"
                    if len(timestamp) > 8:
                        hour = timestamp[9:11]
                        minute = timestamp[11:13]
                        second = timestamp[13:15] if len(timestamp) >= 15 else "00"
                        time_str += f" {hour}:{minute}:{second}"
                else:
                    time_str = timestamp
            except:
                time_str = info['timestamp']
                
            result_str += f"{i}. 策略ID: {info['strategy_id']}\n"
            result_str += f"   股票: {info['symbol']}\n"
            result_str += f"   时间: {time_str}\n"
            result_str += f"   图表链接: {info['chart_path']}\n"
            
            if i < len(chart_files):
                result_str += "\n"
        
        return result_str
        
    except Exception as e:
        logger.error(f"列出回测任务失败: {e}")
        return f"列出回测任务失败: {e}"


def register_tools(mcp: FastMCP):
    """
    注册回测相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册运行策略回测工具
    mcp.tool()(run_strategy_backtest)
    
    # 注册列出回测任务工具
    mcp.tool()(list_backtests)
