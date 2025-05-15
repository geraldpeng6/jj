#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件服务器模块

提供文件服务功能，用于通过HTTP返回HTML内容
"""

import os
import logging
import base64
from typing import Optional, Dict, Any, Tuple

# 获取日志记录器
logger = logging.getLogger('quant_mcp.file_server')

# 文件服务器根目录
SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 静态文件目录
STATIC_DIR = os.path.join(SERVER_ROOT, "data", "static")
# 图表目录
CHARTS_DIR = os.path.join(SERVER_ROOT, "data", "charts")

# 确保目录存在
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

# MIME类型映射
MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".pdf": "application/pdf"
}

def get_mime_type(file_path: str) -> str:
    """
    获取文件的MIME类型

    Args:
        file_path: 文件路径

    Returns:
        str: MIME类型
    """
    ext = os.path.splitext(file_path)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")

def save_html_content(html_content: str, file_name: str, sub_dir: str = "") -> Tuple[bool, str]:
    """
    保存HTML内容到文件

    Args:
        html_content: HTML内容
        file_name: 文件名
        sub_dir: 子目录，相对于CHARTS_DIR

    Returns:
        Tuple[bool, str]: (是否成功, 文件路径或错误信息)
    """
    try:
        # 确保文件名以.html结尾
        if not file_name.endswith(".html"):
            file_name += ".html"

        # 构建目录路径
        dir_path = CHARTS_DIR
        if sub_dir:
            dir_path = os.path.join(CHARTS_DIR, sub_dir)
            os.makedirs(dir_path, exist_ok=True)

        # 构建文件路径
        file_path = os.path.join(dir_path, file_name)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 返回相对路径（相对于SERVER_ROOT）
        rel_path = os.path.relpath(file_path, SERVER_ROOT)
        logger.info(f"HTML内容已保存到文件: {rel_path}")
        return True, rel_path
    except Exception as e:
        logger.error(f"保存HTML内容时发生错误: {e}")
        return False, f"保存HTML内容时发生错误: {e}"

def get_file_content(file_path: str, as_base64: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    获取文件内容

    Args:
        file_path: 文件路径，相对于SERVER_ROOT
        as_base64: 是否以Base64编码返回

    Returns:
        Tuple[bool, Dict[str, Any]]: (是否成功, 文件内容信息)
    """
    try:
        # 构建绝对路径
        abs_path = os.path.join(SERVER_ROOT, file_path)

        # 检查文件是否存在
        if not os.path.exists(abs_path):
            logger.error(f"文件不存在: {abs_path}")
            return False, {"error": f"文件不存在: {file_path}"}

        # 获取MIME类型
        mime_type = get_mime_type(abs_path)

        # 读取文件内容
        with open(abs_path, "rb") as f:
            content = f.read()

        # 如果是文本文件，转换为字符串
        if mime_type.startswith("text/") or mime_type in ["application/javascript", "application/json"]:
            try:
                content = content.decode("utf-8")
                result = {
                    "mime_type": mime_type,
                    "content": content,
                    "is_binary": False,
                    "file_path": file_path
                }
            except UnicodeDecodeError:
                # 如果解码失败，则以二进制方式处理
                if as_base64:
                    content = base64.b64encode(content).decode("ascii")
                    result = {
                        "mime_type": mime_type,
                        "content": content,
                        "is_binary": True,
                        "is_base64": True,
                        "file_path": file_path
                    }
                else:
                    result = {
                        "mime_type": mime_type,
                        "content": None,
                        "is_binary": True,
                        "error": "二进制文件需要以Base64编码返回",
                        "file_path": file_path
                    }
                    return False, result
        else:
            # 二进制文件
            if as_base64:
                content = base64.b64encode(content).decode("ascii")
                result = {
                    "mime_type": mime_type,
                    "content": content,
                    "is_binary": True,
                    "is_base64": True,
                    "file_path": file_path
                }
            else:
                result = {
                    "mime_type": mime_type,
                    "content": None,
                    "is_binary": True,
                    "error": "二进制文件需要以Base64编码返回",
                    "file_path": file_path
                }
                return False, result

        logger.info(f"成功获取文件内容: {file_path}")
        return True, result
    except Exception as e:
        logger.error(f"获取文件内容时发生错误: {e}")
        return False, {"error": f"获取文件内容时发生错误: {e}"}
