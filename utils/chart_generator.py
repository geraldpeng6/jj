#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图表生成模块

提供K线图表生成和浏览器显示功能
"""

import os
import os.path as path
import json
import logging
import webbrowser
import pandas as pd
import datetime
from typing import Optional, Dict, List, Any
from jinja2 import Template

# 获取日志记录器
logger = logging.getLogger('quant_mcp.chart_generator')

# 模板文件路径 - 使用相对路径
# 获取当前文件所在目录的上两级目录，即项目根目录
ROOT_DIR = path.abspath(path.join(path.dirname(__file__), ".."))
# 从项目根目录定位模板文件
TEMPLATE_PATH = path.join(ROOT_DIR, "data", "templates", "kline_chart.html")


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

        # 检查模板文件是否存在
        if not os.path.exists(TEMPLATE_PATH):
            logger.error(f"模板文件不存在: {TEMPLATE_PATH}")
            return None

        # 读取模板文件
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 创建Jinja2模板
        template = Template(template_content)

        # 准备ECharts数据
        echarts_data = prepare_echarts_data(chart_data)

        # 计算统计数据
        stats = calculate_stats(chart_data)

        # 复权方式名称
        fq_name_map = {
            "post": "后复权",
            "pre": "前复权",
            "none": "不复权"
        }
        fq_name = fq_name_map.get(fq, fq)

        # 日期范围
        if len(chart_data) > 0:
            start_date = chart_data['time'].min().strftime('%Y-%m-%d')
            end_date = chart_data['time'].max().strftime('%Y-%m-%d')
            date_range = f"{start_date} 至 {end_date}"
        else:
            date_range = "无数据"

        # 渲染模板
        html_content = template.render(
            title=f"{symbol}.{exchange} {resolution}",
            symbol=symbol,
            exchange=exchange,
            resolution=resolution,
            fq_name=fq_name,
            date_range=date_range,
            data_count=stats['data_count'],
            highest_price=stats['highest_price'],
            lowest_price=stats['lowest_price'],
            price_change=stats['price_change'],
            price_change_class=stats['price_change_class'],
            volatility=stats['volatility'],
            avg_volume=stats['avg_volume'],
            kline_data=json.dumps(echarts_data),
            generation_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # 写入HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 获取绝对路径
        abs_file_path = os.path.abspath(file_path)
        logger.info(f"K线图表已生成: {abs_file_path}")

        return abs_file_path
    except Exception as e:
        logger.error(f"生成K线图表时发生错误: {e}")
        return None


def prepare_echarts_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    准备ECharts所需的数据格式

    Args:
        df: K线数据DataFrame

    Returns:
        Dict[str, Any]: ECharts数据
    """
    # 确保数据按时间排序
    df = df.sort_values('time')

    # 准备日期数据
    dates = df['time'].dt.strftime('%Y-%m-%d').tolist()

    # 准备K线数据 [open, close, low, high]
    values = df[['open', 'close', 'low', 'high']].values.tolist()

    # 准备成交量数据
    volumes = []
    for i, row in df.iterrows():
        # 成交量数据格式: [idx, volume, 1/-1 (涨/跌)]
        volume_item = [
            i,
            row['volume'] if 'volume' in df.columns else 0,
            1 if row['close'] >= row['open'] else -1
        ]
        volumes.append(volume_item)

    # 计算移动平均线
    ma5 = calculate_ma(df, 5)
    ma10 = calculate_ma(df, 10)
    ma20 = calculate_ma(df, 20)
    ma30 = calculate_ma(df, 30)

    return {
        'categoryData': dates,
        'values': values,
        'volumes': volumes,
        'ma5': ma5,
        'ma10': ma10,
        'ma20': ma20,
        'ma30': ma30
    }


def calculate_ma(df: pd.DataFrame, n: int) -> List[float]:
    """
    计算移动平均线

    Args:
        df: K线数据DataFrame
        n: 周期

    Returns:
        List[float]: 移动平均线数据
    """
    result = []
    for i in range(len(df)):
        if i < n - 1:
            result.append('-')
            continue
        sum_val = 0
        for j in range(n):
            sum_val += df['close'].iloc[i - j]
        result.append(round(sum_val / n, 2))
    return result


def calculate_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    计算统计数据

    Args:
        df: K线数据DataFrame

    Returns:
        Dict[str, Any]: 统计数据
    """
    if len(df) == 0:
        return {
            'data_count': 0,
            'highest_price': '-',
            'lowest_price': '-',
            'price_change': '-',
            'price_change_class': 'unchanged',
            'volatility': '-',
            'avg_volume': '-'
        }

    # 数据点数
    data_count = len(df)

    # 最高价和最低价
    highest_price = round(df['high'].max(), 2)
    lowest_price = round(df['low'].min(), 2)

    # 涨跌幅
    first_close = df['close'].iloc[0]
    last_close = df['close'].iloc[-1]
    price_change = round((last_close - first_close) / first_close * 100, 2)

    # 涨跌幅样式类
    if price_change > 0:
        price_change_class = 'econ-positive'
    elif price_change < 0:
        price_change_class = 'econ-negative'
    else:
        price_change_class = 'econ-neutral'

    # 波动率 (收盘价标准差/平均值)
    volatility = round(df['close'].std() / df['close'].mean() * 100, 2)

    # 平均成交量
    if 'volume' in df.columns:
        avg_volume_val = df['volume'].mean()
        if avg_volume_val >= 1e8:
            avg_volume = f"{round(avg_volume_val / 1e8, 2)}亿"
        elif avg_volume_val >= 1e4:
            avg_volume = f"{round(avg_volume_val / 1e4, 2)}万"
        else:
            avg_volume = f"{int(avg_volume_val)}"
    else:
        avg_volume = '-'

    return {
        'data_count': data_count,
        'highest_price': highest_price,
        'lowest_price': lowest_price,
        'price_change': price_change,
        'price_change_class': price_change_class,
        'volatility': volatility,
        'avg_volume': avg_volume
    }


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
