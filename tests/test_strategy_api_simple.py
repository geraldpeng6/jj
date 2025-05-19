#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略API简单测试脚本

该脚本是一个简化版的测试脚本，专门用于测试策略库列表API，并处理可能的压缩响应。
"""

import os
import sys
import json
import logging
import requests
import gzip
import io
import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入项目中的认证工具
from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 设置日志
def setup_logging(log_file: str = None) -> logging.Logger:
    """设置日志记录器"""
    # 创建日志记录器
    logger = logging.getLogger('strategy_api_test')
    logger.setLevel(logging.DEBUG)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def test_strategy_library_api():
    """测试策略库列表API"""
    # 生成日志文件名
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"data/logs/strategy_library_api_test_{timestamp}.log"
    
    # 设置日志
    logger = setup_logging(log_file)
    logger.info("开始测试策略库列表API")
    
    # 确保目录存在
    os.makedirs('data/logs', exist_ok=True)
    
    # 加载认证配置
    if not load_auth_config():
        logger.error("错误: 无法加载认证配置")
        return False
    
    # 获取认证信息
    token, user_id = get_auth_info()
    if not token or not user_id:
        logger.error("错误: 无法获取认证信息")
        return False
    
    # 构建API URL和参数
    base_url = "https://api.yueniusz.com"
    url = f"{base_url}/trader-service/strategy/strategy-library-list"
    params = {"user_id": user_id}
    
    # 获取请求头并禁用压缩
    headers = get_headers()
    headers['Accept-Encoding'] = 'identity'
    
    try:
        # 发送请求
        logger.info(f"发送请求到 {url}")
        response = requests.get(
            url,
            params=params,
            headers=headers,
            verify=True,
            timeout=30
        )
        
        # 记录响应信息
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应头: {dict(response.headers)}")
        
        # 检查响应是否成功
        if response.status_code != 200:
            logger.error(f"请求失败，状态码: {response.status_code}")
            return False
        
        # 获取响应内容
        content = response.content
        
        # 检查是否为gzip压缩内容
        if len(content) > 2 and content[:2] == b'\x1f\x8b':
            logger.info("检测到gzip压缩响应，尝试解压...")
            try:
                content = gzip.decompress(content)
                logger.info("gzip解压成功")
            except Exception as e:
                logger.error(f"gzip解压失败: {e}")
                # 记录原始内容的前100个字节（十六进制格式）
                hex_content = content[:100].hex()
                logger.error(f"原始内容前100字节(十六进制): {hex_content}")
                return False
        
        # 尝试解析JSON
        try:
            if isinstance(content, bytes):
                data = json.loads(content.decode('utf-8'))
            else:
                data = response.json()
            
            # 记录响应内容
            logger.info(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查响应是否成功
            if data.get('code') == 1 and data.get('msg') == 'ok':
                strategy_list = data.get('data', {}).get('strategy_list', [])
                logger.info(f"获取策略库列表成功，共 {len(strategy_list)} 个策略")
                
                # 记录策略列表的基本信息
                for i, strategy in enumerate(strategy_list, 1):
                    logger.info(f"策略 {i}:")
                    logger.info(f"  ID: {strategy.get('strategy_id', '无ID')}")
                    logger.info(f"  名称: {strategy.get('strategy_name', '未命名策略')}")
                
                logger.info("测试成功完成")
                return True
            else:
                logger.error(f"获取策略库列表失败，错误码: {data.get('code')}, 错误信息: {data.get('msg')}")
                return False
        except ValueError as e:
            # JSON解析错误
            logger.error(f"解析JSON内容失败: {e}")
            
            # 尝试以不同编码解码
            for encoding in ['utf-8', 'latin1', 'cp1252', 'gbk']:
                try:
                    decoded = content.decode(encoding)
                    logger.info(f"使用{encoding}解码成功，前1000个字符: {decoded[:1000]}")
                    break
                except UnicodeDecodeError:
                    logger.info(f"使用{encoding}解码失败")
            
            return False
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return False

def main():
    """主函数"""
    # 检查配置文件
    if not os.path.exists('data/config/auth.json'):
        print("错误: 认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息")
        return
    
    # 执行测试
    success = test_strategy_library_api()
    
    # 输出结果
    if success:
        print("测试成功完成，请查看日志文件获取详细信息")
    else:
        print("测试失败，请查看日志文件获取详细信息")

if __name__ == "__main__":
    main()
