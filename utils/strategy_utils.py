#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
策略工具模块

提供策略相关的功能，包括获取策略列表、策略详情、更新/删除策略等，所有策略在远程管理，不进行本地存储
"""

import json
import logging
import requests
import gzip
import io
import zlib
from typing import Dict, Optional, Any, List

from utils.auth_utils import load_auth_config, get_auth_info, get_headers

# 获取日志记录器
logger = logging.getLogger('quant_mcp.strategy_utils')

# API基础URL
BASE_URL = "https://api.yueniusz.com"


def get_strategy_list(strategy_group: str = "user") -> Optional[List[Dict[str, Any]]]:
    """
    获取策略列表，可以是用户策略列表或策略库列表

    Args:
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"user"

    Returns:
        Optional[List[Dict[str, Any]]]: 策略列表，每个策略包含strategy_id、strategy_name等字段，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 根据策略组类型选择不同的URL
    if strategy_group == "library":
        url = f"{BASE_URL}/trader-service/strategy/strategy-library-list"
        log_prefix = "策略库"
    else:
        url = f"{BASE_URL}/trader-service/strategy/user-strategy-list"
        log_prefix = "用户策略"

    params = {"user_id": user_id}
    headers = get_headers()

    # 设置代理为None
    proxies = None

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            verify=True,
            timeout=30  # 增加超时时间到30秒
        )
        response.raise_for_status()

        # 检查响应内容类型和编码
        content_type = response.headers.get('Content-Type', '')
        content_encoding = response.headers.get('Content-Encoding', '')

        logger.debug(f"响应状态码: {response.status_code}")
        logger.debug(f"响应内容类型: {content_type}")
        logger.debug(f"响应内容编码: {content_encoding}")
        logger.debug(f"响应头: {dict(response.headers)}")

        # 处理响应内容
        content = response.content

        # 记录原始内容的前20个字节（十六进制格式）用于调试
        if len(content) > 0:
            hex_content = content[:20].hex()
            logger.debug(f"原始内容前20字节(十六进制): {hex_content}")

        # 尝试多种方法解压内容
        decompressed = False
        original_content = content

        # 方法1: 检查Content-Encoding头
        if content_encoding.lower() == 'gzip':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于Content-Encoding头)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法2: 检查内容特征
        if not decompressed and len(content) > 2 and content[:2] == b'\x1f\x8b':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于内容特征)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法3: 使用zlib解压
        if not decompressed:
            try:
                logger.debug("尝试使用zlib.decompress解压...")
                # 尝试不同的窗口大小
                for window_bits in [15, 15 + 16, -15]:
                    try:
                        decomp_content = zlib.decompress(original_content, window_bits)
                        logger.info(f"zlib.decompress成功(window_bits={window_bits})，解压后大小: {len(decomp_content)} 字节")
                        content = decomp_content
                        decompressed = True
                        break
                    except Exception as e:
                        logger.debug(f"zlib.decompress失败(window_bits={window_bits}): {e}")
            except Exception as e:
                logger.warning(f"所有zlib解压尝试都失败: {e}")

        # 方法4: 使用requests内置的解压功能
        if not decompressed and hasattr(response, 'text'):
            try:
                logger.debug("尝试使用response.text获取解压内容...")
                text_content = response.text
                if text_content and len(text_content) > 0:
                    logger.info(f"使用response.text成功，内容长度: {len(text_content)} 字符")
                    # 将文本转换回字节以保持一致性
                    content = text_content.encode('utf-8')
                    decompressed = True
            except Exception as e:
                logger.warning(f"使用response.text失败: {e}")

        # 尝试解析JSON
        try:
            if isinstance(content, bytes):
                # 尝试多种编码
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        data = json.loads(content.decode(encoding))
                        logger.debug(f"成功使用{encoding}编码从字节内容解析JSON")
                        break
                    except UnicodeDecodeError:
                        logger.debug(f"使用{encoding}解码失败，尝试下一种编码")
                    except json.JSONDecodeError as e:
                        logger.debug(f"使用{encoding}解码后JSON解析失败: {e}")
                        # 如果解码成功但JSON解析失败，记录部分内容
                        decoded = content.decode(encoding, errors='replace')
                        logger.debug(f"解码后内容前100个字符: {decoded[:100]}")
                        raise
            else:
                data = response.json()
                logger.debug("使用response.json()解析JSON")
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            # 尝试记录原始内容的一部分
            if isinstance(content, bytes):
                try:
                    logger.error(f"内容前200个字符: {content[:200].decode('utf-8', errors='replace')}")
                except Exception:
                    logger.error(f"无法解码内容，十六进制表示: {content[:100].hex()}")
            else:
                logger.error(f"内容前200个字符: {str(content)[:200]}")

            # 尝试直接使用response.json()作为最后的手段
            try:
                logger.debug("尝试直接使用response.json()作为最后的手段...")
                data = response.json()
                logger.info("使用response.json()成功解析JSON")
            except Exception as json_e:
                logger.error(f"最后尝试使用response.json()也失败: {json_e}")
                # 如果所有尝试都失败，则返回None
                return None

        if data.get('code') == 1 and data.get('msg') == 'ok':
            strategy_list = data.get('data', {}).get('strategy_list', [])

            # 为每个策略添加策略组标识
            for strategy in strategy_list:
                strategy['strategy_group'] = strategy_group
                # 为缺失的字段添加默认值None
                for field in ['indicator', 'control_risk', 'timing', 'choose_stock']:
                    if field not in strategy:
                        strategy[field] = None

            logger.info(f"获取{log_prefix}列表成功，共 {len(strategy_list)} 个策略")
            return strategy_list
        else:
            logger.error(f"获取{log_prefix}列表失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        # 添加更详细的错误信息
        if hasattr(e, 'response') and e.response:
            logger.error(f"响应状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取{log_prefix}列表时发生未知错误: {e}")
        return None


def get_strategy_detail(strategy_id: str, strategy_group: str = "library") -> Optional[Dict[str, Any]]:
    """
    获取策略详情，可以是用户策略详情或策略库策略详情

    Args:
        strategy_id: 策略ID
        strategy_group: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"library"

    Returns:
        Optional[Dict[str, Any]]: 策略详情，获取失败时返回None
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 根据策略组类型选择不同的URL
    if strategy_group == "user":
        url = f"{BASE_URL}/trader-service/strategy/user-strategy"
        log_prefix = "用户策略"
    else:
        url = f"{BASE_URL}/trader-service/strategy/strategy-library"
        log_prefix = "策略库"

    params = {
        "user_id": user_id,
        "strategy_id": strategy_id
    }
    headers = get_headers()

    # 设置代理为None
    proxies = None

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            verify=True,
            timeout=30  # 增加超时时间到30秒
        )
        response.raise_for_status()

        # 检查响应内容类型和编码
        content_type = response.headers.get('Content-Type', '')
        content_encoding = response.headers.get('Content-Encoding', '')

        logger.debug(f"响应状态码: {response.status_code}")
        logger.debug(f"响应内容类型: {content_type}")
        logger.debug(f"响应内容编码: {content_encoding}")
        logger.debug(f"响应头: {dict(response.headers)}")

        # 处理响应内容
        content = response.content

        # 记录原始内容的前20个字节（十六进制格式）用于调试
        if len(content) > 0:
            hex_content = content[:20].hex()
            logger.debug(f"原始内容前20字节(十六进制): {hex_content}")

        # 尝试多种方法解压内容
        decompressed = False
        original_content = content

        # 方法1: 检查Content-Encoding头
        if content_encoding.lower() == 'gzip':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于Content-Encoding头)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法2: 检查内容特征
        if not decompressed and len(content) > 2 and content[:2] == b'\x1f\x8b':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于内容特征)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法3: 使用zlib解压
        if not decompressed:
            try:
                logger.debug("尝试使用zlib.decompress解压...")
                # 尝试不同的窗口大小
                for window_bits in [15, 15 + 16, -15]:
                    try:
                        decomp_content = zlib.decompress(original_content, window_bits)
                        logger.info(f"zlib.decompress成功(window_bits={window_bits})，解压后大小: {len(decomp_content)} 字节")
                        content = decomp_content
                        decompressed = True
                        break
                    except Exception as e:
                        logger.debug(f"zlib.decompress失败(window_bits={window_bits}): {e}")
            except Exception as e:
                logger.warning(f"所有zlib解压尝试都失败: {e}")

        # 方法4: 使用requests内置的解压功能
        if not decompressed and hasattr(response, 'text'):
            try:
                logger.debug("尝试使用response.text获取解压内容...")
                text_content = response.text
                if text_content and len(text_content) > 0:
                    logger.info(f"使用response.text成功，内容长度: {len(text_content)} 字符")
                    # 将文本转换回字节以保持一致性
                    content = text_content.encode('utf-8')
                    decompressed = True
            except Exception as e:
                logger.warning(f"使用response.text失败: {e}")

        # 尝试解析JSON
        try:
            if isinstance(content, bytes):
                # 尝试多种编码
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        data = json.loads(content.decode(encoding))
                        logger.debug(f"成功使用{encoding}编码从字节内容解析JSON")
                        break
                    except UnicodeDecodeError:
                        logger.debug(f"使用{encoding}解码失败，尝试下一种编码")
                    except json.JSONDecodeError as e:
                        logger.debug(f"使用{encoding}解码后JSON解析失败: {e}")
                        # 如果解码成功但JSON解析失败，记录部分内容
                        decoded = content.decode(encoding, errors='replace')
                        logger.debug(f"解码后内容前100个字符: {decoded[:100]}")
                        raise
            else:
                data = response.json()
                logger.debug("使用response.json()解析JSON")
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            # 尝试记录原始内容的一部分
            if isinstance(content, bytes):
                try:
                    logger.error(f"内容前200个字符: {content[:200].decode('utf-8', errors='replace')}")
                except Exception:
                    logger.error(f"无法解码内容，十六进制表示: {content[:100].hex()}")
            else:
                logger.error(f"内容前200个字符: {str(content)[:200]}")

            # 尝试直接使用response.json()作为最后的手段
            try:
                logger.debug("尝试直接使用response.json()作为最后的手段...")
                data = response.json()
                logger.info("使用response.json()成功解析JSON")
            except Exception as json_e:
                logger.error(f"最后尝试使用response.json()也失败: {json_e}")
                # 如果所有尝试都失败，则返回None
                return None

        if data.get('code') == 1 and data.get('msg') == 'ok':
            strategy_detail = data.get('data', {})

            # 添加策略组标识和策略ID
            strategy_detail['strategy_group'] = strategy_group
            if 'strategy_id' not in strategy_detail:
                strategy_detail['strategy_id'] = strategy_id

            logger.info(f"获取{log_prefix}详情成功，策略ID: {strategy_id}")
            return strategy_detail
        else:
            logger.error(f"获取{log_prefix}详情失败")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        # 添加更详细的错误信息
        if hasattr(e, 'response') and e.response:
            logger.error(f"响应状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        return None
    except Exception as e:
        logger.error(f"获取{log_prefix}详情时发生未知错误: {e}")
        return None








def delete_strategy(strategy_id: str) -> requests.Response:
    """
    删除策略

    Args:
        strategy_id: 策略ID

    Returns:
        requests.Response: 删除请求的响应对象
    """
    # 加载认证配置
    if not load_auth_config():
        return None

    # 获取认证信息
    _, user_id = get_auth_info()
    if not user_id:
        logger.error("错误: 无法获取认证信息")
        return None

    # 构建URL和请求参数
    url = f"{BASE_URL}/trader-service/strategy/user-strategy"
    params = {"user_id": user_id}
    headers = get_headers()

    data = {
        "user_id": user_id,
        "strategy_id": strategy_id
    }

    # 设置代理为None
    proxies = None

    try:
        # 使用DELETE请求
        response = requests.delete(
            url,
            params=params,
            json=data,
            headers=headers,
            proxies=proxies,
            verify=True,
            timeout=30  # 增加超时时间到30秒
        )
        response.raise_for_status()

        # 检查响应内容类型和编码
        content_type = response.headers.get('Content-Type', '')
        content_encoding = response.headers.get('Content-Encoding', '')

        logger.debug(f"响应状态码: {response.status_code}")
        logger.debug(f"响应内容类型: {content_type}")
        logger.debug(f"响应内容编码: {content_encoding}")
        logger.debug(f"响应头: {dict(response.headers)}")

        # 处理响应内容
        content = response.content

        # 记录原始内容的前20个字节（十六进制格式）用于调试
        if len(content) > 0:
            hex_content = content[:20].hex()
            logger.debug(f"原始内容前20字节(十六进制): {hex_content}")

        # 尝试多种方法解压内容
        decompressed = False
        original_content = content

        # 方法1: 检查Content-Encoding头
        if content_encoding.lower() == 'gzip':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于Content-Encoding头)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法2: 检查内容特征
        if not decompressed and len(content) > 2 and content[:2] == b'\x1f\x8b':
            try:
                logger.debug("尝试使用gzip.decompress解压(基于内容特征)...")
                content = gzip.decompress(content)
                logger.info(f"gzip.decompress成功，解压后大小: {len(content)} 字节")
                decompressed = True
            except Exception as e:
                logger.warning(f"gzip.decompress失败: {e}")

        # 方法3: 使用zlib解压
        if not decompressed:
            try:
                logger.debug("尝试使用zlib.decompress解压...")
                # 尝试不同的窗口大小
                for window_bits in [15, 15 + 16, -15]:
                    try:
                        decomp_content = zlib.decompress(original_content, window_bits)
                        logger.info(f"zlib.decompress成功(window_bits={window_bits})，解压后大小: {len(decomp_content)} 字节")
                        content = decomp_content
                        decompressed = True
                        break
                    except Exception as e:
                        logger.debug(f"zlib.decompress失败(window_bits={window_bits}): {e}")
            except Exception as e:
                logger.warning(f"所有zlib解压尝试都失败: {e}")

        # 方法4: 使用requests内置的解压功能
        if not decompressed and hasattr(response, 'text'):
            try:
                logger.debug("尝试使用response.text获取解压内容...")
                text_content = response.text
                if text_content and len(text_content) > 0:
                    logger.info(f"使用response.text成功，内容长度: {len(text_content)} 字符")
                    # 将文本转换回字节以保持一致性
                    content = text_content.encode('utf-8')
                    decompressed = True
            except Exception as e:
                logger.warning(f"使用response.text失败: {e}")

        # 尝试解析JSON
        try:
            if isinstance(content, bytes):
                # 尝试多种编码
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        result = json.loads(content.decode(encoding))
                        logger.debug(f"成功使用{encoding}编码从字节内容解析JSON")
                        break
                    except UnicodeDecodeError:
                        logger.debug(f"使用{encoding}解码失败，尝试下一种编码")
                    except json.JSONDecodeError as e:
                        logger.debug(f"使用{encoding}解码后JSON解析失败: {e}")
                        # 如果解码成功但JSON解析失败，记录部分内容
                        decoded = content.decode(encoding, errors='replace')
                        logger.debug(f"解码后内容前100个字符: {decoded[:100]}")
                        raise
            else:
                result = response.json()
                logger.debug("使用response.json()解析JSON")
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            # 尝试记录原始内容的一部分
            if isinstance(content, bytes):
                try:
                    logger.error(f"内容前200个字符: {content[:200].decode('utf-8', errors='replace')}")
                except Exception:
                    logger.error(f"无法解码内容，十六进制表示: {content[:100].hex()}")
            else:
                logger.error(f"内容前200个字符: {str(content)[:200]}")

            # 尝试直接使用response.json()作为最后的手段
            try:
                logger.debug("尝试直接使用response.json()作为最后的手段...")
                result = response.json()
                logger.info("使用response.json()成功解析JSON")
            except Exception as json_e:
                logger.error(f"最后尝试使用response.json()也失败: {json_e}")
                # 如果所有尝试都失败，则返回None
                return None

        if result.get('code') == 1 and result.get('msg') == 'ok':
            logger.info(f"删除策略成功，策略ID: {strategy_id}")
        else:
            logger.error(f"删除策略失败，响应: {result}")

        # 返回完整的响应对象
        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        # 添加更详细的错误信息
        if hasattr(e, 'response') and e.response:
            logger.error(f"响应状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"解析响应JSON失败: {e}")
        return None
    except Exception as e:
        logger.error(f"删除策略时发生未知错误: {e}")
        return None






