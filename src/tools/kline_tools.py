#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据工具模块

提供K线数据相关的MCP工具
"""

import os
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP

from utils.auth_utils import load_auth_config
from utils.api_client import get_kline_data_from_api
from utils.chart_generator import generate_html, open_in_browser

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_tools')


async def get_kline_data(
    symbol: str, 
    exchange: str, 
    resolution: str = "1D",
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None,
    fq: str = "post", 
    fq_date: Optional[str] = None,
    category: str = "stock", 
    skip_paused: bool = False,
    generate_chart: bool = False
) -> str:
    """
    获取股票历史K线数据

    Args:
        symbol: 股票代码，例如 "600000"
        exchange: 交易所代码，例如 "XSHG"
        resolution: 时间周期，例如 "1D"（日线）, "1"（1分钟）
        from_date: 开始日期，格式为YYYY-MM-DD，默认为30天前
        to_date: 结束日期，格式为YYYY-MM-DD，默认为当前日期
        fq: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
        fq_date: 复权基准日期，格式为YYYY-MM-DD，默认为当前日期
        category: 品种类别，默认为 "stock"（股票），可选值包括 "stock"（股票）, "index"（指数）, "fund"（基金）等
        skip_paused: 是否跳过停牌日期，默认为 False
        generate_chart: 是否生成K线图表并在浏览器中显示，默认为 False

    Returns:
        str: 格式化的K线数据信息，或错误信息
    """
    # 加载认证配置
    if not load_auth_config():
        return "错误: 无法加载认证配置"

    if not symbol or not exchange:
        return "错误: 股票代码和交易所代码不能为空"

    try:
        # 从API获取数据
        data = get_kline_data_from_api(
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            from_date=from_date,
            to_date=to_date,
            fq=fq,
            fq_date=fq_date,
            category=category,
            skip_paused=skip_paused
        )

        if data.get('code') == 1 and data.get('msg') == 'ok':
            kline_data = data.get('data', [])
            logger.info(f"获取K线数据成功，数据条数: {len(kline_data)}")

            # 转换为DataFrame
            if kline_data:
                df = pd.DataFrame(kline_data)

                # 转换时间戳为日期时间
                df['time'] = pd.to_datetime(df['time'], unit='ms')

                # 按时间排序
                df = df.sort_values('time')

                # 格式化输出
                result = f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录\n\n"

                # 显示前5条和后5条数据
                if len(df) > 10:
                    result += "前5条数据:\n"
                    result += df.head(5).to_string() + "\n\n"
                    result += "后5条数据:\n"
                    result += df.tail(5).to_string() + "\n"
                else:
                    result += "数据:\n"
                    result += df.to_string() + "\n"

                # 保存数据到临时文件，方便后续使用
                temp_dir = 'data/temp'
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"{symbol}_{exchange}_{resolution}_temp.csv")
                df.to_csv(temp_file, index=False)
                result += f"\n数据已临时保存到: {temp_file}"

                # 如果需要生成图表
                if generate_chart:
                    try:
                        # 生成图表
                        chart_file = generate_html(
                            df=df,
                            symbol=symbol,
                            exchange=exchange,
                            resolution=resolution,
                            fq=fq
                        )

                        # 在浏览器中打开图表
                        if chart_file:
                            open_in_browser(chart_file)
                            result += f"\n\nK线图表已生成并在浏览器中打开: {chart_file}"
                        else:
                            result += "\n\n生成K线图表失败"
                    except Exception as e:
                        logger.error(f"生成K线图表时发生错误: {e}")
                        result += f"\n\n生成K线图表时发生错误: {e}"

                return result
            else:
                return f"获取K线数据成功，但数据为空"
        else:
            return f"获取K线数据失败: {data.get('msg', '未知错误')}"

    except Exception as e:
        logger.error(f"获取K线数据时发生错误: {e}")
        return f"获取K线数据时发生错误: {e}"


async def save_kline_data(
    symbol: str, 
    exchange: str, 
    resolution: str = "1D",
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None,
    fq: str = "post", 
    output_dir: str = "data/klines",
    file_format: str = "csv"
) -> str:
    """
    获取并保存K线数据到文件

    Args:
        symbol: 股票代码，例如 "600000"
        exchange: 交易所代码，例如 "XSHG"
        resolution: 时间周期，例如 "1D"（日线）, "1"（1分钟）
        from_date: 开始日期，格式为YYYY-MM-DD，默认为30天前
        to_date: 结束日期，格式为YYYY-MM-DD，默认为当前日期
        fq: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
        output_dir: 输出目录，默认为"data/klines"
        file_format: 文件格式，支持"csv"和"excel"，默认为"csv"

    Returns:
        str: 操作结果信息
    """
    # 加载认证配置
    if not load_auth_config():
        return "错误: 无法加载认证配置"

    if not symbol or not exchange:
        return "错误: 股票代码和交易所代码不能为空"

    try:
        # 从API获取数据
        data = get_kline_data_from_api(
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            from_date=from_date,
            to_date=to_date,
            fq=fq
        )

        if data.get('code') == 1 and data.get('msg') == 'ok':
            kline_data = data.get('data', [])
            logger.info(f"获取K线数据成功，数据条数: {len(kline_data)}")

            # 转换为DataFrame
            if kline_data:
                df = pd.DataFrame(kline_data)

                # 转换时间戳为日期时间
                df['time'] = pd.to_datetime(df['time'], unit='ms')

                # 按时间排序
                df = df.sort_values('time')

                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)

                # 生成文件名
                file_name = f"{symbol}_{exchange}_{resolution}_{fq}"
                
                # 保存文件
                if file_format.lower() == 'csv':
                    file_path = os.path.join(output_dir, f"{file_name}.csv")
                    df.to_csv(file_path, index=False)
                elif file_format.lower() == 'excel':
                    file_path = os.path.join(output_dir, f"{file_name}.xlsx")
                    df.to_excel(file_path, index=False)
                else:
                    return f"错误: 不支持的文件格式: {file_format}，支持的格式有: csv, excel"

                return f"成功保存 {symbol} 的K线数据到文件: {file_path}，共 {len(df)} 条记录"
            else:
                return f"获取K线数据成功，但数据为空，未保存文件"
        else:
            return f"获取K线数据失败: {data.get('msg', '未知错误')}"

    except Exception as e:
        logger.error(f"保存K线数据时发生错误: {e}")
        return f"保存K线数据时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册K线数据相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册获取K线数据工具
    mcp.tool()(get_kline_data)
    
    # 注册保存K线数据工具
    mcp.tool()(save_kline_data)
