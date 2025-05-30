#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
特定策略测试脚本

专门用于测试和诊断特定策略ID的详情获取功能
"""

import logging
import sys
import json
import requests
from utils.strategy_utils import get_strategy_detail, get_headers
from utils.auth_utils import get_auth_info, load_auth_config

# 配置日志，设置为DEBUG级别以显示更多信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('test_specific_strategy')

def test_specific_strategy(strategy_id):
    """测试特定策略ID的详情获取功能"""
    logger.info(f"测试特定策略: {strategy_id}")
    
    # 首先直接通过工具函数获取策略详情
    logger.info("使用工具函数获取策略详情...")
    detail = get_strategy_detail(strategy_id)
    
    if detail:
        logger.info("成功获取策略详情:")
        logger.info(f"- 名称: {detail.get('strategy_name', '未命名策略')}")
        logger.info(f"- 组: {detail.get('strategy_group', '未知')}")
        logger.info(f"- 字段: {list(detail.keys())}")
    else:
        logger.error("通过工具函数获取策略详情失败")
    
    # 然后直接调用API进行测试，检查原始响应
    logger.info("直接调用API测试...")
    
    if not load_auth_config():
        logger.error("加载认证配置失败")
        return
    
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("获取认证信息失败")
        return
    
    # 测试用户策略API
    test_api(strategy_id, user_id, "user")
    
    # 测试策略库API
    test_api(strategy_id, user_id, "library")

def test_api(strategy_id, user_id, group):
    """测试特定API端点"""
    
    BASE_URL = "https://api.yueniusz.com"
    
    if group == "user":
        url = f"{BASE_URL}/trader-service/strategy/user-strategy"
        group_name = "用户策略"
    else:
        url = f"{BASE_URL}/trader-service/strategy/strategy-library"
        group_name = "策略库"
    
    logger.info(f"测试 {group_name} API...")
    
    params = {
        "user_id": user_id,
        "strategy_id": strategy_id
    }
    headers = get_headers()
    headers['Accept-Encoding'] = 'identity'  # 禁用压缩响应
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        logger.info(f"API响应状态码: {response.status_code}")
        
        try:
            data = response.json()
            logger.info(f"API响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            if data.get('code') == 1 and data.get('msg') == 'ok':
                strategy_detail = data.get('data', {})
                
                logger.info(f"API响应字段: {list(strategy_detail.keys())}")
                
                if 'strategy_name' in strategy_detail and strategy_detail.get('strategy_name'):
                    logger.info(f"找到策略名称: {strategy_detail.get('strategy_name')}")
                else:
                    logger.warning(f"未找到策略名称或名称为空")
            else:
                logger.warning(f"API响应错误: {data.get('code')}, {data.get('msg')}")
        except json.JSONDecodeError:
            logger.error("无法解析API响应为JSON")
            logger.debug(f"原始响应: {response.text}")
    except Exception as e:
        logger.error(f"请求失败: {e}")

if __name__ == "__main__":
    # 测试问题策略
    test_specific_strategy("RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ") 