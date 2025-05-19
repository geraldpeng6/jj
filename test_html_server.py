#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML服务器测试脚本

测试HTML服务器功能，包括生成HTML文件和获取URL
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.html_server import get_html_url, generate_test_html, is_nginx_available
from utils.chart_generator import generate_html, generate_backtest_html, open_in_browser

def create_test_kline_data():
    """创建测试K线数据"""
    # 创建日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建随机价格数据
    np.random.seed(42)
    n = len(dates)
    
    # 起始价格
    start_price = 100.0
    
    # 生成随机价格变动
    price_changes = np.random.normal(0, 1, n)
    price_changes[0] = 0  # 第一天不变
    
    # 计算收盘价
    closes = start_price + np.cumsum(price_changes)
    
    # 生成开盘价、最高价、最低价
    opens = closes - np.random.normal(0, 0.5, n)
    highs = np.maximum(opens, closes) + np.random.uniform(0, 1, n)
    lows = np.minimum(opens, closes) - np.random.uniform(0, 1, n)
    
    # 生成成交量
    volumes = np.random.uniform(1000, 10000, n)
    
    # 创建DataFrame
    df = pd.DataFrame({
        'time': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    })
    
    return df

def create_test_backtest_data():
    """创建测试回测数据"""
    # 创建日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 创建回测数据
    backtest_data = []
    
    # 初始资金
    initial_cash = 100000.0
    
    # 股票代码和交易所
    symbol = "600000"
    exchange = "XSHG"
    
    # 生成随机价格
    np.random.seed(42)
    n = len(dates)
    prices = 100 + np.cumsum(np.random.normal(0, 1, n))
    
    # 持仓数量
    position_size = 0
    
    # 现金
    cash = initial_cash
    
    # 生成回测数据
    for i, date in enumerate(dates):
        # 时间戳
        timestamp = int(date.timestamp() * 1000)
        
        # 价格
        price = prices[i]
        
        # 随机交易
        if i > 0 and i % 5 == 0:  # 每5天交易一次
            if position_size == 0:  # 买入
                # 买入数量
                buy_size = int(cash * 0.3 / price)  # 使用30%的现金买入
                if buy_size > 0:
                    position_size = buy_size
                    cash -= buy_size * price
            else:  # 卖出
                # 卖出数量
                sell_size = position_size
                cash += sell_size * price
                position_size = 0
        
        # 计算总资产价值
        position_value = position_size * price
        total_value = cash + position_value
        
        # 创建回测数据项
        data_item = {
            "tm": timestamp,
            "value": total_value,
            "positions": [
                {
                    "category": 0,
                    "value": cash
                }
            ]
        }
        
        # 添加股票持仓
        if position_size > 0:
            data_item["positions"].append({
                "category": 1,
                "symbol": symbol,
                "exchange": exchange,
                "size": position_size,
                "price": price,
                "value": position_value
            })
        
        # 添加到回测数据列表
        backtest_data.append(data_item)
    
    return backtest_data

def test_html_server():
    """测试HTML服务器功能"""
    print("开始测试HTML服务器功能...")
    
    # 检查Nginx是否可用
    nginx_available = is_nginx_available()
    print(f"Nginx是否可用: {nginx_available}")
    
    # 生成测试HTML文件
    test_url = generate_test_html()
    print(f"测试HTML文件URL: {test_url}")
    
    # 创建测试K线数据
    kline_df = create_test_kline_data()
    print(f"创建测试K线数据成功，共 {len(kline_df)} 条记录")
    
    # 生成K线图表
    kline_url = generate_html(
        df=kline_df,
        symbol="600000",
        exchange="XSHG",
        resolution="1D",
        fq="post"
    )
    print(f"K线图表URL: {kline_url}")
    
    # 在浏览器中打开K线图表
    open_in_browser(kline_url)
    
    # 创建测试回测数据
    backtest_data = create_test_backtest_data()
    print(f"创建测试回测数据成功，共 {len(backtest_data)} 条记录")
    
    # 生成回测图表
    backtest_url = generate_backtest_html(
        backtest_data=backtest_data,
        strategy_name="测试策略",
        strategy_id="test_strategy",
        kline_df=kline_df,
        symbol="600000",
        exchange="XSHG"
    )
    print(f"回测图表URL: {backtest_url}")
    
    # 在浏览器中打开回测图表
    open_in_browser(backtest_url)
    
    print("测试完成!")

if __name__ == "__main__":
    test_html_server()
