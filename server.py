#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP服务器入口
启动MCP服务器，注册工具、资源、提示模板和采样配置
"""

import sys
import logging
import os
import argparse
from mcp.server.fastmcp import FastMCP

from utils.logging_utils import setup_logging
from src.utils.prompt_utils import patch_fastmcp
from src.tools import register_all_tools
from src.resources import register_all_resources
from src.prompts import register_all_prompts
from src.sampling import register_all_sampling

# 解析命令行参数
parser = argparse.ArgumentParser(description='启动量化交易助手MCP服务器')
parser.add_argument('--transport', type=str, choices=['stdio', 'http', 'sse', 'streamable-http'], default='stdio',
                    help='传输协议 (默认: stdio)')
parser.add_argument('--log-level', type=str, choices=['debug', 'info', 'warning', 'error', 'critical'],
                    default='info', help='日志级别 (默认: info)')

args = parser.parse_args()

# 设置日志级别
log_level_map = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}
log_level = log_level_map.get(args.log_level.lower(), logging.INFO)

# 设置日志
logger = setup_logging('quant_mcp.server', log_level=log_level)

def create_server(name: str = "量化交易助手") -> FastMCP:
    """
    创建MCP服务器

    Args:
        name: 服务器名称

    Returns:
        FastMCP: MCP服务器实例
    """
    # 为FastMCP类添加update_prompt_metadata方法
    patch_fastmcp()

    # 创建FastMCP服务器实例
    mcp = FastMCP(name)

    # 注册所有MCP组件
    register_all_tools(mcp)      # 注册工具
    register_all_resources(mcp)  # 注册资源
    register_all_prompts(mcp)    # 注册提示模板
    register_all_sampling(mcp)   # 注册采样配置

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
        os.makedirs('data/backtest', exist_ok=True)
        os.makedirs('data/templates', exist_ok=True)

        # 检查配置文件
        if not os.path.exists('data/config/auth.json'):
            logger.warning("认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息")
            print("警告: 认证配置文件不存在，请复制 data/config/auth.json.example 并填写认证信息", file=sys.stderr)

        # 创建服务器
        mcp = create_server()

        # 启动服务器
        if transport == 'http':
            # FastMCP不直接支持HTTP传输，使用streamable-http代替
            logger.info(f"启动MCP服务器，使用streamable-http传输协议")
            print(f"启动量化交易助手MCP服务器，使用streamable-http传输协议")
            mcp.run(transport='streamable-http')
        else:
            logger.info(f"启动MCP服务器，使用 {transport} 传输协议")
            print(f"启动量化交易助手MCP服务器，使用 {transport} 传输协议")
            mcp.run(transport=transport)
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        print(f"错误: 启动MCP服务器失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 运行服务器
    run_server(transport=args.transport)
