#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
提示工具模块

提供处理MCP提示模板的工具函数
"""

import logging
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp.types import Prompt, PromptArgument

# 获取日志记录器
logger = logging.getLogger('quant_mcp.prompt_utils')

def update_prompt_metadata(mcp: FastMCP, prompt: Prompt) -> bool:
    """
    更新提示模板的元数据，特别是添加suggestions和default_value等字段

    由于MCP的FastMCP类没有直接提供更新提示模板元数据的方法，
    我们通过修改内部提示模板注册表来实现这一功能。

    Args:
        mcp: MCP服务器实例
        prompt: 包含元数据的提示模板

    Returns:
        bool: 更新是否成功
    """
    try:
        # 检查提示模板是否已注册
        if not hasattr(mcp, '_prompts') or prompt.name not in mcp._prompts:
            logger.warning(f"提示模板 {prompt.name} 未注册，无法更新元数据")
            return False

        # 获取现有提示模板
        existing_prompt = mcp._prompts[prompt.name]

        # 更新提示模板描述
        if prompt.description:
            existing_prompt.description = prompt.description

        # 更新提示模板参数
        if prompt.arguments:
            # 创建参数映射
            arg_map = {arg.name: arg for arg in existing_prompt.arguments} if existing_prompt.arguments else {}

            # 更新或添加参数
            for arg in prompt.arguments:
                if arg.name in arg_map:
                    # 更新现有参数
                    existing_arg = arg_map[arg.name]

                    # 更新描述
                    if arg.description:
                        existing_arg.description = arg.description

                    # 更新required标志
                    if arg.required is not None:
                        existing_arg.required = arg.required

                    # 添加suggestions字段
                    if hasattr(arg, 'suggestions'):
                        setattr(existing_arg, 'suggestions', getattr(arg, 'suggestions'))

                    # 添加default_value字段
                    if hasattr(arg, 'default_value'):
                        setattr(existing_arg, 'default_value', getattr(arg, 'default_value'))
                else:
                    # 添加新参数
                    if not existing_prompt.arguments:
                        existing_prompt.arguments = []
                    existing_prompt.arguments.append(arg)

        logger.info(f"成功更新提示模板 {prompt.name} 的元数据")
        return True
    except Exception as e:
        logger.error(f"更新提示模板 {prompt.name} 元数据时发生错误: {e}")
        return False

def register_prompt_with_metadata(mcp: FastMCP, name: str, handler, metadata: Prompt) -> bool:
    """
    注册带有元数据的提示模板

    先使用装饰器注册提示处理函数，然后手动更新提示模板的元数据

    Args:
        mcp: MCP服务器实例
        name: 提示模板名称
        handler: 提示处理函数
        metadata: 包含元数据的提示模板

    Returns:
        bool: 注册是否成功
    """
    try:
        # 使用装饰器注册提示处理函数
        decorated_handler = mcp.prompt(name)(handler)

        # 确保提示模板已注册
        if not hasattr(mcp, '_prompts') or name not in mcp._prompts:
            logger.warning(f"提示模板 {name} 注册失败")
            return False

        # 获取已注册的提示模板
        registered_prompt = mcp._prompts[name]

        # 更新提示模板描述
        if metadata.description:
            registered_prompt.description = metadata.description

        # 更新提示模板参数
        if metadata.arguments:
            registered_prompt.arguments = metadata.arguments

        logger.info(f"成功注册带有元数据的提示模板 {name}")
        return True
    except Exception as e:
        logger.error(f"注册提示模板 {name} 时发生错误: {e}")
        return False

# 为FastMCP类添加方法
def patch_fastmcp():
    """
    为FastMCP类添加自定义方法
    """
    # 添加update_prompt_metadata方法
    if not hasattr(FastMCP, 'update_prompt_metadata'):
        setattr(FastMCP, 'update_prompt_metadata', lambda self, prompt: update_prompt_metadata(self, prompt))
        logger.info("已为FastMCP类添加update_prompt_metadata方法")

    # 添加register_prompt_with_metadata方法
    if not hasattr(FastMCP, 'register_prompt_with_metadata'):
        setattr(FastMCP, 'register_prompt_with_metadata',
                lambda self, name, handler, metadata: register_prompt_with_metadata(self, name, handler, metadata))
        logger.info("已为FastMCP类添加register_prompt_with_metadata方法") 