#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML服务器工具模块

提供HTML文件服务功能，支持本地和远程服务器部署
"""

import os
import socket
import logging
import platform
from typing import Optional, Dict, Any, Tuple
from urllib.parse import quote

# 获取日志记录器
logger = logging.getLogger('quant_mcp.html_server')

# 默认配置
DEFAULT_SERVER_CONFIG = {
    "enabled": False,  # 默认不启用远程服务器
    "host": "localhost",  # 默认主机
    "port": 80,  # 默认端口
    "base_url": "",  # 基础URL，如果为空则自动构建
    "charts_dir": "data/charts",  # 图表目录
    "use_https": False,  # 是否使用HTTPS
}

# 服务器配置
SERVER_CONFIG = DEFAULT_SERVER_CONFIG.copy()


def load_server_config(config_file: str = 'data/config/server.json') -> bool:
    """
    从配置文件加载服务器配置

    Args:
        config_file: 配置文件路径，默认为'data/config/server.json'

    Returns:
        bool: 加载是否成功
    """
    global SERVER_CONFIG

    # 如果配置文件不存在，使用默认配置
    if not os.path.exists(config_file):
        logger.warning(f"服务器配置文件 {config_file} 不存在，使用默认配置")
        # 尝试获取本机IP地址
        SERVER_CONFIG["host"] = get_local_ip()
        return True

    try:
        import json
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 更新配置，保留默认值
            for key in DEFAULT_SERVER_CONFIG:
                if key in config:
                    SERVER_CONFIG[key] = config[key]

        # 如果base_url为空，则自动构建
        if not SERVER_CONFIG["base_url"]:
            protocol = "https" if SERVER_CONFIG["use_https"] else "http"
            port_str = f":{SERVER_CONFIG['port']}" if SERVER_CONFIG["port"] != 80 and SERVER_CONFIG["port"] != 443 else ""
            SERVER_CONFIG["base_url"] = f"{protocol}://{SERVER_CONFIG['host']}{port_str}"

        logger.info(f"已加载服务器配置: {SERVER_CONFIG}")
        return True
    except Exception as e:
        logger.error(f"加载服务器配置失败: {e}")
        return False


def get_local_ip() -> str:
    """
    获取本机IP地址

    Returns:
        str: 本机IP地址
    """
    try:
        # 创建一个临时socket连接来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"获取本机IP地址失败: {e}")
        return "localhost"


def is_running_on_server() -> bool:
    """
    检查是否在服务器上运行

    Returns:
        bool: 是否在服务器上运行
    """
    # 检查配置是否启用了服务器模式
    if SERVER_CONFIG["enabled"]:
        return True
    
    # 检查是否在EC2或其他云服务器上运行
    # 这里可以添加更多的检测逻辑
    hostname = socket.gethostname()
    if "ec2" in hostname.lower() or "aws" in hostname.lower():
        return True
    
    # 检查操作系统类型
    os_type = platform.system().lower()
    if os_type == "linux" and not os.path.exists("/home"):
        # 可能是服务器环境
        return True
    
    return False


def get_html_url(file_path: str) -> str:
    """
    获取HTML文件的URL

    Args:
        file_path: HTML文件路径

    Returns:
        str: HTML文件的URL
    """
    # 确保已加载配置
    if SERVER_CONFIG == DEFAULT_SERVER_CONFIG:
        load_server_config()
    
    # 检查是否在服务器上运行
    if not is_running_on_server() and not SERVER_CONFIG["enabled"]:
        # 本地模式，返回文件URL
        abs_path = os.path.abspath(file_path)
        return f"file://{abs_path}"
    
    # 服务器模式，构建URL
    # 从文件路径中提取相对路径
    charts_dir = SERVER_CONFIG["charts_dir"]
    if file_path.startswith(charts_dir):
        rel_path = file_path[len(charts_dir):].lstrip('/')
    else:
        # 如果不在charts_dir中，使用文件名
        rel_path = os.path.basename(file_path)
    
    # URL编码路径
    encoded_path = quote(rel_path)
    
    # 构建完整URL
    base_url = SERVER_CONFIG["base_url"]
    return f"{base_url}/{encoded_path}"


def create_nginx_config(output_file: str = 'data/config/nginx.conf') -> bool:
    """
    创建Nginx配置文件

    Args:
        output_file: 输出文件路径

    Returns:
        bool: 是否成功创建
    """
    try:
        # 确保已加载配置
        if SERVER_CONFIG == DEFAULT_SERVER_CONFIG:
            load_server_config()
        
        # 获取图表目录的绝对路径
        charts_dir = os.path.abspath(SERVER_CONFIG["charts_dir"])
        
        # 创建Nginx配置
        config = f"""# Nginx配置文件 - 为量化交易助手提供HTML文件服务
# 将此文件放置在 /etc/nginx/conf.d/ 目录下，然后重启Nginx

server {{
    listen 80;
    server_name _;  # 匹配所有域名

    # 日志配置
    access_log /var/log/nginx/quant_mcp_access.log;
    error_log /var/log/nginx/quant_mcp_error.log;

    # 只允许访问HTML文件
    location / {{
        root {charts_dir};
        
        # 只允许访问HTML文件
        location ~* \\.html$ {{
            # 设置MIME类型
            types {{
                text/html html;
            }}
            
            # 添加安全头
            add_header X-Content-Type-Options "nosniff";
            add_header X-XSS-Protection "1; mode=block";
            add_header X-Frame-Options "SAMEORIGIN";
            
            # 禁用目录列表
            autoindex off;
        }}
        
        # 拒绝访问其他文件
        location ~ \\. {{
            deny all;
        }}
        
        # 禁用目录列表
        autoindex off;
        
        # 默认返回403
        return 403;
    }}
}}
"""
        
        # 写入配置文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(config)
        
        logger.info(f"已创建Nginx配置文件: {output_file}")
        return True
    except Exception as e:
        logger.error(f"创建Nginx配置文件失败: {e}")
        return False


# 初始化时加载配置
load_server_config()
