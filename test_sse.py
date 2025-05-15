#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SSE模式测试脚本

用于测试MCP服务器的SSE模式配置是否正确
"""

import os
import sys
import json
import time
import argparse
import requests
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MCP SSE模式测试脚本')
    parser.add_argument('--host', type=str, default='localhost', help='MCP服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='MCP服务器端口')
    return parser.parse_args()

def test_sse_mode(host: str, port: int) -> None:
    """
    测试MCP服务器的SSE模式配置

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
    """
    url = f"http://{host}:{port}/mcp/"

    # 测试不同的Accept头部
    test_cases = [
        {
            "name": "SSE模式",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
        },
        {
            "name": "混合模式",
            "headers": {
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json"
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
            response = requests.post(url, json=request_body, headers=test_case['headers'], stream=True)
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"内容类型: {content_type}")

                if 'text/event-stream' in content_type:
                    print("SSE模式配置正确!")
                    # 读取事件流
                    try:
                        for line in response.iter_lines():
                            if line:
                                decoded_line = line.decode('utf-8')
                                print(f"事件数据: {decoded_line}")
                                # 如果收到完整的事件，就退出
                                if decoded_line.startswith('data: {"jsonrpc"'):
                                    break
                    except Exception as e:
                        print(f"读取事件流失败: {e}")
                else:
                    print("警告: 响应不是SSE格式")
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

def test_http_mode(host: str, port: int) -> None:
    """
    测试MCP服务器的HTTP模式配置

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
    """
    url = f"http://{host}:{port}/mcp/"

    # 构建请求体 - 使用K线工具
    request_body = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "execute_tool",
        "params": {
            "tool_name": "get_kline_data",
            "tool_params": {
                "symbol": "600000",
                "exchange": "XSHG",
                "resolution": "1D",
                "http_mode": True
            }
        }
    }

    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    print("\n测试: HTTP模式")
    print(f"请求头: {headers}")

    try:
        response = requests.post(url, json=request_body, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            try:
                # 尝试解析JSON
                data = response.json()
                result = data.get('result', {}).get('result', '')
                print(f"响应结果: {result[:200]}...")  # 只显示前200个字符

                # 检查是否包含URL
                import re
                url_match = re.search(r"(http|file)://[^\s]+\.html", result)
                if url_match:
                    print(f"找到URL: {url_match.group(0)}")
                    print("HTTP模式配置正确!")
                else:
                    print("警告: 响应中没有找到URL")
            except Exception as e:
                print(f"解析响应失败: {e}")
        else:
            print(f"测试失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def main():
    """主函数"""
    args = parse_args()

    print("=== 测试MCP服务器的SSE模式配置 ===")
    test_sse_mode(args.host, args.port)

    print("\n=== 测试MCP服务器的HTTP模式配置 ===")
    test_http_mode(args.host, args.port)

if __name__ == "__main__":
    main()
