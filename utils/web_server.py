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
import ssl
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
_https_enabled = False
_https_port = None
_cert_file = None
_key_file = None

# HTTPS服务器类
class HTTPSServer(HTTPServer):
    """支持HTTPS的服务器类"""

    def __init__(self, server_address, RequestHandlerClass, certfile, keyfile, bind_and_activate=True):
        HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)
        self.certfile = certfile
        self.keyfile = keyfile
        self.socket = ssl.wrap_socket(
            self.socket,
            server_side=True,
            certfile=certfile,
            keyfile=keyfile,
            ssl_version=ssl.PROTOCOL_TLS
        )

def generate_self_signed_cert(cert_dir="certs"):
    """
    生成自签名证书

    Args:
        cert_dir: 证书存放目录

    Returns:
        tuple: (证书文件路径, 密钥文件路径)
    """
    try:
        # 确保证书目录存在
        os.makedirs(cert_dir, exist_ok=True)

        cert_file = os.path.join(cert_dir, "server.crt")
        key_file = os.path.join(cert_dir, "server.key")

        # 如果证书已存在，直接返回
        if os.path.exists(cert_file) and os.path.exists(key_file):
            logger.info(f"使用现有证书: {cert_file}")
            return cert_file, key_file

        # 生成私钥
        os.system(f'openssl genrsa -out {key_file} 2048')

        # 生成证书签名请求
        os.system(f'openssl req -new -key {key_file} -out {cert_dir}/server.csr -subj "/CN=localhost"')

        # 生成自签名证书
        os.system(f'openssl x509 -req -days 3650 -in {cert_dir}/server.csr -signkey {key_file} -out {cert_file}')

        logger.info(f"已生成自签名证书: {cert_file}")
        return cert_file, key_file
    except Exception as e:
        logger.error(f"生成自签名证书失败: {e}")
        return None, None

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

def get_free_port(start_port=80, max_attempts=100):
    """
    获取一个可用的端口号

    Args:
        start_port: 起始端口号，默认为80（HTTP标准端口）
        max_attempts: 最大尝试次数

    Returns:
        int: 可用的端口号，如果没有找到则返回None
    """
    # 首先尝试使用标准端口80
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', start_port))
            return start_port
    except OSError:
        # 如果端口80不可用（可能需要root权限或已被占用），尝试其他端口
        logger.warning(f"端口 {start_port} 不可用，尝试其他端口")

        # 如果是标准端口但不可用，从8080开始尝试
        if start_port < 1024:
            start_port = 8080

    # 尝试其他端口
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
    # 尝试多个公共API获取公网IP
    apis = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ident.me',
        'https://ipecho.net/plain'
    ]

    for api in apis:
        try:
            logger.debug(f"尝试从 {api} 获取公网IP")
            response = requests.get(api, timeout=5)
            if response.status_code == 200:
                ip = response.text.strip()
                logger.info(f"成功获取公网IP: {ip}")
                return ip
        except Exception as e:
            logger.debug(f"从 {api} 获取公网IP失败: {e}")

    logger.error("所有API都无法获取公网IP")
    return None

