#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP客户端测试脚本

用于测试部署后的MCP服务，获取K线图和回测结果
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
    parser = argparse.ArgumentParser(description='MCP客户端测试脚本')
    parser.add_argument('--host', type=str, default='localhost', help='MCP服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='MCP服务器端口')
    parser.add_argument('--action', type=str, choices=['kline', 'backtest'], required=True, help='要执行的操作')
    parser.add_argument('--symbol', type=str, help='股票代码，例如 600000')
    parser.add_argument('--exchange', type=str, help='交易所代码，例如 XSHG')
    parser.add_argument('--resolution', type=str, default='1D', help='时间周期，例如 1D')
    parser.add_argument('--strategy-id', type=str, help='策略ID')
    return parser.parse_args()

def send_mcp_request(host: str, port: int, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送MCP请求

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
        tool_name: 工具名称
        params: 工具参数

    Returns:
        Dict[str, Any]: MCP响应
    """
    url = f"http://{host}:{port}/mcp/"

    # 构建请求体
    request_body = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "execute_tool",
        "params": {
            "tool_name": tool_name,
            "tool_params": params
        }
    }

    # 设置请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }

    # 发送请求
    response = requests.post(url, json=request_body, headers=headers)

    # 检查响应状态码
    if response.status_code != 200:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return {"error": f"请求失败，状态码: {response.status_code}"}

    # 解析响应
    try:
        return response.json()
    except Exception as e:
        print(f"解析响应JSON失败: {e}")
        print(f"响应内容: {response.text}")
        return {"error": f"解析响应JSON失败: {e}"}

def get_kline(host: str, port: int, symbol: str, exchange: str, resolution: str = "1D") -> Optional[str]:
    """
    获取K线图

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
        symbol: 股票代码
        exchange: 交易所代码
        resolution: 时间周期

    Returns:
        Optional[str]: K线图URL
    """
    # 构建参数
    params = {
        "symbol": symbol,
        "exchange": exchange,
        "resolution": resolution,
        "http_mode": True
    }

    # 发送请求
    response = send_mcp_request(host, port, "get_kline_data", params)

    # 检查响应
    if "error" in response:
        print(f"获取K线图失败: {response['error']}")
        return None

    # 解析响应
    result = response.get("result", {}).get("result", "")

    # 提取URL
    import re
    url_match = re.search(r"http://[^\s]+\.html", result)
    if url_match:
        return url_match.group(0)
    else:
        print("无法从响应中提取URL")
        print(f"响应内容: {result}")
        return None

def run_backtest(host: str, port: int, strategy_id: str) -> Optional[str]:
    """
    运行回测

    Args:
        host: MCP服务器主机地址
        port: MCP服务器端口
        strategy_id: 策略ID

    Returns:
        Optional[str]: 回测结果URL
    """
    # 构建参数
    params = {
        "strategy_id": strategy_id,
        "http_mode": True
    }

    # 发送请求
    response = send_mcp_request(host, port, "run_strategy_backtest", params)

    # 检查响应
    if "error" in response:
        print(f"运行回测失败: {response['error']}")
        return None

    # 解析响应
    result = response.get("result", {}).get("result", "")

    # 提取URL
    import re
    url_match = re.search(r"http://[^\s]+\.html", result)
    if url_match:
        return url_match.group(0)
    else:
        print("无法从响应中提取URL")
        print(f"响应内容: {result}")
        return None

def main():
    """主函数"""
    args = parse_args()

    if args.action == "kline":
        if not args.symbol or not args.exchange:
            print("获取K线图需要提供股票代码和交易所代码")
            return

        url = get_kline(args.host, args.port, args.symbol, args.exchange, args.resolution)
        if url:
            print(f"K线图URL: {url}")
    elif args.action == "backtest":
        if not args.strategy_id:
            print("运行回测需要提供策略ID")
            return

        url = run_backtest(args.host, args.port, args.strategy_id)
        if url:
            print(f"回测结果URL: {url}")

if __name__ == "__main__":
    main()
