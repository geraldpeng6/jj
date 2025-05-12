#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据资源模块

提供K线数据相关的MCP资源
"""

import logging
import os
from typing import List, Dict, Any, Optional
import pandas as pd
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, ResourceContents

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_resources')

def register_resources(mcp: FastMCP):
    """
    注册K线数据相关的资源到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册K线数据目录中的所有CSV文件作为资源
    klines_dir = "data/klines"
    if os.path.exists(klines_dir):
        for filename in os.listdir(klines_dir):
            if filename.endswith(".csv"):
                # 从文件名解析信息
                parts = filename.replace(".csv", "").split("_")
                if len(parts) >= 3:
                    symbol = parts[0]
                    exchange = parts[1]
                    resolution = parts[2]

                    # 创建资源
                    uri = f"kline://{exchange}/{symbol}/{resolution}"
                    name = f"{symbol} {resolution} K线数据"

                    # 添加资源
                    mcp.add_resource(Resource(
                        uri=uri,
                        name=name,
                        description=f"{symbol} 在 {exchange} 的 {resolution} K线数据",
                        mimeType="text/csv"
                    ))

    # 注册资源模板 - 使用不同的方式注册模板
    # 不使用add_resource，而是直接在resource装饰器中处理

    # 注册读取K线数据的处理函数
    @mcp.resource("kline://{exchange}/{symbol}/{resolution}")
    async def read_kline_data(exchange: str, symbol: str, resolution: str) -> str:
        """读取K线数据资源内容"""
        try:
            # 构建文件路径
            file_path = f"data/klines/{symbol}_{exchange}_{resolution}.csv"

            if not os.path.exists(file_path):
                return f"找不到K线数据文件: {file_path}"

            # 读取CSV文件
            df = pd.read_csv(file_path)

            # 返回CSV内容
            return df.to_csv(index=False)

        except Exception as e:
            logger.error(f"读取K线资源时发生错误: {e}")
            return f"读取K线资源时发生错误: {e}"


