#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
静态文件服务模块

提供静态文件服务功能，用于通过HTTP返回HTML内容
"""

import os
import logging
import time
import json
import uuid
from typing import Optional, Dict, Any, Tuple, List

# 获取日志记录器
logger = logging.getLogger('quant_mcp.static_server')

# 文件服务器根目录
SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# 静态文件目录
STATIC_DIR = os.path.join(SERVER_ROOT, "data", "charts")
# 确保目录存在
os.makedirs(STATIC_DIR, exist_ok=True)

# 文件映射表，用于将内部文件路径映射到外部URL
# 格式: {file_path: {url: url, created_at: timestamp}}
FILE_MAPPINGS = {}

def get_server_url() -> str:
    """
    获取服务器URL

    从环境变量中获取服务器URL，如果没有设置，则使用默认值

    Returns:
        str: 服务器URL
    """
    server_host = os.environ.get("MCP_SERVER_HOST", "localhost")
    server_port = os.environ.get("MCP_SERVER_PORT", "8000")  # 默认使用8000端口，与MCP服务器一致
    server_protocol = os.environ.get("MCP_SERVER_PROTOCOL", "http")

    # 始终包含端口号，确保URL正确
    return f"{server_protocol}://{server_host}:{server_port}"

def save_html_file(html_content: str, file_name: str, sub_dir: str = "") -> Tuple[bool, str, str]:
    """
    保存HTML内容到文件并生成访问URL

    Args:
        html_content: HTML内容
        file_name: 文件名
        sub_dir: 子目录，相对于STATIC_DIR

    Returns:
        Tuple[bool, str, str]: (是否成功, 文件路径, 访问URL)
    """
    try:
        # 确保文件名以.html结尾
        if not file_name.endswith(".html"):
            file_name += ".html"

        # 生成唯一的文件名，避免冲突
        unique_id = str(uuid.uuid4())[:8]
        file_name = f"{os.path.splitext(file_name)[0]}_{unique_id}.html"

        # 构建目录路径
        dir_path = STATIC_DIR
        if sub_dir:
            dir_path = os.path.join(STATIC_DIR, sub_dir)
            os.makedirs(dir_path, exist_ok=True)

        # 构建文件路径
        file_path = os.path.join(dir_path, file_name)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 计算相对路径（相对于STATIC_DIR）
        rel_path = os.path.relpath(file_path, STATIC_DIR)

        # 生成访问URL
        # 使用文件URL协议，直接指向本地文件
        url = f"file://{os.path.abspath(file_path)}"

        # 添加到映射表
        FILE_MAPPINGS[file_path] = {
            "url": url,
            "created_at": time.time()
        }

        logger.info(f"HTML内容已保存到文件: {file_path}")
        logger.info(f"访问URL: {url}")

        return True, file_path, url
    except Exception as e:
        logger.error(f"保存HTML内容时发生错误: {e}")
        return False, str(e), ""

def get_file_url(file_path: str) -> str:
    """
    获取文件的访问URL

    Args:
        file_path: 文件路径

    Returns:
        str: 访问URL，如果文件不存在则返回空字符串
    """
    # 如果文件路径在映射表中，则直接返回URL
    if file_path in FILE_MAPPINGS:
        return FILE_MAPPINGS[file_path]["url"]

    # 如果文件路径不在映射表中，则尝试生成URL
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return ""

        # 计算相对路径（相对于STATIC_DIR）
        rel_path = os.path.relpath(file_path, STATIC_DIR)

        # 生成访问URL
        # 使用文件URL协议，直接指向本地文件
        url = f"file://{os.path.abspath(file_path)}"

        # 添加到映射表
        FILE_MAPPINGS[file_path] = {
            "url": url,
            "created_at": time.time()
        }

        return url
    except Exception as e:
        logger.error(f"获取文件URL时发生错误: {e}")
        return ""

def clean_old_files(max_age_days: int = 7) -> int:
    """
    清理旧文件

    Args:
        max_age_days: 最大保留天数，默认为7天

    Returns:
        int: 清理的文件数量
    """
    try:
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        files_to_delete = []

        # 遍历映射表，找出过期的文件
        for file_path, info in FILE_MAPPINGS.items():
            if now - info["created_at"] > max_age_seconds:
                files_to_delete.append(file_path)

        # 删除过期的文件
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                # 从映射表中删除
                del FILE_MAPPINGS[file_path]
            except Exception as e:
                logger.error(f"删除文件时发生错误: {file_path}, {e}")

        logger.info(f"清理了 {deleted_count} 个过期文件")
        return deleted_count
    except Exception as e:
        logger.error(f"清理旧文件时发生错误: {e}")
        return 0

def list_files(sub_dir: str = "", pattern: str = "*.html") -> List[Dict[str, Any]]:
    """
    列出静态文件目录中的文件

    Args:
        sub_dir: 子目录，相对于STATIC_DIR
        pattern: 文件匹配模式

    Returns:
        List[Dict[str, Any]]: 文件列表，每个文件包含名称、路径、URL和创建时间
    """
    import glob

    try:
        # 构建目录路径
        dir_path = STATIC_DIR
        if sub_dir:
            dir_path = os.path.join(STATIC_DIR, sub_dir)

        # 检查目录是否存在
        if not os.path.exists(dir_path):
            logger.error(f"目录不存在: {dir_path}")
            return []

        # 获取文件列表
        file_pattern = os.path.join(dir_path, pattern)
        files = glob.glob(file_pattern)

        result = []
        for file_path in files:
            # 获取文件名
            file_name = os.path.basename(file_path)
            # 获取文件URL
            url = get_file_url(file_path)
            # 获取文件创建时间
            created_at = FILE_MAPPINGS.get(file_path, {}).get("created_at", os.path.getctime(file_path))

            result.append({
                "name": file_name,
                "path": file_path,
                "url": url,
                "created_at": created_at
            })

        return result
    except Exception as e:
        logger.error(f"列出文件时发生错误: {e}")
        return []
