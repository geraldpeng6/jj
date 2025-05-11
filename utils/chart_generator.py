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
    timestamps = []
    cash_values = []

    try:
        for item in backtest_data:
            if not isinstance(item, dict):
                continue

            # 获取时间戳
            timestamp = item.get('tm')
            if not timestamp:
                continue

            # 获取持仓信息，找到现金持仓（category=0）
            positions = item.get('positions', [])
            for pos in positions:
                if pos.get('category') == 0:
                    cash_value = pos.get('value', 0)
                    timestamps.append(timestamp)
                    cash_values.append(float(cash_value))
                    break

        logger.info(f"成功提取现金序列，共 {len(timestamps)} 个数据点")
        return timestamps, cash_values
    except Exception as e:
        logger.error(f"提取现金序列时发生错误: {e}")
        return [], []


def extract_buy_sell_points(backtest_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, List]]:
    """
    从回测数据中提取买入卖出点

    Args:
        backtest_data: 回测数据列表

    Returns:
        Dict[str, Dict[str, List]]: 按股票代码组织的买卖点数据
    """
    # 初始化结果字典
    trade_points = {}

    # 记录每个股票的持仓状态
    symbol_positions = {}

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

            # 当前持仓的股票集合
            current_symbols = set()

            # 处理持仓信息
            for pos in positions:
                # 只处理股票持仓（category=1）
                if pos.get('category') != 1 or not pos.get('symbol'):
                    continue

                symbol = pos.get('symbol')
                current_size = pos.get('size', 0)
                current_symbols.add(symbol)

                # 如果是新的股票代码，初始化数据结构
                if symbol not in trade_points:
                    trade_points[symbol] = {
                        'buy_timestamps': [],
                        'buy_prices': [],
                        'sell_timestamps': [],
                        'sell_prices': []
                    }

                # 检查是否是买入点
                prev_size = symbol_positions.get(symbol, 0)
                if current_size > prev_size:
                    # 买入点
                    trade_points[symbol]['buy_timestamps'].append(timestamp)
                    trade_points[symbol]['buy_prices'].append(pos.get('price', 0))
                elif current_size < prev_size and prev_size > 0:
                    # 卖出点
                    trade_points[symbol]['sell_timestamps'].append(timestamp)
                    trade_points[symbol]['sell_prices'].append(pos.get('price', 0))

                # 更新持仓记录
                symbol_positions[symbol] = current_size

            # 检查是否有完全卖出的股票
            for symbol, size in list(symbol_positions.items()):
                if size > 0 and symbol not in current_symbols:
                    # 股票已完全卖出
                    if symbol in trade_points:
                        # 使用最后一个时间戳作为卖出时间
                        trade_points[symbol]['sell_timestamps'].append(timestamp)
                        # 由于没有价格信息，使用0作为占位符
                        trade_points[symbol]['sell_prices'].append(0)
                    # 更新持仓记录
                    symbol_positions[symbol] = 0

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

        for symbol, points in trade_points.items():
            buy_timestamps = points.get('buy_timestamps', [])
            sell_timestamps = points.get('sell_timestamps', [])
            buy_prices = points.get('buy_prices', [])
            sell_prices = points.get('sell_prices', [])

            # 计算交易次数（以卖出点为准）
            symbol_trade_count = len(sell_timestamps)
            trade_count += symbol_trade_count

            # 计算盈利交易次数
            for i in range(min(len(buy_prices), len(sell_prices))):
                if sell_prices[i] > buy_prices[i]:
                    win_count += 1

        metrics["trade_count"] = trade_count

        # 计算胜率
        if trade_count > 0:
            metrics["win_rate"] = round((win_count / trade_count) * 100, 2)

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

        # 确保时间戳列表一致
        if len(timestamps) == len(cash_values):
            for i in range(len(timestamps)):
                position_value = values[i] - cash_values[i]
                position_values.append(position_value)
        else:
            logger.warning("总资产序列和现金序列长度不一致，无法计算持仓价值序列")
            # 使用总资产作为占位符
            position_values = values.copy()

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
            sell_timestamps = points.get('sell_timestamps', [])
            sell_prices = points.get('sell_prices', [])

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

            buy_points[symbol] = {
                'dates': buy_dates,
                'prices': buy_prices
            }

            sell_points[symbol] = {
                'dates': sell_dates,
                'prices': sell_prices
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
    output_dir: str = "data/charts"
) -> Optional[str]:
    """
    分析已保存的回测结果并生成图表

    Args:
        backtest_file_path: 回测结果文件路径
        kline_file_path: K线数据文件路径，可选
        output_dir: 输出目录

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
            if isinstance(item, dict) and item.get('strategy_name'):
                strategy_name = item.get('strategy_name')
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
            output_dir=output_dir
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
    output_dir: str = "data/charts"
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

    Returns:
        Optional[str]: 生成的HTML文件路径，如果生成失败则返回None
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if symbol and exchange:
            file_name = f"backtest_{strategy_id}_{symbol}_{exchange}_{timestamp}.html"
        else:
            file_name = f"backtest_{strategy_id}_{timestamp}.html"

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
            generation_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # 写入HTML文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 获取绝对路径
        abs_file_path = os.path.abspath(file_path)
        logger.info(f"回测结果图表已生成: {abs_file_path}")

        return abs_file_path
    except Exception as e:
        logger.error(f"生成回测结果图表时发生错误: {e}")
        return None
