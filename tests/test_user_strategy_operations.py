#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户策略操作测试模块

测试用户策略的创建、更新和删除功能
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import requests
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.strategy_utils import (
    create_user_strategy, 
    update_user_strategy, 
    get_strategy_detail, 
    delete_strategy
)


class TestUserStrategyOperations(unittest.TestCase):
    """测试用户策略操作"""

    def setUp(self):
        """测试前的准备工作"""
        # 禁用日志输出
        logging.disable(logging.CRITICAL)
        
        # 模拟认证信息
        self.auth_patcher = patch('utils.strategy_utils.load_auth_config')
        self.mock_load_auth = self.auth_patcher.start()
        self.mock_load_auth.return_value = True
        
        self.auth_info_patcher = patch('utils.strategy_utils.get_auth_info')
        self.mock_get_auth_info = self.auth_info_patcher.start()
        self.mock_get_auth_info.return_value = ('fake_token', 'fake_user_id')
        
        # 创建示例策略数据
        self.sample_strategy = {
            "strategy_name": "测试单均线策略",
            "indicator": "def indicators(context):\n    context.sma = SMA(period=20)\n",
            "choose_stock": "def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            "timing": "def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n",
            "control_risk": "def control_risk(context):\n    pass\n"
        }
        
        # 更新策略的数据
        self.update_strategy = {
            "strategy_id": "fake_strategy_id",
            "strategy_name": "更新后的策略",
            "indicator": "def indicators(context):\n    context.sma = SMA(period=15)\n",
            "choose_stock": "def choose_stock(context):\n    context.symbol_list = [\"600000.XSHG\"]\n",
            "timing": "def timing(context):\n    if context.data.close > context.sma:\n        context.buy()\n    else:\n        context.sell()\n",
            "control_risk": "def control_risk(context):\n    pass\n"
        }

    def tearDown(self):
        """测试后的清理工作"""
        # 恢复日志输出
        logging.disable(logging.NOTSET)
        
        # 停止所有 patcher
        self.auth_patcher.stop()
        self.auth_info_patcher.stop()

    @patch('utils.strategy_utils.requests.post')
    def test_create_user_strategy_success(self, mock_post):
        """测试成功创建用户策略"""
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1,
            "msg": "ok",
            "data": {
                "strategy_id": "new_strategy_id"
            }
        }
        mock_post.return_value = mock_response
        
        # 调用被测试的函数
        result = create_user_strategy(self.sample_strategy)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.get('strategy_id'), 'new_strategy_id')
        
        # 验证请求
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('user_id', kwargs['json'])
        self.assertEqual(kwargs['json']['strategy_name'], '测试单均线策略')

    @patch('utils.strategy_utils.requests.post')
    def test_create_user_strategy_failure(self, mock_post):
        """测试创建用户策略失败"""
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "错误信息",
            "data": {}
        }
        mock_post.return_value = mock_response
        
        # 调用被测试的函数
        result = create_user_strategy(self.sample_strategy)
        
        # 验证结果
        self.assertIsNone(result)

    @patch('utils.strategy_utils.get_strategy_detail')
    @patch('utils.strategy_utils.requests.put')
    def test_update_user_strategy_success(self, mock_put, mock_get_detail):
        """测试成功更新用户策略"""
        # 模拟获取策略详情
        mock_get_detail.return_value = {
            "strategy_id": "fake_strategy_id",
            "strategy_name": "原策略名称",
            "strategy_group": "user"
        }
        
        # 模拟成功响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 1,
            "msg": "ok",
            "data": {}
        }
        mock_put.return_value = mock_response
        
        # 调用被测试的函数
        result = update_user_strategy(self.update_strategy)
        
        # 验证结果
        self.assertTrue(result)
        
        # 验证请求
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        self.assertIn('user_id', kwargs['json'])
        self.assertEqual(kwargs['json']['strategy_name'], '更新后的策略')

    @patch('utils.strategy_utils.get_strategy_detail')
    def test_update_nonexistent_strategy(self, mock_get_detail):
        """测试更新不存在的策略"""
        # 模拟策略不存在
        mock_get_detail.return_value = None
        
        # 调用被测试的函数
        result = update_user_strategy(self.update_strategy)
        
        # 验证结果
        self.assertFalse(result)

    @patch('utils.strategy_utils.get_strategy_detail')
    def test_update_library_strategy(self, mock_get_detail):
        """测试更新策略库策略（不允许）"""
        # 模拟获取策略详情（策略库策略）
        mock_get_detail.return_value = {
            "strategy_id": "fake_strategy_id",
            "strategy_name": "策略库策略",
            "strategy_group": "library"
        }
        
        # 调用被测试的函数
        result = update_user_strategy(self.update_strategy)
        
        # 验证结果
        self.assertFalse(result)

    @patch('utils.strategy_utils.get_strategy_detail')
    @patch('utils.strategy_utils.requests.put')
    def test_update_user_strategy_failure(self, mock_put, mock_get_detail):
        """测试更新用户策略失败"""
        # 模拟获取策略详情
        mock_get_detail.return_value = {
            "strategy_id": "fake_strategy_id",
            "strategy_name": "原策略名称",
            "strategy_group": "user"
        }
        
        # 模拟失败响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "错误信息",
            "data": {}
        }
        mock_put.return_value = mock_response
        
        # 调用被测试的函数
        result = update_user_strategy(self.update_strategy)
        
        # 验证结果
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main() 