#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP服务器入口
启动MCP服务器，注册工具、资源、提示模板和采样配置
支持stdio和streamable_http传输协议
"""

import sys
import logging
import os
import argparse
from mcp.server.fastmcp import FastMCP

from utils.logging_utils import setup_logging
from src.tools import register_all_tools
from src.resources import register_all_resources
from src.prompts import register_all_prompts
from src.sampling import register_all_sampling

# 设置日志
logger = setup_logging('quant_mcp.server')

def create_server(name: str = "量化交易助手", stateless_http: bool = False) -> FastMCP:
    """
    创建MCP服务器

    Args:
        name: 服务器名称
        stateless_http: 是否使用无状态HTTP模式（适用于云服务器部署）

    Returns:
        FastMCP: MCP服务器实例
    """
    # 创建FastMCP服务器实例
    # 对于云服务器部署，建议使用stateless_http=True以提高可扩展性
    mcp = FastMCP(name, stateless_http=stateless_http)

    # 注册所有MCP组件
    register_all_tools(mcp)      # 注册工具
    register_all_resources(mcp)  # 注册资源
    register_all_prompts(mcp)    # 注册提示模板
    register_all_sampling(mcp)   # 注册采样配置

    if stateless_http:
        logger.info("将使用无状态HTTP模式")

    return mcp

def run_server(transport: str = 'stdio', host: str = '0.0.0.0', port: int = 8000, stateless: bool = False):
    """
    运行MCP服务器

    Args:
        transport: 传输协议，可选 'stdio', 'streamable-http'
        host: HTTP服务器主机地址，默认为0.0.0.0（所有网络接口）
        port: HTTP服务器端口，默认为8000
        stateless: 是否使用无状态HTTP模式，适用于云服务器部署
    """
    try:
        # 确保必要的目录存在
        os.makedirs('data/logs', exist_ok=True)
        os.makedirs('data/klines', exist_ok=True)
        os.makedirs('data/charts', exist_ok=True)
        os.makedirs('data/temp', exist_ok=True)
        os.makedirs('data/config', exist_ok=True)
        os.makedirs('data/backtest', exist_ok=True)
        os.makedirs('data/templates', exist_ok=True)

        # 检查配置文件
        if not os.path.exists('data/config/auth.json'):
            logger.warning("认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息")
            print("警告: 认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息", file=sys.stderr)

        # 创建服务器
        mcp = create_server(stateless_http=stateless)

        # 启动服务器
        logger.info(f"启动MCP服务器，使用 {transport} 传输协议")
        print(f"启动量化交易助手MCP服务器，使用 {transport} 传输协议")

        if transport == 'streamable-http':
            # 对于streamable-http传输协议，需要设置主机和端口
            logger.info(f"HTTP服务器监听地址: {host}:{port}")
            print(f"HTTP服务器监听地址: {host}:{port}")
            # 设置服务器主机和端口
            mcp.settings.host = host
            mcp.settings.port = port

            # 如果使用streamable-http传输协议，直接使用MCP的streamable_http_app
            if stateless:
                logger.info("使用MCP内置的streamable_http服务器")
                print("使用MCP内置的streamable_http服务器")
                print("注意: 可以使用http_mode=True参数来获取HTML内容")

        # 运行服务器
        mcp.run(transport=transport)
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        print(f"错误: 启动MCP服务器失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='量化交易助手MCP服务器')
    parser.add_argument('--transport', '-t', type=str, default='stdio',
                        choices=['stdio', 'streamable-http'],
                        help='传输协议: stdio或streamable-http')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='HTTP服务器主机地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='HTTP服务器端口 (默认: 8000)')
    parser.add_argument('--stateless', action='store_true',
                        help='使用无状态HTTP模式 (推荐用于云服务器部署)')

    args = parser.parse_args()

    # 运行服务器
    run_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        stateless=args.stateless
    )
