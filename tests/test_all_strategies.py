#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
全面策略测试脚本

测试所有用户策略和策略库策略的详情获取功能
"""

import logging
import sys
import json
from utils.strategy_utils import get_strategy_detail, get_strategy_list

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('test_all_strategies')

def test_all_strategies():
    """测试所有策略的详情获取功能"""
    # 获取用户策略列表
    logger.info("获取用户策略列表...")
    user_strategies = get_strategy_list("user")
    
    if not user_strategies:
        logger.error("无法获取用户策略列表")
    else:
        logger.info(f"获取到 {len(user_strategies)} 个用户策略")
    
    # 获取策略库列表
    logger.info("获取策略库列表...")
    library_strategies = get_strategy_list("library")
    
    if not library_strategies:
        logger.error("无法获取策略库列表")
    else:
        logger.info(f"获取到 {len(library_strategies)} 个策略库策略")
    
    # 测试所有用户策略
    if user_strategies:
        logger.info("========== 测试所有用户策略 ==========")
        test_strategies_from_group(user_strategies, "user")
    
    # 测试所有策略库策略
    if library_strategies:
        logger.info("========== 测试所有策略库策略 ==========")
        test_strategies_from_group(library_strategies, "library")
    
    logger.info("所有测试完成")

def test_strategies_from_group(strategies, expected_group):
    """测试指定组的所有策略"""
    success_count = 0
    error_count = 0
    
    for i, strategy in enumerate(strategies, 1):
        strategy_id = strategy.get('strategy_id')
        strategy_name = strategy.get('strategy_name', '未命名策略')
        
        logger.info(f"[{i}/{len(strategies)}] 测试策略: {strategy_name} (ID: {strategy_id})")
        
        # 获取详情
        detail = get_strategy_detail(strategy_id)
        
        if detail:
            found_name = detail.get('strategy_name', '未命名策略')
            found_group = detail.get('strategy_group', '未知')
            
            # 检查策略组是否正确
            if found_group == expected_group:
                logger.info(f"✓ 成功: 策略组正确 ({found_group})")
                success_count += 1
            else:
                logger.error(f"✗ 错误: 策略组错误 (预期: {expected_group}, 实际: {found_group})")
                error_count += 1
                
            # 检查策略名称是否正确
            if found_name == strategy_name:
                logger.info(f"✓ 成功: 策略名称正确 ({found_name})")
            else:
                logger.error(f"✗ 错误: 策略名称错误 (预期: {strategy_name}, 实际: {found_name})")
        else:
            logger.error(f"✗ 错误: 无法获取策略详情")
            error_count += 1
    
    # 总结
    logger.info(f"测试完成: 成功 {success_count}/{len(strategies)}, 错误 {error_count}/{len(strategies)}")

if __name__ == "__main__":
    test_all_strategies() 