#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP HTTP头部测试脚本

用于测试MCP服务器的HTTP头部配置
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MCP HTTP头部测试脚本')
    parser.add_argument('--host', type=str, default='localhost', help='MCP服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='MCP服务器端口')
    return parser.parse_args()

def test_headers(host: str, port: int) -> None:
    """
    测试MCP服务器的HTTP头部配置

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
    """
    url = f"http://{host}:{port}/mcp/"

    # 测试不同的Accept头部
    test_cases = [
        {
            "name": "默认头部",
            "headers": {
                "Content-Type": "application/json"
            }
        },
        {
            "name": "只接受JSON",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        },
        {
            "name": "只接受事件流",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        },
        {
            "name": "接受JSON和事件流",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        }
    ]

    # 构建请求体 - 使用一个简单的工具调用
    request_body = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "list_tools",
        "params": {}
    }

    # 测试每种情况
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"请求头: {test_case['headers']}")
        
        try:
            response = requests.post(url, json=request_body, headers=test_case['headers'])
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("测试成功!")
                try:
                    # 尝试解析JSON
                    data = response.json()
                    print(f"响应包含 {len(data.get('result', {}).get('tools', []))} 个工具")
                except Exception as e:
                    print(f"解析响应失败: {e}")
            else:
                print(f"测试失败: {response.text}")
        except Exception as e:
            print(f"请求失败: {e}")

def main():
    """主函数"""
    args = parse_args()
    test_headers(args.host, args.port)

if __name__ == "__main__":
    main()
