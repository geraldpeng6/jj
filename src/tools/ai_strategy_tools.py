#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI策略生成工具模块

提供AI生成交易策略并添加到用户策略库的工具
"""

import logging
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP, Context

from utils.strategy_utils import create_user_strategy
from src.resources.hitrader_resource import HiTraderDocs

# 获取日志记录器
logger = logging.getLogger('quant_mcp.ai_strategy_tools')


async def enhance_strategy_description(description: str) -> str:
    """
    丰富和润色策略描述，使其更专业和详细
    
    此函数将接收一个基本策略描述，然后返回一个更丰富、更专业的描述
    
    Args:
        description: 原始策略描述
        
    Returns:
        str: 增强后的策略描述
    """
    try:
        # 对布林带策略进行特殊处理
        if "布林带" in description:
            # 如果是布林带策略，返回更丰富的描述
            enhanced_desc = f"""
# 布林带交易策略 (Bollinger Bands Trading Strategy)

## 策略概述
该策略基于布林带指标进行交易，布林带是一种结合了均线和标准差的通道型技术指标。该指标由三条线组成：上轨（Upper Band）、中轨（Middle Band）和下轨（Lower Band）。中轨通常是20期移动平均线，上下轨则是在中轨基础上加减标准差得出。

## 核心理念
布林带策略基于价格回归假设，即价格在大多数时间内会在均值附近波动，当价格触及或突破布林带边界时，往往意味着价格即将回归。该策略特别适用于横盘震荡行情。

## 信号逻辑
- 当收盘价跌破布林带下轨时，视为超卖信号，产生买入信号
- 当收盘价突破布林带上轨时，视为超买信号，产生卖出信号

## 参数设置
- 使用日线数据进行交易
- 布林带周期设置为20（标准中期参数）
- 标准差倍数设置为2（覆盖约95%的价格波动）

## 优势分析
- 信号明确，易于判断
- 适合波动市场，能有效识别超买超卖点
- 结合了趋势和波动性指标，信息更全面

## 风险控制
策略内置止损机制，以控制单笔交易风险。建议结合市场环境进行适当参数调整。

## 重要实现提示
- 如果策略涉及多只股票，必须指定基准标的，如：`context.benchmark = "000300.XSHG"`

原始描述: {description}
"""
            return enhanced_desc
        else:
            # 对其他类型策略的增强模板
            enhanced_desc = f"""
# 增强交易策略

## 策略概述
{description}

## 扩展详情
该策略通过技术指标分析市场行为，识别潜在的买入和卖出机会。结合历史数据分析和技术指标的交叉信号，实现更精准的市场时机判断。

## 优势分析
- 信号明确，规则清晰
- 适合特定市场环境
- 具有止损机制控制风险

## 重要实现提示
- 如果策略涉及多只股票，必须指定基准标的，如：`context.benchmark = "000300.XSHG"`

原始描述: {description}
"""
            return enhanced_desc

    except Exception as e:
        logger.error(f"增强策略描述时发生错误: {e}")
        return description  # 如果出错，返回原始描述


async def generate_strategy(description: str, strategy_name: str = "", ctx: Context = None) -> str:
    """
    基于用户描述生成交易策略并保存到用户策略库
    
    此工具将执行以下步骤:
    1. 增强和润色策略描述
    2. 加载HiTrader完整文档资源作为参考
    3. 分析用户的策略需求描述
    4. 生成策略需求文档和要求
    5. 返回需求和文档，让LLM自行使用工具完成策略
    
    Args:
        description: 用户对所需策略的描述，包括目标、条件、规则等
        strategy_name: 策略名称，如不提供则根据策略特点自动生成
        ctx: MCP上下文对象，不再使用
    
    Returns:
        str: 策略需求文档和指导信息
    """
    try:
        # 1. 增强策略描述
        enhanced_description = await enhance_strategy_description(description)
        
        # 2. 加载HiTrader文档内容作为参考 - 使用完整文档
        doc_content = HiTraderDocs._load_full_doc()
        if not doc_content:
            return "无法加载HiTrader文档，策略生成失败"
        
        # 3. 构建提示词，包含文档和要求
        prompt = f"""请根据以下需求生成一个完整的HiTrader交易策略。

策略需求描述：
{enhanced_description}

请生成以下四个函数的Python代码：
1. choose_stock(context) - 选股函数
2. indicator(context) - 指标计算函数
3. timing(context) - 择时函数
4. control_risk(context) - 风控函数

特别注意：
- 多股情况下（symbol_list包含多个股票）必须指定基准标的！例如：context.benchmark = "000300.XSHG"
- 单股情况下无需特别指定基准标的

参考以下HiTrader文档:
{doc_content}

代码要求：
- 每个函数必须符合HiTrader平台的API规范
- 代码必须可以直接运行，不能有语法错误
- 添加必要的注释解释策略逻辑
- 不要包含与策略无关的内容
- 不要使用未在HiTrader平台支持的函数或API

