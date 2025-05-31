#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试AI策略生成工具的简单脚本
"""

import asyncio
import logging
import os
import sys

# 设置日志级别
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_ai_strategy_generator')

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.ai_strategy_tools import generate_strategy, extract_code, extract_strategy_name
from unittest.mock import patch, MagicMock


# 模拟HiTraderDocs._load_full_doc函数
def mock_load_doc():
    """模拟加载文档的函数"""
    return """
HiTrader平台策略开发文档

选股函数：choose_stock(context)
该函数用于选择要交易的股票，一般在每个交易周期开始时被调用。
参数：context - 策略上下文对象，包含股票列表、指标、持仓等信息
返回值：股票列表

常用API：
get_index_stocks(index_code) - 获取指定指数的成分股
get_industry_stocks(industry_code) - 获取指定行业的股票
get_stock_list() - 获取所有可交易的股票

示例：
def choose_stock(context):
    context.stock_list = get_index_stocks('000300.SH')  # 获取沪深300成分股
    return context.stock_list
"""


async def test_generate_strategy():
    """测试生成策略的函数"""
    logger.info("开始测试生成策略...")
    
    # 使用patch来模拟文档加载功能
    with patch('src.tools.ai_strategy_tools.HiTraderDocs._load_full_doc', return_value=mock_load_doc()):
        # 测试生成策略文档
        result = await generate_strategy(
            description="创建一个基于双均线交叉的策略，当5日均线上穿10日均线时买入，当5日均线下穿10日均线时卖出",
            strategy_name="测试双均线策略"
        )
        
        # 打印结果
        print("\n测试结果:")
        print(result)
        
        # 验证结果包含必要的部分
        assert "## 策略需求" in result
        assert "策略名称: 测试双均线策略" in result
        assert "## HiTrader文档参考" in result
        assert "## 开发指南" in result
        
        # 测试自动生成策略名称
        result_auto_name = await generate_strategy(
            description="创建一个基于MACD指标的择时策略"
        )
        
        print("\n自动生成策略名称测试结果:")
        print(result_auto_name)
        
        # 验证结果
        assert "策略名称: AI生成策略-创建一个基于MACD指标的择时策略" in result_auto_name
    
    # 测试文档加载失败的情况
    with patch('src.tools.ai_strategy_tools.HiTraderDocs._load_full_doc', return_value=None):
        result_no_doc = await generate_strategy(
            description="这是一个文档加载失败的测试"
        )
        
        print("\n文档加载失败测试结果:")
        print(result_no_doc)
        
        # 验证结果
        assert result_no_doc == "无法加载HiTrader文档，策略生成失败"
    
    logger.info("测试完成")


async def main():
    """主函数"""
    await test_generate_strategy()


if __name__ == "__main__":
    asyncio.run(main()) 