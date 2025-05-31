#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试多股基准标的验证
"""

from utils.backtest_utils import validate_multiple_stocks_benchmark

def test_no_benchmark():
    """测试没有基准标的的情况"""
    code = '''
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600000.XSHG", "000001.XSHE"]
'''
    try:
        validate_multiple_stocks_benchmark(code)
        print('Test 1 failed: 没有基准标的但未抛出错误')
        return False
    except ValueError as e:
        print(f'Test 1 passed: {str(e)}')
        return True

def test_with_benchmark():
    """测试有基准标的的情况"""
    code = '''
def choose_stock(context):
    """标的"""
    context.benchmark = "000300.XSHG"
    context.symbol_list = ["600000.XSHG", "000001.XSHE"]
'''
    try:
        validate_multiple_stocks_benchmark(code)
        print('Test 2 passed: 有基准标的，未抛出错误')
        return True
    except ValueError as e:
        print(f'Test 2 failed: {str(e)}')
        return False

if __name__ == "__main__":
    print("测试多股基准标的验证...")
    
    test_no_benchmark()
    test_with_benchmark()
    
    print("测试完成") 