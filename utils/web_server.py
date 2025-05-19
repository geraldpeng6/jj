#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web服务器模块

提供静态文件服务，用于托管图表HTML文件
"""

import os
import logging
import threading
import requests
from typing import Optional, Tuple
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import socket

# 获取日志记录器
logger = logging.getLogger('quant_mcp.web_server')

# 全局变量，存储服务器实例
_server_instance = None
_server_thread = None
_server_port = None
_server_host = None
_server_root = None
_public_ip = None

class ChartRequestHandler(SimpleHTTPRequestHandler):
    """处理图表请求的HTTP请求处理器"""

    def __init__(self, *args, **kwargs):
        # 设置目录为指定的根目录
        self.directory = _server_root
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """重写日志方法，使用我们的日志记录器"""
        logger.debug("%s - - [%s] %s" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format % args))

    def list_directory(self, path):
        """
        禁用目录浏览功能
        """
        # 返回403 Forbidden错误
        self.send_error(403, "目录浏览功能已禁用")
        return None

    def do_GET(self):
        """
        处理GET请求，只允许访问特定的HTML文件
        """
        # 获取请求的文件路径
        file_path = self.translate_path(self.path)

        # 如果请求的是目录，返回403错误
        if os.path.isdir(file_path):
            self.send_error(403, "目录浏览功能已禁用")
            return

        # 如果请求的不是HTML文件，返回403错误
        if not file_path.endswith('.html'):
            self.send_error(403, "只允许访问HTML文件")
            return

        # 调用父类方法处理请求
        return super().do_GET()

def get_free_port(start_port=8080, max_attempts=100):
    """
    获取一个可用的端口号

    Args:
        start_port: 起始端口号
        max_attempts: 最大尝试次数

    Returns:
        int: 可用的端口号，如果没有找到则返回None
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def get_public_ip() -> Optional[str]:
    """
    获取公网IP地址

    Returns:
        Optional[str]: 公网IP地址，如果获取失败则返回None
    """
    try:
        # 使用公共API获取公网IP
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        logger.error(f"获取公网IP失败: {e}")

    return None

def get_local_ip() -> Optional[str]:
    """
    获取本地IP地址

    Returns:
        Optional[str]: 本地IP地址，如果获取失败则返回None
    """
    try:
        # 创建一个临时socket连接，用于获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接到8.8.8.8，只是用来确定使用哪个网络接口
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"获取本地IP失败: {e}")
        return None

def start_server(root_dir: str = "data/charts", host: str = "0.0.0.0", port: Optional[int] = None) -> Optional[int]:
    """
    启动Web服务器

    Args:
        root_dir: 根目录，存放HTML文件的目录
        host: 主机地址
        port: 端口号，如果为None则自动选择一个可用端口

    Returns:
        Optional[int]: 服务器端口号，如果启动失败则返回None
    """
    global _server_instance, _server_thread, _server_port, _server_host, _server_root, _public_ip

    # 如果服务器已经在运行，则返回当前端口
    if _server_instance is not None and _server_thread is not None and _server_thread.is_alive():
        return _server_port

    try:
        # 确保根目录存在
        os.makedirs(root_dir, exist_ok=True)

        # 如果没有指定端口，则自动选择一个可用端口
        if port is None:
            port = get_free_port()
            if port is None:
                logger.error("无法找到可用端口")
                return None

        # 设置全局变量
        _server_root = os.path.abspath(root_dir)
        _server_host = host
        _server_port = port

        # 尝试获取公网IP
        _public_ip = get_public_ip()

        # 创建HTTP服务器
        handler = ChartRequestHandler
        _server_instance = socketserver.TCPServer((host, port), handler)

        # 在新线程中启动服务器
        _server_thread = threading.Thread(target=_server_instance.serve_forever)
        _server_thread.daemon = True  # 设置为守护线程，这样主程序退出时，服务器也会退出
        _server_thread.start()

        # 获取本地IP用于日志显示
        local_ip = get_local_ip() or host

        # 记录服务器信息
        if _public_ip:
            logger.info(f"Web服务器已启动，本地地址: http://{local_ip}:{port}/, 公网地址: http://{_public_ip}:{port}/")
        else:
            logger.info(f"Web服务器已启动，地址: http://{local_ip}:{port}/")

        return port

    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        return None

def stop_server():
    """停止Web服务器"""
    global _server_instance, _server_thread, _server_port, _server_host, _server_root, _public_ip

    if _server_instance is not None:
        try:
            _server_instance.shutdown()
            _server_instance.server_close()
            _server_instance = None
            _server_thread = None
            _server_port = None
            _server_host = None
            _server_root = None
            _public_ip = None
            logger.info("Web服务器已停止")
        except Exception as e:
            logger.error(f"停止Web服务器失败: {e}")

def get_file_url(file_path: str, use_public_ip: bool = True) -> Optional[str]:
    """
    获取文件的URL

    Args:
        file_path: 文件路径
        use_public_ip: 是否使用公网IP，默认为True

    Returns:
        Optional[str]: 文件URL，如果服务器未启动或文件不存在则返回None
    """
    global _server_port, _server_host, _server_root, _public_ip

    if _server_instance is None or _server_port is None:
        logger.warning("Web服务器未启动")
        return None

    # 获取文件的绝对路径
    abs_file_path = os.path.abspath(file_path)

    # 检查文件是否存在
    if not os.path.exists(abs_file_path):
        logger.error(f"文件不存在: {abs_file_path}")
        return None

    # 检查文件是否在根目录下
    if not abs_file_path.startswith(_server_root):
        logger.error(f"文件不在服务器根目录下: {abs_file_path}")
        return None

    # 检查文件是否是HTML文件
    if not abs_file_path.endswith('.html'):
        logger.error(f"只允许访问HTML文件: {abs_file_path}")
        return None

    # 计算相对路径
    rel_path = os.path.relpath(abs_file_path, _server_root)

    # 构建URL
    host = _public_ip if use_public_ip and _public_ip else get_local_ip() or _server_host
    url = f"http://{host}:{_server_port}/{rel_path}"

    # 记录URL但不记录本地文件路径
    logger.info(f"生成文件URL: {url}")

    return url
