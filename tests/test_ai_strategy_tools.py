#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试AI策略生成工具
"""

import asyncio
import unittest
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock, patch

from src.tools.ai_strategy_tools import generate_strategy, extract_code, extract_strategy_name
from mcp.server.fastmcp import Context


class TestAIStrategyTools(unittest.TestCase):
    """测试AI策略生成工具的类"""

    def test_extract_code(self):
        """测试从生成内容中提取代码的功能"""
        # 测试通过函数签名提取
        content = """这是一些说明文字
def choose_stock(context):
    # 选择沪深300成分股
    context.stock_list = get_index_stocks('000300.SH')
    return context.stock_list

def indicator(context):
    # 其他代码
    pass
"""
        result = extract_code(content, "选股函数", "def choose_stock")
        self.assertIn("def choose_stock(context):", result)
        self.assertIn("context.stock_list = get_index_stocks('000300.SH')", result)

        # 测试通过部分名称提取
        content = """这里是一些文字
```选股函数
def choose_stock(context):
    # 选择沪深300成分股
    context.stock_list = get_index_stocks('000300.SH')
```

```指标函数
def indicator(context):
    pass
```
"""
        result = extract_code(content, "选股函数", "def choose_stock")
        self.assertIn("def choose_stock(context):", result)
        self.assertIn("context.stock_list = get_index_stocks('000300.SH')", result)

    def test_extract_strategy_name(self):
        """测试从生成内容中提取策略名称的功能"""
        # 测试冒号提取
        content = "策略名称: 均线交叉策略\n其他内容"
        result = extract_strategy_name(content)
        self.assertEqual("均线交叉策略", result)

        # 测试中文冒号提取
        content = "策略名称：双均线突破策略\n其他内容"
        result = extract_strategy_name(content)
        self.assertEqual("双均线突破策略", result)

        # 测试找不到名称时的默认值
        content = "没有策略名称的内容"
        result = extract_strategy_name(content)
        self.assertEqual("AI生成策略", result)


class TestAsyncAIStrategyTools(unittest.IsolatedAsyncioTestCase):
    """测试AI策略生成工具的异步方法"""

    @patch('src.tools.ai_strategy_tools.HiTraderDocs._load_full_doc')
    async def test_generate_strategy_with_doc(self, mock_load_doc):
        """测试生成策略文档和指导信息"""
        # 设置模拟的文档内容
        mock_load_doc.return_value = "HiTrader文档内容"
        
        # 执行函数
        result = await generate_strategy("测试策略", "测试策略名称")
        
        # 验证结果包含必要的部分
        self.assertIn("## 策略需求", result)
        self.assertIn("策略名称: 测试策略名称", result)
        self.assertIn("策略描述: 测试策略", result)
        self.assertIn("## HiTrader文档参考", result)
        self.assertIn("## 开发指南", result)
        self.assertIn("create_user_strategy", result)
        self.assertIn("choose_stock", result)
        self.assertIn("indicator", result)
        self.assertIn("timing", result)
        self.assertIn("control_risk", result)

    @patch('src.tools.ai_strategy_tools.HiTraderDocs._load_full_doc')
    async def test_generate_strategy_without_name(self, mock_load_doc):
        """测试没有提供策略名称时的行为"""
        # 设置模拟的文档内容
        mock_load_doc.return_value = "HiTrader文档内容"
        
        # 执行函数
        result = await generate_strategy("测试策略描述")
        
        # 验证结果包含自动生成的策略名称
        self.assertIn("策略名称: AI生成策略-测试策略描述", result)

    @patch('src.tools.ai_strategy_tools.HiTraderDocs._load_full_doc')
    async def test_generate_strategy_doc_load_failure(self, mock_load_doc):
        """测试文档加载失败的情况"""
        # 设置模拟的文档内容为空
        mock_load_doc.return_value = None
        
        # 执行函数
        result = await generate_strategy("测试策略")
        
        # 验证结果
        self.assertEqual("无法加载HiTrader文档，策略生成失败", result)


if __name__ == '__main__':
    unittest.main() 