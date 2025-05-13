#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据工具模块

提供K线数据相关的MCP工具
"""

import logging
from typing import Optional
from mcp.server.fastmcp import FastMCP

from utils.chart_generator import generate_html, open_in_browser
from utils.kline_utils import fetch_and_save_kline

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
        from_date: 开始日期，格式为YYYY-MM-DD，默认为一年前
        to_date: 结束日期，格式为YYYY-MM-DD，默认为当前日期
        fq: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权），默认为 "post"
        fq_date: 复权基准日期，格式为YYYY-MM-DD，默认与to_date相同
        category: 品种类别，默认为 "stock"（股票），可选值包括 "stock"（股票）, "index"（指数）, "fund"（基金）等
        skip_paused: 是否跳过停牌日期，默认为 False
        generate_chart: 是否生成K线图表并在浏览器中显示，默认为 False

    Returns:
        str: 格式化的K线数据信息，或错误信息
    """
    try:
        # 从utils模块获取并保存K线数据
        success, result, file_path = fetch_and_save_kline(
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            from_date=from_date,
            to_date=to_date,
            fq=fq,
            fq_date=fq_date,
            category=category,
            skip_paused=skip_paused,
            output_dir="data/klines",
            file_format="csv"
        )

        if not success:
            return result  # 返回错误信息

        # 获取DataFrame
        df = result

        # 格式化输出
        result_str = f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录\n\n"

        # 显示所有数据
        result_str += "所有数据:\n"
        result_str += df.to_string() + "\n"

        # 添加保存信息
        result_str += f"\n数据已保存到: {file_path}"

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
                    result_str += f"\n\nK线图表已生成并在浏览器中打开: {chart_file}"
                else:
                    result_str += "\n\n生成K线图表失败"
            except Exception as e:
                logger.error(f"生成K线图表时发生错误: {e}")
                result_str += f"\n\n生成K线图表时发生错误: {e}"

        return result_str

    except Exception as e:
        logger.error(f"获取K线数据时发生错误: {e}")
        return f"获取K线数据时发生错误: {e}"





def register_tools(mcp: FastMCP):
    """
    注册K线数据相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册获取K线数据工具
    mcp.tool()(get_kline_data)