生成完整策略后，请使用适当的工具保存策略到用户策略库。
"""
        
        # 4. 返回需求文档，让LLM自行使用工具完成策略
        if not strategy_name:
            strategy_name = f"AI生成策略-{description[:20]}"
            
        result_str = f"""## 策略需求
策略名称: {strategy_name}
策略描述: 
{enhanced_description}

## 重要提示
多股情况下（symbol_list包含多个股票）必须指定基准标的！例如：`context.benchmark = "000300.XSHG"`
单股情况下无需特别指定基准标的。

## HiTrader文档参考
{doc_content}

## 开发指南
请根据以上需求和文档，生成完整的交易策略代码，包括以下四个函数：
1. choose_stock(context) - 选股函数
2. indicator(context) - 指标计算函数
3. timing(context) - 择时函数
4. control_risk(context) - 风控函数

完成后，使用create_user_strategy函数保存策略：
```python
strategy_data = {{
    "strategy_name": "{strategy_name}", 
    "choose_stock": choose_stock_code,
    "indicator": indicator_code, 
    "timing": timing_code,
    "control_risk": control_risk_code,
    "strategy_id": ""
}}
result = create_user_strategy(strategy_data)
```

请立即开始编写策略代码，返回四个完整函数。
"""
        return result_str
    
    except Exception as e:
        logger.error(f"生成策略时发生错误: {e}")
        return f"生成策略时发生错误: {e}"


def extract_code(content: str, section_name: str, func_signature: str) -> str:
    """
    从生成的内容中提取特定函数的代码
    
    Args:
        content: 生成的策略内容
        section_name: 部分名称，如"选股函数"
        func_signature: 函数签名，如"def choose_stock"
    
    Returns:
        str: 提取的函数代码
    """
    try:
        # 查找函数代码块
        lines = content.split('\n')
        code_block = []
        in_target_block = False
        
        # 查找代码块
        for i, line in enumerate(lines):
            # 检查函数签名
            if func_signature in line and not in_target_block:
                in_target_block = True
                code_block.append(line)
            # 如果在目标代码块中，继续收集代码
            elif in_target_block:
                # 如果遇到下一个函数定义或者结束标记，停止收集
                if line.startswith("def ") and func_signature not in line:
                    break
                # 如果是空代码块（只有函数定义和注释），添加一个pass语句
                if line.strip() == "" and i+1 < len(lines) and (lines[i+1].startswith("def ") or "```" in lines[i+1]):
                    code_block.append("    pass")
                    break
                code_block.append(line)
        
        # 如果代码块为空，尝试通过其他方式查找
        if not code_block:
            # 通过部分名称查找代码块
            start_marker = f"```{section_name}"
            end_marker = "```"
            
            start_idx = -1
            end_idx = -1
            
            for i, line in enumerate(lines):
                if start_marker in line and start_idx == -1:
                    start_idx = i
                elif end_marker in line and start_idx != -1 and end_idx == -1:
                    end_idx = i
                    break
            
            if start_idx != -1 and end_idx != -1:
                # 跳过标记行
                code_block = lines[start_idx+1:end_idx]
        
        # 如果代码块仍为空，尝试直接搜索函数定义
        if not code_block:
            in_func = False
            
            for i, line in enumerate(lines):
                if func_signature in line and not in_func:
                    in_func = True
                    code_block.append(line)
                elif in_func:
                    if line.strip() == "" and i+1 < len(lines) and lines[i+1].startswith("def "):
                        break
                    code_block.append(line)
        
        return "\n".join(code_block)
    
    except Exception as e:
        logger.error(f"提取{section_name}代码时发生错误: {e}")
        return ""


def extract_strategy_name(content: str) -> str:
    """
    从生成的内容中提取策略名称
    
    Args:
        content: 生成的策略内容
    
    Returns:
        str: 提取的策略名称，如果没有找到则返回默认名称
    """
    lines = content.lower().split('\n')
    
    # 常见的策略名称标记
    name_markers = ["策略名称", "策略名", "name", "策略：", "策略:"]
    
    for line in lines:
        for marker in name_markers:
            if marker in line:
                # 提取冒号或其他分隔符后的内容
                parts = line.split(":")
                if len(parts) > 1:
                    name = parts[1].strip()
                    # 如果名称太长，截断它
                    if len(name) > 30:
                        name = name[:30]
                    # 将首字母大写
                    return name.title()
                
                # 尝试其他分隔符
                parts = line.split("：")
                if len(parts) > 1:
                    name = parts[1].strip()
                    if len(name) > 30:
                        name = name[:30]
                    return name.title()
    
    # 默认策略名称
    return "AI生成策略"


def register_tools(mcp: FastMCP):
    """
    注册AI策略生成工具到MCP服务器
    
    Args:
        mcp: MCP服务器实例
    """
    # 添加日志记录
    logger.info("注册AI策略生成工具")
    
    # 注册AI策略生成工具
    mcp.tool()(generate_strategy) 