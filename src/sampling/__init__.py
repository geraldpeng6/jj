#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
采样模块初始化文件

导入并注册所有采样配置
"""

import logging
from mcp.server.fastmcp import FastMCP

# 获取日志记录器
logger = logging.getLogger('quant_mcp.sampling')

def register_all_sampling(mcp: FastMCP):
    """
    注册所有采样配置到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 导入采样路由模块
    from src.sampling.sampling_routes import register_sampling_routes

    # 注册采样路由
    register_sampling_routes(mcp)

    logger.info("已注册所有采样配置")
