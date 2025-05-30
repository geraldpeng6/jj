#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT回测数据测试脚本

该脚本运行指定策略的回测，并保存完整的MQTT数据
策略ID: Pgjpw3OdBknbEoxEOb0KMGr1mvyVZD5R
回测日期范围: 2024/05/31-2025/05/31
"""

import logging
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.backtest_utils import run_backtest, MQTTBacktestClient, get_mqtt_info
from utils.date_utils import get_beijing_now, validate_date_range
from utils.chart_generator import open_in_browser
from utils.chart_utils import check_existing_backtest
from utils.strategy_utils import get_strategy_detail

# 配置日志，设置为INFO级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('test_mqtt_backtest_data')

def run_mqtt_backtest():
    """运行回测并保存完整的MQTT数据"""
    # 策略ID
    strategy_id = "Pgjpw3OdBknbEoxEOb0KMGr1mvyVZD5R"
    
    # 获取策略详情
    logger.info(f"获取策略 {strategy_id} 的详情...")
    strategy_detail = get_strategy_detail(strategy_id)
    
    if not strategy_detail:
        logger.error(f"无法获取策略 {strategy_id} 的详情")
        return
    
    strategy_name = strategy_detail.get('strategy_name', '未命名策略')
    logger.info(f"策略名称: {strategy_name}")
    
    # 设置固定的回测日期范围 - 2024/05/31-2025/05/31
    start_date = "2024-05-31"
    end_date = "2025-05-31"
    start_date, end_date = validate_date_range(start_date, end_date)
    
    logger.info(f"回测日期范围: {start_date} 至 {end_date} (一年)")
    
    # 检查是否已存在相同回测
    existing_result = check_existing_backtest(strategy_id, start_date, end_date, choose_stock=None)
    if existing_result:
        logger.info(f"找到已存在的回测结果: {existing_result}")
        if input("已找到现有回测结果，是否重新运行? (y/n): ").lower() != 'y':
            logger.info(f"使用已有回测结果: {existing_result}")
            return
    
    # 增加监听时间，确保接收到所有MQTT数据
    listen_time = 120  # 增加到120秒
    
    # 运行回测
    logger.info(f"开始运行回测，监听时间设置为{listen_time}秒...")
    result = run_backtest(
        strategy_id=strategy_id,
        listen_time=listen_time,
        start_date=start_date,
        end_date=end_date
    )
    
    if not result.get('success'):
        logger.error(f"回测失败: {result.get('error')}")
        return
    
    # 输出回测结果
    position_count = result.get('position_count', 0)
    chart_path = result.get('chart_path')
    file_path = result.get('file_path')
    
    logger.info(f"回测完成，接收到 {position_count} 条position数据")
    logger.info(f"MQTT数据保存路径: {file_path}")
    
    if chart_path:
        logger.info(f"回测结果图表链接: {chart_path}")
        # 自动打开浏览器查看结果
        if open_in_browser(chart_path):
            logger.info("已在浏览器中打开回测结果")
    else:
        logger.warning("未生成回测图表")

    # 分析和显示MQTT数据
    if file_path and os.path.exists(file_path):
        analyze_mqtt_data(file_path)

def analyze_mqtt_data(file_path):
    """分析MQTT数据内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            mqtt_data = json.load(f)
        
        logger.info(f"===== MQTT数据分析 =====")
        logger.info(f"总数据条数: {len(mqtt_data)}")
        
        # 数据类型统计
        data_types = {}
        for item in mqtt_data:
            # 检查是否为原始二进制数据
            if 'raw_data' in item:
                data_type = item.get('format', 'unknown')
            # 检查是否包含positions字段
            elif 'positions' in item:
                data_type = 'positions'
            # 其他数据类型
            else:
                data_type = 'other'
            
            data_types[data_type] = data_types.get(data_type, 0) + 1
        
        logger.info(f"数据类型统计:")
        for data_type, count in data_types.items():
            logger.info(f"  - {data_type}: {count}条")
        
        # 显示示例数据
        if mqtt_data:
            sample_index = min(5, len(mqtt_data) - 1)
            sample_data = mqtt_data[sample_index]
            logger.info(f"示例数据 (第{sample_index+1}条):")
            
            # 打印主要字段，避免过长的输出
            sample_keys = list(sample_data.keys())
            logger.info(f"  字段: {', '.join(sample_keys)}")
            
            # 如果有positions字段，打印第一个position的信息
            if 'positions' in sample_data and sample_data['positions']:
                pos = sample_data['positions'][0]
                pos_info = {k: v for k, v in pos.items() if k in ['symbol', 'size', 'profit_and_loss', 'price']}
                logger.info(f"  第一个position: {pos_info}")
            
            # 如果有raw_data字段，打印其格式和一小部分内容
            if 'raw_data' in sample_data:
                raw_format = sample_data.get('format', 'unknown')
                raw_preview = sample_data['raw_data'][:50] + "..." if len(sample_data['raw_data']) > 50 else sample_data['raw_data']
                logger.info(f"  原始数据格式: {raw_format}")
                logger.info(f"  原始数据预览: {raw_preview}")
    
    except Exception as e:
        logger.error(f"分析MQTT数据失败: {e}")

def manual_mqtt_test():
    """手动测试MQTT连接和数据接收"""
    logger.info("开始手动MQTT连接测试...")
    
    # 获取MQTT连接信息
    mqtt_info = get_mqtt_info()
    if not mqtt_info:
        logger.error("无法获取MQTT连接信息")
        return
    
    # 创建MQTT客户端
    client = MQTTBacktestClient()
    
    # 连接到MQTT服务器
    if not client.connect(mqtt_info):
        logger.error("MQTT连接失败")
        return
    
    logger.info("MQTT连接成功，开始监听数据...")
    
    # 监听一段时间
    try:
        listen_time = 30  # 监听30秒
        logger.info(f"将监听{listen_time}秒...")
        time.sleep(listen_time)
    except KeyboardInterrupt:
        logger.info("监听被用户中断")
    
    # 断开连接
    client.disconnect()
    
    # 查看接收到的数据
    data_count = len(client.position_data)
    logger.info(f"共接收到{data_count}条MQTT数据")
    
    # 保存数据
    if data_count > 0:
        file_path = client.save_position_data("manual_test", "手动MQTT测试")
        if file_path:
            logger.info(f"数据已保存到: {file_path}")
            analyze_mqtt_data(file_path)

if __name__ == "__main__":
    # 如果命令行参数包含--manual，则运行手动测试
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        manual_mqtt_test()
    else:
        run_mqtt_backtest() 