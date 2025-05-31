#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测命令行工具

提供命令行接口运行回测并配置各种参数
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta

# 添加项目根目录到路径，以便正确导入模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.backtest_utils import run_backtest, format_choose_stock
from utils.logging_utils import setup_logging
from utils.date_utils import get_beijing_now

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行回测并配置参数')
    
    # 策略参数
    parser.add_argument('--strategy_id', type=str, help='策略ID（必填）')
    parser.add_argument('--symbol', type=str, help='股票代码，如 600000.XSHG，多个用&分隔')
    
    # 时间参数
    parser.add_argument('--start_date', type=str, help='回测开始日期，格式 YYYY-MM-DD')
    parser.add_argument('--end_date', type=str, help='回测结束日期，格式 YYYY-MM-DD')
    
    # 资金参数
    parser.add_argument('--capital', type=int, default=200000, help='初始资金，默认200000元')
    parser.add_argument('--order', type=int, default=500, help='每笔交易数量，默认500股')
    
    # 数据参数
    parser.add_argument('--resolution', type=str, default='1D', 
                      help='数据频次，如1s, 5s, 1m, 5m, 15m, 30m, 1h, 1d等，默认1D')
    parser.add_argument('--fq', type=str, default='post', choices=['post', 'pre', 'none'],
                      help='复权方式：post(后复权), pre(前复权), none(不复权)，默认post')
    
    # 交易参数
    parser.add_argument('--commission', type=float, default=0.0003, 
                      help='手续费率，默认0.0003(0.03%%)')
    parser.add_argument('--margin', type=float, default=0.05,
                      help='保证金比率，默认0.05(5%%)')
    parser.add_argument('--riskfreerate', type=float, default=0.01,
                      help='无风险利率，默认0.01(1%%)')
    parser.add_argument('--pyramiding', type=int, default=1,
                      help='金字塔加仓次数，默认1次')
    
    # 策略代码文件
    parser.add_argument('--indicator_file', type=str, help='指标代码文件路径')
    parser.add_argument('--timing_file', type=str, help='择时代码文件路径')
    parser.add_argument('--control_risk_file', type=str, help='风控代码文件路径')
    parser.add_argument('--choose_stock_file', type=str, help='选股代码文件路径')
    
    # 其他参数
    parser.add_argument('--listen_time', type=int, default=60, 
                      help='监听回测结果时间（秒），默认60秒')
    parser.add_argument('--open_chart', action='store_true',
                      help='是否自动打开回测图表')
    
    # 解析参数
    args = parser.parse_args()
    
    # 验证必填参数
    if not args.strategy_id and not args.symbol:
        parser.error("必须提供 --strategy_id 或 --symbol 参数")
    
    return args

def read_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        return None

def create_simple_strategy(symbol=None):
    """
    创建简单策略模板
    
    Args:
        symbol: 股票代码，如果提供则使用此代码，否则使用默认代码
        
    Returns:
        Dict[str, Any]: 策略数据字典
    """
    strategy_name = f"回测策略 - {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 选股代码 - 如果提供了股票代码则使用，否则使用默认的600000.XSHG
    choose_stock_code = f'''def choose_stock(context):
    """选股"""
    context.symbol_list = ["{symbol or '600000.XSHG'}"]
'''

    # 返回策略数据
    return {
        "name": strategy_name,
        "strategy_name": strategy_name,
        "indicator": '''def indicators(context):
    """指标"""
    # 计算15日均价，赋值给变量context.sma
    context.sma = SMA(period=15)
''',
        "choose_stock": choose_stock_code,
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

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志
    setup_logging(logger_name='quant_mcp.backtest_cli', log_level=logging.INFO)
    logger = logging.getLogger('quant_mcp.backtest_cli')
    
    # 获取当前时间作为时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 获取当前日期和一年前的日期（如果未指定）
    today = get_beijing_now()
    one_year_ago = today - timedelta(days=365)
    start_date = args.start_date or one_year_ago.strftime('%Y-%m-%d')
    end_date = args.end_date or today.strftime('%Y-%m-%d')
    
    # 读取策略代码文件（如果指定）
    indicator = None
    if args.indicator_file:
        indicator = read_file_content(args.indicator_file)
    
    timing = None
    if args.timing_file:
        timing = read_file_content(args.timing_file)
    
    control_risk = None
    if args.control_risk_file:
        control_risk = read_file_content(args.control_risk_file)
    
    choose_stock = None
    if args.choose_stock_file:
        choose_stock = read_file_content(args.choose_stock_file)
    elif args.symbol:
        # 如果提供了股票代码但没有选股文件，使用股票代码生成选股函数
        choose_stock = args.symbol
    
    # 如果没有提供策略ID，但提供了股票代码，创建一个简单的策略
    strategy_data = None
    strategy_id = args.strategy_id
    if not strategy_id and args.symbol:
        strategy_data = create_simple_strategy(args.symbol)
        strategy_id = f"CLI_TEST_{timestamp}"  # 生成一个临时策略ID
    
    # 打印参数
    print("回测参数:")
    print(f"- 策略ID: {strategy_id}")
    print(f"- 回测时间范围: {start_date} 至 {end_date}")
    print(f"- 初始资金: {args.capital}")
    print(f"- 每笔交易数量: {args.order}")
    print(f"- 数据频次: {args.resolution}")
    print(f"- 复权方式: {args.fq}")
    print(f"- 手续费率: {args.commission}")
    print(f"- 保证金比率: {args.margin}")
    print(f"- 无风险利率: {args.riskfreerate}")
    print(f"- 金字塔加仓次数: {args.pyramiding}")
    if args.symbol:
        print(f"- 股票代码: {args.symbol}")
    if indicator:
        print("- 提供了自定义指标代码")
    if timing:
        print("- 提供了自定义择时代码")
    if control_risk:
        print("- 提供了自定义风控代码")
    if choose_stock and not args.symbol:
        print("- 提供了自定义选股代码")
    if strategy_data:
        print("- 使用自动生成的策略模板")
    
    try:
        # 运行回测
        result = run_backtest(
            strategy_id=strategy_id,
            listen_time=args.listen_time,
            start_date=start_date,
            end_date=end_date,
            indicator=indicator,
            control_risk=control_risk,
            timing=timing,
            choose_stock=choose_stock,
            timestamp=timestamp,
            capital=args.capital,
            order=args.order,
            resolution=args.resolution,
            fq=args.fq,
            commission=args.commission,
            margin=args.margin,
            riskfreerate=args.riskfreerate,
            pyramiding=args.pyramiding,
            strategy_data=strategy_data  # 传入策略数据（如果有）
        )
        
        # 输出结果
        if result.get('success'):
            print(f"\n回测成功，共收到 {result.get('position_count', 0)} 条数据")
            print(f"图表路径: {result.get('chart_path')}")
            
            # 如果指定了自动打开图表
            if args.open_chart and result.get('chart_path'):
                from utils.chart_generator import open_in_browser
                open_in_browser(result.get('chart_path'))
                print(f"已在浏览器中打开图表")
            
            # 保存回测结果为JSON
            result_file = f"data/backtest/results/backtest_result_{timestamp}.json"
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"回测结果已保存到: {result_file}")
            
            return 0  # 成功退出
        else:
            print(f"\n回测失败: {result.get('error')}")
            return 1  # 失败退出
            
    except Exception as e:
        print(f"\n回测过程中发生异常: {e}")
        logger.exception("回测异常")
        return 1  # 失败退出

if __name__ == "__main__":
    sys.exit(main()) 