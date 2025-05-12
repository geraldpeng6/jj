#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
采样测试脚本

测试自定义采样路由
"""

import sys
import json
import asyncio
import argparse
import logging
import httpx

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sampling_test')

async def test_sampling(server_url: str, test_type: str):
    """
    测试采样路由
    
    Args:
        server_url: MCP服务器URL
        test_type: 测试类型，可选值: 'kline', 'strategy'
    """
    # 构建采样请求URL
    sampling_url = f"{server_url}/sampling"
    
    # 根据测试类型构建消息
    if test_type == 'kline':
        messages = [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "请分析贵州茅台(600519)的K线图，给出技术分析和未来趋势预测。"
                }
            }
        ]
    elif test_type == 'strategy':
        messages = [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "请设计一个基于MACD和KDJ指标的趋势跟踪交易策略，适用于日线级别。"
                }
            }
        ]
    else:
        messages = [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "你好，这是一条测试消息。"
                }
            }
        ]
    
    # 构建请求体
    request_body = {
        "messages": messages,
        "systemPrompt": "你是一个助手。"
    }
    
    # 发送请求
    logger.info(f"发送采样请求到 {sampling_url}")
    logger.info(f"请求体: {json.dumps(request_body, ensure_ascii=False, indent=2)}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                sampling_url,
                json=request_body,
                timeout=10.0
            )
            
            # 检查响应
            if response.status_code == 200:
                result = response.json()
                logger.info("采样请求成功")
                logger.info(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                logger.error(f"采样请求失败: {response.status_code}")
                logger.error(f"错误信息: {response.text}")
                return None
    
    except Exception as e:
        logger.error(f"发送采样请求时发生错误: {e}")
        return None

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试MCP采样路由')
    parser.add_argument('--url', type=str, default='http://localhost:8000',
                        help='MCP服务器URL (默认: http://localhost:8000)')
    parser.add_argument('--type', type=str, choices=['kline', 'strategy', 'default'],
                        default='kline', help='测试类型 (默认: kline)')
    
    args = parser.parse_args()
    
    # 运行测试
    asyncio.run(test_sampling(args.url, args.type))

if __name__ == '__main__':
    main()
