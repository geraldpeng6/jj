#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Symbol工具模块调试脚本

专门用于调试symbol_utils.py中的日期验证逻辑
"""

import os
import sys
import json
import logging
import datetime
import traceback
from typing import Dict, Any, Optional, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/debug_symbol_utils.log', mode='w'),
        logging.StreamHandler()
    ]
)

# 获取日志记录器
logger = logging.getLogger('debug_symbol_utils')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
try:
    from utils.date_utils import get_beijing_now, parse_date_string, validate_date_range
    from utils.symbol_utils import validate_date_range as validate_symbol_date_range
    from utils.symbol_utils import get_symbol_info
    from utils.auth_utils import load_auth_config, get_auth_info, get_headers
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.error(traceback.format_exc())
    sys.exit(1)

def log_dict(name: str, data: Dict[str, Any]) -> None:
    """打印字典内容到日志"""
    logger.info(f"===== {name} =====")
    for key, value in data.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * (len(name) + 12))

def debug_validate_date_range(full_name: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> None:
    """调试股票日期范围验证函数"""
    logger.info(f"调试日期范围验证: {full_name} 从 '{from_date}' 到 '{to_date}'")
    
    # 记录当前北京时间
    beijing_now = get_beijing_now()
    logger.info(f"当前北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 调用函数获取股票信息
    logger.info(f"获取股票信息: {full_name}")
    symbol_info = get_symbol_info(full_name)
    
    if symbol_info:
        logger.info("股票信息获取成功")
        
        # 记录关键日期信息
        listing_date = symbol_info.get('start_date')
        last_date = symbol_info.get('end_date')
        
        logger.info(f"上市日期: {listing_date}")
        logger.info(f"最后交易日期: {last_date}")
        
        # 尝试解析日期
        if listing_date:
            listing_dt = parse_date_string(listing_date)
            logger.info(f"解析上市日期: {listing_dt}")
        
        if last_date:
            last_dt = parse_date_string(last_date)
            logger.info(f"解析最后交易日期: {last_dt}")
            
            # 检查最后交易日期与当前日期的关系
            if last_dt:
                if last_dt.date() < beijing_now.date():
                    logger.warning(f"最后交易日期 {last_date} 早于当前日期 {beijing_now.strftime('%Y-%m-%d')}")
                else:
                    logger.info(f"最后交易日期 {last_date} 不早于当前日期 {beijing_now.strftime('%Y-%m-%d')}")
        
        # 调用validate_date_range函数并记录结果
        result_from, result_to, result_info = validate_symbol_date_range(
            full_name=full_name,
            from_date=from_date,
            to_date=to_date
        )
        
        logger.info(f"验证后的开始日期: {result_from} (原始值: {from_date})")
        logger.info(f"验证后的结束日期: {result_to} (原始值: {to_date})")
        
        # 记录详细的验证结果
        log_dict("验证结果信息", result_info)
        
        # 分析未来日期是否被截断
        if to_date and result_to:
            to_date_dt = parse_date_string(to_date)
            result_to_dt = parse_date_string(result_to)
            
            if to_date_dt and result_to_dt and to_date_dt > result_to_dt:
                logger.warning(f"未来日期被截断: {to_date} -> {result_to}")
                
                # 详细分析调整原因
                if result_info.get('to_date_adjusted'):
                    logger.warning("结束日期被调整的原因:")
                    for msg in result_info.get('message', []):
                        logger.warning(f"- {msg}")
                    
                    # 检查最后交易日期是否影响了结果
                    if last_date and result_to == last_date:
                        logger.warning(f"结束日期被调整为最后交易日期: {last_date}")
                        
                        # 检查symbol_utils.py中的条件判断
                        if last_dt and last_dt.date() < beijing_now.date():
                            logger.error("发现问题: 最后交易日期早于当前日期，但未来日期仍被截断")
                            logger.error("在symbol_utils.py中，当最后交易日期早于当前日期时，不应该调整未来日期")
                            
                            # 显示相关代码行号
                            logger.error("请检查utils/symbol_utils.py中的validate_date_range函数，特别是以下逻辑:")
                            logger.error("if to_date_dt > last_date_dt and last_date_dt < current_date_dt:")
                            logger.error("    to_date = last_date")
                        else:
                            logger.info("最后交易日期不早于当前日期，调整未来日期是合理的")
    else:
        logger.error(f"无法获取股票信息: {full_name}")
    
    logger.info("-" * 60)

def run_debug_tests() -> None:
    """运行调试测试"""
    logger.info("======== 开始调试股票日期范围验证 ========")
    
    # 获取当前北京日期
    beijing_now = get_beijing_now()
    current_date = beijing_now.strftime("%Y-%m-%d")
    
    # 创建一系列未来日期进行测试
    future_dates = []
    for days in [1, 7, 30, 90, 180, 365]:
        future_date = (beijing_now + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
        future_dates.append((days, future_date))
    
    # 测试不同股票代码
    stock_codes = [
        ("600000", "XSHG"),  # 浦发银行
        ("000001", "XSHE"),  # 平安银行
        ("601398", "XSHG"),  # 工商银行
        ("600519", "XSHG"),  # 贵州茅台
        ("000651", "XSHE")   # 格力电器
    ]
    
    # 对每个股票进行测试
    for symbol, exchange in stock_codes:
        full_name = f"{symbol}.{exchange}"
        logger.info(f"\n## 测试股票: {full_name} ##")
        
        # 测试当前日期到未来日期
        for days, future_date in future_dates:
            logger.info(f"\n# 测试范围: 当前 {current_date} 到未来 {future_date} (+{days}天) #")
            debug_validate_date_range(full_name, current_date, future_date)
        
        # 测试一个月前到未来日期
        one_month_ago = (beijing_now - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        for days, future_date in future_dates:
            logger.info(f"\n# 测试范围: 一个月前 {one_month_ago} 到未来 {future_date} (+{days}天) #")
            debug_validate_date_range(full_name, one_month_ago, future_date)
    
    # 测试问题的范围 - 2024-05-28到2025-05-28
    logger.info("\n## 测试特定问题的日期范围 ##")
    for symbol, exchange in stock_codes:
        full_name = f"{symbol}.{exchange}"
        logger.info(f"\n# 测试股票 {full_name} 的问题范围: 2024-05-28 到 2025-05-28 #")
        debug_validate_date_range(full_name, "2024-05-28", "2025-05-28")
    
    logger.info("======== 调试股票日期范围验证结束 ========")

if __name__ == "__main__":
    try:
        # 加载认证配置
        if not load_auth_config():
            logger.error("无法加载认证配置，请检查认证文件")
            sys.exit(1)
            
        # 运行调试测试
        run_debug_tests()
    except Exception as e:
        logger.error(f"调试过程中发生未捕获的异常: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 