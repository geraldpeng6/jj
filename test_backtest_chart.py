#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试回测图表生成
"""

import os
import json
import pandas as pd
from utils.chart_generator import generate_backtest_html, open_in_browser

# 测试数据
def create_test_data():
    """创建测试数据"""
    # 创建一个简单的回测数据
    backtest_data = []

    # 初始资金
    initial_cash = 100000

    # 股票代码
    symbol = "600000"
    exchange = "XSHG"

    # 模拟20天的数据，创建更多的买卖点和价格变化
    cash_value = initial_cash
    size = 0
    buy_price = 0

    for i in range(20):
        day = i + 1
        timestamp = 1609430400000 + day * 86400000  # 从2021-01-01开始

        # 股价波动，创造一些上涨和下跌
        if i < 5:
            price = 10.0 + i * 0.2  # 前5天上涨
        elif i < 10:
            price = 11.0 - (i - 5) * 0.15  # 接下来5天下跌
        elif i < 15:
            price = 10.25 + (i - 10) * 0.3  # 接下来5天强势上涨
        else:
            price = 11.75 - (i - 15) * 0.1  # 最后5天小幅下跌

        # 交易策略
        # 第3天买入1000股
        if day == 3:
            buy_size = 1000
            buy_price = price
            buy_amount = buy_size * buy_price
            size += buy_size
            cash_value -= buy_amount

        # 第7天再买入500股
        elif day == 7:
            buy_size = 500
            buy_price = price
            buy_amount = buy_size * buy_price
            size += buy_size
            cash_value -= buy_amount

        # 第11天卖出800股
        elif day == 11:
            sell_size = 800
            sell_price = price
            sell_amount = sell_size * sell_price
            size -= sell_size
            cash_value += sell_amount

        # 第15天买入1000股
        elif day == 15:
            buy_size = 1000
            buy_price = price
            buy_amount = buy_size * buy_price
            size += buy_size
            cash_value -= buy_amount

        # 第18天全部卖出
        elif day == 18:
            sell_size = size
            sell_price = price
            sell_amount = sell_size * sell_price
            size = 0
            cash_value += sell_amount

        # 如果有持仓，计算持仓价值
        position_value = size * price

        # 总资产价值
        total_value = cash_value + position_value

        # 创建持仓数据
        positions = [
            {
                "category": 0,  # 现金
                "value": cash_value
            }
        ]

        # 如果有股票持仓，添加股票持仓信息
        if size > 0:
            positions.append({
                "category": 1,  # 股票
                "symbol": symbol,
                "exchange": exchange,
                "size": size,
                "price": price,
                "value": position_value
            })

        # 添加到回测数据
        item = {
            "tm": timestamp,
            "value": total_value,
            "positions": positions,
            "name": "单均线策略",  # 使用name字段存储策略名称
            "strategy_name": "测试策略"  # 保留strategy_name字段作为备用
        }

        backtest_data.append(item)

    return backtest_data

def main():
    """主函数"""
    # 创建测试数据
    backtest_data = create_test_data()

    # 保存测试数据到文件
    os.makedirs("data/test", exist_ok=True)
    with open("data/test/test_backtest_data.json", "w", encoding="utf-8") as f:
        json.dump(backtest_data, f, indent=2)

    # 生成回测图表
    html_path = generate_backtest_html(
        backtest_data=backtest_data,
        strategy_name="测试策略",
        strategy_id="test001",
        symbol="600000",
        exchange="XSHG",
        output_dir="data/test"
    )

    # 在浏览器中打开
    if html_path:
        print(f"回测图表已生成: {html_path}")
        open_in_browser(html_path)
    else:
        print("生成回测图表失败")

if __name__ == "__main__":
    main()
