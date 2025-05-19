#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML服务器工具模块

提供HTML文件服务器相关的功能，包括URL生成和Nginx配置
"""

import os
import logging
import socket
import requests
import subprocess
from typing import Optional, Tuple

# 获取日志记录器
logger = logging.getLogger('quant_mcp.html_server')

# 默认配置
DEFAULT_SERVER_PORT = 8081  # 本地开发环境使用8081端口
DEFAULT_CHARTS_DIR = "data/charts"
DEFAULT_SERVER_HOST = None  # 将在运行时确定


def get_server_host() -> str:
    """
    获取服务器主机地址

    在本地开发环境中返回localhost，在生产环境中尝试获取公网IP

    Returns:
        str: 服务器主机地址
    """
    # 检查是否是本地开发环境
    if os.environ.get('MCP_ENV') == 'production':
        # 尝试获取公网IP
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"获取公网IP失败: {e}")

        # 如果获取公网IP失败，尝试获取本地IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.warning(f"获取本地IP失败: {e}")

    # 在本地开发环境中或者其他方法都失败时，返回localhost
    return "localhost"


def get_html_url(file_path: str) -> str:
    """
    根据文件路径生成HTML文件的URL

    Args:
        file_path: HTML文件的本地路径

    Returns:
        str: HTML文件的URL
    """
    global DEFAULT_SERVER_HOST

    # 如果主机地址未初始化，则获取
    if DEFAULT_SERVER_HOST is None:
        DEFAULT_SERVER_HOST = get_server_host()

    # 确保文件路径是绝对路径
    abs_file_path = os.path.abspath(file_path)

    # 获取charts目录的绝对路径
    charts_dir = os.path.abspath(DEFAULT_CHARTS_DIR)

    # 检查文件是否在charts目录下
    if not abs_file_path.startswith(charts_dir):
        logger.error(f"文件不在charts目录下: {abs_file_path}")
        return f"file://{abs_file_path}"  # 如果不在charts目录下，返回本地文件URL

    # 提取相对路径
    rel_path = os.path.relpath(abs_file_path, charts_dir)

    # 构建URL
    url = f"http://{DEFAULT_SERVER_HOST}:{DEFAULT_SERVER_PORT}/charts/{rel_path}"

    return url


def generate_nginx_config() -> Tuple[bool, str]:
    """
    生成Nginx配置文件

    Returns:
        Tuple[bool, str]: 是否成功和配置文件内容或错误信息
    """
    # 获取charts目录的绝对路径
    charts_dir = os.path.abspath(DEFAULT_CHARTS_DIR)

    # 生成Nginx配置
    config = f"""
# MCP HTML服务器配置
server {{
    listen {DEFAULT_SERVER_PORT};
    server_name _;

    # 禁止访问隐藏文件
    location ~ /\\. {{
        deny all;
    }}

    # 静态文件服务
    location /charts/ {{
        alias {charts_dir}/;

        # 只允许访问HTML文件
        location ~* \\.(html)$ {{
            add_header Content-Type text/html;
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }}

        # 禁止目录列表
        autoindex off;

        # 禁止访问其他类型的文件
        location ~* \\.(php|py|js|json|txt|log|ini|conf)$ {{
            deny all;
        }}
    }}

    # 默认页面 - 生成一个测试页面
    location = / {{
        return 200 '<html><head><title>MCP HTML服务器</title></head><body><h1>MCP HTML服务器</h1><p>服务器运行正常</p></body></html>';
        add_header Content-Type text/html;
    }}
}}
"""
    return True, config


def setup_nginx() -> Tuple[bool, str]:
    """
    设置Nginx配置

    Returns:
        Tuple[bool, str]: 是否成功和成功/错误信息
    """
    try:
        # 生成配置
        success, config = generate_nginx_config()
        if not success:
            return False, config

        # 检测操作系统和环境
        import platform
        system = platform.system()

        # 根据不同操作系统设置不同的配置路径
        if system == 'Darwin':  # macOS
            config_path = "/opt/homebrew/etc/nginx/servers/mcp_html_server.conf"
        elif system == 'Linux':
            if os.environ.get('MCP_ENV') == 'production':
                config_path = "/etc/nginx/conf.d/mcp_html_server.conf"
            else:
                # 本地Linux开发环境
                config_path = "/etc/nginx/conf.d/mcp_html_server.conf"
        else:
            return False, f"不支持的操作系统: {system}"

        # 保存配置文件
        try:
            with open(config_path, 'w') as f:
                f.write(config)
        except PermissionError:
            logger.warning(f"无权限写入配置文件: {config_path}，尝试使用临时文件")
            # 如果没有权限，则保存到当前目录
            with open("mcp_html_server.conf", 'w') as f:
                f.write(config)
            return False, f"无权限写入配置文件: {config_path}，已保存到当前目录的mcp_html_server.conf文件，请手动复制到Nginx配置目录"

        # 测试配置
        result = subprocess.run(['nginx', '-t'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Nginx配置测试失败: {result.stderr}"

        # 重新加载Nginx
        if system == 'Darwin':  # macOS
            result = subprocess.run(['brew', 'services', 'reload', 'nginx'], capture_output=True, text=True)
        else:
            result = subprocess.run(['nginx', '-s', 'reload'], capture_output=True, text=True)

        if result.returncode != 0:
            return False, f"重新加载Nginx失败: {result.stderr}"

        # 生成测试HTML文件
        test_html_path = os.path.join(DEFAULT_CHARTS_DIR, "test.html")
        os.makedirs(os.path.dirname(test_html_path), exist_ok=True)

        with open(test_html_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>MCP HTML服务器测试</title>
</head>
<body>
    <h1>MCP HTML服务器测试</h1>
    <p>如果您看到此页面，说明HTML服务器配置成功。</p>
    <p>生成时间: <span id="time"></span></p>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
""")

        # 获取测试URL
        test_url = get_html_url(test_html_path)

        return True, f"Nginx配置成功，测试URL: {test_url}"

    except Exception as e:
        logger.error(f"设置Nginx失败: {e}")
        return False, f"设置Nginx失败: {e}"


def is_nginx_available() -> bool:
    """
    检查Nginx是否可用

    Returns:
        bool: Nginx是否可用
    """
    try:
        result = subprocess.run(['nginx', '-v'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def generate_test_html() -> Optional[str]:
    """
    生成测试HTML文件

    Returns:
        Optional[str]: 测试HTML文件的URL，如果生成失败则返回None
    """
    try:
        # 生成测试HTML文件
        test_html_path = os.path.join(DEFAULT_CHARTS_DIR, "test.html")
        os.makedirs(os.path.dirname(test_html_path), exist_ok=True)

        with open(test_html_path, 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>MCP HTML服务器测试</title>
</head>
<body>
    <h1>MCP HTML服务器测试</h1>
    <p>如果您看到此页面，说明HTML服务器配置成功。</p>
    <p>生成时间: <span id="time"></span></p>
    <script>
        document.getElementById('time').textContent = new Date().toLocaleString();
    </script>
</body>
</html>
""")

        # 获取测试URL
        test_url = get_html_url(test_html_path)

        return test_url

    except Exception as e:
        logger.error(f"生成测试HTML文件失败: {e}")
        return None
