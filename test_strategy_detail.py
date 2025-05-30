#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略详情测试脚本

用于测试和诊断策略详情获取功能中的问题
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
logger = logging.getLogger('test_strategy_detail')

def test_strategy_detail():
    """测试获取策略详情功能"""
    # 首先获取用户策略列表
    logger.info("获取用户策略列表...")
    user_strategies = get_strategy_list("user")
    
    if not user_strategies:
        logger.error("无法获取用户策略列表")
        return
    
    logger.info(f"获取到 {len(user_strategies)} 个用户策略")
    
    # 获取策略库列表
    logger.info("获取策略库列表...")
    library_strategies = get_strategy_list("library")
    
    if not library_strategies:
        logger.error("无法获取策略库列表")
        return
    
    logger.info(f"获取到 {len(library_strategies)} 个策略库策略")
    
    # 测试一个用户策略
    if user_strategies:
        user_strategy = user_strategies[0]
        user_strategy_id = user_strategy.get('strategy_id')
        user_strategy_name = user_strategy.get('strategy_name', '未命名策略')
        
        logger.info(f"测试用户策略: {user_strategy_name} (ID: {user_strategy_id})")
        logger.info("原始策略信息:")
        logger.info(f"- 名称: {user_strategy_name}")
        logger.info(f"- 组: user")
        
        # 获取详情
        detail = get_strategy_detail(user_strategy_id)
        
        if detail:
            logger.info("获取到的策略详情:")
            logger.info(f"- 名称: {detail.get('strategy_name', '未命名策略')}")
            logger.info(f"- 组: {detail.get('strategy_group', '未知')}")
            logger.info(f"- 描述: {detail.get('strategy_desc', '无描述')}")
            logger.info(f"- 详情字段: {list(detail.keys())}")
        else:
            logger.error("获取用户策略详情失败")
    
    # 测试一个策略库策略
    if library_strategies:
        library_strategy = library_strategies[0]
        library_strategy_id = library_strategy.get('strategy_id')
        library_strategy_name = library_strategy.get('strategy_name', '未命名策略')
        
        logger.info(f"测试策略库策略: {library_strategy_name} (ID: {library_strategy_id})")
        logger.info("原始策略信息:")
        logger.info(f"- 名称: {library_strategy_name}")
        logger.info(f"- 组: library")
        
        # 获取详情
        detail = get_strategy_detail(library_strategy_id)
        
        if detail:
            logger.info("获取到的策略详情:")
            logger.info(f"- 名称: {detail.get('strategy_name', '未命名策略')}")
            logger.info(f"- 组: {detail.get('strategy_group', '未知')}")
            logger.info(f"- 描述: {detail.get('strategy_desc', '无描述')}")
            logger.info(f"- 详情字段: {list(detail.keys())}")
        else:
            logger.error("获取策略库策略详情失败")
    
    # 测试一个不存在的策略ID
    fake_id = "nonexistent_strategy_id"
    logger.info(f"测试不存在的策略ID: {fake_id}")
    detail = get_strategy_detail(fake_id)
    
    if detail:
        logger.error("错误: 获取到了不存在的策略详情")
    else:
        logger.info("正确: 未获取到不存在的策略详情")
    
    logger.info("测试完成")

if __name__ == "__main__":
    test_strategy_detail() 