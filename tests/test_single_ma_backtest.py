#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
单均线策略回测测试脚本

测试单均线策略在过去一年的回测效果
策略ID: RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ
"""

import logging
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.backtest_utils import run_backtest
from utils.date_utils import get_beijing_now, validate_date_range
from utils.chart_generator import open_in_browser, load_backtest_data
from utils.chart_utils import check_existing_backtest
from utils.strategy_utils import get_strategy_detail

# 配置日志，设置为INFO级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('test_single_ma_backtest')

def run_single_ma_backtest():
    """运行单均线策略回测"""
    # 策略ID
    strategy_id = "RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ"
    
    # 获取策略详情
    logger.info(f"获取策略 {strategy_id} 的详情...")
    strategy_detail = get_strategy_detail(strategy_id)
    
    if not strategy_detail:
        logger.error(f"无法获取策略 {strategy_id} 的详情")
        return
    
    strategy_name = strategy_detail.get('strategy_name', '单均线策略')
    logger.info(f"策略名称: {strategy_name}")
    
    # 计算回测日期范围 - 过去一年
    end_date = get_beijing_now().strftime('%Y-%m-%d')
    start_date = (get_beijing_now() - timedelta(days=365)).strftime('%Y-%m-%d')
    start_date, end_date = validate_date_range(start_date, end_date)
    
    logger.info(f"回测日期范围: {start_date} 至 {end_date} (一年)")
    
    # 检查是否已存在相同回测
    existing_result = check_existing_backtest(strategy_id, start_date, end_date, choose_stock=None)
    if existing_result:
        logger.info(f"找到已存在的回测结果: {existing_result}")
        # 可以选择使用已有结果或重新运行
        if input("已找到现有回测结果，是否重新运行? (y/n): ").lower() != 'y':
            chart_path = existing_result.split("回测结果图表链接: ")[-1].strip()
            logger.info(f"使用已有回测结果: {chart_path}")
            analyze_backtest_result(chart_path)
            return
    
    # 运行回测
    logger.info(f"开始运行回测...")
    result = run_backtest(
        strategy_id=strategy_id,
        listen_time=60,  # 等待时间增加到60秒，确保接收到足够的数据
        start_date=start_date,
        end_date=end_date
    )
    
    if not result.get('success'):
        logger.error(f"回测失败: {result.get('error')}")
        return
    
    # 输出回测结果
    position_count = result.get('position_count', 0)
    chart_path = result.get('chart_path')
    
    logger.info(f"回测完成，接收到 {position_count} 条position数据")
    if chart_path:
        logger.info(f"回测结果图表链接: {chart_path}")
        # 自动打开浏览器查看结果
        if open_in_browser(chart_path):
            logger.info("已在浏览器中打开回测结果")
        
        # 分析回测结果
        analyze_backtest_result(chart_path)
    else:
        logger.warning("未生成回测图表")

def analyze_backtest_result(chart_path):
    """分析回测结果数据"""
    # 从URL解析文件路径
    if chart_path.startswith("http"):
        # 从URL解析文件名
        file_name = chart_path.split("/")[-1]
        file_path = os.path.join("data", "charts", file_name)
    else:
        file_path = chart_path
    
    if not os.path.exists(file_path):
        logger.error(f"回测结果文件不存在: {file_path}")
        return
    
    # 读取HTML文件中的图表数据
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找chart_data部分
        import re
        match = re.search(r'var chartData = (.+?);', content, re.DOTALL)
        if not match:
            match = re.search(r'const chartData = (.+?);', content, re.DOTALL)
        
        if match:
            chart_data_str = match.group(1)
            # 将JavaScript对象转换为Python对象
            import json
            chart_data = json.loads(chart_data_str)
            
            # 分析图表数据
            logger.info("===== 回测数据分析 =====")
            
            # 检查日期范围
            if 'dates' in chart_data:
                dates = chart_data['dates']
                logger.info(f"日期范围: {dates[0]} 至 {dates[-1]}, 共 {len(dates)} 个交易日")
            
            # 分析资产价值
            if 'values' in chart_data:
                values = chart_data['values']
                if values and len(values) > 0:
                    initial_value = values[0]
                    final_value = values[-1]
                    total_return = (final_value / initial_value - 1) * 100
                    
                    logger.info(f"初始资产: {initial_value:.2f}")
                    logger.info(f"最终资产: {final_value:.2f}")
                    logger.info(f"总收益率: {total_return:.2f}%")
                    
                    # 计算最大回撤
                    max_drawdown = 0
                    peak = values[0]
                    
                    for value in values:
                        if value > peak:
                            peak = value
                        drawdown = (peak - value) / peak * 100
                        if drawdown > max_drawdown:
                            max_drawdown = drawdown
                    
                    logger.info(f"最大回撤: {max_drawdown:.2f}%")
            
            # 分析交易信号
            if 'buy_points' in chart_data:
                buy_signals = 0
                sell_signals = 0
                
                for symbol in chart_data['buy_points']:
                    buy_signals += len(chart_data['buy_points'][symbol]['dates'])
                
                for symbol in chart_data['sell_points']:
                    sell_signals += len(chart_data['sell_points'][symbol]['dates'])
                
                logger.info(f"买入信号数量: {buy_signals}")
                logger.info(f"卖出信号数量: {sell_signals}")
                
                # 计算信号胜率
                if buy_signals > 0:
                    win_trades = 0
                    for symbol in chart_data['buy_points']:
                        buy_dates = chart_data['buy_points'][symbol]['dates']
                        buy_prices = chart_data['buy_points'][symbol]['prices']
                        
                        for i, buy_date in enumerate(buy_dates):
                            # 查找买入后的卖出点
                            sell_date = None
                            sell_price = None
                            
                            for j, sell_date_candidate in enumerate(chart_data['sell_points'].get(symbol, {}).get('dates', [])):
                                if sell_date_candidate > buy_date:
                                    sell_date = sell_date_candidate
                                    sell_price = chart_data['sell_points'][symbol]['prices'][j]
                                    break
                            
                            if sell_date and sell_price and i < len(buy_prices):
                                buy_price = buy_prices[i]
                                profit = (sell_price / buy_price - 1) * 100
                                
                                if profit > 0:
                                    win_trades += 1
                    
                    win_rate = (win_trades / buy_signals) * 100
                    logger.info(f"交易胜率: {win_rate:.2f}%")
            
            # 可视化分析
            try:
                if 'dates' in chart_data and 'values' in chart_data:
                    # 转换数据为DataFrame
                    df = pd.DataFrame({
                        'date': chart_data['dates'],
                        'value': chart_data['values']
                    })
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    
                    # 计算每日收益率
                    df['daily_return'] = df['value'].pct_change() * 100
                    
                    # 计算波动率
                    volatility = df['daily_return'].std()
                    logger.info(f"日波动率: {volatility:.2f}%")
                    
                    # 计算夏普比率 (假设无风险利率为3%)
                    risk_free_rate = 3.0 / 252  # 每日无风险利率
                    sharpe_ratio = (df['daily_return'].mean() - risk_free_rate) / df['daily_return'].std() * (252 ** 0.5)
                    logger.info(f"夏普比率: {sharpe_ratio:.2f}")
                    
                    # 绘制收益率分布直方图
                    plt.figure(figsize=(12, 6))
                    plt.hist(df['daily_return'].dropna(), bins=50, alpha=0.75)
                    plt.title('日收益率分布')
                    plt.xlabel('日收益率 (%)')
                    plt.ylabel('频率')
                    plt.grid(True)
                    
                    # 保存图表
                    output_dir = "data/charts"
                    os.makedirs(output_dir, exist_ok=True)
                    fig_path = os.path.join(output_dir, f"return_dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    plt.savefig(fig_path)
                    logger.info(f"收益率分布图已保存: {fig_path}")
                    
                    # 显示图表
                    plt.show()
            except Exception as e:
                logger.error(f"绘制图表时出错: {e}")
        else:
            logger.error("无法从HTML文件中提取图表数据")
    except Exception as e:
        logger.error(f"分析回测结果时出错: {e}")

if __name__ == "__main__":
    run_single_ma_backtest() 