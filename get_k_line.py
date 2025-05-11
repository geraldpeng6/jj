#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
历史数据MCP服务器

这个脚本实现了一个基于Model Context Protocol (MCP)的历史数据服务器，
提供三个主要工具：
1. 获取股票历史K线数据
2. 保存K线数据到文件
3. 生成K线图表并在浏览器中显示

使用yueniusz的API获取数据。
"""

import json
import logging
import requests
import sys
import time
import os
import datetime
import pandas as pd
from typing import Any, Dict, List, Optional, Union, Tuple
from mcp.server.fastmcp import FastMCP
from utils.chart_generator import chart_generator


# 初始化FastMCP服务器实例，设置服务名称为"历史数据服务"
mcp = FastMCP("历史数据服务")

# 确保日志目录存在
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# 创建日志记录器
logger = logging.getLogger('yueniusz.history_mcp')
logger.setLevel(logging.INFO)

# 创建日志处理器，使用RotatingFileHandler进行日志轮转
log_file = os.path.join(log_dir, 'history_mcp.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(file_handler)

# 防止日志重复输出
logger.propagate = False

# API基础URL
BASE_URL = "https://api.yueniusz.com"

# 认证信息
TOKEN = None
USER_ID = None


def load_auth_config():
    """
    从配置文件加载认证信息

    Returns:
        bool: 加载是否成功
    """
    global TOKEN, USER_ID

    # 检查配置文件是否存在
    config_file = 'config/auth.json'
    if not os.path.exists(config_file):
        error_msg = f"错误: 登录配置文件 {config_file} 不存在，请先创建配置文件"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            TOKEN = config.get('token')
            USER_ID = config.get('user_id')

        if not TOKEN or not USER_ID:
            error_msg = "错误: 配置文件中缺少token或user_id"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            return False

        return True
    except Exception as e:
        error_msg = f"错误: 读取配置文件失败: {e}"
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False


def get_headers():
    """
    获取HTTP请求头，包含认证信息

    Returns:
        dict: HTTP请求头
    """
    return {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://hitrader.yueniusz.com',
        'Referer': 'https://hitrader.yueniusz.com/',
        'Sec-Ch-Ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }


@mcp.tool()
async def get_kline_data(symbol: str, exchange: str, resolution: str = "1D",
                        from_date: Optional[str] = None, to_date: Optional[str] = None,
                        fq: str = "post", fq_date: Optional[str] = None,
                        category: str = "stock", skip_paused: bool = False,
                        generate_chart: bool = False) -> str:
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

    # 处理日期参数
    if from_date is None:
        # 默认获取最近30天的数据
        from_date_ts = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp() * 1000)
    else:
        # 如果是日期字符串，转换为时间戳
        try:
            from_date_ts = int(datetime.datetime.strptime(from_date, "%Y-%m-%d").timestamp() * 1000)
        except ValueError:
            return f"错误: 无效的开始日期格式: {from_date}，应为YYYY-MM-DD"

    if to_date is None:
        # 默认获取到当前的数据
        to_date_ts = int(datetime.datetime.now().timestamp() * 1000)
    else:
        # 如果是日期字符串，转换为时间戳
        try:
            to_date_ts = int(datetime.datetime.strptime(to_date, "%Y-%m-%d").timestamp() * 1000)
        except ValueError:
            return f"错误: 无效的结束日期格式: {to_date}，应为YYYY-MM-DD"

    # 处理复权基准日期参数
    if fq_date is None:
        # 默认使用当前时间
        fq_date_ts = int(time.time() * 1000)
    else:
        # 如果是日期字符串，转换为时间戳
        try:
            fq_date_ts = int(datetime.datetime.strptime(fq_date, "%Y-%m-%d").timestamp() * 1000)
        except ValueError:
            return f"错误: 无效的复权基准日期格式: {fq_date}，应为YYYY-MM-DD"

    # 构建请求参数
    params = {
        "category": category,
        "exchange": exchange,
        "symbol": symbol,
        "resolution": resolution,
        "from_date": from_date_ts,
        "to_date": to_date_ts,
        "fq_date": fq_date_ts,
        "fq": fq,
        "skip_paused": str(skip_paused).lower(),
        "user_id": USER_ID
    }

    url = f"{BASE_URL}/trader-service/history"
    headers = get_headers()

    logger.debug(f"发送GET请求到: {url}")
    logger.debug(f"请求参数: {params}")
    logger.debug(f"请求头: {headers}")

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        logger.debug(f"收到响应: {data}")

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
                temp_dir = 'temp'
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, f"{symbol}_{exchange}_{resolution}_temp.csv")
                df.to_csv(temp_file, index=False)
                result += f"\n数据已临时保存到: {temp_file}"

                # 如果需要生成图表
                if generate_chart:
                    try:
                        # 生成图表
                        chart_file = chart_generator.generate_html(
                            df=df,
                            symbol=symbol,
                            exchange=exchange,
                            resolution=resolution,
                            fq=fq
                        )

                        # 在浏览器中打开图表
                        if chart_file:
                            chart_generator.open_in_browser(chart_file)
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

    except requests.exceptions.RequestException as e:
        return f"请求失败: {e}"
    except json.JSONDecodeError as e:
        return f"解析响应JSON失败: {e}"
    except Exception as e:
        return f"获取K线数据时发生未知错误: {e}"

if __name__ == "__main__":
    # 初始化并运行服务器
    # 使用stdio传输协议，这是与Claude桌面应用等客户端通信的标准方式
    mcp.run(transport='stdio')
