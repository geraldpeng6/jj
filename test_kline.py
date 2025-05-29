#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据获取测试脚本

用于测试K线数据获取功能，特别是日期处理相关的问题
"""

import os
import sys
import json
import logging
import datetime
import traceback
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/test_kline.log', mode='w'),
        logging.StreamHandler()
    ]
)

# 获取日志记录器
logger = logging.getLogger('test_kline')

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
try:
    from utils.date_utils import get_beijing_now, parse_date_string, validate_date_range
    from utils.kline_utils import fetch_and_save_kline
    from utils.auth_utils import load_auth_config, get_auth_info, get_headers
    from utils.symbol_utils import validate_date_range as validate_symbol_date_range
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

def test_date_parsing(date_str: str) -> None:
    """测试日期字符串解析"""
    logger.info(f"测试日期解析: '{date_str}'")
    
    # 调用parse_date_string函数并记录结果
    result = parse_date_string(date_str)
    if result:
        logger.info(f"解析成功: {result.strftime('%Y-%m-%d')}")
    else:
        logger.warning(f"解析失败: {date_str} 不是有效日期")
    
    logger.info("-" * 40)

def test_date_range_validation(start_date: str, end_date: str) -> None:
    """测试日期范围验证"""
    logger.info(f"测试日期范围验证: 从 '{start_date}' 到 '{end_date}'")
    
    # 调用validate_date_range函数并记录结果
    validated_start, validated_end = validate_date_range(start_date, end_date)
    
    logger.info(f"验证后的开始日期: {validated_start}")
    logger.info(f"验证后的结束日期: {validated_end}")
    
    # 检查日期是否被修改
    if validated_start != start_date:
        logger.warning(f"开始日期被修改: {start_date} -> {validated_start}")
    if validated_end != end_date:
        logger.warning(f"结束日期被修改: {end_date} -> {validated_end}")
    
    logger.info("-" * 40)

def test_symbol_date_validation(symbol: str, exchange: str, start_date: str, end_date: str) -> None:
    """测试股票日期范围验证"""
    full_name = f"{symbol}.{exchange}"
    logger.info(f"测试股票日期范围验证: {full_name} 从 '{start_date}' 到 '{end_date}'")
    
    # 调用validate_symbol_date_range函数并记录结果
    validated_start, validated_end, result_info = validate_symbol_date_range(
        full_name=full_name,
        from_date=start_date,
        to_date=end_date
    )
    
    logger.info(f"验证后的开始日期: {validated_start}")
    logger.info(f"验证后的结束日期: {validated_end}")
    
    # 记录详细的验证结果
    log_dict("验证结果信息", result_info)
    
    logger.info("-" * 40)

def test_fetch_kline(
    symbol: str, 
    exchange: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    resolution: str = "1D",
    save_to_csv: bool = True
) -> None:
    """测试获取K线数据"""
    full_name = f"{symbol}.{exchange}"
    logger.info(f"测试获取K线数据: {full_name} 从 '{start_date}' 到 '{end_date}', 周期: {resolution}")
    
    # 记录测试时的北京时间
    beijing_now = get_beijing_now()
    logger.info(f"当前北京时间: {beijing_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 调用fetch_and_save_kline函数并记录结果
        success, result, file_path = fetch_and_save_kline(
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            from_date=start_date,
            to_date=end_date,
            output_dir="data/klines",
            file_format="csv"
        )
        
        logger.info(f"获取K线数据结果: {'成功' if success else '失败'}")
        
        if success and isinstance(result, pd.DataFrame):
            # 记录获取的数据信息
            df = result
            logger.info(f"获取到 {len(df)} 条K线数据")
            
            if not df.empty:
                # 获取日期范围
                min_date = df['time'].min().strftime('%Y-%m-%d')
                max_date = df['time'].max().strftime('%Y-%m-%d')
                logger.info(f"数据日期范围: {min_date} 至 {max_date}")
                
                # 记录最后几行数据
                logger.info("最后5行数据:")
                for _, row in df.tail(5).iterrows():
                    date_str = row['time'].strftime('%Y-%m-%d')
                    logger.info(f"{date_str}: 开盘价={row['open']}, 收盘价={row['close']}, 最高价={row['high']}, 最低价={row['low']}")
                
                # 检查是否存在日期断点
                if len(df) > 1:
                    dates = pd.to_datetime(df['time'])
                    date_diffs = (dates.shift(-1) - dates).dropna()
                    
                    # 检查超过1天的间隔
                    gaps = date_diffs[date_diffs > pd.Timedelta(days=1)]
                    if not gaps.empty:
                        logger.warning(f"检测到 {len(gaps)} 个日期断点:")
                        for i, gap in enumerate(gaps):
                            idx = gaps.index[i]
                            from_date = df.loc[idx, 'time'].strftime('%Y-%m-%d')
                            to_date = df.loc[idx+1, 'time'].strftime('%Y-%m-%d')
                            gap_days = gap.days
                            logger.warning(f"断点 {i+1}: {from_date} -> {to_date} (间隔 {gap_days} 天)")
                
                # 保存结果到CSV（如果需要）
                if save_to_csv:
                    # 创建测试结果目录
                    os.makedirs("test_results", exist_ok=True)
                    
                    # 生成文件名
                    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                    result_file = f"test_results/{symbol}_{exchange}_{start_date}_{end_date}_{timestamp}.csv"
                    
                    # 保存DataFrame
                    df.to_csv(result_file, index=False)
                    logger.info(f"测试结果已保存到: {result_file}")
            else:
                logger.warning("获取的数据为空")
        else:
            # 如果失败，记录错误信息
            logger.error(f"获取K线数据失败: {result}")
        
        logger.info("-" * 40)
        
        return success, result, file_path
    
    except Exception as e:
        logger.error(f"测试过程中发生异常: {e}")
        logger.error(traceback.format_exc())
        logger.info("-" * 40)
        return False, str(e), None

def run_tests() -> None:
    """运行一系列测试"""
    logger.info("======== 开始K线数据获取测试 ========")
    
    # 测试日期解析
    logger.info("\n## 测试日期字符串解析 ##")
    test_date_parsing("2024-05-28")        # 正常日期
    test_date_parsing("2024.05.28")        # 点分隔符
    test_date_parsing("2024/05/28")        # 斜杠分隔符
    test_date_parsing("2025-02-29")        # 非闰年2月29日
    test_date_parsing("2024-02-29")        # 闰年2月29日
    test_date_parsing("2025.02.29")        # 非闰年2月29日，点分隔符
    test_date_parsing("2025-13-01")        # 无效月份
    test_date_parsing("2025-05-32")        # 无效日期
    test_date_parsing("abc")               # 非日期字符串
    
    # 测试日期范围验证
    logger.info("\n## 测试日期范围验证 ##")
    # 正常日期范围
    test_date_range_validation("2024-01-01", "2024-05-28")
    # 日期顺序错误
    test_date_range_validation("2024-05-28", "2024-01-01")
    # 无效日期
    test_date_range_validation("2025-02-29", "2025-05-29")
    # 使用不同分隔符
    test_date_range_validation("2024.01.01", "2024-05-28")
    # 未来日期
    current_date = get_beijing_now()
    future_date = (current_date + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    test_date_range_validation("2024-01-01", future_date)
    
    # 测试股票日期范围验证
    logger.info("\n## 测试股票日期范围验证 ##")
    test_symbol_date_validation("600000", "XSHG", "2024-01-01", "2024-05-28")
    test_symbol_date_validation("600000", "XSHG", "2025-02-29", "2025-05-29")
    test_symbol_date_validation("600000", "XSHG", "2010-01-01", "2024-05-28")
    test_symbol_date_validation("600000", "XSHG", "2024-01-01", future_date)
    
    # 测试获取K线数据
    logger.info("\n## 测试获取K线数据 ##")
    
    # 测试1: 正常日期范围
    test_fetch_kline("600000", "XSHG", "2024-01-01", "2024-05-28")
    
    # 测试2: 无效日期 - 非闰年2月29日
    test_fetch_kline("600000", "XSHG", "2025-02-01", "2025-05-29")
    
    # 测试3: 未来日期范围
    test_fetch_kline("600000", "XSHG", "2024-05-01", future_date)
    
    # 测试4: 使用不同分隔符
    test_fetch_kline("600000", "XSHG", "2024.01.01", "2024.05.28")
    
    # 测试5: 一年数据测试
    one_year_ago = (current_date - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    test_fetch_kline("600000", "XSHG", one_year_ago, current_date.strftime("%Y-%m-%d"))
    
    # 测试问题的日期范围
    logger.info("\n## 测试特定问题的日期范围 ##")
    test_fetch_kline("600000", "XSHG", "2024-05-28", "2025-05-28")
    
    logger.info("======== K线数据获取测试结束 ========")

if __name__ == "__main__":
    try:
        # 加载认证配置
        if not load_auth_config():
            logger.error("无法加载认证配置，请检查认证文件")
            sys.exit(1)
            
        # 运行测试
        run_tests()
    except Exception as e:
        logger.error(f"测试过程中发生未捕获的异常: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1) 