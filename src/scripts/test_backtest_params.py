#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测参数测试脚本

演示如何使用不同的回测参数进行策略回测
"""

import os
import sys
import logging
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径，以便正确导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.backtest_utils import run_backtest
from utils.logging_utils import setup_logging
from utils.date_utils import get_beijing_now

# 设置日志
setup_logging(logger_name='quant_mcp.test_backtest_params', log_level=logging.INFO)
logger = logging.getLogger('quant_mcp.test_backtest_params')

def create_test_strategy():
    """
    创建用于测试的策略模板
    """
    return {
        "name": "回测参数测试策略",
        "strategy_name": "回测参数测试策略",
        "indicator": '''def indicators(context):
    """指标"""
    # 计算15日均价，赋值给变量context.sma
    context.sma = SMA(period=15)
''',
        "choose_stock": '''def choose_stock(context):
    """选股"""
    context.symbol_list = ["600000.XSHG"]
''',
        "timing": '''def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当股票收盘价低于并且交叉穿过15日均价时，出现买入信号
        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.1)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当股票收盘价小于15日均价时，出现卖出信号
        if context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
            # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)
''',
        "control_risk": '''def control_risk(context):
    """风控"""
    pass
'''
    }

def test_backtest_with_custom_params():
    """
    测试使用自定义参数运行回测
    """
    # 测试用的策略ID，这只是一个占位符
    strategy_id = "TEST_STRATEGY"
    
    # 创建测试策略
    strategy_data = create_test_strategy()
    
    # 生成时间戳，用于区分不同的回测结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 获取当前日期和一年前的日期
    today = get_beijing_now()
    one_year_ago = today - timedelta(days=365)
    
    # 测试用例: 不同的初始资金和订单数量
    test_cases = [
        {
            "name": "默认参数",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "post",
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "小资金测试",
            "params": {
                "capital": 50000,
                "order": 100,
                "resolution": "1D",
                "fq": "post",
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "高频数据测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1m",  # 1分钟线
                "fq": "post",
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "前复权测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "pre",  # 前复权
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "不复权测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "none",  # 不复权
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "高手续费测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "post",
                "commission": 0.001,  # 0.1%手续费
                "margin": 0.05,
                "riskfreerate": 0.01
            }
        },
        {
            "name": "高保证金测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "post",
                "commission": 0.0003,
                "margin": 0.2,  # 20%保证金
                "riskfreerate": 0.01
            }
        },
        {
            "name": "高无风险利率测试",
            "params": {
                "capital": 200000,
                "order": 500,
                "resolution": "1D",
                "fq": "post",
                "commission": 0.0003,
                "margin": 0.05,
                "riskfreerate": 0.05  # 5%无风险利率
            }
        }
    ]
    
    # 记录测试结果
    results = []
    
    # 运行每个测试用例
    for i, case in enumerate(test_cases):
        logger.info(f"运行测试用例 {i+1}/{len(test_cases)}: {case['name']}")
        
        # 更新时间戳以区分不同的测试用例
        case_timestamp = f"{timestamp}_{i+1}"
        
        # 运行回测
        try:
            result = run_backtest(
                strategy_id=strategy_id,
                strategy_data=strategy_data,  # 直接传入策略数据
                listen_time=30,  # 监听30秒
                start_date=one_year_ago.strftime('%Y-%m-%d'),
                end_date=today.strftime('%Y-%m-%d'),
                capital=case['params']['capital'],
                order=case['params']['order'],
                resolution=case['params']['resolution'],
                fq=case['params']['fq'],
                commission=case['params']['commission'],
                margin=case['params']['margin'],
                riskfreerate=case['params']['riskfreerate'],
                timestamp=case_timestamp
            )
            
            # 记录结果
            results.append({
                "case_name": case['name'],
                "success": result.get('success', False),
                "error": result.get('error'),
                "chart_path": result.get('chart_path'),
                "position_count": result.get('position_count', 0),
                "parameters": result.get('parameters', {})
            })
            
            if result.get('success'):
                logger.info(f"测试用例 {case['name']} 成功，共收到 {result.get('position_count', 0)} 条数据")
                logger.info(f"图表路径: {result.get('chart_path')}")
            else:
                logger.error(f"测试用例 {case['name']} 失败: {result.get('error')}")
                
        except Exception as e:
            logger.exception(f"测试用例 {case['name']} 发生异常: {e}")
            results.append({
                "case_name": case['name'],
                "success": False,
                "error": str(e),
                "parameters": case['params']
            })
    
    # 保存测试结果到文件
    try:
        result_file = f"data/test/backtest_params_test_{timestamp}.json"
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"测试结果已保存到 {result_file}")
    except Exception as e:
        logger.error(f"保存测试结果失败: {e}")

def test_with_specific_params():
    """
    使用特定参数测试单个回测
    """
    # 测试用的策略ID，这只是一个占位符
    strategy_id = "TEST_STRATEGY"
    
    # 创建测试策略
    strategy_data = create_test_strategy()
    print(f"创建测试策略: {strategy_data.get('name')}")
    logger.info(f"创建测试策略: {strategy_data.get('name')}")
    
    # 获取当前日期和一年前的日期
    today = get_beijing_now()
    one_year_ago = today - timedelta(days=365)
    
    # 定义测试参数
    test_capital = 100000
    test_order = 200
    test_resolution = "15m"
    test_fq = "pre"
    test_commission = 0.0005
    test_margin = 0.1
    test_riskfreerate = 0.03
    
    print(f"开始运行回测，使用以下参数:")
    print(f"- 初始资金: {test_capital}")
    print(f"- 订单数量: {test_order}")
    print(f"- 数据频次: {test_resolution}")
    print(f"- 复权方式: {test_fq}")
    print(f"- 手续费率: {test_commission}")
    print(f"- 保证金比率: {test_margin}")
    print(f"- 无风险利率: {test_riskfreerate}")
    
    logger.info(f"开始运行回测，使用以下参数:")
    logger.info(f"- 初始资金: {test_capital}")
    logger.info(f"- 订单数量: {test_order}")
    logger.info(f"- 数据频次: {test_resolution}")
    logger.info(f"- 复权方式: {test_fq}")
    logger.info(f"- 手续费率: {test_commission}")
    logger.info(f"- 保证金比率: {test_margin}")
    logger.info(f"- 无风险利率: {test_riskfreerate}")
    
    # 指定参数运行回测
    try:
        result = run_backtest(
            strategy_id=strategy_id,
            strategy_data=strategy_data,  # 直接传入策略数据
            listen_time=30,  # 监听30秒
            start_date=one_year_ago.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d'),
            capital=test_capital,
            order=test_order,
            resolution=test_resolution,
            fq=test_fq,
            commission=test_commission,
            margin=test_margin,
            riskfreerate=test_riskfreerate
        )
        
        print(f"回测完成，结果: {'成功' if result.get('success') else '失败'}")
        logger.info(f"回测完成，结果: {'成功' if result.get('success') else '失败'}")
        
        if result.get('success'):
            print(f"回测成功，共收到 {result.get('position_count', 0)} 条数据")
            print(f"图表路径: {result.get('chart_path')}")
            print(f"使用参数:")
            for key, value in result.get('parameters', {}).items():
                print(f"- {key}: {value}")
                
            logger.info(f"回测成功，共收到 {result.get('position_count', 0)} 条数据")
            logger.info(f"图表路径: {result.get('chart_path')}")
            logger.info(f"使用参数:")
            for key, value in result.get('parameters', {}).items():
                logger.info(f"- {key}: {value}")
        else:
            error_msg = f"回测失败: {result.get('error')}"
            print(error_msg)
            logger.error(error_msg)
            
    except Exception as e:
        error_msg = f"回测发生异常: {e}"
        print(error_msg)
        logger.exception(error_msg)

def test_different_resolutions():
    """
    测试不同的分辨率设置
    """
    # 测试用的策略ID，这只是一个占位符
    strategy_id = "TEST_STRATEGY"
    
    # 创建测试策略
    strategy_data = create_test_strategy()
    print(f"创建测试策略: {strategy_data.get('name')}")
    
    # 获取当前日期和一年前的日期
    today = get_beijing_now()
    one_year_ago = today - timedelta(days=365)
    
    # 要测试的分辨率
    resolutions = ["1s", "5s", "1m", "5m", "15m", "30m", "1h", "1d", "1D"]
    
    for resolution in resolutions:
        print(f"\n测试分辨率: {resolution}")
        
        try:
            result = run_backtest(
                strategy_id=strategy_id,
                strategy_data=strategy_data,
                listen_time=10,  # 缩短监听时间以加快测试
                start_date=one_year_ago.strftime('%Y-%m-%d'),
                end_date=today.strftime('%Y-%m-%d'),
                resolution=resolution
            )
            
            print(f"回测完成，结果: {'成功' if result.get('success') else '失败'}")
            
            if result.get('success'):
                print(f"分辨率 {resolution} 转换为 {result['parameters']['resolution']}")
            else:
                print(f"回测失败: {result.get('error')}")
                
        except Exception as e:
            print(f"回测发生异常: {e}")

if __name__ == "__main__":
    # 运行不同分辨率测试
    test_different_resolutions()
    
    # 运行特定参数测试
    # test_with_specific_params() 