#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试运行脚本

运行所有测试用例
"""

import unittest
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def run_tests():
    """运行所有测试"""
    # 发现并加载所有测试
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    test_suite = unittest.defaultTestLoader.discover(tests_dir, pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    # 如果测试失败，以非零状态码退出
    sys.exit(0 if success else 1) 