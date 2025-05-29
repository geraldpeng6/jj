#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测管理器模块

提供回测任务的异步管理和状态跟踪功能
"""

import os
import json
import time
import logging
import threading
import queue
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import traceback

from utils.backtest_utils import run_backtest

# 获取日志记录器
logger = logging.getLogger('quant_mcp.backtest_manager')

# 回测结果目录
DATA_DIR = 'data'
BACKTEST_DIR = os.path.join(DATA_DIR, 'backtest')
STATUS_DIR = os.path.join(BACKTEST_DIR, 'status')

# 确保目录存在
os.makedirs(STATUS_DIR, exist_ok=True)

# 全局任务队列
task_queue = queue.Queue()

# 存储正在运行的回测任务
RUNNING_BACKTESTS = {}

# 工作线程是否已启动
_worker_started = False
_worker_thread = None


def start_worker():
    """
    启动工作线程，处理回测任务队列
    """
    global _worker_started, _worker_thread
    
    if _worker_started:
        logger.debug("工作线程已经启动，无需重新启动")
        return
        
    logger.info("启动回测工作线程")
    _worker_thread = threading.Thread(target=_process_task_queue, daemon=True)
    _worker_thread.start()
    _worker_started = True


def _process_task_queue():
    """
    处理任务队列的工作线程函数
    """
    logger.info("回测工作线程已启动")
    
    while True:
        try:
            # 从队列获取任务，阻塞等待
            task = task_queue.get()
            
            if task is None:
                # None 任务表示停止线程
                logger.info("收到停止信号，工作线程退出")
                task_queue.task_done()
                break
                
            # 开始处理任务
            task_id = task.get('task_id')
            logger.info(f"开始处理回测任务: {task_id}")
            
            # 更新任务状态
            update_task_status(task_id, '正在执行', 10)
            
            try:
                # 执行回测
                result = run_backtest(
                    strategy_id=task.get('strategy_id'),
                    listen_time=task.get('listen_time', 120),  # 在后台模式下可以使用更长的监听时间
                    start_date=task.get('start_date'),
                    end_date=task.get('end_date'),
                    indicator=task.get('indicator'),
                    control_risk=task.get('control_risk'),
                    timing=task.get('timing'),
                    choose_stock=task.get('choose_stock'),
                    timestamp=task.get('timestamp')  # 传递时间戳参数
                )
                
                # 更新任务状态和结果
                if result.get('success'):
                    update_task_status(task_id, '成功', 100, result=result)
                    logger.info(f"回测任务 {task_id} 执行成功，接收到 {result.get('position_count', 0)} 条数据")
                else:
                    update_task_status(task_id, '失败', 100, result=result)
                    logger.error(f"回测任务 {task_id} 执行失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                logger.error(f"回测任务 {task_id} 执行异常: {str(e)}")
                logger.error(traceback.format_exc())
                update_task_status(task_id, f'错误: {str(e)}', 100)
                
            finally:
                # 标记任务完成
                task_queue.task_done()
                
        except Exception as e:
            logger.error(f"处理任务队列时发生异常: {str(e)}")
            logger.error(traceback.format_exc())
            # 继续处理下一个任务
            continue


def submit_backtest_task(
    strategy_id: str,
    strategy_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    indicator: Optional[str] = None,
    control_risk: Optional[str] = None,
    timing: Optional[str] = None,
    choose_stock: Optional[str] = None,
    listen_time: int = 120,
    expected_chart_paths: Optional[List[Tuple[str, str]]] = None,
    timestamp: Optional[str] = None
) -> str:
    """
    提交回测任务到队列
    
    Args:
        strategy_id: 策略ID
        strategy_name: 策略名称
        start_date: 回测开始日期
        end_date: 回测结束日期
        indicator: 自定义指标代码
        control_risk: 自定义风控代码
        timing: 自定义择时代码
        choose_stock: 自定义标的代码
        listen_time: 监听时间（秒）
        expected_chart_paths: 预期的图表路径列表，每项为(股票代码,图表URL)元组，可选
        timestamp: 时间戳，用于生成图表文件名
        
    Returns:
        str: 任务ID
    """
    # 创建任务ID
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    task_id = f"{strategy_id}_{start_date}_{end_date}_{timestamp}"
    
    # 创建任务配置
    task = {
        'task_id': task_id,
        'strategy_id': strategy_id,
        'strategy_name': strategy_name,
        'start_date': start_date,
        'end_date': end_date,
        'indicator': indicator,
        'control_risk': control_risk,
        'timing': timing,
        'choose_stock': choose_stock,
        'listen_time': listen_time,
        'submit_time': datetime.now().isoformat(),
        'status': '等待中',
        'progress': 0,
        'result': None,
        'expected_chart_paths': expected_chart_paths,
        'timestamp': timestamp
    }
    
    # 保存任务到运行列表和磁盘
    RUNNING_BACKTESTS[task_id] = task
    save_task_status(task_id, task)
    
    # 确保工作线程已启动
    start_worker()
    
    # 将任务添加到队列
    task_queue.put(task)
    logger.info(f"已提交回测任务 {task_id} 到队列")
    
    return task_id


def update_task_status(
    task_id: str, 
    status: str, 
    progress: int, 
    result: Optional[Dict[str, Any]] = None
) -> None:
    """
    更新任务状态
    
    Args:
        task_id: 任务ID
        status: 状态描述
        progress: 进度百分比（0-100）
        result: 任务结果（可选）
    """
    if task_id in RUNNING_BACKTESTS:
        RUNNING_BACKTESTS[task_id]['status'] = status
        RUNNING_BACKTESTS[task_id]['progress'] = progress
        
        if result is not None:
            RUNNING_BACKTESTS[task_id]['result'] = result
            
        # 保存到磁盘
        save_task_status(task_id, RUNNING_BACKTESTS[task_id])
    else:
        logger.warning(f"尝试更新不存在的任务状态: {task_id}")


def save_task_status(task_id: str, task_data: Dict[str, Any]) -> None:
    """
    保存任务状态到磁盘
    
    Args:
        task_id: 任务ID
        task_data: 任务数据
    """
    try:
        # 创建副本以避免修改原始数据
        task_data_copy = task_data.copy()
        
        # 将datetime对象转换为字符串
        for key, value in task_data_copy.items():
            if isinstance(value, datetime):
                task_data_copy[key] = value.isoformat()
                
        # 保存文件路径
        file_path = os.path.join(STATUS_DIR, f"{task_id}.json")
        
        # 保存为JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(task_data_copy, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"保存任务状态失败: {str(e)}")


def load_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    从磁盘加载任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Optional[Dict[str, Any]]: 任务数据，如果不存在则返回None
    """
    try:
        file_path = os.path.join(STATUS_DIR, f"{task_id}.json")
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
            
        return task_data
            
    except Exception as e:
        logger.error(f"加载任务状态失败: {str(e)}")
        return None


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        Optional[Dict[str, Any]]: 任务状态数据，如果不存在则返回None
    """
    # 先从内存中查找
    if task_id in RUNNING_BACKTESTS:
        return RUNNING_BACKTESTS[task_id]
        
    # 如果内存中没有，从磁盘加载
    return load_task_status(task_id)


def get_all_tasks() -> List[Dict[str, Any]]:
    """
    获取所有任务列表
    
    Returns:
        List[Dict[str, Any]]: 所有任务的状态数据列表
    """
    tasks = []
    
    # 先添加内存中的任务
    for task_id, task_data in RUNNING_BACKTESTS.items():
        tasks.append(task_data)
        
    # 从磁盘加载其他任务
    try:
        for filename in os.listdir(STATUS_DIR):
            if not filename.endswith('.json'):
                continue
                
            task_id = filename[:-5]  # 去除.json后缀
            
            # 如果任务不在内存中，从磁盘加载
            if task_id not in RUNNING_BACKTESTS:
                task_data = load_task_status(task_id)
                if task_data:
                    tasks.append(task_data)
    except Exception as e:
        logger.error(f"获取所有任务列表失败: {str(e)}")
        
    return tasks


def find_task_by_params(
    strategy_id: str,
    start_date: Optional[str],
    end_date: Optional[str],
    choose_stock: Optional[str]
) -> Optional[Dict[str, Any]]:
    """
    根据参数查找任务
    
    Args:
        strategy_id: 策略ID
        start_date: 回测开始日期
        end_date: 回测结束日期
        choose_stock: 自定义标的代码
        
    Returns:
        Optional[Dict[str, Any]]: 找到的任务数据，如果不存在则返回None
    """
    # 先检查内存中的任务
    for task_id, task_data in RUNNING_BACKTESTS.items():
        if (task_data.get('strategy_id') == strategy_id and
            task_data.get('start_date') == start_date and
            task_data.get('end_date') == end_date and
            task_data.get('choose_stock') == choose_stock):
            return task_data
            
    # 从磁盘检查其他任务
    all_tasks = get_all_tasks()
    for task_data in all_tasks:
        if (task_data.get('strategy_id') == strategy_id and
            task_data.get('start_date') == start_date and
            task_data.get('end_date') == end_date and
            task_data.get('choose_stock') == choose_stock):
            return task_data
            
    return None


def cleanup_old_tasks(days: int = 30) -> None:
    """
    清理旧的任务记录
    
    Args:
        days: 保留的天数，默认30天
    """
    try:
        now = datetime.now()
        deleted_count = 0
        
        for filename in os.listdir(STATUS_DIR):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(STATUS_DIR, filename)
            
            # 获取文件修改时间
            mtime = os.path.getmtime(file_path)
            mtime_datetime = datetime.fromtimestamp(mtime)
            
            # 计算文件年龄（天）
            age_days = (now - mtime_datetime).days
            
            # 如果文件超过指定天数，删除它
            if age_days > days:
                os.remove(file_path)
                deleted_count += 1
                
        if deleted_count > 0:
            logger.info(f"清理了 {deleted_count} 个旧的任务记录")
            
    except Exception as e:
        logger.error(f"清理旧任务记录失败: {str(e)}")


def stop_worker():
    """
    停止工作线程
    """
    global _worker_started, _worker_thread
    
    if _worker_started and _worker_thread is not None:
        logger.info("正在停止回测工作线程")
        task_queue.put(None)  # 发送停止信号
        _worker_thread.join(timeout=5)  # 等待线程退出，最多等待5秒
        _worker_started = False
        _worker_thread = None
        logger.info("回测工作线程已停止")


# 启动应用程序时自动启动工作线程
start_worker()

# 应用程序退出时清理资源
import atexit
atexit.register(stop_worker) 