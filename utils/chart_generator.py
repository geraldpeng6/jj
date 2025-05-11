#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图表生成模块

提供K线图表生成和浏览器显示功能
"""

import os
import logging
import webbrowser
import pandas as pd
from typing import Optional

# 获取日志记录器
logger = logging.getLogger('quant_mcp.chart_generator')


def generate_html(
    df: pd.DataFrame,
    symbol: str,
    exchange: str,
    resolution: str = "1D",
    fq: str = "post",
    output_dir: str = "data/charts"
) -> Optional[str]:
    """
    生成K线图表HTML文件

    Args:
        df: 包含K线数据的DataFrame
        symbol: 股票代码
        exchange: 交易所代码
        resolution: 时间周期
        fq: 复权方式
        output_dir: 输出目录

    Returns:
        Optional[str]: 生成的HTML文件路径，如果生成失败则返回None
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        file_name = f"{symbol}_{exchange}_{resolution}_{fq}.html"
        file_path = os.path.join(output_dir, file_name)

        # 准备数据
        chart_data = df.copy()
        
        # 确保时间列是日期时间类型
        if 'time' in chart_data.columns:
            chart_data['time'] = pd.to_datetime(chart_data['time'])
        
        # 使用Plotly生成交互式K线图
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            logger.error("未安装plotly库，请使用pip install plotly安装")
            return None

        # 创建带有成交量子图的图表
        fig = make_subplots(
            rows=2, 
            cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{symbol} {exchange} {resolution} K线图 ({fq}复权)", "成交量")
        )

        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=chart_data['time'],
                open=chart_data['open'],
                high=chart_data['high'],
                low=chart_data['low'],
                close=chart_data['close'],
                name="K线"
            ),
            row=1, col=1
        )

        # 添加成交量图
        if 'volume' in chart_data.columns:
            colors = ['red' if row['close'] >= row['open'] else 'green' 
                     for _, row in chart_data.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=chart_data['time'],
                    y=chart_data['volume'],
                    name="成交量",
                    marker_color=colors
                ),
                row=2, col=1
            )

        # 更新布局
        fig.update_layout(
            title=f"{symbol} {exchange} {resolution} K线图 ({fq}复权)",
            xaxis_title="日期",
            yaxis_title="价格",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            height=800,
            width=1200,
            showlegend=False
        )

        # 保存为HTML文件
        fig.write_html(file_path)
        logger.info(f"K线图表已生成: {file_path}")
        
        return file_path
    except Exception as e:
        logger.error(f"生成K线图表时发生错误: {e}")
        return None


def open_in_browser(file_path: str) -> bool:
    """
    在浏览器中打开HTML文件

    Args:
        file_path: HTML文件路径

    Returns:
        bool: 是否成功打开
    """
    try:
        if os.path.exists(file_path):
            # 获取文件的绝对路径
            abs_path = os.path.abspath(file_path)
            # 转换为URL格式
            file_url = f"file://{abs_path}"
            # 在浏览器中打开
            webbrowser.open(file_url)
            logger.info(f"已在浏览器中打开: {file_url}")
            return True
        else:
            logger.error(f"文件不存在: {file_path}")
            return False
    except Exception as e:
        logger.error(f"在浏览器中打开文件时发生错误: {e}")
        return False
