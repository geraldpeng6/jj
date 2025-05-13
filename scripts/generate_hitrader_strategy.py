#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成HiTrader策略示例脚本

演示如何使用HiTrader策略生成功能
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入HiTrader工具
from src.tools.hitrader_tools import generate_hitrader_strategy, backtest_hitrader_strategy

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='生成HiTrader策略代码')
    parser.add_argument('--strategy_type', type=str, default='dual_ma',
                        help='策略类型 (trend_following, mean_reversion, breakout, momentum, dual_ma, macd, rsi, kdj, boll)')
    parser.add_argument('--timeframe', type=str, default='daily',
                        help='交易时间框架 (daily, weekly, 60min, 30min, 15min)')
    parser.add_argument('--risk_level', type=str, default='medium',
                        help='风险水平 (low, medium, high)')
    parser.add_argument('--stock_selection', type=str, default='single',
                        help='选股方式 (single, multiple, index, sector)')
    parser.add_argument('--specific_stocks', type=str, default='600000.XSHG',
                        help='指定股票代码，多个股票用&分隔')
    parser.add_argument('--indicators_required', type=str, default='all',
                        help='需要的技术指标 (ma, macd, rsi, kdj, boll, all)')
    parser.add_argument('--position_sizing', type=str, default='fixed',
                        help='仓位管理方式 (fixed, dynamic, risk_based)')
    parser.add_argument('--stop_loss', type=str, default='fixed',
                        help='止损方式 (fixed, trailing, atr, none)')
    parser.add_argument('--backtest', action='store_true',
                        help='是否进行回测')
    parser.add_argument('--start_date', type=str, default='2022-01-01',
                        help='回测开始日期，格式为 YYYY-MM-DD')
    parser.add_argument('--end_date', type=str, default='2023-01-01',
                        help='回测结束日期，格式为 YYYY-MM-DD')
    
    args = parser.parse_args()
    
    # 生成HiTrader策略代码
    print(f"正在生成 {args.strategy_type} 类型的HiTrader策略代码...")
    result = await generate_hitrader_strategy(
        strategy_type=args.strategy_type,
        timeframe=args.timeframe,
        risk_level=args.risk_level,
        stock_selection=args.stock_selection,
        specific_stocks=args.specific_stocks,
        indicators_required=args.indicators_required,
        position_sizing=args.position_sizing,
        stop_loss=args.stop_loss
    )
    
    print(result)
    
    # 如果需要回测，则进行回测
    if args.backtest:
        # 从结果中提取策略代码
        import re
        strategy_code = re.search(r'```python\n(.*?)\n```', result, re.DOTALL)
        if strategy_code:
            strategy_code = strategy_code.group(1)
            print("\n正在进行回测...")
            backtest_result = await backtest_hitrader_strategy(
                strategy_code=strategy_code,
                start_date=args.start_date,
                end_date=args.end_date,
                specific_stocks=args.specific_stocks
            )
            print(backtest_result)
        else:
            print("无法从结果中提取策略代码，回测失败")

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
