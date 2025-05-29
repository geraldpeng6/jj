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
from utils.backtest_manager import (
    submit_backtest_task, get_task_status, get_all_tasks,
    find_task_by_params, cleanup_old_tasks
)

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


def generate_chart_path(strategy_id: str, symbol: str, exchange: str, timestamp: str) -> str:
    """
    生成图表路径

    Args:
        strategy_id: 策略ID
        symbol: 股票代码
        exchange: 交易所代码
        timestamp: 时间戳

    Returns:
        str: 图表路径
    """
    file_name = f"backtest_{strategy_id}_{symbol}_{exchange}_{timestamp}.html"
    file_path = os.path.join(CHARTS_DIR, file_name)
    
    # 生成URL
    base_url = "http://3.84.20.36/charts"
    url = f"{base_url}/{file_name}"
    
    return url


async def run_strategy_backtest(
    strategy_id: str,
    listen_time: int = 30,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    indicator: Optional[str] = None,
    control_risk: Optional[str] = None,
    timing: Optional[str] = None,
    choose_stock: Optional[str] = None,
    check_existing: bool = False,
    background: bool = False
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
        background: 是否在后台运行，默认为False。当设置为True时，将回测提交到任务队列异步执行，
                   特别适合长时间回测（如1年以上）或需要较长监听时间的场景

    Returns:
        str: 回测结果信息，或错误信息
    """
    # 创建回测任务ID
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    task_id = f"{strategy_id}_{start_date}_{end_date}_{timestamp}"
    
    # 解析股票代码和交易所
    symbol = None
    exchange = None
    if choose_stock and not choose_stock.strip().startswith("def choose_stock"):
        # 解析股票代码和交易所
        parts = choose_stock.split('.')
        if len(parts) == 2:
            symbol = parts[0]
            exchange = parts[1]
    
    # 如果check_existing为True，则检查是否有相同参数的回测结果
    if check_existing:
        existing_result = check_existing_backtest(strategy_id, start_date, end_date, choose_stock)
        if existing_result:
            return f"找到已存在的回测结果:\n\n{existing_result}"
    
    # 检查是否有正在运行的相同回测任务
    existing_task = find_task_by_params(strategy_id, start_date, end_date, choose_stock)
    if existing_task:
        task_id = existing_task.get('task_id', 'unknown')
        progress = existing_task.get('progress', 0)
        task_status = existing_task.get('status', '运行中')
        
        # 如果任务已完成，返回结果
        if task_status in ['成功', '完成'] and existing_task.get('result'):
            result = existing_task.get('result', {})
            chart_path = result.get('chart_path')
            
            if chart_path:
                return f"回测任务已完成！\n\n" \
                       f"策略: {existing_task.get('strategy_name', '未命名策略')} (ID: {existing_task.get('strategy_id', 'unknown')})\n" \
                       f"回测结果图表链接: {chart_path}"
        
        # 如果任务仍在运行，返回预期的图表链接
        expected_chart_path = existing_task.get('expected_chart_path')
        if expected_chart_path:
            return f"回测任务正在运行中（进度: {progress}%）。\n\n" \
                   f"策略: {existing_task.get('strategy_name', '未命名策略')} (ID: {existing_task.get('strategy_id', 'unknown')})\n" \
                   f"完成后结果将显示在: {expected_chart_path}\n\n" \
                   f"请稍后访问该链接查看结果。"
            
        return f"回测任务已在运行中，请稍后再查询结果。任务ID: {task_id}, 状态: {task_status}, 进度: {progress}%"
        
    try:
        # 检查策略ID
        if not strategy_id:
            return "错误: 策略ID不能为空"

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
                choose_stock = format_choose_stock(choose_stock)
                logger.info(f"使用指定股票 {stock_info} 进行回测")

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

        # 获取策略名称 - 同时尝试从用户策略和策略库中获取
        # 在函数内部导入，避免循环导入问题
        from utils.strategy_utils import get_strategy_detail
        strategy_name = None
        
        # 首先尝试从用户策略库获取
        user_strategy = get_strategy_detail(strategy_id, "user")
        if user_strategy and (user_strategy.get('name') or user_strategy.get('strategy_name')):
            strategy_name = user_strategy.get('name') or user_strategy.get('strategy_name')
            logger.info(f"从用户策略库获取到策略名称: {strategy_name}")
        else:
            # 尝试从系统策略库获取
            library_strategy = get_strategy_detail(strategy_id, "library")
            if library_strategy and (library_strategy.get('name') or library_strategy.get('strategy_name')):
                strategy_name = library_strategy.get('name') or library_strategy.get('strategy_name')
                logger.info(f"从系统策略库获取到策略名称: {strategy_name}")
            else:
                strategy_name = "未命名策略"
                logger.warning(f"无法获取策略名称，使用默认名称: {strategy_name}")
        
        # 预先生成预期的图表路径（使用开始时间戳）
        expected_chart_path = None
        if symbol and exchange:
            expected_chart_path = generate_chart_path(strategy_id, symbol, exchange, timestamp)
        
        # 如果是后台模式，提交到任务队列并立即返回
        if background:
            # 提交任务
            task_id = submit_backtest_task(
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                start_date=start_date,
                end_date=end_date,
                indicator=indicator,
                control_risk=control_risk,
                timing=timing,
                choose_stock=choose_stock,
                listen_time=max(120, listen_time),  # 后台模式下使用更长的监听时间
                expected_chart_path=expected_chart_path,  # 传递预期的图表路径
                timestamp=timestamp  # 传递时间戳
            )
            
            # 返回任务提交成功的消息及预期的图表链接
            if stock_info and not stock_info.startswith("def choose_stock"):
                if expected_chart_path:
                    return f"使用股票 {stock_info} 的回测任务已提交到后台运行！\n\n" \
                           f"策略: {strategy_name} (ID: {strategy_id})\n" \
                           f"任务ID: {task_id}\n\n" \
                           f"完成后结果将显示在: {expected_chart_path}\n\n" \
                           f"请稍后访问该链接查看结果。"
                else:
                    return f"使用股票 {stock_info} 的回测任务已提交到后台运行！\n\n" \
                           f"策略: {strategy_name} (ID: {strategy_id})\n" \
                           f"任务ID: {task_id}\n\n" \
                           f"请等待任务完成后查看结果。"
            else:
                if expected_chart_path:
                    return f"使用策略自带标的的回测任务已提交到后台运行！\n\n" \
                           f"策略: {strategy_name} (ID: {strategy_id})\n" \
                           f"任务ID: {task_id}\n\n" \
                           f"完成后结果将显示在: {expected_chart_path}\n\n" \
                           f"请稍后访问该链接查看结果。"
                else:
                    return f"使用策略自带标的的回测任务已提交到后台运行！\n\n" \
                           f"策略: {strategy_name} (ID: {strategy_id})\n" \
                           f"任务ID: {task_id}\n\n" \
                           f"请等待任务完成后查看结果。"

        # 将回测任务添加到运行列表
        RUNNING_BACKTESTS[task_id] = {
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'start_date': start_date,
            'end_date': end_date,
            'choose_stock': choose_stock,
            'start_time': datetime.now(),
            'status': '初始化中',
            'progress': 0,
            'result': None,
            'expected_chart_path': expected_chart_path
        }

        # 在非阻塞模式下启动回测过程，减小listen_time避免MCP超时
        safe_listen_time = min(listen_time, 30)
        logger.info(f"开始运行回测任务 {task_id}，设置listen_time={safe_listen_time}秒")
        
        # 更新状态
        RUNNING_BACKTESTS[task_id]['status'] = '正在运行'
        
        # 运行回测（这里使用较短的超时确保MCP不会超时）
        result = run_backtest(
            strategy_id=strategy_id,
            listen_time=safe_listen_time,
            start_date=start_date,
            end_date=end_date,
            indicator=indicator,
            control_risk=control_risk,
            timing=timing,
            choose_stock=choose_stock,
            timestamp=timestamp  # 传递时间戳，用于生成图表文件名
        )
        
        # 如果回测返回了策略名称，但我们获取的策略名称不是"未命名策略"，则优先使用我们获取的名称
        if result['success'] and result['strategy_name'] == '未命名策略' and strategy_name != '未命名策略':
            result['strategy_name'] = strategy_name
            logger.info(f"使用API获取的策略名称: {strategy_name}")

        # 更新回测结果
        RUNNING_BACKTESTS[task_id]['result'] = result
        RUNNING_BACKTESTS[task_id]['status'] = '完成' if result['success'] else '失败'
        RUNNING_BACKTESTS[task_id]['progress'] = 100

        # 保存回测结果到磁盘，便于后续查询
        save_backtest_result(task_id, RUNNING_BACKTESTS[task_id])

        # 格式化输出
        if result['success']:
            # 根据是否使用指定股票生成不同的标题
            if stock_info and not stock_info.startswith("def choose_stock"):
                result_str = f"使用股票 {stock_info} 回测成功完成！\n\n"
            else:
                result_str = f"使用策略自带标的进行，回测成功完成！\n\n"

            result_str += f"策略: {result['strategy_name']} (ID: {result['strategy_id']})\n"
            result_str += f"接收到 {result['position_count']} 条position数据\n"
            result_str += f"数据已保存到: {result['file_path']}\n"
            result_str += f"任务ID: {task_id}\n"

            if result.get('chart_path'):
                result_str += f"\n回测结果图表链接如下: {result['chart_path']}"
            else:
                result_str += "\n未生成回测结果图表"

            # 添加日期验证信息
            date_validation = result.get('date_validation', {})
            if date_validation.get('from_date_adjusted') or date_validation.get('to_date_adjusted'):
                result_str += "\n\n日期范围已自动调整:"
                if date_validation.get('from_date_adjusted'):
                    result_str += f"\n- 开始日期从 {date_validation.get('original_from_date')} 调整为 {date_validation.get('adjusted_from_date')} (股票上市日期: {date_validation.get('listing_date')})"
                if date_validation.get('to_date_adjusted'):
                    result_str += f"\n- 结束日期从 {date_validation.get('original_to_date')} 调整为 {date_validation.get('adjusted_to_date')} (股票最后交易日期: {date_validation.get('last_date')})"

            return result_str
        else:
            return f"回测失败: {result.get('error', '未知错误')}"

    except Exception as e:
        logger.error(f"运行回测时发生错误: {e}")
        # 更新回测状态
        if task_id in RUNNING_BACKTESTS:
            RUNNING_BACKTESTS[task_id]['status'] = f'错误: {str(e)}'
            RUNNING_BACKTESTS[task_id]['progress'] = 100
        return f"运行回测时发生错误: {e}"


async def list_backtests(
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
    # 获取所有任务
    all_tasks = get_all_tasks()
    
    # 过滤任务
    if filter_status:
        filtered_tasks = [
            task for task in all_tasks 
            if task.get('status') == filter_status or 
            (filter_status == '运行中' and task.get('status') not in ['成功', '完成', '失败'] and not task.get('status', '').startswith('错误'))
        ]
    else:
        filtered_tasks = all_tasks
        
    # 按提交时间降序排序
    sorted_tasks = sorted(
        filtered_tasks, 
        key=lambda x: x.get('submit_time', ''), 
        reverse=True
    )
    
    # 限制返回数量
    limited_tasks = sorted_tasks[:limit]
    
    if not limited_tasks:
        if filter_status:
            return f"未找到状态为'{filter_status}'的回测任务"
        else:
            return "未找到任何回测任务"
    
    # 生成任务列表
    result_str = f"回测任务列表 (共{len(limited_tasks)}个):\n\n"
    for i, task in enumerate(limited_tasks, 1):
        task_id = task.get('task_id', 'unknown')
        strategy_name = task.get('strategy_name', '未命名策略')
        status = task.get('status', '未知')
        progress = task.get('progress', 0)
        submit_time_str = task.get('submit_time', '')
        
        # 处理日期显示
        if submit_time_str:
            try:
                submit_time = datetime.fromisoformat(submit_time_str)
                submit_time_display = submit_time.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                submit_time_display = submit_time_str
        else:
            submit_time_display = '未知'
            
        # 获取股票代码信息
        choose_stock = task.get('choose_stock', '')
        stock_info = ""
        if choose_stock:
            if not choose_stock.strip().startswith("def choose_stock(context):"):
                stock_info = f"股票: {choose_stock}"
        
        result_str += f"{i}. 任务ID: {task_id}\n"
        result_str += f"   策略: {strategy_name} (ID: {task.get('strategy_id', 'unknown')})\n"
        result_str += f"   状态: {status} (进度: {progress}%)\n"
        result_str += f"   提交时间: {submit_time_display}\n"
        
        if stock_info:
            result_str += f"   {stock_info}\n"
            
        if i < len(limited_tasks):
            result_str += "\n"
    
    return result_str


def check_existing_backtest(
    strategy_id: str, 
    start_date: Optional[str], 
    end_date: Optional[str],
    choose_stock: Optional[str]
) -> Optional[str]:
    """
    检查是否存在相同参数的回测结果

    Args:
        strategy_id: 策略ID
        start_date: 回测开始日期
        end_date: 回测结束日期
        choose_stock: 自定义标的代码

    Returns:
        Optional[str]: 找到的回测结果信息，如果不存在则返回None
    """
    # 使用backtest_manager的find_task_by_params函数查找任务
    task_data = find_task_by_params(strategy_id, start_date, end_date, choose_stock)
    
    if task_data:
        task_id = task_data.get('task_id', 'unknown')
        status = task_data.get('status', '未知')
        
        # 只有成功的任务才返回结果
        if status in ['成功', '完成']:
            result = task_data.get('result', {})
            strategy_name = result.get('strategy_name', task_data.get('strategy_name', '未命名策略'))
            
            result_str = f"找到现有回测结果 (任务ID: {task_id})\n\n"
            result_str += f"策略: {strategy_name} (ID: {result.get('strategy_id', 'unknown')})\n"
            result_str += f"接收到 {result.get('position_count', 0)} 条position数据\n"
            
            if result.get('file_path'):
                result_str += f"数据已保存到: {result.get('file_path')}\n"

            if result.get('chart_path'):
                result_str += f"\n回测结果图表链接如下: {result['chart_path']}"
            else:
                result_str += "\n未生成回测结果图表"
                
            return result_str
    
    return None


def save_backtest_result(task_id: str, task_data: Dict[str, Any]) -> None:
    """
    保存回测结果到磁盘

    Args:
        task_id: 回测任务ID
        task_data: 回测任务数据
    """
    try:
        # 确保目录存在
        backtest_status_dir = os.path.join(BACKTEST_DIR, 'status')
        os.makedirs(backtest_status_dir, exist_ok=True)
        
        # 保存文件路径
        file_path = os.path.join(backtest_status_dir, f"{task_id}.json")
        
        # 将datetime对象转换为字符串
        task_data_copy = task_data.copy()
        if 'start_time' in task_data_copy and isinstance(task_data_copy['start_time'], datetime):
            task_data_copy['start_time'] = task_data_copy['start_time'].isoformat()
            
        # 保存为JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(task_data_copy, f, ensure_ascii=False, indent=2)
            
        logger.info(f"回测任务 {task_id} 结果已保存到 {file_path}")
    except Exception as e:
        logger.error(f"保存回测任务 {task_id} 结果时出错: {e}")


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
    
    # 定期清理旧任务记录（30天前）
    cleanup_old_tasks(30)
