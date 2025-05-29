#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
K线数据工具模块

提供K线数据获取和处理的核心功能
"""

import os
import json
import logging
import requests
import datetime
import pandas as pd
from typing import Optional, Union, Tuple

from utils.auth_utils import load_auth_config, get_auth_info, get_headers
from utils.date_utils import get_beijing_now, parse_date_string, validate_date_range

# 获取日志记录器
logger = logging.getLogger('quant_mcp.kline_utils')

# API基础URL
BASE_URL = "https://api.yueniusz.com"

def fetch_and_save_kline(
    symbol: str,
    exchange: str,
    resolution: str = "1D",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    fq: str = "post",
    fq_date: Optional[str] = None,
    category: str = "stock",
    skip_paused: bool = False,
    output_dir: str = "data/klines",
    file_format: str = "csv"
) -> Tuple[bool, Union[pd.DataFrame, str], Optional[str]]:
    """
    获取并保存K线数据

    Args:
        symbol: 股票代码，例如 "600000"
        exchange: 交易所代码，例如 "XSHG"
        resolution: 时间周期，例如 "1D"（日线）, "1"（1分钟）
        from_date: 开始日期，格式为YYYY-MM-DD, YYYY.MM.DD或YYYY/MM/DD，默认为一年前
        to_date: 结束日期，格式为YYYY-MM-DD, YYYY.MM.DD或YYYY/MM/DD，默认为当前日期
        fq: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
        fq_date: 复权基准日期，格式为YYYY-MM-DD，默认与to_date相同
        category: 品种类别，默认为 "stock"（股票）
        skip_paused: 是否跳过停牌日期，默认为 False
        output_dir: 输出目录，默认为"data/klines"
        file_format: 文件格式，支持"csv"和"excel"，默认为"csv"

    Returns:
        Tuple[bool, Union[pd.DataFrame, str], Optional[str]]:
            - 第一个元素表示是否成功
            - 第二个元素为成功时的DataFrame或失败时的错误信息
            - 第三个元素为成功时的文件路径，失败时为None
    """
    # 加载认证配置
    if not load_auth_config():
        return False, "错误: 无法加载认证配置", None

    if not symbol or not exchange:
        return False, "错误: 股票代码和交易所代码不能为空", None

    try:
        # 获取认证信息
        _, user_id = get_auth_info()
        if not user_id:
            return False, "错误: 无法获取认证信息", None

        # 验证并修复日期格式
        from_date, to_date = validate_date_range(from_date, to_date)
        
        # 处理日期参数
        # 获取当前北京时间和日期
        current_dt = get_beijing_now()
        current_date = current_dt.strftime("%Y-%m-%d")
        
        # 处理开始日期
        try:
            from_date_dt = datetime.datetime.strptime(from_date, "%Y-%m-%d")
            from_date_ts = int(from_date_dt.timestamp() * 1000)
        except (ValueError, TypeError):
            # 如果日期解析失败，使用一年前的日期
            from_date_dt = current_dt - datetime.timedelta(days=365)
            from_date_ts = int(from_date_dt.timestamp() * 1000)
            from_date = from_date_dt.strftime("%Y-%m-%d")
            logger.warning(f"开始日期格式无效，已使用默认日期: {from_date}")
            
        # 处理结束日期
        try:
            to_date_dt = datetime.datetime.strptime(to_date, "%Y-%m-%d")
            to_date_ts = int(to_date_dt.timestamp() * 1000)
            # 如果结束日期在未来，记录一条信息
            if to_date_dt.date() > current_dt.date():
                logger.info(f"请求的结束日期 {to_date} 在未来，实际可能只返回到当前日期 {current_date} 的数据")
        except (ValueError, TypeError):
            # 如果日期解析失败，使用当前日期
            to_date_dt = current_dt
            to_date_ts = int(to_date_dt.timestamp() * 1000)
            to_date = current_date
            logger.warning(f"结束日期格式无效，已使用当前日期: {to_date}")

        # 处理复权基准日期 - 始终使用to_date作为fq_date
        if fq_date is None:
            # 使用to_date作为复权基准日期
            fq_date_ts = to_date_ts
        else:
            try:
                # 尝试解析和验证fq_date
                fq_date_parsed = parse_date_string(fq_date)
                if fq_date_parsed:
                    fq_date = fq_date_parsed.strftime("%Y-%m-%d")
                    fq_date_ts = int(fq_date_parsed.timestamp() * 1000)
                else:
                    # 如果日期无效，使用to_date
                    logger.warning(f"复权基准日期 '{fq_date}' 无效，使用结束日期 {to_date} 作为复权基准")
                    fq_date = to_date
                    fq_date_ts = to_date_ts
            except Exception as e:
                logger.warning(f"解析复权基准日期异常: {e}，使用结束日期 {to_date} 作为复权基准")
                fq_date = to_date
                fq_date_ts = to_date_ts

        # 构建请求参数
        params = {
            "category": category,
            "exchange": exchange,
            "symbol": symbol,
            "resolution": resolution,
            "from_date": from_date_ts,
            "to_date": to_date_ts,
            "fq": fq,
            "fq_date": fq_date_ts,
            "skip_paused": str(skip_paused).lower(),
            "user_id": user_id
        }

        url = f"{BASE_URL}/trader-service/history"
        headers = get_headers()

        logger.debug(f"发送GET请求到: {url}")
        logger.debug(f"请求参数: {params}")
        logger.debug(f"请求头: {headers}")

        # 发送API请求
        # 如果响应使用压缩，可能会导致JSON解析错误，所以我们使用不压缩的请求
        headers_no_compression = headers.copy()
        headers_no_compression['Accept-Encoding'] = 'identity'

        response = requests.get(url, params=params, headers=headers_no_compression)
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
                
                # 记录日期范围
                actual_start_date = df['time'].min().strftime('%Y-%m-%d')
                actual_end_date = df['time'].max().strftime('%Y-%m-%d')
                logger.info(f"实际获取到的数据日期范围: {actual_start_date} 至 {actual_end_date}")
                
                # 如果请求的结束日期在未来，但实际数据没有达到今天，记录警告
                if to_date > current_date and actual_end_date < current_date:
                    logger.warning(f"请求了未来日期 {to_date}，但最新数据仅到 {actual_end_date}，可能是数据源尚未更新")

                # 按时间排序
                df = df.sort_values('time')

                # 保存数据到文件
                try:
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
                        return False, f"错误: 不支持的文件格式: {file_format}，支持的格式有: csv, excel", None

                    # 获取绝对路径
                    abs_file_path = os.path.abspath(file_path)
                    logger.info(f"成功保存K线数据到文件: {abs_file_path}，共 {len(df)} 条记录")
                    return True, df, abs_file_path
                except Exception as e:
                    logger.error(f"保存K线数据时发生错误: {e}")
                    return False, f"保存K线数据时发生错误: {e}", None
            else:
                return False, "获取K线数据成功，但数据为空", None
        else:
            return False, f"获取K线数据失败: {data.get('msg', '未知错误')}", None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return False, f"请求失败: {e}", None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        return False, f"解析响应JSON失败: {e}", None
    except Exception as e:
        logger.error(f"获取K线数据时发生错误: {e}")
        return False, f"获取K线数据时发生错误: {e}", None
