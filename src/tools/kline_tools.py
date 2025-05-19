#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据工具模块

提供K线数据相关的MCP工具
"""

import logging
import os
from typing import Optional, Dict, Any, Tuple
from mcp.server.fastmcp import FastMCP

from utils.chart_generator import generate_html, open_in_browser
from utils.kline_utils import fetch_and_save_kline
from utils.web_server import start_server, get_file_url, get_all_urls, diagnose_network

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





async def get_kline_data_with_url(
    symbol: str,
    exchange: str,
    resolution: str = "1D",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    fq: str = "post",
    fq_date: Optional[str] = None,
    category: str = "stock",
    skip_paused: bool = False
) -> str:
    """
    获取股票历史K线数据，同时返回CSV文件路径和HTML网址

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

    Returns:
        str: 格式化的K线数据信息，包含CSV文件路径和HTML网址，或错误信息
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

        # 生成图表
        chart_file = generate_html(
            df=df,
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            fq=fq
        )

        if not chart_file:
            return f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录，但生成图表失败\n\nCSV数据已保存到: {file_path}"

        # 启动Web服务器（如果尚未启动）
        port = start_server()
        if port is None:
            # 如果启动服务器失败，返回错误信息
            return f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录\n\n注意：启动Web服务器失败，无法提供网址访问"

        # 获取图表URL
        chart_url = get_file_url(chart_file)
        if chart_url is None:
            # 如果获取URL失败，返回错误信息
            return f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录\n\n注意：获取图表URL失败，无法提供网址访问"

        # 获取所有可能的URL
        urls = get_all_urls(chart_file)

        # 格式化输出
        result_str = f"成功获取 {symbol} 的K线数据，共 {len(df)} 条记录\n\n"
        result_str += "图表URL:\n"

        # 添加HTTPS URL（如果有）
        if urls.get("public_https"):
            result_str += f"- 公网访问 (HTTPS): {urls['public_https']}\n"
        if urls.get("local_https") and urls.get("local_https") != urls.get("public_https"):
            result_str += f"- 局域网访问 (HTTPS): {urls['local_https']}\n"
        if urls.get("localhost_https"):
            result_str += f"- 本地访问 (HTTPS): {urls['localhost_https']}\n"

        # 添加HTTP URL
        if urls.get("public_http"):
            result_str += f"- 公网访问 (HTTP): {urls['public_http']}\n"
        if urls.get("local_http") and urls.get("local_http") != urls.get("public_http"):
            result_str += f"- 局域网访问 (HTTP): {urls['local_http']}\n"
        result_str += f"- 本地访问 (HTTP): {urls['localhost_http']}\n\n"

        result_str += "您可以通过上述URL在浏览器中访问K线图表\n"
        result_str += "注意: \n"
        result_str += "1. 优先使用HTTPS URL，如果HTTPS不可用，再使用HTTP URL\n"
        result_str += "2. 如果Safari浏览器无法访问，请尝试使用Chrome或Firefox\n"
        result_str += "3. 如果公网URL无法访问，请尝试使用局域网或本地URL\n"
        result_str += "4. 首次访问HTTPS URL时，浏览器可能会显示安全警告，这是因为使用了自签名证书，请选择继续访问"

        return result_str

    except Exception as e:
        logger.error(f"获取K线数据时发生错误: {e}")
        return f"获取K线数据时发生错误: {e}"


async def diagnose_web_server() -> str:
    """
    诊断Web服务器状态

    Returns:
        str: 诊断结果
    """
    try:
        # 启动服务器（如果尚未启动）
        port = start_server(enable_https=True)
        if port is None:
            return "启动Web服务器失败，无法进行诊断"

        # 获取诊断结果
        result = diagnose_network()

        # 格式化输出
        output = "Web服务器诊断结果:\n\n"

        # 服务器状态
        output += f"服务器状态: {'运行中' if result['server_running'] else '未运行'}\n"
        output += f"本地IP: {result['local_ip']}\n"
        output += f"公网IP: {result['public_ip'] or '无法获取'}\n"
        output += f"HTTP端口: {result['http_port']} {'(标准端口)' if result['http_port'] == 80 else ''}\n"

        if result['https_enabled']:
            output += f"HTTPS端口: {result['https_port']} {'(标准端口)' if result['https_port'] == 443 else ''}\n"
            output += f"HTTPS状态: {'已启用' if result['https_enabled'] else '未启用'}\n"

        output += f"特权端口权限: {'有' if result['can_use_privileged_port'] else '无'}\n"

        # 端口状态
        output += "\n端口状态:\n"
        if 'http_port_open_local' in result:
            output += f"HTTP端口本地可访问: {'是' if result['http_port_open_local'] else '否'}\n"
        if 'http_port_open_public' in result:
            output += f"HTTP端口公网可访问: {'是' if result['http_port_open_public'] else '否'}\n"

        if result['https_enabled']:
            if 'https_port_open_local' in result:
                output += f"HTTPS端口本地可访问: {'是' if result['https_port_open_local'] else '否'}\n"
            if 'https_port_open_public' in result:
                output += f"HTTPS端口公网可访问: {'是' if result['https_port_open_public'] else '否'}\n"

        # 诊断建议
        if result['suggestions']:
            output += "\n诊断建议:\n"
            for i, suggestion in enumerate(result['suggestions'], 1):
                output += f"{i}. {suggestion}\n"

        # 如果公网访问存在问题，添加额外建议
        if not result.get('http_port_open_public', False) and not result.get('https_port_open_public', False):
            output += "\n要使服务器可以从公网访问，您可能需要:\n"
            output += "1. 在路由器上设置端口转发，将外部端口映射到服务器的端口\n"
            output += "2. 检查防火墙设置，确保允许相应端口的入站流量\n"
            output += "3. 如果使用云服务器，检查安全组设置，确保开放相应端口\n"
            output += "4. 联系网络管理员，确认是否有其他网络限制\n"

        # 如果没有特权端口权限，添加额外建议
        if not result.get('can_use_privileged_port', False):
            output += "\n要使用标准端口(80/443)，您需要:\n"
            output += "1. 在Linux/Mac上，使用sudo运行程序\n"
            output += "2. 在Windows上，以管理员身份运行程序\n"
            output += "3. 或者，配置系统允许非特权用户使用这些端口\n"
            output += "4. 如果在Docker中运行，确保正确映射端口\n"

        return output
    except Exception as e:
        logger.error(f"诊断Web服务器时发生错误: {e}")
        return f"诊断Web服务器时发生错误: {e}"


def register_tools(mcp: FastMCP):
    """
    注册K线数据相关的工具到MCP服务器

    Args:
        mcp: MCP服务器实例
    """
    # 注册获取K线数据工具
    mcp.tool()(get_kline_data)

    # 注册获取K线数据并返回URL的工具
    mcp.tool()(get_kline_data_with_url)

    # 注册诊断Web服务器工具
    mcp.tool()(diagnose_web_server)
