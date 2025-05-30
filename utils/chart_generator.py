#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图表生成模块

提供K线图表生成和浏览器显示功能，以及回测结果分析和可视化
"""

import os
import os.path as path
import json
import logging
import webbrowser
import pandas as pd
import numpy as np
import datetime
from datetime import datetime as dt
from typing import Optional, Dict, List, Any, Tuple, Union
from jinja2 import Template

from utils.html_server import get_html_url, generate_test_html
from utils.date_utils import get_beijing_now

# 获取日志记录器
logger = logging.getLogger('quant_mcp.chart_generator')

# 模板文件路径 - 使用相对路径
# 获取当前文件所在目录的上两级目录，即项目根目录
ROOT_DIR = path.abspath(path.join(path.dirname(__file__), ".."))
# 从项目根目录定位模板文件
TEMPLATE_PATH = path.join(ROOT_DIR, "data", "templates", "kline_chart.html")
# 回测结果模板文件路径
BACKTEST_TEMPLATE_PATH = path.join(ROOT_DIR, "data", "templates", "backtest_chart.html")


def generate_html(
    df: pd.DataFrame,
    symbol: str,
    exchange: str,
    resolution: str = "1D",
    fq: str = "post",
    output_dir: str = "data/charts",
    timestamp: Optional[str] = None
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
        timestamp: 时间戳，用于生成文件名，可选，如果不提供则自动生成

    Returns:
        Optional[str]: 生成的HTML文件路径，如果生成失败则返回None
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        if timestamp is None:
            timestamp = get_beijing_now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{symbol}_{exchange}_{resolution}_{fq}_{timestamp}.html"
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
            
            # 获取最新日期信息（使用北京时间）
            current_date = get_beijing_now().strftime('%Y-%m-%d')
            latest_date_info = ""
            
            # 如果最新数据不是今天的，添加提示信息
            if end_date != current_date:
                latest_date_info = f"（最新数据截至 {end_date}，当前日期 {current_date}）"
                logger.info(f"图表数据不是最新的: 最新数据日期 {end_date}, 当前日期 {current_date}")
            
            # 更新日期范围显示
            date_range = f"{start_date} 至 {end_date} {latest_date_info}"
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
            generation_time=get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # 写入HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 获取绝对路径
        abs_file_path = os.path.abspath(file_path)

        # 获取Web URL
        web_url = get_html_url(abs_file_path)

        logger.info(f"K线图表已生成: {abs_file_path}")
        logger.info(f"K线图表Web URL: {web_url}")
        logger.info(f"图表数据日期范围: {date_range}")

        return web_url
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

    如果文件在charts目录下，则通过Web服务器访问；否则使用本地文件URL

    Args:
        file_path: HTML文件路径或URL

    Returns:
        bool: 是否成功打开
    """
    try:
        # 检查是否已经是URL
        if file_path.startswith('http://') or file_path.startswith('https://'):
            # 直接使用URL
            file_url = file_path
            logger.info(f"直接使用提供的URL: {file_url}")
        else:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False

            # 获取文件的绝对路径
            abs_path = os.path.abspath(file_path)

            # 检查文件是否在charts目录下
            charts_dir = os.path.abspath("data/charts")
            if abs_path.startswith(charts_dir):
                # 使用HTML服务器URL
                file_url = get_html_url(file_path)
                logger.info(f"使用Web服务器URL: {file_url}")
            else:
                # 使用本地文件URL
                file_url = f"file://{abs_path}"
                logger.info(f"使用本地文件URL: {file_url}")

        # 不再自动打开浏览器，只返回URL
        logger.info(f"生成URL: {file_url}")
        return True
    except Exception as e:
        logger.error(f"生成URL时发生错误: {e}")
        return False


