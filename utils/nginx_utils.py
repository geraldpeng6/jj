#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Nginx工具模块
提供与Nginx服务器交互的工具函数，主要用于生成HTML文件URL
"""

import os
import socket
import logging
import requests
from typing import Optional

# 获取日志记录器
logger = logging.getLogger('quant_mcp.nginx_utils')

def is_running_on_ec2() -> bool:
    """
    检测是否在EC2实例上运行

    Returns:
        bool: 是否在EC2实例上运行
    """
    try:
        # 尝试访问EC2元数据服务
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=0.1)
        return response.status_code == 200
    except:
        return False

def get_server_ip() -> str:
    """
    获取服务器IP地址
    
    如果在EC2上运行，尝试获取公网IP
    否则，返回本地IP地址
    
    Returns:
        str: 服务器IP地址
    """
    try:
        # 检查是否在EC2上运行
        if is_running_on_ec2():
            # 尝试从EC2元数据服务获取公网IP
            try:
                response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=0.5)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                logger.warning(f"无法从EC2元数据服务获取公网IP: {e}")
        
        # 如果不在EC2上运行或无法获取公网IP，使用本地IP
        # 创建一个临时socket连接，用于获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接到8.8.8.8，只是用来确定使用哪个网络接口
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"获取服务器IP失败: {e}")
        # 如果所有方法都失败，返回localhost
        return "localhost"

def generate_html_url(file_path: str) -> str:
    """
    生成HTML文件的URL
    
    Args:
        file_path: HTML文件路径
        
    Returns:
        str: HTML文件的URL
    """
    # 获取服务器IP
    server_ip = get_server_ip()
    
    # 获取文件名
    file_name = os.path.basename(file_path)
    
    # 构建URL
    url = f"http://{server_ip}/{file_name}"
    
    logger.info(f"生成HTML文件URL: {url}")
    return url

def get_chart_url(file_path: Optional[str] = None, file_name: Optional[str] = None) -> Optional[str]:
    """
    获取图表文件的URL
    
    Args:
        file_path: 图表文件的完整路径，与file_name二选一
        file_name: 图表文件名，与file_path二选一
        
    Returns:
        Optional[str]: 图表文件的URL，如果文件不存在则返回None
    """
    if file_path is None and file_name is None:
        logger.error("必须提供file_path或file_name参数")
        return None
    
    # 如果提供了file_path，从中提取file_name
    if file_path is not None:
        file_name = os.path.basename(file_path)
    
    # 检查文件是否存在
    charts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "charts")
    full_path = os.path.join(charts_dir, file_name)
    
    if not os.path.exists(full_path):
        logger.warning(f"图表文件不存在: {full_path}")
        return None
    
    # 生成URL
    return generate_html_url(full_path)