def check_port_open(host: str, port: int) -> bool:
    """
    检查指定主机的端口是否开放

    Args:
        host: 主机地址
        port: 端口号

    Returns:
        bool: 端口是否开放
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception as e:
        logger.error(f"检查端口开放状态失败: {e}")
        return False

def can_use_privileged_port() -> bool:
    """
    检查当前进程是否有权限使用特权端口（小于1024的端口）

    Returns:
        bool: 是否有权限使用特权端口
    """
    # 尝试绑定到端口80
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 80))
        s.close()
        return True
    except OSError:
        return False

def diagnose_network() -> dict:
    """
    诊断网络连接状态

    Returns:
        dict: 诊断结果
    """
    result = {
        "local_ip": get_local_ip(),
        "public_ip": get_public_ip(),
        "http_port": _server_port,
        "https_port": _https_port,
        "http_port_open": False,
        "https_port_open": False,
        "server_running": False,
        "https_enabled": _https_enabled,
        "can_use_privileged_port": can_use_privileged_port()
    }

    # 检查服务器是否运行
    if _server_instance is not None and _server_thread is not None and _server_thread.is_alive():
        result["server_running"] = True

        # 检查HTTP端口是否开放
        if result["local_ip"] and _server_port:
            result["http_port_open_local"] = check_port_open(result["local_ip"], _server_port)

        if result["public_ip"] and _server_port:
            result["http_port_open_public"] = check_port_open(result["public_ip"], _server_port)

        # 如果启用了HTTPS，检查HTTPS端口是否开放
        if _https_enabled and _https_port:
            if result["local_ip"]:
                result["https_port_open_local"] = check_port_open(result["local_ip"], _https_port)

            if result["public_ip"]:
                result["https_port_open_public"] = check_port_open(result["public_ip"], _https_port)

    # 添加诊断建议
    result["suggestions"] = []

    if not result["public_ip"]:
        result["suggestions"].append("无法获取公网IP，请检查网络连接")

    if result.get("http_port_open_local", False) and not result.get("http_port_open_public", False):
        result["suggestions"].append(f"HTTP端口 {_server_port} 在本地可访问但在公网不可访问，可能需要配置端口转发或检查防火墙设置")

    if _https_enabled and result.get("https_port_open_local", False) and not result.get("https_port_open_public", False):
        result["suggestions"].append(f"HTTPS端口 {_https_port} 在本地可访问但在公网不可访问，可能需要配置端口转发或检查防火墙设置")

    # 添加特权端口相关的建议
    if not result["can_use_privileged_port"]:
        if _server_port != 80:
            result["suggestions"].append("当前进程无权使用标准HTTP端口80，正在使用备用端口。如需使用标准端口，请以管理员/root权限运行程序")

        if _https_enabled and _https_port != 443:
            result["suggestions"].append("当前进程无权使用标准HTTPS端口443，正在使用备用端口。如需使用标准端口，请以管理员/root权限运行程序")

    return result

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

def start_server(root_dir: str = "data/charts", host: str = "0.0.0.0", port: Optional[int] = None,
               enable_https: bool = False, https_port: Optional[int] = None) -> Optional[int]:
    """
    启动Web服务器

    Args:
        root_dir: 根目录，存放HTML文件的目录
        host: 主机地址
        port: 端口号，如果为None则自动选择一个可用端口
        enable_https: 是否启用HTTPS，默认为False
        https_port: HTTPS端口号，如果为None则自动选择一个可用端口

    Returns:
        Optional[int]: 服务器端口号，如果启动失败则返回None
    """
    global _server_instance, _server_thread, _server_port, _server_host, _server_root, _public_ip
    global _https_enabled, _https_port, _cert_file, _key_file

    # 如果服务器已经在运行，则返回当前端口
    if _server_instance is not None and _server_thread is not None and _server_thread.is_alive():
        return _server_port

    try:
        # 确保根目录存在
        os.makedirs(root_dir, exist_ok=True)

        # 如果没有指定端口，则尝试使用标准端口80
        if port is None:
            # 检查是否有权限使用特权端口
            if can_use_privileged_port():
                port = 80
                logger.info("使用HTTP标准端口80")
            else:
                # 如果没有权限，则自动选择一个可用端口
                port = get_free_port(start_port=8080)
                if port is None:
                    logger.error("无法找到可用端口")
                    return None
                logger.warning(f"无权使用端口80，使用备用端口: {port}")

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

        # 设置全局变量
        _https_enabled = enable_https

        # 创建HTTP服务器
        handler = ChartRequestHandler

        # 允许端口复用，避免"Address already in use"错误
        socketserver.TCPServer.allow_reuse_address = True

        # 启动HTTP服务器
        try:
            _server_instance = socketserver.TCPServer((host, port), handler)
            logger.info(f"HTTP服务器成功绑定到 {host}:{port}")
        except Exception as e:
            logger.error(f"HTTP服务器绑定失败: {e}")
            # 尝试使用localhost
            try:
                logger.info("尝试绑定到localhost...")
                _server_instance = socketserver.TCPServer(("localhost", port), handler)
                logger.info(f"HTTP服务器成功绑定到 localhost:{port}")
            except Exception as e2:
                logger.error(f"绑定到localhost也失败: {e2}")
                return None

        # 在新线程中启动HTTP服务器
        _server_thread = threading.Thread(target=_server_instance.serve_forever)
        _server_thread.daemon = True  # 设置为守护线程，这样主程序退出时，服务器也会退出
        _server_thread.start()

        # 如果启用HTTPS，启动HTTPS服务器
        if enable_https:
            # 如果没有指定HTTPS端口，则尝试使用标准端口443
            if https_port is None:
                # 检查是否有权限使用特权端口
                if can_use_privileged_port():
                    https_port = 443
                    logger.info("使用HTTPS标准端口443")
                else:
                    # 如果没有权限，则自动选择一个可用端口
                    https_port = get_free_port(start_port=8443)
                    if https_port is None:
                        logger.error("无法为HTTPS找到可用端口")
                        return port  # 仍然返回HTTP端口
                    logger.warning(f"无权使用端口443，使用备用端口: {https_port}")

            # 生成自签名证书
            _cert_file, _key_file = generate_self_signed_cert()
            if _cert_file is None or _key_file is None:
                logger.error("生成自签名证书失败，无法启动HTTPS服务器")
                return port  # 仍然返回HTTP端口

            # 启动HTTPS服务器
            try:
                https_server = HTTPSServer((host, https_port), handler, _cert_file, _key_file)
                logger.info(f"HTTPS服务器成功绑定到 {host}:{https_port}")

                # 在新线程中启动HTTPS服务器
                https_thread = threading.Thread(target=https_server.serve_forever)
                https_thread.daemon = True
                https_thread.start()

                # 设置全局变量
                _https_port = https_port
                logger.info(f"HTTPS服务器已启动，端口: {https_port}")
            except Exception as e:
                logger.error(f"启动HTTPS服务器失败: {e}")
                # 仍然返回HTTP端口
                return port

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

    # 构建HTTP URL
    http_url = f"http://{host}:{_server_port}/{file_name}"

    # 如果启用了HTTPS，构建HTTPS URL
    https_url = None
    if _https_enabled and _https_port is not None:
        https_url = f"https://{host}:{_https_port}/{file_name}"

    # 选择返回的URL，优先使用HTTPS
    url = https_url if https_url else http_url

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
        "public_http": f"http://{_public_ip}:{_server_port}/{file_name}" if _public_ip else None,
        "local_http": f"http://{local_ip}:{_server_port}/{file_name}" if local_ip != "localhost" else None,
        "localhost_http": f"http://localhost:{_server_port}/{file_name}"
    }

    # 如果启用了HTTPS，添加HTTPS URL
    if _https_enabled and _https_port is not None:
        urls.update({
            "public_https": f"https://{_public_ip}:{_https_port}/{file_name}" if _public_ip else None,
            "local_https": f"https://{local_ip}:{_https_port}/{file_name}" if local_ip != "localhost" else None,
            "localhost_https": f"https://localhost:{_https_port}/{file_name}"
        })

    # 为了向后兼容，保留原来的键名
    urls.update({
        "public": urls["public_https"] if _https_enabled and _https_port is not None and _public_ip else urls["public_http"],
        "local": urls["local_https"] if _https_enabled and _https_port is not None and local_ip != "localhost" else urls["local_http"],
        "localhost": urls["localhost_https"] if _https_enabled and _https_port is not None else urls["localhost_http"]
    })

    logger.info(f"生成多个URL选项: {urls}")
    return urls
