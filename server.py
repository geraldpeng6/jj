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

# 修补FastMCP的绑定地址
def patch_fastmcp_binding():
    """
    修补FastMCP的网络绑定行为，强制使用0.0.0.0
    """
    try:
        import mcp.server.fastmcp
        import mcp.server.sse
        import mcp.server.http
        
        # 保存原始函数
        original_run = mcp.server.fastmcp.FastMCP.run
        
        # 定义新的run函数
        def patched_run(self, transport='stdio', host='0.0.0.0', port=8000, path='/mcp'):
            logger.info(f"修补的FastMCP.run被调用: transport={transport}, host={host}, port={port}")
            print(f"修补的FastMCP.run被调用: transport={transport}, host={host}, port={port}")
            
            # 强制修改SSE服务器的host_binding
            if hasattr(mcp.server.sse, 'SSEServer'):
                original_init = mcp.server.sse.SSEServer.__init__
                def patched_init(self, *args, **kwargs):
                    if len(args) >= 2:
                        # 第一个参数是self，第二个参数是host
                        args_list = list(args)
                        args_list[1] = '0.0.0.0'
                        args = tuple(args_list)
                    kwargs['host'] = '0.0.0.0'
                    logger.info(f"修补SSE服务器绑定地址为0.0.0.0")
                    print(f"修补SSE服务器绑定地址为0.0.0.0")
                    return original_init(self, *args, **kwargs)
                mcp.server.sse.SSEServer.__init__ = patched_init
            
            # 直接修改uvicorn的host参数
            try:
                import uvicorn
                original_uvicorn_run = uvicorn.run
                def patched_uvicorn_run(*args, **kwargs):
                    kwargs['host'] = '0.0.0.0'
                    logger.info(f"修补uvicorn绑定地址为0.0.0.0")
                    print(f"修补uvicorn绑定地址为0.0.0.0")
                    return original_uvicorn_run(*args, **kwargs)
                uvicorn.run = patched_uvicorn_run
            except Exception as e:
                logger.error(f"修补uvicorn失败: {e}")
                print(f"修补uvicorn失败: {e}", file=sys.stderr)
            
            # 调用原始函数
            return original_run(self, transport=transport, host=host, port=port, path=path)
        
        # 替换原始函数
        mcp.server.fastmcp.FastMCP.run = patched_run
        
        # 如果有HTTP服务器，也进行修补
        if hasattr(mcp.server.http, 'HTTPServer'):
            original_http_init = mcp.server.http.HTTPServer.__init__
            def patched_http_init(self, *args, **kwargs):
                if len(args) >= 2:
                    # 第一个参数是self，第二个参数是host
                    args_list = list(args)
                    args_list[1] = '0.0.0.0'
                    args = tuple(args_list)
                kwargs['host'] = '0.0.0.0'
                logger.info(f"修补HTTP服务器绑定地址为0.0.0.0")
                print(f"修补HTTP服务器绑定地址为0.0.0.0")
                return original_http_init(self, *args, **kwargs)
            mcp.server.http.HTTPServer.__init__ = patched_http_init
        
        logger.info("成功修补FastMCP的网络绑定行为")
        print("成功修补FastMCP的网络绑定行为")
        
    except Exception as e:
        logger.error(f"修补FastMCP失败: {e}")
        print(f"修补FastMCP失败: {e}", file=sys.stderr)

# 在导入其他MCP相关模块之前修补FastMCP
patch_fastmcp_binding()

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

def run_server(transport: str = 'stdio', host: str = '0.0.0.0', port: int = 8000):
    """
    运行MCP服务器

    Args:
        transport: 传输协议，默认为stdio，支持 'stdio', 'sse', 'streamable-http'
        host: 主机地址，当使用 'sse' 或 'streamable-http' 传输协议时有效
        port: 端口号，当使用 'sse' 或 'streamable-http' 传输协议时有效
    """
    try:
        # 强制设置环境变量，确保绑定到0.0.0.0
        os.environ['MCP_SERVER_HOST'] = '0.0.0.0'
        os.environ['MCP_SSE_HOST'] = '0.0.0.0'
        os.environ['MCP_HTTP_HOST'] = '0.0.0.0'
        
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
            print(f"SSE服务器将在 http://{host}:{port}/sse 上运行")
            logger.info(f"SSE服务器将在 http://{host}:{port}/sse 上运行")

            # 检查MCP版本，不同版本的API可能不同
            run_params = inspect.signature(mcp.run).parameters

            # 打印调试信息
            print(f"Debug - Host: {host}, Port: {port}, Env MCP_SSE_HOST: {os.environ.get('MCP_SSE_HOST')}")
            logger.info(f"Debug - Host: {host}, Port: {port}, Env MCP_SSE_HOST: {os.environ.get('MCP_SSE_HOST')}")

            if 'host' in run_params and 'port' in run_params:
                # 新版本API
                print(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port})")
                logger.info(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port})")
                mcp.run(transport=transport, host=host, port=port)
            else:
                # 旧版本API，需要设置环境变量
                print(f"使用旧版本API: mcp.run(transport='{transport}')")
                logger.info(f"使用旧版本API: mcp.run(transport='{transport}')")
                os.environ['MCP_SSE_HOST'] = host
                os.environ['MCP_SSE_PORT'] = str(port)
                mcp.run(transport=transport)

        elif transport == 'streamable-http':
            print(f"Streamable HTTP服务器将在 http://{host}:{port}/mcp 上运行")
            logger.info(f"Streamable HTTP服务器将在 http://{host}:{port}/mcp 上运行")

            # 检查MCP版本，不同版本的API可能不同
            run_params = inspect.signature(mcp.run).parameters

            # 打印调试信息
            print(f"Debug - Host: {host}, Port: {port}, Env MCP_HTTP_HOST: {os.environ.get('MCP_HTTP_HOST')}")
            logger.info(f"Debug - Host: {host}, Port: {port}, Env MCP_HTTP_HOST: {os.environ.get('MCP_HTTP_HOST')}")

            if 'host' in run_params and 'port' in run_params and 'path' in run_params:
                # 新版本API
                print(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port}, path='/mcp')")
                logger.info(f"使用新版本API: mcp.run(transport='{transport}', host='{host}', port={port}, path='/mcp')")
                mcp.run(transport=transport, host=host, port=port, path='/mcp')
            else:
                # 旧版本API，需要设置环境变量
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

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='启动MCP服务器')
    parser.add_argument('--transport', '-t', type=str, default='stdio',
                        choices=['stdio', 'sse', 'streamable-http'],
                        help='传输协议 (stdio, sse, streamable-http)')
    parser.add_argument('--host', '-H', type=str, default='0.0.0.0',
                        help='主机地址，当使用 sse 或 streamable-http 传输协议时有效')
    parser.add_argument('--port', '-p', type=int, default=8000,
                        help='端口号，当使用 sse 或 streamable-http 传输协议时有效')

    # 解析命令行参数
    args = parser.parse_args()

    # 运行服务器
    run_server(transport=args.transport, host=args.host, port=args.port)
