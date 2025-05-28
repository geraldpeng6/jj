#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MCP服务器入口
启动MCP服务器，注册工具、资源、提示模板和采样配置
"""

import sys
import logging
import os
import inspect
from mcp.server.fastmcp import FastMCP

from utils.logging_utils import setup_logging
from utils.html_server import generate_test_html, is_nginx_available
from src.tools import register_all_tools
from src.resources import register_all_resources
from src.prompts import register_all_prompts
from src.sampling import register_all_sampling

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

    # 注册所有MCP组件
    register_all_tools(mcp)      # 注册工具
    register_all_resources(mcp)  # 注册资源
    register_all_prompts(mcp)    # 注册提示模板
    register_all_sampling(mcp)   # 注册采样配置

    return mcp

def run_server(transport: str = 'stdio', host: str = '0.0.0.0', port: int = 8000, timeout: int = 300):
    """
    运行MCP服务器

    Args:
        transport: 传输协议，默认为stdio，支持 'stdio', 'sse', 'streamable-http'
        host: 主机地址，当使用 'sse' 或 'streamable-http' 传输协议时有效
        port: 端口号，当使用 'sse' 或 'streamable-http' 传输协议时有效
        timeout: 服务器超时时间（秒），默认300秒（5分钟）
    """
    try:
        # 设置环境变量，确保主机绑定为0.0.0.0
        os.environ['MCP_SERVER_HOST'] = host
        os.environ['MCP_SSE_HOST'] = host
        os.environ['MCP_HTTP_HOST'] = host
        
        # 设置Uvicorn超时
        os.environ['UVICORN_TIMEOUT_KEEP_ALIVE'] = str(timeout)
        
        # 设置MCP超时
        os.environ['MCP_REQUEST_TIMEOUT'] = str(timeout)
        
        # 设置更详细的日志
        logger.info(f"服务器配置: 传输协议={transport}, 主机={host}, 端口={port}, 超时={timeout}秒")
        logger.info(f"环境变量: MCP_SERVER_HOST={os.environ.get('MCP_SERVER_HOST')}, "
                   f"MCP_SSE_HOST={os.environ.get('MCP_SSE_HOST')}, "
                   f"MCP_HTTP_HOST={os.environ.get('MCP_HTTP_HOST')}")

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

        # 生成测试HTML文件
        try:
            test_url = generate_test_html()
            if test_url:
                logger.info(f"测试HTML文件已生成，URL: {test_url}")
                print(f"测试HTML文件已生成，URL: {test_url}")

                # 检查Nginx是否可用
                if is_nginx_available():
                    logger.info("检测到Nginx已安装，HTML文件可通过Web服务器访问")
                    print("检测到Nginx已安装，HTML文件可通过Web服务器访问")
                else:
                    logger.warning("未检测到Nginx，HTML文件将通过本地文件URL访问")
                    print("警告: 未检测到Nginx，HTML文件将通过本地文件URL访问", file=sys.stderr)
            else:
                logger.warning("生成测试HTML文件失败")
                print("警告: 生成测试HTML文件失败", file=sys.stderr)
        except Exception as e:
            logger.error(f"生成测试HTML文件时发生错误: {e}")
            print(f"错误: 生成测试HTML文件时发生错误: {e}", file=sys.stderr)

        # 创建服务器
        mcp = create_server()

        # 启动服务器
        logger.info(f"启动MCP服务器，使用 {transport} 传输协议")
        print(f"启动量化交易助手MCP服务器，使用 {transport} 传输协议")

        # 根据传输协议选择不同的启动方式
        if transport == 'stdio':
            mcp.run(transport=transport)
        elif transport == 'sse':
            print(f"SSE服务器将在 http://{host}:{port}/sse 上运行，超时时间: {timeout}秒")
            logger.info(f"SSE服务器将在 http://{host}:{port}/sse 上运行，超时时间: {timeout}秒")

            run_params = inspect.signature(mcp.run).parameters
            print(f"Debug - Host: {host}, Port: {port}, Env MCP_SSE_HOST: {os.environ.get('MCP_SSE_HOST')}")
            logger.info(f"Debug - Host: {host}, Port: {port}, Env MCP_SSE_HOST: {os.environ.get('MCP_SSE_HOST')}")

            if 'host' in run_params and 'port' in run_params:
                print(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port})")
                logger.info(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port})")
                if 'timeout' in run_params:
                    mcp.run(transport=transport, host=host, port=port, timeout=timeout)
                else:
                    mcp.run(transport=transport, host=host, port=port)
            else:
                print(f"使用旧版本API: mcp.run(transport='{transport}')")
                logger.info(f"使用旧版本API: mcp.run(transport='{transport}')")
                os.environ['MCP_SSE_HOST'] = host
                os.environ['MCP_SSE_PORT'] = str(port)
                mcp.run(transport=transport)

        elif transport == 'streamable-http':
            print(f"Streamable HTTP服务器将在 http://{host}:{port}/mcp 上运行，超时时间: {timeout}秒")
            logger.info(f"Streamable HTTP服务器将在 http://{host}:{port}/mcp 上运行，超时时间: {timeout}秒")

            run_params = inspect.signature(mcp.run).parameters
            print(f"Debug - Host: {host}, Port: {port}, Env MCP_HTTP_HOST: {os.environ.get('MCP_HTTP_HOST')}")
            logger.info(f"Debug - Host: {host}, Port: {port}, Env MCP_HTTP_HOST: {os.environ.get('MCP_HTTP_HOST')}")

            if 'host' in run_params and 'port' in run_params and 'path' in run_params:
                print(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port}, path='/mcp')")
                logger.info(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port}, path='/mcp')")
                if 'timeout' in run_params:
                    mcp.run(transport=transport, host=host, port=port, path='/mcp', timeout=timeout)
                else:
                    mcp.run(transport=transport, host=host, port=port, path='/mcp')
            else:
                print(f"使用旧版本API: mcp.run(transport='{transport}')")
                logger.info(f"使用旧版本API: mcp.run(transport='{transport}')")
                os.environ['MCP_HTTP_HOST'] = host
                os.environ['MCP_HTTP_PORT'] = str(port)
                os.environ['MCP_HTTP_PATH'] = '/mcp'
                mcp.run(transport=transport)
        else:
            raise ValueError(f"不支持的传输协议: {transport}")
    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        print(f"错误: 启动MCP服务器失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='启动MCP服务器')
    parser.add_argument('--transport', '-t', type=str, default='stdio',
                        choices=['stdio', 'sse', 'streamable-http'],
                        help='传输协议 (stdio, sse, streamable-http)')
    parser.add_argument('--host', '-H', type=str, default='0.0.0.0',
                        help='主机地址，当使用 sse 或 streamable-http 传输协议时有效')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='端口号，当使用 sse 或 streamable-http 传输协议时有效')
    parser.add_argument('--timeout', '-T', type=int, default=300,
                        help='服务器超时时间（秒），默认300秒（5分钟）')

    args = parser.parse_args()
    run_server(transport=args.transport, host=args.host, port=args.port, timeout=args.timeout)
