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
import json
from typing import Optional, Dict, Any

# 获取日志记录器
logger = logging.getLogger('quant_mcp.nginx_utils')

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config", "nginx_config.json")

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

    优先使用配置中的公网IP
    如果配置中没有公网IP，则尝试从EC2元数据服务获取
    如果不在EC2上运行或无法获取公网IP，使用本地IP地址

    Returns:
        str: 服务器IP地址
    """
    try:
        # 首先尝试从配置中获取公网IP
        config = load_nginx_config()
        if config.get("use_public_ip", True) and config.get("public_ip"):
            logger.info(f"使用配置中的公网IP: {config['public_ip']}")
            return config["public_ip"]

        # 检查是否在EC2上运行
        if is_running_on_ec2():
            # 尝试从EC2元数据服务获取公网IP
            try:
                response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=0.5)
                if response.status_code == 200:
                    public_ip = response.text
                    # 保存到配置中
                    set_public_ip(public_ip)
                    return public_ip
            except Exception as e:
                logger.warning(f"无法从EC2元数据服务获取公网IP: {e}")

        # 如果不在EC2上运行或无法获取公网IP，尝试从外部服务获取公网IP
        try:
            # 使用ipify API获取公网IP
            response = requests.get('https://api.ipify.org', timeout=2)
            if response.status_code == 200:
                public_ip = response.text
                # 保存到配置中
                set_public_ip(public_ip)
                logger.info(f"从ipify获取到公网IP: {public_ip}")
                return public_ip
        except Exception as e:
            logger.warning(f"无法从ipify获取公网IP: {e}")

            # 尝试使用其他服务
            try:
                response = requests.get('https://ifconfig.me', timeout=2)
                if response.status_code == 200:
                    public_ip = response.text
                    # 保存到配置中
                    set_public_ip(public_ip)
                    logger.info(f"从ifconfig.me获取到公网IP: {public_ip}")
                    return public_ip
            except Exception as e:
                logger.warning(f"无法从ifconfig.me获取公网IP: {e}")

        # 如果无法获取公网IP，使用本地IP
        # 创建一个临时socket连接，用于获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接到8.8.8.8，只是用来确定使用哪个网络接口
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"使用本地IP: {local_ip}")
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

def load_nginx_config() -> Dict[str, Any]:
    """
    加载Nginx配置

    Returns:
        Dict[str, Any]: Nginx配置
    """
    default_config = {
        "public_ip": None,
        "use_public_ip": True,
        "port": 80
    }

    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            # 如果配置文件不存在，创建默认配置
            save_nginx_config(default_config)
            return default_config
    except Exception as e:
        logger.error(f"加载Nginx配置失败: {e}")
        return default_config

def save_nginx_config(config: Dict[str, Any]) -> bool:
    """
    保存Nginx配置

    Args:
        config: Nginx配置

    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保配置目录存在
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        logger.info("Nginx配置已保存")
        return True
    except Exception as e:
        logger.error(f"保存Nginx配置失败: {e}")
        return False

def set_public_ip(ip: str) -> bool:
    """
    设置公网IP

    Args:
        ip: 公网IP

    Returns:
        bool: 是否设置成功
    """
    config = load_nginx_config()
    config["public_ip"] = ip
    return save_nginx_config(config)

def get_public_ip_from_config() -> Optional[str]:
    """
    从配置中获取公网IP

    Returns:
        Optional[str]: 公网IP，如果未设置则返回None
    """
    config = load_nginx_config()
    return config.get("public_ip")

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
