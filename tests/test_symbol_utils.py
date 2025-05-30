#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
符号工具模块测试

测试股票符号相关的功能
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.symbol_utils import search_symbols, get_symbol_info


class TestSymbolUtils(unittest.TestCase):
    """测试符号工具类"""

    @patch('utils.symbol_utils.load_auth_config')
    @patch('utils.symbol_utils.get_auth_info')
    @patch('utils.symbol_utils.get_headers')
    @patch('requests.get')
    def test_search_symbols_success(self, mock_get, mock_headers, mock_auth_info, mock_load_auth):
        """测试成功搜索股票符号"""
        # 设置模拟数据
        mock_load_auth.return_value = True
        mock_auth_info.return_value = ('token', 'user123')
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        # 创建模拟响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Encoding': 'gzip'}
        
        # 创建测试数据
        test_symbols = [
            {"full_name": "600000.XSHG", "symbol": "600000", "exchange": "XSHG", "type": "stock", "description": "浦发银行"},
            {"full_name": "600001.XSHG", "symbol": "600001", "exchange": "XSHG", "type": "stock", "description": "邯郸钢铁"},
            {"full_name": "600002.XSHG", "symbol": "600002", "exchange": "XSHG", "type": "stock", "description": "齐鲁石化"}
        ]
        mock_response.json.return_value = {'code': 1, 'msg': 'ok', 'data': test_symbols}
        mock_get.return_value = mock_response
        
        # 测试默认参数
        result = search_symbols("银行")
        
        # 验证结果
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['symbol'], '600000')
        
        # 验证请求参数
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['query'], '银行')
        self.assertEqual(kwargs['params']['exchange'], 'ANY')
        self.assertEqual(kwargs['params']['type'], '')
        
    @patch('utils.symbol_utils.load_auth_config')
    @patch('utils.symbol_utils.get_auth_info')
    @patch('utils.symbol_utils.get_headers')
    @patch('requests.get')
    def test_search_symbols_with_limit(self, mock_get, mock_headers, mock_auth_info, mock_load_auth):
        """测试带结果限制的搜索"""
        # 设置模拟数据
        mock_load_auth.return_value = True
        mock_auth_info.return_value = ('token', 'user123')
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        # 创建模拟响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Encoding': 'gzip'}
        
        # 创建测试数据 - 10个结果
        test_symbols = [
            {"full_name": f"60000{i}.XSHG", "symbol": f"60000{i}", "exchange": "XSHG", 
             "type": "stock", "description": f"测试股票{i}"} for i in range(10)
        ]
        mock_response.json.return_value = {'code': 1, 'msg': 'ok', 'data': test_symbols}
        mock_get.return_value = mock_response
        
        # 测试限制为5个结果
        result = search_symbols("测试", limit=5)
        
        # 验证结果
        self.assertEqual(len(result), 5)
        
    @patch('utils.symbol_utils.load_auth_config')
    @patch('utils.symbol_utils.get_auth_info')
    @patch('utils.symbol_utils.get_headers')
    @patch('requests.get')
    def test_search_symbols_sorting(self, mock_get, mock_headers, mock_auth_info, mock_load_auth):
        """测试结果排序"""
        # 设置模拟数据
        mock_load_auth.return_value = True
        mock_auth_info.return_value = ('token', 'user123')
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        # 创建模拟响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Encoding': 'gzip'}
        
        # 创建不按顺序的测试数据
        test_symbols = [
            {"full_name": "600002.XSHG", "symbol": "600002", "exchange": "XSHG", "type": "stock", "description": "B公司"},
            {"full_name": "600001.XSHG", "symbol": "600001", "exchange": "XSHG", "type": "stock", "description": "C公司"},
            {"full_name": "600003.XSHG", "symbol": "600003", "exchange": "XSHG", "type": "stock", "description": "A公司"}
        ]
        mock_response.json.return_value = {'code': 1, 'msg': 'ok', 'data': test_symbols}
        mock_get.return_value = mock_response
        
        # 测试按描述排序（升序）
        result = search_symbols("公司", sort_by="description", sort_order="asc")
        
        # 验证结果
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['description'], 'A公司')
        self.assertEqual(result[1]['description'], 'B公司')
        self.assertEqual(result[2]['description'], 'C公司')
        
        # 测试按描述排序（降序）
        result = search_symbols("公司", sort_by="description", sort_order="desc")
        
        # 验证结果
        self.assertEqual(result[0]['description'], 'C公司')
        self.assertEqual(result[1]['description'], 'B公司')
        self.assertEqual(result[2]['description'], 'A公司')
        
    @patch('utils.symbol_utils.load_auth_config')
    @patch('utils.symbol_utils.get_auth_info')
    @patch('utils.symbol_utils.get_headers')
    @patch('requests.get')
    def test_search_symbols_empty_query(self, mock_get, mock_headers, mock_auth_info, mock_load_auth):
        """测试空查询"""
        # 设置模拟数据
        mock_load_auth.return_value = True
        mock_auth_info.return_value = ('token', 'user123')
        
        # 测试空查询
        result = search_symbols("")
        
        # 验证结果
        self.assertIsNone(result)
        mock_get.assert_not_called()
        
    @patch('utils.symbol_utils.load_auth_config')
    @patch('utils.symbol_utils.get_auth_info')
    @patch('utils.symbol_utils.get_headers')
    @patch('requests.get')
    def test_search_symbols_api_error(self, mock_get, mock_headers, mock_auth_info, mock_load_auth):
        """测试API错误响应"""
        # 设置模拟数据
        mock_load_auth.return_value = True
        mock_auth_info.return_value = ('token', 'user123')
        mock_headers.return_value = {'Authorization': 'Bearer token'}
        
        # 创建模拟响应
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.headers = {'Content-Encoding': 'gzip'}
        
        # 创建错误响应
        mock_response.json.return_value = {'code': 0, 'msg': 'error', 'data': None}
        mock_get.return_value = mock_response
        
        # 测试API错误
        result = search_symbols("测试")
        
        # 验证结果
        self.assertIsNone(result)
        
    @patch('utils.symbol_utils.load_auth_config')
    def test_search_symbols_auth_failure(self, mock_load_auth):
        """测试认证失败"""
        # 设置模拟数据
        mock_load_auth.return_value = False
        
        # 测试认证失败
        result = search_symbols("测试")
        
        # 验证结果
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main() 