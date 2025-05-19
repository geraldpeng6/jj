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
        logger.debug(f"ChartRequestHandler初始化，设置目录为: {self.directory}")

        # 确保目录存在
        if not os.path.exists(self.directory):
            logger.warning(f"目录不存在，尝试创建: {self.directory}")
            try:
                os.makedirs(self.directory, exist_ok=True)
            except Exception as e:
                logger.error(f"创建目录失败: {e}")

        # 检查目录是否可访问
        if not os.access(self.directory, os.R_OK):
            logger.warning(f"目录不可读: {self.directory}")

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
        self.send_error(403, "Directory listing disabled")  # 使用英文错误消息
        return None

    def end_headers(self):
        """添加CORS头和安全头，允许跨域访问"""
        # CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        # 缓存控制
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')

        # 安全头
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'SAMEORIGIN')
        self.send_header('X-XSS-Protection', '1; mode=block')

        # 内容安全策略，禁止自动升级到HTTPS
        self.send_header('Content-Security-Policy', "upgrade-insecure-requests 'none'")

        # 完成头部发送
        super().end_headers()

    def do_GET(self):
        """
        处理GET请求，只允许访问特定的HTML文件
        """
        # 记录请求信息
        logger.info(f"收到GET请求: {self.path}")

        # 获取请求的文件路径
        file_path = self.translate_path(self.path)
        logger.debug(f"原始请求文件路径: {file_path}")

        # 直接从请求路径获取文件名
        file_name = os.path.basename(self.path)

        # 首先尝试在服务器根目录下查找文件
        root_path = os.path.join(_server_root, file_name)
        logger.debug(f"尝试在服务器根目录下查找文件: {root_path}")

        # 如果文件存在于服务器根目录，使用该路径
        if os.path.exists(root_path) and os.path.isfile(root_path):
            file_path = root_path
            logger.debug(f"文件在服务器根目录中找到: {file_path}")
        else:
            logger.debug(f"文件在服务器根目录中未找到，尝试原始路径: {file_path}")

        logger.debug(f"最终使用的文件路径: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 记录更多调试信息
            logger.warning(f"文件不存在: {file_path}")
            logger.warning(f"服务器根目录: {_server_root}")
            logger.warning(f"当前工作目录: {os.getcwd()}")

            # 列出服务器根目录中的文件
            try:
                files = os.listdir(_server_root)
                logger.debug(f"服务器根目录中的文件: {files}")
            except Exception as e:
                logger.error(f"无法列出服务器根目录中的文件: {e}")

        # 如果请求的是目录，返回403错误
        if os.path.isdir(file_path):
            logger.warning(f"拒绝访问目录: {self.path}")
            self.send_error(403, "Directory listing disabled")  # 使用英文错误消息
            return

        # 如果请求的不是HTML文件，返回403错误
        if not file_path.endswith('.html') and not self.path == '/favicon.ico':
            logger.warning(f"拒绝访问非HTML文件: {self.path}")
            self.send_error(403, "Only HTML files are allowed")  # 使用英文错误消息
            return

        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 特殊处理favicon.ico请求
            if self.path == '/favicon.ico':
                self.send_error(404, "File not found")
                return

            # 尝试在当前工作目录下查找文件
            cwd_path = os.path.join(os.getcwd(), os.path.basename(self.path))
            logger.debug(f"尝试在当前工作目录下查找文件: {cwd_path}")

            if os.path.exists(cwd_path) and os.path.isfile(cwd_path):
                file_path = cwd_path
                logger.debug(f"文件在当前工作目录中找到: {file_path}")
            else:
                # 尝试在data目录下查找文件
                data_path = os.path.join(os.getcwd(), "data", os.path.basename(self.path))
                logger.debug(f"尝试在data目录下查找文件: {data_path}")

                if os.path.exists(data_path) and os.path.isfile(data_path):
                    file_path = data_path
                    logger.debug(f"文件在data目录中找到: {file_path}")
                else:
                    # 尝试在data/charts目录下查找文件
                    charts_path = os.path.join(os.getcwd(), "data", "charts", os.path.basename(self.path))
                    logger.debug(f"尝试在data/charts目录下查找文件: {charts_path}")

                    if os.path.exists(charts_path) and os.path.isfile(charts_path):
                        file_path = charts_path
                        logger.debug(f"文件在data/charts目录中找到: {file_path}")
                    else:
                        logger.warning(f"请求的文件在所有可能的位置都不存在: {self.path}")
                        self.send_error(404, "File not found")  # 使用英文错误消息
                        return

        # 如果是HTML文件，设置正确的Content-Type
        if file_path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Server', 'QuantMCP/1.0')
            self.send_header('Connection', 'keep-alive')

            # 明确指示这是HTTP协议
            self.send_header('X-Served-By', 'QuantMCP HTTP Server')

            # 添加安全头
            self.end_headers()

            # 读取文件内容并发送
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()

                    # 在HTML内容中添加meta标签，防止浏览器自动升级到HTTPS
                    if content.startswith(b'<!DOCTYPE html>') or content.startswith(b'<html'):
                        meta_tag = b'<meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests \'none\'">'
                        if b'<head>' in content:
                            content = content.replace(b'<head>', b'<head>' + meta_tag)
                        else:
                            content = content.replace(b'<html>', b'<html><head>' + meta_tag + b'</head>')

                    self.wfile.write(content)
                logger.info(f"成功提供文件: {os.path.basename(file_path)}")
                return
            except Exception as e:
                logger.error(f"读取或发送文件时出错: {e}")
                self.send_error(500, "Internal Server Error")
                return
        else:
            # 对于其他类型的文件，使用父类方法处理
            logger.info(f"提供文件: {os.path.basename(file_path)}")
            return super().do_GET()

    def do_OPTIONS(self):
        """处理OPTIONS请求，支持CORS预检请求"""
        self.send_response(200)
        self.end_headers()
        return

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
        logger.info(f"服务器根目录设置为: {_server_root}")

        # 检查根目录中的文件
        try:
            files = os.listdir(_server_root)
            logger.info(f"服务器根目录中的文件: {files}")
        except Exception as e:
            logger.error(f"无法列出服务器根目录中的文件: {e}")

        _server_host = host
        _server_port = port

        # 尝试获取公网IP
        _public_ip = get_public_ip()

        # 创建HTTP服务器
        handler = ChartRequestHandler

        # 允许端口复用，避免"Address already in use"错误
        socketserver.TCPServer.allow_reuse_address = True

        try:
            _server_instance = socketserver.TCPServer((host, port), handler)
            logger.info(f"服务器成功绑定到 {host}:{port}")
        except Exception as e:
            logger.error(f"服务器绑定失败: {e}")
            # 尝试使用localhost
            try:
                logger.info("尝试绑定到localhost...")
                _server_instance = socketserver.TCPServer(("localhost", port), handler)
                logger.info(f"服务器成功绑定到 localhost:{port}")
            except Exception as e2:
                logger.error(f"绑定到localhost也失败: {e2}")
                return None

        # 在新线程中启动服务器
        _server_thread = threading.Thread(target=_server_instance.serve_forever)
        _server_thread.daemon = True  # 设置为守护线程，这样主程序退出时，服务器也会退出
        _server_thread.start()

        # 验证服务器是否正在运行
        if not _server_thread.is_alive():
            logger.error("服务器线程未能成功启动")
            return None

        logger.info(f"服务器线程已启动，ID: {_server_thread.ident}")

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

def get_file_url(file_path: str, use_public_ip: bool = True, force_localhost: bool = False) -> Optional[str]:
    """
    获取文件的URL

    Args:
        file_path: 文件路径
        use_public_ip: 是否使用公网IP，默认为True
        force_localhost: 是否强制使用localhost，用于本地测试，默认为False

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

    # 只使用文件名，而不是相对路径，避免暴露目录结构
    file_name = os.path.basename(abs_file_path)

    # 构建URL
    if force_localhost:
        # 强制使用localhost，用于本地测试
        host = "localhost"
    else:
        # 根据配置选择IP
        local_ip = get_local_ip() or "localhost"
        host = _public_ip if use_public_ip and _public_ip else local_ip

    url = f"http://{host}:{_server_port}/{file_name}"

    # 同时生成本地URL，确保至少有一个可用
    local_url = f"http://localhost:{_server_port}/{file_name}"

    # 记录URL但不记录本地文件路径
    logger.info(f"生成文件URL: {url}")
    logger.info(f"本地访问URL: {local_url}")

    # 返回首选URL
    return url

def get_all_urls(file_path: str) -> dict:
    """
    获取文件的所有可能的URL（公网、局域网、本地）

    Args:
        file_path: 文件路径

    Returns:
        dict: 包含不同类型URL的字典
    """
    global _server_port, _server_host, _server_root, _public_ip

    if _server_instance is None or _server_port is None:
        logger.warning("Web服务器未启动")
        return {"error": "服务器未启动"}

    # 获取文件的绝对路径
    abs_file_path = os.path.abspath(file_path)

    # 检查文件是否存在
    if not os.path.exists(abs_file_path):
        logger.error(f"文件不存在: {abs_file_path}")
        return {"error": "文件不存在"}

    # 检查文件是否在根目录下
    if not abs_file_path.startswith(_server_root):
        logger.error(f"文件不在服务器根目录下: {abs_file_path}")
        return {"error": "文件不在服务器根目录下"}

    # 检查文件是否是HTML文件
    if not abs_file_path.endswith('.html'):
        logger.error(f"只允许访问HTML文件: {abs_file_path}")
        return {"error": "只允许访问HTML文件"}

    # 只使用文件名，而不是相对路径，避免暴露目录结构
    file_name = os.path.basename(abs_file_path)

    # 获取本地IP
    local_ip = get_local_ip() or "localhost"

    # 构建不同的URL
    urls = {
        "public": f"http://{_public_ip}:{_server_port}/{file_name}" if _public_ip else None,
        "local": f"http://{local_ip}:{_server_port}/{file_name}" if local_ip != "localhost" else None,
        "localhost": f"http://localhost:{_server_port}/{file_name}"
    }

    logger.info(f"生成多个URL选项: {urls}")
    return urls
