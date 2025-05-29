#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测日期修复测试脚本

专门用于测试和修复backtest_utils.py中的日期处理问题
"""

import os
import sys
import logging
import traceback
import datetime
import pandas as pd
from typing import Dict, Any, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_backtest_dates.log', mode='w'),
        logging.StreamHandler()
    ]
)

# 获取日志记录器
logger = logging.getLogger('fix_backtest_dates')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
try:
    from utils.date_utils import get_beijing_now, parse_date_string, validate_date_range
    from utils.backtest_utils import run_backtest
    from utils.symbol_utils import validate_date_range as validate_symbol_date_range
    from utils.auth_utils import load_auth_config
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def test_run_backtest(
    strategy_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    listen_time: int = 10  # 使用较短的监听时间以加快测试
) -> Dict[str, Any]:
    """
    测试运行回测函数
    
    Args:
        strategy_id: 策略ID
        start_date: 开始日期，格式为 "YYYY-MM-DD"，可选
        end_date: 结束日期，格式为 "YYYY-MM-DD"，可选
        listen_time: 监听时间（秒），默认10秒
        
    Returns:
        Dict[str, Any]: 回测结果
    """
    logger.info(f"测试运行回测: 策略ID={strategy_id}, 从 {start_date} 到 {end_date}")
    
    # 获取当前北京时间
    beijing_now = get_beijing_now()
    logger.info(f"当前北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行回测
    result = run_backtest(
        strategy_id=strategy_id,
        listen_time=listen_time,
        start_date=start_date,
        end_date=end_date
    )
    
    # 记录结果
    success = result.get('success', False)
    logger.info(f"回测结果: {'成功' if success else '失败'}")
    
    if success:
        position_count = result.get('position_count', 0)
        logger.info(f"接收到 {position_count} 条position数据")
        
        # 检查日期验证信息
        date_validation = result.get('date_validation', {})
        
        if date_validation:
            logger.info("日期验证结果:")
            
            # 检查日期是否被调整
            if date_validation.get('from_date_adjusted'):
                original_from = date_validation.get('original_from_date')
                adjusted_from = date_validation.get('adjusted_from_date')
                logger.warning(f"开始日期被调整: {original_from} -> {adjusted_from}")
            
            if date_validation.get('to_date_adjusted'):
                original_to = date_validation.get('original_to_date')
                adjusted_to = date_validation.get('adjusted_to_date')
                logger.warning(f"结束日期被调整: {original_to} -> {adjusted_to}")
            
            # 检查上市日期和最后交易日期
            listing_date = date_validation.get('listing_date')
            last_date = date_validation.get('last_date')
            
            if listing_date:
                logger.info(f"上市日期: {listing_date}")
            
            if last_date:
                logger.info(f"最后交易日期: {last_date}")
                
                # 检查最后交易日期与当前日期的关系
                last_dt = parse_date_string(last_date)
                if last_dt and last_dt.date() < beijing_now.date():
                    logger.warning(f"最后交易日期 {last_date} 早于当前日期 {beijing_now.strftime('%Y-%m-%d')}")
            
            # 检查调整信息
            messages = date_validation.get('messages', [])
            if messages:
                logger.info("日期调整信息:")
                for msg in messages:
                    logger.info(f"- {msg}")
        
        # 检查图表路径
        chart_path = result.get('chart_path')
        if chart_path:
            logger.info(f"生成的图表路径: {chart_path}")
    else:
        error = result.get('error')
        logger.error(f"回测失败: {error}")
    
    logger.info("-" * 60)
    return result

def run_date_tests() -> None:
    """运行一系列日期测试"""
    logger.info("======== 开始测试回测日期处理 ========")
    
    # 获取当前北京时间
    beijing_now = get_beijing_now()
    current_date = beijing_now.strftime("%Y-%m-%d")
    
    # 策略ID - 可以根据实际情况修改
    strategy_id = "CAN_双均线"  # 使用一个简单的策略进行测试
    
    # 创建一系列测试用例
    test_cases = [
        {
            "name": "当前日期到未来30天",
            "start_date": current_date,
            "end_date": (beijing_now + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        },
        {
            "name": "当前日期到未来一年",
            "start_date": current_date,
            "end_date": (beijing_now + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        },
        {
            "name": "一个月前到未来一个月",
            "start_date": (beijing_now - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (beijing_now + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        },
        {
            "name": "2024-05-28到2025-05-28",
            "start_date": "2024-05-28",
            "end_date": "2025-05-28"
        }
    ]
    
    # 运行测试用例
    for test_case in test_cases:
        logger.info(f"\n## 测试用例: {test_case['name']} ##")
        result = test_run_backtest(
            strategy_id=strategy_id,
            start_date=test_case['start_date'],
            end_date=test_case['end_date']
        )
    
    logger.info("======== 测试完成 ========")

if __name__ == "__main__":
    try:
        # 加载认证配置
        if not load_auth_config():
            logger.error("无法加载认证配置，请检查认证文件")
            sys.exit(1)
            
        # 运行测试
        run_date_tests()
    except Exception as e:
        logger.error(f"测试过程中发生未捕获的异常: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 