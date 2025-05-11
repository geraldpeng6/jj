#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP服务器入口
启动MCP服务器，注册工具
"""

import sys
import logging
import os
from mcp.server.fastmcp import FastMCP

from utils.logging_utils import setup_logging
from src.tools.kline_tools import register_tools as register_kline_tools
from src.tools.symbol_tools import register_tools as register_symbol_tools
from src.tools.strategy_tools import register_tools as register_strategy_tools
from src.tools.backtest_tools import register_tools as register_backtest_tools

# 设置日志
logger = setup_logging('quant_mcp.server')

def create_server(name: str = "量化交易助手") -> FastMCP:
    """
    创建MCP服务器

    Args:
        name: 服务器名称

    Returns:
        FastMCP: MCP服务器实例
    """
    # 创建FastMCP服务器实例
    mcp = FastMCP(name)

    # 注册工具
    register_kline_tools(mcp)
    register_symbol_tools(mcp)
    register_strategy_tools(mcp)
    register_backtest_tools(mcp)

    return mcp

def run_server(transport: str = 'stdio'):
    """
    运行MCP服务器

    Args:
        transport: 传输协议，默认为stdio
    """
    try:
        # 确保必要的目录存在
        os.makedirs('data/logs', exist_ok=True)
        os.makedirs('data/klines', exist_ok=True)
        os.makedirs('data/charts', exist_ok=True)
        os.makedirs('data/temp', exist_ok=True)
        os.makedirs('data/config', exist_ok=True)
        os.makedirs('data/strategy', exist_ok=True)
        os.makedirs('data/backtest', exist_ok=True)
        os.makedirs('data/templates', exist_ok=True)

        # 检查配置文件
        if not os.path.exists('data/config/auth.json'):
            logger.warning("认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息")
            print("警告: 认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息", file=sys.stderr)

        # 创建服务器
        mcp = create_server()

        # 启动服务器
        logger.info(f"启动MCP服务器，使用 {transport} 传输协议")
        print(f"启动量化交易助手MCP服务器，使用 {transport} 传输协议")
        mcp.run(transport=transport)
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        print(f"错误: 启动MCP服务器失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 从命令行参数获取传输协议
    transport = 'stdio'
    if len(sys.argv) > 1:
        transport = sys.argv[1]

    # 运行服务器
    run_server(transport)
