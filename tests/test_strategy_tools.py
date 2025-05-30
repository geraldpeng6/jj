#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具测试模块

测试策略相关的MCP工具
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import asyncio
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.strategy_tools import (
    create_strategy,
    update_strategy,
    delete_user_strategy,
    get_strategy
)


class TestStrategyTools(unittest.TestCase):
    """测试策略工具"""

    def setUp(self):
        """测试前的准备工作"""
        # 禁用日志输出
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """测试后的清理工作"""
        # 恢复日志输出
        logging.disable(logging.NOTSET)

    @patch('src.tools.strategy_tools.create_user_strategy')
    def test_create_strategy(self, mock_create):
        """测试创建策略工具"""
        # 模拟成功创建策略
        mock_create.return_value = {"strategy_id": "new_strategy_id"}
        
        # 调用被测试的函数（异步函数需要通过事件循环调用）
        result = asyncio.run(create_strategy(
            strategy_name="测试策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=20)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n",
            control_risk="def control_risk(context):\n    pass\n"
        ))
        
        # 验证结果
        self.assertIn("创建策略成功", result)
        self.assertIn("new_strategy_id", result)
        
        # 验证调用
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        self.assertEqual(args[0]["strategy_name"], "测试策略")

    @patch('src.tools.strategy_tools.create_user_strategy')
    def test_create_strategy_failure(self, mock_create):
        """测试创建策略失败"""
        # 模拟创建策略失败
        mock_create.return_value = None
        
        # 调用被测试的函数
        result = asyncio.run(create_strategy(
            strategy_name="测试策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=20)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n"
        ))
        
        # 验证结果
        self.assertIn("创建策略失败", result)

    @patch('src.tools.strategy_tools.get_strategy_detail')
    @patch('src.tools.strategy_tools.update_user_strategy')
    def test_update_strategy(self, mock_update, mock_get_detail):
        """测试更新策略工具"""
        # 模拟获取策略详情
        mock_get_detail.return_value = {
            "strategy_id": "existing_strategy_id",
            "strategy_name": "原策略名称",
            "strategy_group": "user"
        }
        
        # 模拟成功更新策略
        mock_update.return_value = True
        
        # 调用被测试的函数
        result = asyncio.run(update_strategy(
            strategy_id="existing_strategy_id",
            strategy_name="更新后的策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=15)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n",
            control_risk="def control_risk(context):\n    pass\n"
        ))
        
        # 验证结果
        self.assertIn("成功更新策略", result)
        self.assertIn("existing_strategy_id", result)
        
        # 验证调用
        mock_update.assert_called_once()
        args, kwargs = mock_update.call_args
        self.assertEqual(args[0]["strategy_name"], "更新后的策略")

    @patch('src.tools.strategy_tools.get_strategy_detail')
    def test_update_nonexistent_strategy(self, mock_get_detail):
        """测试更新不存在的策略"""
        # 模拟策略不存在
        mock_get_detail.return_value = None
        
        # 调用被测试的函数
        result = asyncio.run(update_strategy(
            strategy_id="nonexistent_id",
            strategy_name="更新后的策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=15)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n"
        ))
        
        # 验证结果
        self.assertIn("更新策略失败", result)
        self.assertIn("找不到策略ID", result)

    @patch('src.tools.strategy_tools.get_strategy_detail')
    def test_update_library_strategy(self, mock_get_detail):
        """测试更新策略库策略（不允许）"""
        # 模拟获取策略详情（策略库策略）
        mock_get_detail.return_value = {
            "strategy_id": "library_strategy_id",
            "strategy_name": "策略库策略",
            "strategy_group": "library"
        }
        
        # 调用被测试的函数
        result = asyncio.run(update_strategy(
            strategy_id="library_strategy_id",
            strategy_name="更新后的策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=15)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n"
        ))
        
        # 验证结果
        self.assertIn("更新策略失败", result)
        self.assertIn("不是用户策略", result)

    @patch('src.tools.strategy_tools.get_strategy_detail')
    @patch('src.tools.strategy_tools.update_user_strategy')
    def test_update_strategy_failure(self, mock_update, mock_get_detail):
        """测试更新策略失败"""
        # 模拟获取策略详情
        mock_get_detail.return_value = {
            "strategy_id": "existing_strategy_id",
            "strategy_name": "原策略名称",
            "strategy_group": "user"
        }
        
        # 模拟更新策略失败
        mock_update.return_value = False
        
        # 调用被测试的函数
        result = asyncio.run(update_strategy(
            strategy_id="existing_strategy_id",
            strategy_name="更新后的策略",
            choose_stock="def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            indicator="def indicators(context):\n    context.sma = SMA(period=15)\n",
            timing="def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n"
        ))
        
        # 验证结果
        self.assertIn("更新策略失败", result)


if __name__ == '__main__':
    unittest.main() 