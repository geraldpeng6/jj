#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略API完整测试脚本

该脚本用于全面测试策略相关的API功能，包括：
1. 获取用户策略列表
2. 获取策略库列表
3. 获取策略详情
4. 将完整的请求和响应记录到测试日志文件中
5. 提供适当的错误处理机制
6. 支持多种输出格式和测试选项
"""

import os
import sys
import json
import logging
import requests
import argparse
import datetime
import time
from typing import Dict, Optional, Any, Tuple, List, Union

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入项目中的认证工具
from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 设置日志
def setup_logging(log_file: str = None, log_level: int = logging.DEBUG) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        log_file: 日志文件路径，如果为None则输出到控制台
        log_level: 日志级别
        
    Returns:
        logging.Logger: 日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger('strategy_api_test')
    logger.setLevel(log_level)
    
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
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def test_strategy_list_api(
    strategy_group: str = "library", 
    base_url: str = "https://api.yueniusz.com",
    output_format: str = "log",
    log_file: str = None
) -> Union[bool, Dict[str, Any]]:
    """
    测试获取策略列表的API功能
    
    Args:
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略
        base_url: API基础URL
        output_format: 输出格式，"log"表示日志输出，"json"表示返回JSON数据
        log_file: 日志文件路径，如果为None则自动生成
        
    Returns:
        Union[bool, Dict[str, Any]]: 
            - 当output_format为"log"时，返回测试是否成功
            - 当output_format为"json"时，返回API响应数据
    """
    # 生成日志文件名，包含时间戳和策略组类型
    if log_file is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"data/logs/strategy_{strategy_group}_list_api_test_{timestamp}.log"
    
    # 设置日志
    logger = setup_logging(log_file)
    logger.info(f"开始测试{'策略库' if strategy_group == 'library' else '用户策略'}列表API")
    
    # 加载认证配置
    logger.info("加载认证配置")
    if not load_auth_config():
        logger.error("错误: 无法加载认证配置，请确保 data/config/auth.json 文件存在且包含有效的token和user_id")
        return False if output_format == "log" else {"error": "无法加载认证配置"}
    
    # 获取认证信息
    token, user_id = get_auth_info()
    if not token or not user_id:
        logger.error("错误: 无法获取认证信息")
        return False if output_format == "log" else {"error": "无法获取认证信息"}
    
    logger.info(f"成功获取认证信息，用户ID: {user_id}")
    
    # 根据策略组类型选择不同的URL
    if strategy_group == "library":
        url = f"{base_url}/trader-service/strategy/strategy-library-list"
        log_prefix = "策略库"
    else:
        url = f"{base_url}/trader-service/strategy/user-strategy-list"
        log_prefix = "用户策略"
    
    logger.info(f"API URL: {url}")
    
    # 构建请求参数
    params = {"user_id": user_id}
    logger.info(f"请求参数: {params}")
    
    # 获取请求头
    headers = get_headers()
    # 记录请求头（移除敏感信息）
    safe_headers = headers.copy()
    if 'Authorization' in safe_headers:
        safe_headers['Authorization'] = 'Bearer ***'  # 隐藏实际token
    logger.info(f"请求头: {json.dumps(safe_headers, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送API请求
        logger.info("发送API请求...")
        start_time = time.time()
        response = requests.get(
            url,
            params=params,
            headers=headers,
            verify=True,
            timeout=30  # 增加超时时间到30秒
        )
        end_time = time.time()
        
        # 记录请求信息
        logger.info(f"请求方法: GET")
        logger.info(f"请求URL: {response.request.url}")
        logger.info(f"请求耗时: {end_time - start_time:.2f}秒")
        
        # 尝试解析响应
        try:
            response.raise_for_status()  # 检查HTTP错误
            data = response.json()
            
            # 记录响应状态和内容
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            # 检查响应是否成功
            if data.get('code') == 1 and data.get('msg') == 'ok':
                strategy_list = data.get('data', {}).get('strategy_list', [])
                logger.info(f"获取{log_prefix}列表成功，共 {len(strategy_list)} 个策略")
                
                # 记录策略列表的基本信息
                for i, strategy in enumerate(strategy_list, 1):
                    logger.info(f"策略 {i}:")
                    logger.info(f"  ID: {strategy.get('strategy_id', '无ID')}")
                    logger.info(f"  名称: {strategy.get('strategy_name', '未命名策略')}")
                    
                    # 检查策略描述的格式
                    strategy_desc = strategy.get('strategy_desc')
                    if strategy_desc:
                        if isinstance(strategy_desc, list):
                            logger.info(f"  描述: {', '.join(strategy_desc)}")
                        else:
                            logger.info(f"  描述: {strategy_desc}")
                    
                    # 检查策略描述URL
                    strategy_desc_url = strategy.get('strategy_desc_url')
                    if strategy_desc_url:
                        logger.info(f"  描述URL: {strategy_desc_url}")
                
                logger.info("测试成功完成")
                
                if output_format == "log":
                    return True
                else:
                    return data
            else:
                logger.error(f"获取{log_prefix}列表失败，错误码: {data.get('code')}, 错误信息: {data.get('msg')}")
                
                if output_format == "log":
                    return False
                else:
                    return {"error": f"获取{log_prefix}列表失败", "data": data}
                
        except ValueError as e:
            # JSON解析错误
            logger.error(f"解析响应内容失败: {e}")
            logger.error(f"原始响应内容: {response.text[:1000]}...")  # 只记录前1000个字符
            
            if output_format == "log":
                return False
            else:
                return {"error": f"解析响应内容失败: {e}", "raw_response": response.text[:1000]}
            
    except requests.exceptions.RequestException as e:
        # 请求异常
        logger.error(f"请求异常: {e}")
        
        if output_format == "log":
            return False
        else:
            return {"error": f"请求异常: {e}"}
    except Exception as e:
        # 其他异常
        logger.error(f"发生未预期的异常: {e}")
        
        if output_format == "log":
            return False
        else:
            return {"error": f"发生未预期的异常: {e}"}

def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='测试策略API')
    parser.add_argument('--type', '-t', type=str, default='library',
                        choices=['library', 'user', 'both'],
                        help='策略类型 (library, user, both)')
    parser.add_argument('--url', '-u', type=str, default='https://api.yueniusz.com',
                        help='API基础URL')
    parser.add_argument('--format', '-f', type=str, default='log',
                        choices=['log', 'json'],
                        help='输出格式 (log, json)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='输出文件路径，仅当format为json时有效')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 确保必要的目录存在
    os.makedirs('data/logs', exist_ok=True)
    os.makedirs('data/config', exist_ok=True)
    
    # 检查配置文件
    if not os.path.exists('data/config/auth.json'):
        print("错误: 认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息")
        return
    
    # 根据参数执行测试
    if args.type == 'both':
        # 测试两种类型
        if args.format == 'json':
            # JSON输出
            results = {
                'library': test_strategy_list_api('library', args.url, 'json'),
                'user': test_strategy_list_api('user', args.url, 'json')
            }
            
            # 输出结果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"结果已保存到 {args.output}")
            else:
                print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            # 日志输出
            library_success = test_strategy_list_api('library', args.url)
            user_success = test_strategy_list_api('user', args.url)
            
            if library_success and user_success:
                print("所有测试成功完成，请查看日志文件获取详细信息")
            else:
                print("部分测试失败，请查看日志文件获取详细信息")
    else:
        # 测试单一类型
        if args.format == 'json':
            # JSON输出
            result = test_strategy_list_api(args.type, args.url, 'json')
            
            # 输出结果
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"结果已保存到 {args.output}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            # 日志输出
            success = test_strategy_list_api(args.type, args.url)
            
            if success:
                print("测试成功完成，请查看日志文件获取详细信息")
            else:
                print("测试失败，请查看日志文件获取详细信息")

if __name__ == "__main__":
    main()
