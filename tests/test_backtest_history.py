#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
回测历史记录工具测试脚本
"""

import sys
import os
from utils.backtest_history_utils import get_strategy_backtest_history, format_backtest_history

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_backtest_history.py <策略ID>")
        sys.exit(1)
    
    strategy_id = sys.argv[1]
    print(f"获取策略 {strategy_id} 的回测历史记录...")
    
    # 获取策略回测历史记录
    history_list = get_strategy_backtest_history(strategy_id)
    
    if history_list is None:
        print("获取回测历史记录失败")
        sys.exit(1)
    
    # 格式化并显示回测历史记录
    formatted_history = format_backtest_history(history_list)
    print(formatted_history)

if __name__ == "__main__":
    main() 