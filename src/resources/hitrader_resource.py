#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HiTrader文档资源模块 (HiTrader Documentation Resource Module)

本模块提供HiTrader量化交易平台的文档资源，通过MCP（Model Context Protocol）框架将文档内容
暴露为可查询的资源。主要功能包括：

1. 提供完整文档内容的访问接口
2. 提供文档目录的访问接口
3. 按章节名称查询文档内容
4. 按关键词搜索文档内容
5. 提供特定交易功能的语法和用法说明

文档内容来源于data/hitrader_manual/combined目录下的合并文件。

使用示例:
    # 获取文档目录
    toc = await get_hitrader_toc()
    
    # 获取完整文档
    doc = await get_hitrader_full_doc()
    
    # 获取特定章节内容
    chapter = await get_hitrader_chapter("选股模块")
    
    # 按关键词搜索文档
    search_results = await get_hitrader_docs(query="均线")
    
    # 获取特定功能的语法说明
    syntax = await get_hitrader_syntax("交易操作")
"""

import logging
import os
import re
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

# 获取日志记录器
logger = logging.getLogger('quant_mcp.hitrader_resource')

class HiTraderDocs:
    """
    HiTrader文档资源类
    
    该类提供访问HiTrader文档的各种方法，包括加载文档目录、加载完整文档内容、
    提取文档章节结构、查找特定章节内容等。使用缓存机制减少重复文件读取，
    提高性能。
    
    主要功能:
        - 加载文档目录 (_load_toc)
        - 加载完整文档 (_load_full_doc)
        - 提取文档章节结构 (_extract_chapters)
        - 查找特定章节内容 (_find_chapter)
        - 提供文档查询接口 (get_hitrader_*)
    
    文档内容基于data/hitrader_manual/combined目录下的合并文件。
    """
    
    # 文档路径配置
    DOCS_DIR = "data/hitrader_manual"  # 原始文档目录
    COMBINED_DOCS_DIR = "data/hitrader_manual/combined"  # 合并后文档目录
    
    # 缓存变量，用于存储已加载的文档内容，避免重复读取文件
    _toc_cache = None  # 文档目录缓存
    _full_doc_cache = None  # 完整文档缓存
    _chapters_cache = None  # 章节结构缓存
    
    @staticmethod
    def _load_toc() -> str:
        """
        加载HiTrader文档目录
        
        该方法从合并后的文档目录文件中加载目录内容。如果目录已经被加载过，
        则直接返回缓存的内容，避免重复读取文件。
        
        加载过程:
            1. 检查缓存是否存在，如存在则直接返回
            2. 尝试从COMBINED_DOCS_DIR/hitrader_toc.md文件中读取目录
            3. 如果文件不存在，返回错误信息
        
        Returns:
            str: 文档目录内容，包含所有章节的链接和描述。如果加载失败，
                 则返回错误信息字符串。
        
        错误处理:
            - 如果文件不存在，返回提示信息
            - 如果读取过程中发生异常，记录错误日志并返回错误信息
        """
        # 如果有缓存，直接返回
        if HiTraderDocs._toc_cache:
            return HiTraderDocs._toc_cache
            
        try:
            # 从合并目录加载
            toc_path = f"{HiTraderDocs.COMBINED_DOCS_DIR}/hitrader_toc.md"
            if os.path.exists(toc_path):
                with open(toc_path, 'r', encoding='utf-8') as f:
                    HiTraderDocs._toc_cache = f.read()
                    return HiTraderDocs._toc_cache
            
            # 如果目录文件不存在，返回错误
            return "文档目录文件不存在，请检查combined目录"
            
        except Exception as e:
            logger.error(f"加载文档目录时发生错误: {e}")
            return f"加载文档目录时发生错误: {e}"
    
    @staticmethod
    def _load_full_doc() -> str:
        """
        加载HiTrader完整文档内容
        
        该方法从合并后的完整文档文件中加载所有内容。如果文档已经被加载过，
        则直接返回缓存的内容，避免重复读取文件。
        
        加载过程:
            1. 检查缓存是否存在，如存在则直接返回
            2. 尝试从COMBINED_DOCS_DIR/hitrader_full.md文件中读取完整文档
            3. 如果文件不存在，返回错误信息
        
        Returns:
            str: 完整的文档内容，包含所有章节。如果加载失败，则返回错误信息字符串。
        
        错误处理:
            - 如果文件不存在，返回提示信息
            - 如果读取过程中发生异常，记录错误日志并返回错误信息
        """
        # 如果有缓存，直接返回
        if HiTraderDocs._full_doc_cache:
            return HiTraderDocs._full_doc_cache
            
        try:
            # 从合并文件加载
            full_doc_path = f"{HiTraderDocs.COMBINED_DOCS_DIR}/hitrader_full.md"
            if os.path.exists(full_doc_path):
                with open(full_doc_path, 'r', encoding='utf-8') as f:
                    HiTraderDocs._full_doc_cache = f.read()
                    return HiTraderDocs._full_doc_cache
            
            # 如果合并文件不存在，返回错误
            return "完整文档文件不存在，请检查combined目录"
            
        except Exception as e:
            logger.error(f"加载完整文档时发生错误: {e}")
            return f"加载完整文档时发生错误: {e}"
    
    @staticmethod
    def _extract_chapters(content: str = None) -> Dict[str, Dict[str, Any]]:
        """
        从文档中提取章节结构
        
        该方法分析文档内容，提取所有章节、子章节和小节的结构，形成一个多层嵌套的字典。
        提取过程基于Markdown标题格式（#、##、###、####等），不同级别的标题对应不同
        层级的章节。
        
        章节结构提取规则:
            - 二级标题(##)作为主章节
            - 三级标题(###)作为子章节
            - 四级标题(####)作为小节
            - 每个章节包含其下所有内容，直到下一个同级或更高级标题出现
        
        Args:
            content (str, optional): 要分析的文档内容。如果为None，则自动加载完整文档。
                                     默认为None。
        
        Returns:
            Dict[str, Dict[str, Any]]: 章节结构字典，格式如下:
                {
                    "章节名1": {
                        "level": 2,
                        "content": "章节内容...",
                        "subchapters": {
                            "子章节名1": {
                                "level": 3,
                                "content": "子章节内容...",
                                "sections": {
                                    "小节名1": {
                                        "level": 4,
                                        "content": "小节内容..."
                                    },
                                    ...
                                }
                            },
                            ...
                        }
                    },
                    ...
                }
        
        错误处理:
            - 如果提取过程中发生异常，记录错误日志并返回空字典
        
        缓存机制:
            - 提取结果会被缓存，后续调用直接返回缓存结果
        """
        # 如果有缓存，直接返回
        if HiTraderDocs._chapters_cache:
            return HiTraderDocs._chapters_cache
            
        try:
            # 如果未提供内容，则加载完整文档
            if content is None:
                content = HiTraderDocs._load_full_doc()
                
            # 初始化章节结构
            chapters = {}
            current_chapter = None  # 当前主章节
            current_subchapter = None  # 当前子章节
            current_section = None  # 当前小节
            
            chapter_content = []  # 当前章节的内容行
            
            # 逐行分析文档内容
            for line in content.split('\n'):
                # 如果是二级标题，开始新的主章节
                if line.startswith('## '):
                    # 保存上一个章节的内容
                    if current_chapter:
                        chapters[current_chapter]['content'] = '\n'.join(chapter_content)
                        
                    # 创建新章节
                    current_chapter = line[3:].strip()  # 去除"## "前缀
                    current_subchapter = None  # 重置子章节
                    current_section = None  # 重置小节
                    chapters[current_chapter] = {
                        'level': 2,  # 二级标题
                        'subchapters': {},  # 子章节字典
                        'content': ''  # 初始化内容为空
                    }
                    chapter_content = [line]  # 开始收集新章节内容
                    
                # 如果是三级标题，开始新的子章节
                elif line.startswith('### '):
                    if current_chapter:
                        # 创建新子章节
                        current_subchapter = line[4:].strip()  # 去除"### "前缀
                        current_section = None  # 重置小节
                        # 如果子章节不存在，则创建
                        if current_subchapter not in chapters[current_chapter]['subchapters']:
                            chapters[current_chapter]['subchapters'][current_subchapter] = {
                                'level': 3,  # 三级标题
                                'sections': {},  # 小节字典
                                'content': ''  # 初始化内容为空
                            }
                    chapter_content.append(line)  # 将标题添加到章节内容
                    
                # 如果是四级标题，开始新的小节
                elif line.startswith('#### '):
                    if current_chapter and current_subchapter:
                        # 创建新小节
                        current_section = line[5:].strip()  # 去除"#### "前缀
                        # 添加小节到子章节中
                        chapters[current_chapter]['subchapters'][current_subchapter]['sections'][current_section] = {
                            'level': 4,  # 四级标题
                            'content': ''  # 初始化内容为空
                        }
                    chapter_content.append(line)  # 将标题添加到章节内容
                    
                # 其他普通行，直接添加到当前章节内容
                else:
                    chapter_content.append(line)
            
            # 保存最后一个章节的内容
            if current_chapter:
                chapters[current_chapter]['content'] = '\n'.join(chapter_content)
                
            # 缓存章节结构
            HiTraderDocs._chapters_cache = chapters
            return chapters
            
        except Exception as e:
            logger.error(f"提取章节结构时发生错误: {e}")
            return {}  # 发生错误时返回空字典
    
    @staticmethod
    def _find_chapter(chapter_name: str) -> str:
        """
        查找指定章节的内容
        
        该方法根据提供的章节名称，在文档的章节结构中查找匹配的章节，并返回该章节的内容。
        支持模糊匹配，即章节名称可以是部分匹配。查找过程遵循以下优先级：
        1. 精确匹配主章节名
        2. 精确匹配子章节名
        3. 精确匹配小节名
        4. 模糊匹配（如包含关键词）
        
        Args:
            chapter_name (str): 要查找的章节名称。不区分大小写，支持部分匹配。
                               例如："选股模块"、"交易操作"、"止损"等。
        
        Returns:
            str: 找到的章节内容。如果找不到匹配的章节，则返回错误信息。
        
        查找流程:
            1. 提取文档的章节结构
            2. 尝试直接匹配主章节名
            3. 如果没找到，尝试匹配子章节名，并提取对应内容
            4. 如果仍未找到，尝试模糊匹配（检查章节名是否包含查询词的任何部分）
            
        错误处理:
            - 如果找不到匹配的章节，返回提示信息
            - 如果查找过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            # 获取章节结构
            chapters = HiTraderDocs._extract_chapters()
            
            # 将查询转为小写，便于不区分大小写的匹配
            chapter_name_lower = chapter_name.lower()
            
            # 步骤1: 直接匹配主章节名
            for name, data in chapters.items():
                # 检查主章节名是否包含查询词
                if chapter_name_lower in name.lower():
                    return data['content']
                    
                # 步骤2: 检查子章节
                for subname, subdata in data['subchapters'].items():
                    # 检查子章节名是否包含查询词
                    if chapter_name_lower in subname.lower():
                        # 从主章节内容中提取子章节内容
                        # 通过查找子章节标题和下一个同级标题之间的内容
                        lines = data['content'].split('\n')
                        start = -1  # 子章节开始行
                        end = len(lines)  # 默认到文档末尾
                        
                        # 查找子章节开始位置和结束位置
                        for i, line in enumerate(lines):
                            # 找到子章节开始位置
                            if line.startswith('### ') and chapter_name_lower in line.lower():
                                start = i
                            # 找到子章节结束位置（下一个同级标题）
                            elif start >= 0 and line.startswith('### '):
                                end = i
                                break
                                
                        # 如果找到了子章节，返回对应内容
                        if start >= 0:
                            return '\n'.join(lines[start:end])
                    
                    # 步骤3: 检查小节（四级标题）
                    # 注：这部分逻辑留空，因为小节内容提取需要重新解析主内容
                    for secname, secdata in subdata['sections'].items():
                        if chapter_name_lower in secname.lower():
                            # 这里需要实现小节内容提取
                            # 但由于结构限制，可能需要重新解析主内容
                            # 留待后续实现
                            pass
            
            # 步骤4: 如果没有找到精确匹配，尝试模糊匹配
            # 检查主章节名是否包含查询词中的任何单词
            for name, data in chapters.items():
                # 分解查询词为单词列表，检查章节名是否包含任何一个单词
                if any(word in name.lower() for word in chapter_name_lower.split()):
                    return data['content']
            
            # 如果所有匹配都失败，返回未找到的信息
            return f"未找到章节: {chapter_name}"
            
        except Exception as e:
            logger.error(f"查找章节时发生错误: {e}")
            return f"查找章节时发生错误: {e}"
    
    @staticmethod
    async def get_hitrader_toc() -> str:
        """
        获取HiTrader文档目录
        
        该方法提供HiTrader文档的目录结构，包含所有章节的链接和简要描述。
        目录内容来自于合并文档目录文件。
        
        Returns:
            str: 文档目录内容。如果加载失败，则返回错误信息。
        
        使用示例:
            ```python
            # 获取HiTrader文档目录
            toc = await get_hitrader_toc()
            print(toc)
            ```
        
        错误处理:
            - 如果目录文件不存在，返回提示信息
            - 如果读取过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            return HiTraderDocs._load_toc()
        except Exception as e:
            logger.error(f"获取HiTrader文档目录时发生错误: {e}")
            return f"获取文档目录时发生错误: {e}"
    
    @staticmethod
    async def get_hitrader_full_doc() -> str:
        """
        获取HiTrader完整文档内容
        
        该方法提供HiTrader文档的完整内容，包含所有章节和详细说明。
        文档内容来自于合并文档文件。
        
        Returns:
            str: 完整的文档内容。如果加载失败，则返回错误信息。
        
        使用示例:
            ```python
            # 获取HiTrader完整文档
            doc = await get_hitrader_full_doc()
            print(doc)
            ```
        
        错误处理:
            - 如果文档文件不存在，返回提示信息
            - 如果读取过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            return HiTraderDocs._load_full_doc()
        except Exception as e:
            logger.error(f"获取HiTrader完整文档时发生错误: {e}")
            return f"获取完整文档时发生错误: {e}"
    
    @staticmethod
    async def get_hitrader_chapter(
        chapter: str
    ) -> str:
        """
        获取HiTrader指定章节内容
        
        该方法根据提供的章节名称，返回对应章节的详细内容。支持模糊匹配，
        可以查找主章节、子章节或特定主题的内容。
        
        Args:
            chapter (str): 要查找的章节名称。不区分大小写，支持部分匹配。
                           例如："选股模块"、"交易操作"、"止损"等。
        
        Returns:
            str: 找到的章节内容。如果找不到匹配的章节，则返回错误信息。
        
        使用示例:
            ```python
            # 获取"选股模块"章节的内容
            content = await get_hitrader_chapter("选股模块")
            print(content)
            
            # 获取关于"MACD"的内容
            macd_content = await get_hitrader_chapter("MACD")
            print(macd_content)
            ```
        
        查找流程:
            该方法调用内部的_find_chapter方法，按照以下优先级查找章节:
            1. 精确匹配主章节名
            2. 精确匹配子章节名
            3. 精确匹配小节名
            4. 模糊匹配（如包含关键词）
        
        错误处理:
            - 如果找不到匹配的章节，返回提示信息
            - 如果查找过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            return HiTraderDocs._find_chapter(chapter)
        except Exception as e:
            logger.error(f"获取HiTrader章节内容时发生错误: {e}")
            return f"获取章节内容时发生错误: {e}"
    
    @staticmethod
    async def get_hitrader_docs(
        query: Optional[str] = None,
        section: Optional[str] = None
    ) -> str:
        """
        获取HiTrader文档内容，支持搜索和章节查询
        
        该方法提供了统一的接口来访问HiTrader文档，支持以下功能：
        1. 按关键词搜索文档内容
        2. 获取指定章节的内容
        3. 如果未指定查询参数，则返回文档目录
        
        Args:
            query (str, optional): 搜索关键词，用于在文档中搜索特定内容。
                                   例如："均线"、"止损"、"风控"等。默认为None。
            section (str, optional): 指定章节名称，如"核心概念"或"代码框架结构"。
                                     默认为None。
        
        Returns:
            str: 根据查询参数返回不同内容:
                - 如果指定了query，返回搜索结果
                - 如果指定了section，返回该章节内容
                - 如果都未指定，返回文档目录
        
        使用示例:
            ```python
            # 搜索关键词"均线"
            search_results = await get_hitrader_docs(query="均线")
            print(search_results)
            
            # 获取"代码框架结构"章节的内容
            chapter_content = await get_hitrader_docs(section="代码框架结构")
            print(chapter_content)
            
            # 获取文档目录
            toc = await get_hitrader_docs()
            print(toc)
            ```
        
        搜索机制:
            关键词搜索会在文档的每一行中查找匹配，返回匹配行及其上下文（前后各2行）。
            搜索不区分大小写，可以找到部分匹配的内容。
        
        错误处理:
            - 如果查询未找到匹配结果，返回提示信息
            - 如果查询过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            # 加载完整文档
            content = HiTraderDocs._load_full_doc()
            
            # 如果指定了搜索关键词，则在内容中搜索
            if query is not None and query.strip():
                query = query.lower()  # 转为小写，不区分大小写搜索
                lines = content.split('\n')
                results = []
                
                # 逐行搜索匹配内容
                for i, line in enumerate(lines):
                    if query in line.lower():
                        # 找到匹配行，提取上下文（前后各2行）
                        start = max(0, i-2)  # 上文开始行（不超出文档开头）
                        end = min(len(lines), i+3)  # 下文结束行（不超出文档末尾）
                        context = '\n'.join(lines[start:end])  # 提取上下文
                        results.append(f"匹配行 {i+1}:\n{context}\n---")  # 添加到结果
                
                # 返回搜索结果
                if results:
                    return f"关键词 '{query}' 的搜索结果:\n\n" + '\n'.join(results)
                else:
                    return f"未找到关键词 '{query}' 的匹配结果"
            
            # 如果指定了章节，则查找章节内容
            if section is not None and section.strip():
                return await HiTraderDocs.get_hitrader_chapter(section)
            
            # 如果未指定查询参数，返回文档目录
            return HiTraderDocs._load_toc()
            
        except Exception as e:
            logger.error(f"获取HiTrader文档时发生错误: {e}")
            return f"获取文档时发生错误: {e}"
    
    @staticmethod
    async def get_hitrader_syntax(
        feature: str
    ) -> str:
        """
        获取HiTrader特定功能的语法说明
        
        该方法提供了查询HiTrader特定功能语法和用法的专门接口。通过功能名映射到相应的
        文档章节，返回详细的语法说明和示例代码。
        
        Args:
            feature (str): 功能名称，如"选股"、"指标计算"、"交易操作"等。
                           支持多种常见功能的快捷名称。
        
        Returns:
            str: 该功能的语法说明和示例代码。如果找不到匹配的功能，则返回错误信息。
        
        功能映射:
            该方法维护了一个功能名称到文档章节的映射表，包括：
            - 选股 -> 选股模块
            - 指标 -> 指标模块
            - 择时 -> 择时模块
            - 风控 -> 风控模块
            - 交易操作 -> 交易操作
            - 持仓管理 -> 持仓管理
            - 技术指标 -> 技术指标
            - 常见指标（MA、MACD、RSI、KDJ等）
            - 其他功能（回测、风险管理、止损等）
        
        使用示例:
            ```python
            # 获取选股功能的语法说明
            syntax = await get_hitrader_syntax("选股")
            print(syntax)
            
            # 获取MACD指标的语法说明
            macd_syntax = await get_hitrader_syntax("MACD")
            print(macd_syntax)
            ```
        
        查找流程:
            1. 在功能映射表中查找对应的章节名
            2. 调用get_hitrader_chapter方法获取该章节内容
        
        错误处理:
            - 如果找不到匹配的功能章节，返回提示信息
            - 如果查询过程中发生异常，记录错误日志并返回错误信息
        """
        try:
            # 定义功能和对应的章节映射表
            # 这个映射表将用户输入的功能名映射到文档中的章节名
            feature_map = {
                # 基础模块
                "选股": "选股模块",
                "指标": "指标模块",
                "择时": "择时模块",
                "风控": "风控模块",
                
                # 常用操作
                "交易操作": "交易操作",
                "持仓管理": "持仓管理",
                "数据访问": "标的数据访问",
                "context": "Context对象",
                
                # 技术指标
                "技术指标": "技术指标",
                "MA": "移动平均线",
                "MACD": "MACD",
                "RSI": "RSI",
                "KDJ": "KDJ",
                "布林带": "布林带",
                
                # 其他功能
                "回测": "回测",
                "风险管理": "风险管理",
                "止损": "止损",
                "策略": "策略",
            }
            
            # 查找匹配的章节名
            # 如果在映射表中找到匹配项，使用映射的章节名
            # 否则直接使用输入的功能名作为章节名
            section = feature_map.get(feature, feature)
            
            # 使用章节查找功能获取内容
            return await HiTraderDocs.get_hitrader_chapter(section)
            
        except Exception as e:
            logger.error(f"获取HiTrader语法说明时发生错误: {e}")
            return f"获取语法说明时发生错误: {e}"


def register_resources(mcp: FastMCP):
    """
    注册HiTrader文档资源到MCP服务器
    
    该函数将HiTraderDocs类中的各种文档访问方法注册为MCP资源，使它们可以通过MCP框架
    被调用。注册后，这些资源可以在MCP客户端中使用。
    
    注册的资源包括:
        - get_hitrader_toc: 获取文档目录
        - get_hitrader_full_doc: 获取完整文档
        - get_hitrader_chapter: 获取指定章节内容
        - get_hitrader_docs: 搜索文档或获取章节
        - get_hitrader_syntax: 获取特定功能的语法说明
    
    Args:
        mcp (FastMCP): MCP服务器实例，用于注册资源。
    
    使用示例:
        ```python
        from mcp.server.fastmcp import FastMCP
        
        # 创建MCP服务器实例
        mcp = FastMCP("HiTrader文档服务")
        
        # 注册资源
        register_resources(mcp)
        
        # 启动服务器
        mcp.run()
        ```
    """
    # 注册目录资源
    mcp.resource()(HiTraderDocs.get_hitrader_toc)
    
    # 注册完整文档资源
    mcp.resource()(HiTraderDocs.get_hitrader_full_doc)
    
    # 注册章节资源
    mcp.resource()(HiTraderDocs.get_hitrader_chapter)
    
    # 注册文档搜索资源
    mcp.resource()(HiTraderDocs.get_hitrader_docs)
    
    # 注册语法资源
    mcp.resource()(HiTraderDocs.get_hitrader_syntax) 