def load_backtest_data(file_path: str) -> List[Dict[str, Any]]:
    """
    加载回测数据

    Args:
        file_path: 回测数据文件路径

    Returns:
        List[Dict[str, Any]]: 回测数据列表
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"回测数据文件不存在: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error(f"回测数据格式错误，应为列表: {file_path}")
            return []

        logger.info(f"成功加载回测数据，共 {len(data)} 条记录")
        return data
    except Exception as e:
        logger.error(f"加载回测数据时发生错误: {e}")
        return []


def extract_value_series(backtest_data: List[Dict[str, Any]]) -> Tuple[List[int], List[float]]:
    """
    从回测数据中提取总资产价值序列

    Args:
        backtest_data: 回测数据列表

    Returns:
        Tuple[List[int], List[float]]: 时间戳列表和对应的总资产价值列表
    """
    timestamps = []
    values = []

    try:
        for item in backtest_data:
            if not isinstance(item, dict):
                continue

            # 获取时间戳和总资产价值
            timestamp = item.get('tm')
            value = item.get('value')

            if timestamp and value is not None:
                timestamps.append(timestamp)
                values.append(float(value))

        logger.info(f"成功提取总资产价值序列，共 {len(timestamps)} 个数据点")
        return timestamps, values
    except Exception as e:
        logger.error(f"提取总资产价值序列时发生错误: {e}")
        return [], []


def extract_position_series(backtest_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, List]]:
    """
    从回测数据中提取持仓序列

    Args:
        backtest_data: 回测数据列表

    Returns:
        Dict[str, Dict[str, List]]: 按股票代码组织的持仓数据，包含时间戳、持仓数量、持仓价值等
    """
    # 初始化结果字典，按股票代码组织
    position_series = {}

    try:
        for item in backtest_data:
            if not isinstance(item, dict):
                continue

            # 获取时间戳
            timestamp = item.get('tm')
            if not timestamp:
                continue

            # 获取持仓信息
            positions = item.get('positions', [])
            for pos in positions:
                # 只处理股票持仓（category=1）
                if pos.get('category') != 1 or not pos.get('symbol'):
                    continue

                symbol = pos.get('symbol')

                # 如果是新的股票代码，初始化数据结构
                if symbol not in position_series:
                    position_series[symbol] = {
                        'timestamps': [],
                        'sizes': [],
                        'values': [],
                        'prices': [],
                        'pprices': [],  # 持仓成本价
                        'profits': []   # 持仓盈亏
                    }

                # 添加数据
                position_series[symbol]['timestamps'].append(timestamp)
                position_series[symbol]['sizes'].append(pos.get('size', 0))
                position_series[symbol]['values'].append(pos.get('value', 0))
                position_series[symbol]['prices'].append(pos.get('price', 0))
                position_series[symbol]['pprices'].append(pos.get('pprice', 0))
                position_series[symbol]['profits'].append(pos.get('profit_and_loss', 0))

        logger.info(f"成功提取持仓序列，共 {len(position_series)} 个股票")
        return position_series
    except Exception as e:
        logger.error(f"提取持仓序列时发生错误: {e}")
        return {}


def extract_cash_series(backtest_data: List[Dict[str, Any]]) -> Tuple[List[int], List[float]]:
    """
    从回测数据中提取现金序列

    Args:
        backtest_data: 回测数据列表

    Returns:
        Tuple[List[int], List[float]]: 时间戳列表和对应的现金价值列表
    """
    # 首先提取所有时间戳，确保与总资产价值序列一致
    timestamps, _ = extract_value_series(backtest_data)
    cash_values = [0.0] * len(timestamps)  # 初始化现金值列表，默认为0

    try:
        # 创建时间戳到索引的映射
        timestamp_to_index = {ts: i for i, ts in enumerate(timestamps)}

        for item in backtest_data:
            if not isinstance(item, dict):
                continue

            # 获取时间戳
            timestamp = item.get('tm')
            if not timestamp or timestamp not in timestamp_to_index:
                continue

            # 获取该时间戳在列表中的索引
            index = timestamp_to_index[timestamp]

            # 获取持仓信息，找到现金持仓（category=0）
            positions = item.get('positions', [])
            for pos in positions:
                if pos.get('category') == 0:
                    cash_value = pos.get('value', 0)
                    cash_values[index] = float(cash_value)
                    break

        logger.info(f"成功提取现金序列，共 {len(cash_values)} 个数据点")
        return timestamps, cash_values
    except Exception as e:
        logger.error(f"提取现金序列时发生错误: {e}")
        return timestamps, [0.0] * len(timestamps)  # 返回与时间戳长度一致的现金值列表


def extract_buy_sell_points(backtest_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, List]]:
    """
    从回测数据中提取买入卖出点，通过跟踪钱包(id=0)的现金变化判断买入卖出

    Args:
        backtest_data: 回测数据列表

    Returns:
        Dict[str, Dict[str, List]]: 按股票代码组织的买卖点数据，包含交易金额信息
    """
    # 初始化结果字典
    trade_points = {}

    # 记录每个时间点的数据
    time_data = {}

    # 记录每个股票的持仓状态
    symbol_positions = {}

    # 记录上一个时间点的现金值
    prev_cash_value = None
    prev_timestamp = None

    # 调试信息
    logger.info("开始提取买卖点...")

    try:
        # 第一步：收集所有时间点的数据
        for item in backtest_data:
            if not isinstance(item, dict):
                continue

            # 获取时间戳
            timestamp = item.get('tm')
            if not timestamp:
                continue

            # 收集该时间点的数据
            time_data[timestamp] = {
                'cash_value': None,
                'positions': {},
                'total_value': item.get('value', 0)
            }

            # 处理持仓信息
            positions = item.get('positions', [])
            for pos in positions:
                category = pos.get('category')

                if category == 0:  # 现金持仓
                    time_data[timestamp]['cash_value'] = float(pos.get('value', 0))
                    logger.debug(f"时间点 {timestamp}: 现金值 = {time_data[timestamp]['cash_value']}")
                elif category == 1:  # 股票持仓
                    symbol = pos.get('symbol')
                    if not symbol:
                        continue

                    time_data[timestamp]['positions'][symbol] = {
                        'size': pos.get('size', 0),
                        'price': pos.get('price', 0),
                        'value': pos.get('value', 0)
                    }
                    logger.debug(f"时间点 {timestamp}: 股票 {symbol} 持仓 = {pos.get('size', 0)}, 价格 = {pos.get('price', 0)}")

        # 按时间戳排序
        sorted_timestamps = sorted(time_data.keys())
        logger.info(f"共收集到 {len(sorted_timestamps)} 个时间点的数据")

        # 第二步：分析相邻时间点的变化，识别买入卖出点
        for i in range(1, len(sorted_timestamps)):
            curr_ts = sorted_timestamps[i]
            prev_ts = sorted_timestamps[i-1]

            curr_data = time_data[curr_ts]
            prev_data = time_data[prev_ts]

            # 获取现金变化
            curr_cash = curr_data['cash_value']
            prev_cash = prev_data['cash_value']

            if curr_cash is None or prev_cash is None:
                continue

            cash_change = curr_cash - prev_cash
            logger.debug(f"时间点 {curr_ts}: 现金变化 = {cash_change}")

            # 分析持仓变化
            curr_positions = curr_data['positions']
            prev_positions = prev_data['positions']

            # 检查所有当前持仓的股票
            for symbol, curr_pos in curr_positions.items():
                # 如果是新的股票代码，初始化数据结构
                if symbol not in trade_points:
                    trade_points[symbol] = {
                        'buy_timestamps': [],
                        'buy_prices': [],
                        'buy_amounts': [],
                        'buy_sizes': [],
                        'sell_timestamps': [],
                        'sell_prices': [],
                        'sell_amounts': [],
                        'sell_sizes': []
                    }

                curr_size = curr_pos['size']
                curr_price = curr_pos['price']

                # 检查该股票在上一个时间点的持仓
                prev_size = 0
                if symbol in prev_positions:
                    prev_size = prev_positions[symbol]['size']

                # 持仓增加，判断为买入
                if curr_size > prev_size:
                    size_change = curr_size - prev_size
                    # 估算买入金额（如果现金减少，使用现金变化的绝对值；否则使用持仓价值变化）
                    buy_amount = abs(cash_change) if cash_change < 0 else (curr_price * size_change)
                    
                    # 确保金额计算正确 - 使用价格乘以数量作为标准计算方式
                    # 如果使用现金变化值显著小于标准计算方式（差异超过20%），则使用标准计算方式
                    standard_amount = curr_price * size_change
                    if buy_amount < standard_amount * 0.8:
                        logger.warning(f"买入金额计算异常: 使用现金变化估算值 {buy_amount} 与标准计算值 {standard_amount} 差异过大，使用标准计算值")
                        buy_amount = standard_amount

                    # 添加买入点
                    trade_points[symbol]['buy_timestamps'].append(curr_ts)
                    trade_points[symbol]['buy_prices'].append(curr_price)
                    trade_points[symbol]['buy_amounts'].append(buy_amount)
                    trade_points[symbol]['buy_sizes'].append(size_change)

                    logger.info(f"检测到买入: 时间={curr_ts}, 股票={symbol}, 价格={curr_price}, 数量={size_change}, 金额={buy_amount}")

            # 检查上一个时间点有但当前没有的股票（完全卖出）
            for symbol, prev_pos in prev_positions.items():
                if symbol not in curr_positions:
                    # 如果是新的股票代码，初始化数据结构
                    if symbol not in trade_points:
                        trade_points[symbol] = {
                            'buy_timestamps': [],
                            'buy_prices': [],
                            'buy_amounts': [],
                            'buy_sizes': [],
                            'sell_timestamps': [],
                            'sell_prices': [],
                            'sell_amounts': [],
                            'sell_sizes': []
                        }

                    prev_size = prev_pos['size']
                    prev_price = prev_pos['price']

                    # 估算卖出金额（如果现金增加，使用现金变化；否则使用持仓价值）
                    sell_amount = cash_change if cash_change > 0 else (prev_price * prev_size)
                    
                    # 确保金额计算正确 - 使用价格乘以数量作为标准计算方式
                    standard_amount = prev_price * prev_size
                    if sell_amount < standard_amount * 0.8 or sell_amount > standard_amount * 1.2:
                        logger.warning(f"卖出金额计算异常: 使用现金变化估算值 {sell_amount} 与标准计算值 {standard_amount} 差异过大，使用标准计算值")
                        sell_amount = standard_amount

                    # 添加卖出点
                    trade_points[symbol]['sell_timestamps'].append(curr_ts)
                    trade_points[symbol]['sell_prices'].append(prev_price)  # 使用上一个时间点的价格
                    trade_points[symbol]['sell_amounts'].append(sell_amount)
                    trade_points[symbol]['sell_sizes'].append(prev_size)

                    logger.info(f"检测到完全卖出: 时间={curr_ts}, 股票={symbol}, 价格={prev_price}, 数量={prev_size}, 金额={sell_amount}")
                elif curr_positions[symbol]['size'] < prev_pos['size']:
                    # 部分卖出
                    curr_size = curr_positions[symbol]['size']
                    prev_size = prev_pos['size']
                    size_change = prev_size - curr_size
                    curr_price = curr_positions[symbol]['price']

                    # 估算卖出金额（如果现金增加，使用现金变化；否则使用持仓价值）
                    sell_amount = cash_change if cash_change > 0 else (curr_price * size_change)
                    
                    # 确保金额计算正确 - 使用价格乘以数量作为标准计算方式
                    standard_amount = curr_price * size_change
                    if sell_amount < standard_amount * 0.8 or sell_amount > standard_amount * 1.2:
                        logger.warning(f"部分卖出金额计算异常: 使用现金变化估算值 {sell_amount} 与标准计算值 {standard_amount} 差异过大，使用标准计算值")
                        sell_amount = standard_amount

                    # 添加卖出点
                    trade_points[symbol]['sell_timestamps'].append(curr_ts)
                    trade_points[symbol]['sell_prices'].append(curr_price)
                    trade_points[symbol]['sell_amounts'].append(sell_amount)
                    trade_points[symbol]['sell_sizes'].append(size_change)

                    logger.info(f"检测到部分卖出: 时间={curr_ts}, 股票={symbol}, 价格={curr_price}, 数量={size_change}, 金额={sell_amount}")

        # 打印提取结果
        for symbol, points in trade_points.items():
            buy_count = len(points['buy_timestamps'])
            sell_count = len(points['sell_timestamps'])
            logger.info(f"股票 {symbol}: 买入点 {buy_count} 个, 卖出点 {sell_count} 个")

            # 打印买入点详情
            for i in range(buy_count):
                ts = points['buy_timestamps'][i]
                price = points['buy_prices'][i]
                amount = points['buy_amounts'][i] if i < len(points['buy_amounts']) else 0
                size = points['buy_sizes'][i] if i < len(points['buy_sizes']) else 0
                date_str = dt.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                logger.info(f"  买入点 {i+1}: 日期={date_str}, 价格={price}, 数量={size}, 金额={amount}")

            # 打印卖出点详情
            for i in range(sell_count):
                ts = points['sell_timestamps'][i]
                price = points['sell_prices'][i]
                amount = points['sell_amounts'][i] if i < len(points['sell_amounts']) else 0
                size = points['sell_sizes'][i] if i < len(points['sell_sizes']) else 0
                date_str = dt.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                logger.info(f"  卖出点 {i+1}: 日期={date_str}, 价格={price}, 数量={size}, 金额={amount}")

        logger.info(f"成功提取买卖点，共 {len(trade_points)} 个股票")
        return trade_points
    except Exception as e:
        logger.error(f"提取买卖点时发生错误: {e}")
        return {}


def calculate_backtest_metrics(backtest_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    计算回测性能指标

    Args:
        backtest_data: 回测数据列表

    Returns:
        Dict[str, float]: 性能指标，包含总收益率、年化收益率、最大回撤等
    """
    # 初始化指标字典
    metrics = {
        "total_return": 0.0,        # 总收益
        "annual_return": 0.0,       # 年化收益率
        "benchmark_return": 0.0,    # 基准收益率
        "benchmark_annual": 0.0,    # 基准年化收益率
        "trade_count": 0,           # 交易次数
        "win_rate": 0.0,            # 胜率
        "sharpe_ratio": 0.0,        # 夏普比率
        "max_drawdown": 0.0,        # 最大回撤
        "avg_trade": 0.0            # 平均每笔交易
    }

    try:
        if not backtest_data:
            return metrics

        # 提取总资产价值序列
        timestamps, values = extract_value_series(backtest_data)

        if not timestamps or not values:
            return metrics

        # 计算总收益率
        initial_value = values[0]
        final_value = values[-1]

        if initial_value > 0:
            total_return = (final_value - initial_value) / initial_value
            metrics["total_return"] = round(total_return * 100, 2)

        # 计算年化收益率
        if len(timestamps) >= 2:
            start_time = dt.fromtimestamp(timestamps[0] / 1000)
            end_time = dt.fromtimestamp(timestamps[-1] / 1000)
            days = (end_time - start_time).days

            if days > 0:
                annual_return = total_return * (365 / days)
                metrics["annual_return"] = round(annual_return * 100, 2)

        # 计算最大回撤
        max_drawdown = 0
        peak_value = values[0]

        for value in values:
            if value > peak_value:
                peak_value = value
            else:
                drawdown = (peak_value - value) / peak_value if peak_value > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)

        metrics["max_drawdown"] = round(max_drawdown * 100, 2)

        # 提取买卖点计算交易次数
        trade_points = extract_buy_sell_points(backtest_data)
        trade_count = 0
        win_count = 0

        # 记录每个交易的盈亏情况
        trade_results = []

        for symbol, points in trade_points.items():
            buy_timestamps = points.get('buy_timestamps', [])
            sell_timestamps = points.get('sell_timestamps', [])
            buy_prices = points.get('buy_prices', [])
            sell_prices = points.get('sell_prices', [])
            buy_amounts = points.get('buy_amounts', [])
            sell_amounts = points.get('sell_amounts', [])
            buy_sizes = points.get('buy_sizes', [])
            sell_sizes = points.get('sell_sizes', [])

            # 计算交易次数（以卖出点为准）
            symbol_trade_count = len(sell_timestamps)
            trade_count += symbol_trade_count

            # 计算盈利交易次数
            for i in range(min(len(buy_timestamps), len(sell_timestamps))):
                # 获取买入和卖出信息
                buy_price = buy_prices[i] if i < len(buy_prices) else 0
                sell_price = sell_prices[i] if i < len(sell_prices) else 0
                buy_amount = buy_amounts[i] if i < len(buy_amounts) else 0
                sell_amount = sell_amounts[i] if i < len(sell_amounts) else 0
                buy_size = buy_sizes[i] if i < len(buy_sizes) else 0
                sell_size = sell_sizes[i] if i < len(sell_sizes) else 0

                # 判断是否盈利
                is_profitable = False

                # 方法1：通过价格和数量判断
                if buy_price > 0 and sell_price > 0 and buy_size > 0 and sell_size > 0:
                    buy_value = buy_price * buy_size
                    sell_value = sell_price * sell_size
                    if sell_value > buy_value:
                        is_profitable = True
                        logger.debug(f"交易盈利(价格*数量): 买入={buy_value}, 卖出={sell_value}")

                # 方法2：直接通过金额判断
                elif buy_amount > 0 and sell_amount > 0:
                    if sell_amount > buy_amount:
                        is_profitable = True
                        logger.debug(f"交易盈利(金额): 买入={buy_amount}, 卖出={sell_amount}")

                # 方法3：通过价格判断（如果数量相同）
                elif buy_price > 0 and sell_price > 0:
                    if sell_price > buy_price:
                        is_profitable = True
                        logger.debug(f"交易盈利(价格): 买入={buy_price}, 卖出={sell_price}")

                # 记录结果
                if is_profitable:
                    win_count += 1
                    trade_results.append(1)  # 盈利
                else:
                    trade_results.append(-1)  # 亏损

        metrics["trade_count"] = trade_count

        # 计算胜率
        if trade_count > 0:
            metrics["win_rate"] = round((win_count / trade_count) * 100, 2)
            logger.info(f"交易次数: {trade_count}, 盈利次数: {win_count}, 胜率: {metrics['win_rate']}%")

        # 计算平均每笔交易收益
        if trade_count > 0:
            avg_trade = total_return / trade_count
            metrics["avg_trade"] = round(avg_trade * 100, 2)

        # 计算夏普比率（简化版，使用日收益率）
        if len(values) > 1:
            daily_returns = []
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    daily_return = (values[i] - values[i-1]) / values[i-1]
                    daily_returns.append(daily_return)

            if daily_returns:
                avg_return = sum(daily_returns) / len(daily_returns)
                std_return = (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5

                if std_return > 0:
                    sharpe_ratio = avg_return / std_return * (252 ** 0.5)  # 年化
                    metrics["sharpe_ratio"] = round(sharpe_ratio, 2)

        logger.info(f"成功计算回测指标: {metrics}")
        return metrics
    except Exception as e:
        logger.error(f"计算回测指标时发生错误: {e}")
        return metrics


def prepare_backtest_chart_data(
    backtest_data: List[Dict[str, Any]],
    kline_df: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    准备回测图表数据

    Args:
        backtest_data: 回测数据列表
        kline_df: K线数据DataFrame，可选

    Returns:
        Dict[str, Any]: 图表数据
    """
    chart_data = {
        'timestamps': [],
        'dates': [],
        'values': [],
        'cash_values': [],
        'position_values': [],
        'buy_points': {},
        'sell_points': {},
        'kline_data': None
    }

    try:
        # 提取总资产价值序列
        timestamps, values = extract_value_series(backtest_data)

        if not timestamps or not values:
            logger.error("无法提取总资产价值序列")
            return chart_data

        # 提取现金序列
        cash_timestamps, cash_values = extract_cash_series(backtest_data)

        # 计算持仓价值序列（总资产 - 现金）
        position_values = []

        # 由于我们修改了extract_cash_series函数，现在时间戳列表一定一致
        for i in range(len(timestamps)):
            position_value = max(0.0, values[i] - cash_values[i])  # 确保持仓价值不为负
            position_values.append(position_value)

        # 转换时间戳为日期字符串
        dates = []
        for ts in timestamps:
            date_str = dt.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
            dates.append(date_str)

        # 提取买卖点
        trade_points = extract_buy_sell_points(backtest_data)
        buy_points = {}
        sell_points = {}

        for symbol, points in trade_points.items():
            buy_timestamps = points.get('buy_timestamps', [])
            buy_prices = points.get('buy_prices', [])
            buy_amounts = points.get('buy_amounts', [])
            buy_sizes = points.get('buy_sizes', [])
            sell_timestamps = points.get('sell_timestamps', [])
            sell_prices = points.get('sell_prices', [])
            sell_amounts = points.get('sell_amounts', [])
            sell_sizes = points.get('sell_sizes', [])

            # 转换买入点时间戳为日期字符串
            buy_dates = []
            for ts in buy_timestamps:
                date_str = dt.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                buy_dates.append(date_str)

            # 转换卖出点时间戳为日期字符串
            sell_dates = []
            for ts in sell_timestamps:
                date_str = dt.fromtimestamp(ts / 1000).strftime('%Y-%m-%d')
                sell_dates.append(date_str)

            # 准备买入点详情文本
            buy_details = []
            for i in range(len(buy_prices)):
                price = buy_prices[i]
                amount = buy_amounts[i] if i < len(buy_amounts) else 0
                size = buy_sizes[i] if i < len(buy_sizes) else 0

                if amount > 0 and size > 0:
                    detail = f"买入 {symbol}\n价格: {round(price, 2)}元\n数量: {size}股\n金额: {round(amount, 2)}元"
                elif amount > 0:
                    detail = f"买入 {symbol}\n价格: {round(price, 2)}元\n金额: {round(amount, 2)}元"
                else:
                    detail = f"买入 {symbol}\n价格: {round(price, 2)}元"

                buy_details.append(detail)

            # 准备卖出点详情文本
            sell_details = []
            for i in range(len(sell_prices)):
                price = sell_prices[i]
                amount = sell_amounts[i] if i < len(sell_amounts) else 0
                size = sell_sizes[i] if i < len(sell_sizes) else 0

                if amount > 0 and size > 0:
                    detail = f"卖出 {symbol}\n价格: {round(price, 2)}元\n数量: {size}股\n金额: {round(amount, 2)}元"
                elif amount > 0:
                    detail = f"卖出 {symbol}\n价格: {round(price, 2)}元\n金额: {round(amount, 2)}元"
                else:
                    detail = f"卖出 {symbol}\n价格: {round(price, 2)}元"

                sell_details.append(detail)

            buy_points[symbol] = {
                'dates': buy_dates,
                'prices': buy_prices,
                'details': buy_details,
                'amounts': buy_amounts,
                'sizes': buy_sizes
            }

            sell_points[symbol] = {
                'dates': sell_dates,
                'prices': sell_prices,
                'details': sell_details,
                'amounts': sell_amounts,
                'sizes': sell_sizes
            }

        # 准备K线数据（如果提供）
        kline_data = None
        if kline_df is not None and not kline_df.empty:
            kline_data = prepare_echarts_data(kline_df)

        # 更新图表数据
        chart_data['timestamps'] = timestamps
        chart_data['dates'] = dates
        chart_data['values'] = values
        chart_data['cash_values'] = cash_values
        chart_data['position_values'] = position_values
        chart_data['buy_points'] = buy_points
        chart_data['sell_points'] = sell_points
        chart_data['kline_data'] = kline_data

        logger.info("成功准备回测图表数据")
        return chart_data
    except Exception as e:
        logger.error(f"准备回测图表数据时发生错误: {e}")
        return chart_data


def analyze_backtest_result(
    backtest_file_path: str,
    kline_file_path: Optional[str] = None,
    output_dir: str = "data/charts",
    timestamp: Optional[str] = None
) -> Optional[str]:
    """
    分析回测结果并生成图表

    Args:
        backtest_file_path: 回测结果文件路径
        kline_file_path: K线数据文件路径，可选
        output_dir: 输出目录
        timestamp: 时间戳，用于生成文件名，可选，如果不提供则自动生成

    Returns:
        Optional[str]: 生成的HTML文件路径，如果生成失败则返回None
    """
    try:
        # 加载回测数据
        backtest_data = load_backtest_data(backtest_file_path)
        if not backtest_data:
            logger.error(f"无法加载回测数据: {backtest_file_path}")
            return None

        # 提取策略信息
        strategy_id = "unknown"
        strategy_name = "未知策略"
        symbol = None
        exchange = None

        # 尝试从文件名中提取策略ID
        file_name = os.path.basename(backtest_file_path)
        if "_" in file_name:
            parts = file_name.split("_")
            if len(parts) > 0:
                strategy_id = parts[0]

        # 尝试从回测数据中提取策略名称
        for item in backtest_data:
            if isinstance(item, dict):
                # 首先尝试获取name字段
                if item.get('name'):
                    strategy_name = item.get('name')
                    break
                # 然后尝试获取strategy_name字段
                elif item.get('strategy_name'):
                    strategy_name = item.get('strategy_name')
                    break
                # 最后尝试获取title字段
                elif item.get('title'):
                    strategy_name = item.get('title')
                    break
                # 尝试从message中获取title
                elif isinstance(item.get('message'), dict) and item.get('message', {}).get('title'):
                    strategy_name = item.get('message', {}).get('title')
                    break

        # 尝试从回测数据中提取股票代码
        for item in backtest_data:
            if isinstance(item, dict) and item.get('symbols'):
                symbols = item.get('symbols')
                if symbols and len(symbols) > 0:
                    if isinstance(symbols[0], dict):
                        symbol = symbols[0].get('symbol')
                        exchange = symbols[0].get('exchange')
                    elif isinstance(symbols[0], str):
                        if '.' in symbols[0]:
                            symbol, exchange = symbols[0].split('.')
                    break

        # 加载K线数据（如果提供）
        kline_df = None
        if kline_file_path and os.path.exists(kline_file_path):
            try:
                kline_df = pd.read_csv(kline_file_path)
                logger.info(f"成功加载K线数据: {kline_file_path}")
            except Exception as e:
                logger.error(f"加载K线数据失败: {e}")

        # 生成回测结果图表
        return generate_backtest_html(
            backtest_data=backtest_data,
            strategy_name=strategy_name,
            strategy_id=strategy_id,
            kline_df=kline_df,
            symbol=symbol,
            exchange=exchange,
            output_dir=output_dir,
            timestamp=timestamp
        )
    except Exception as e:
        logger.error(f"分析回测结果时发生错误: {e}")
        return None


def generate_backtest_html(
    backtest_data: List[Dict[str, Any]],
    strategy_name: str,
    strategy_id: str,
    kline_df: pd.DataFrame = None,
    symbol: str = None,
    exchange: str = None,
    output_dir: str = "data/charts",
    timestamp: Optional[str] = None
) -> Optional[str]:
    """
    生成回测结果HTML文件

    Args:
        backtest_data: 回测数据列表
        strategy_name: 策略名称
        strategy_id: 策略ID
        kline_df: K线数据DataFrame，可选
        symbol: 股票代码，可选
        exchange: 交易所代码，可选
        output_dir: 输出目录
        timestamp: 时间戳，用于生成文件名，可选，如果不提供则自动生成

    Returns:
        Optional[str]: 生成的HTML文件路径，如果生成失败则返回None
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 使用提供的时间戳或生成新的时间戳
        if timestamp is None:
            timestamp = get_beijing_now().strftime('%Y%m%d_%H%M%S')

        # 生成文件名
        if symbol and exchange:
            file_name = f"backtest_{strategy_id}_{symbol}_{exchange}_{timestamp}.html"
        else:
            file_name = f"backtest_{strategy_id}_{timestamp}.html"

        # 如果没有提供symbol和exchange，尝试从回测数据中提取
        if not symbol or not exchange:
            for item in backtest_data:
                if isinstance(item, dict) and item.get('positions'):
                    for pos in item.get('positions', []):
                        if pos.get('category') == 1 and pos.get('symbol') and pos.get('exchange'):
                            symbol = pos.get('symbol')
                            exchange = pos.get('exchange')
                            # 更新文件名，但保持原始时间戳
                            file_name = f"backtest_{strategy_id}_{symbol}_{exchange}_{timestamp}.html"
                            break
                    if symbol and exchange:
                        break

        file_path = os.path.join(output_dir, file_name)

        # 检查模板文件是否存在
        if not os.path.exists(BACKTEST_TEMPLATE_PATH):
            # 如果回测模板不存在，尝试使用K线模板
            if not os.path.exists(TEMPLATE_PATH):
                logger.error(f"模板文件不存在: {BACKTEST_TEMPLATE_PATH} 和 {TEMPLATE_PATH}")
                return None
            else:
                logger.warning(f"回测模板文件不存在: {BACKTEST_TEMPLATE_PATH}，使用K线模板: {TEMPLATE_PATH}")
                template_path = TEMPLATE_PATH
        else:
            template_path = BACKTEST_TEMPLATE_PATH

        # 读取模板文件
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 创建Jinja2模板
        template = Template(template_content)

        # 计算回测指标
        metrics = calculate_backtest_metrics(backtest_data)

        # 准备图表数据
        chart_data = prepare_backtest_chart_data(backtest_data, kline_df)

        # 日期范围
        if chart_data['dates']:
            start_date = chart_data['dates'][0]
            end_date = chart_data['dates'][-1]
            date_range = f"{start_date} 至 {end_date}"
        else:
            date_range = "无数据"

        # 渲染模板
        html_content = template.render(
            title=f"回测结果 - {strategy_name}",
            strategy_name=strategy_name,
            strategy_id=strategy_id,
            symbol=symbol or "多股票",
            exchange=exchange or "",
            date_range=date_range,
            metrics=metrics,
            chart_data=json.dumps(chart_data),
            generation_time=get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # 写入HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 获取绝对路径
        abs_file_path = os.path.abspath(file_path)

        # 获取Web URL
        web_url = get_html_url(abs_file_path)

        logger.info(f"回测结果图表已生成: {abs_file_path}")
        logger.info(f"回测结果图表Web URL: {web_url}")

        return web_url
    except Exception as e:
        logger.error(f"生成回测结果图表时发生错误: {e}")
        return None
