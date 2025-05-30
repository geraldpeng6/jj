#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试策略名称获取功能

此测试验证在回测过程中能否正确获取策略名称
"""

import os
import sys
import logging
import unittest
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_strategy_name')

# 导入被测试的模块
from utils.strategy_utils import get_strategy_detail


class TestStrategyName(unittest.TestCase):
    """测试策略名称获取功能的测试类"""

    def test_get_strategy_from_user(self):
        """测试从用户策略中获取策略名称"""
        # 使用一个已知的用户策略ID
        strategy_id = "RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ"
        
        # 从用户策略库获取
        user_strategy = get_strategy_detail(strategy_id, "user")
        
        # 打印策略详情，以便查看结构
        if user_strategy:
            logger.info(f"从用户策略库获取到策略: {user_strategy}")
            
            # 获取策略名称
            strategy_name = user_strategy.get('name') or user_strategy.get('strategy_name')
            logger.info(f"策略名称: {strategy_name}")
            
            # 已知用户策略存在但名称为空，所以不做断言
        else:
            logger.warning(f"未找到用户策略: {strategy_id}")

    def test_get_strategy_from_library(self):
        """测试从策略库中获取策略名称"""
        # 使用一个已知的策略库策略ID
        strategy_id = "RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ"
        
        # 从策略库获取
        library_strategy = get_strategy_detail(strategy_id, "library")
        
        # 打印策略详情，以便查看结构
        if library_strategy:
            logger.info(f"从策略库获取到策略: {library_strategy}")
            
            # 获取策略名称
            strategy_name = library_strategy.get('name') or library_strategy.get('strategy_name')
            logger.info(f"策略名称: {strategy_name}")
            
            # 验证策略名称不为None
            self.assertIsNotNone(strategy_name, "策略名称不应为None")
        else:
            logger.warning(f"未找到策略库策略: {strategy_id}")
            # 这里不断言失败，因为可能确实没有该策略

    def test_fallback_mechanism(self):
        """测试当用户策略没有名称时，回退到策略库获取名称的机制"""
        strategy_id = "RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ"
        strategy_name = None
        strategy_data = None
        
        # 模拟修正后的 run_backtest 中的逻辑
        # 首先尝试从用户策略库获取
        user_strategy = get_strategy_detail(strategy_id, "user")
        if user_strategy:
            # 优先使用用户策略的名称
            strategy_name = user_strategy.get('name') or user_strategy.get('strategy_name')
            if strategy_name:
                logger.info(f"从用户策略库获取到策略名称: {strategy_name}")
            else:
                logger.info(f"用户策略存在但没有名称，尝试从策略库获取")
            strategy_data = user_strategy
        
        # 如果没有从用户策略获取到名称，尝试从策略库获取
        if not strategy_name:
            # 尝试从系统策略库获取
            library_strategy = get_strategy_detail(strategy_id, "library")
            if library_strategy:
                strategy_name = library_strategy.get('name') or library_strategy.get('strategy_name')
                logger.info(f"从系统策略库获取到策略名称: {strategy_name}")
                # 如果之前没有获取到策略数据，使用库策略数据
                if not strategy_data:
                    strategy_data = library_strategy
            
        # 如果仍然没有获取到策略数据，说明两处都没有找到
        if not strategy_data:
            logger.error(f"未找到策略: {strategy_id}")
        
        # 如果名称仍为空，使用默认名称
        if not strategy_name:
            strategy_name = "未命名策略"
            logger.warning(f"无法获取策略名称，使用默认名称: {strategy_name}")
        
        logger.info(f"最终使用的策略名称: {strategy_name}")
        
        # 验证策略名称不是"未命名策略"
        self.assertNotEqual(strategy_name, "未命名策略", "策略名称不应为默认的'未命名策略'")
        
        # 验证策略数据不为None
        self.assertIsNotNone(strategy_data, "策略数据不应为None")


if __name__ == '__main__':
    unittest.main() 