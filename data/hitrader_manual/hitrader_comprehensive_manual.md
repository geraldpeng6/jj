# HiTrader 量化交易平台全面指南

这是一份全面的HiTrader量化交易平台使用手册，包含了平台的所有功能、语法规则和使用案例。本手册分为四个部分，涵盖了从基础架构到高级应用的所有内容。

## 文档结构

### [第一部分：基础架构与核心语法](hitrader_comprehensive_manual_part1.md)

* 平台概述
* 代码框架结构（选股、指标、择时、风控）
* 核心概念和API
* Context对象使用
* 标的数据访问
* 持仓管理
* 交易操作
* 工具函数
* 基础功能代码示例

### [第二部分：技术指标全解](hitrader_comprehensive_manual_part2.md)

* 技术指标概述
* 趋势指标（MA, MACD, 布林带等）
* 震荡指标（RSI, KDJ, CCI等）
* 量价指标（ATR, OBV等）
* 辅助指标（CrossOver, StdDev等）
* 复合指标使用示例

### [第三部分：高级功能与风险管理](hitrader_comprehensive_manual_part3.md)

* 高级功能（订单管理、资金管理、时间管理）
* 风险管理（各类止损策略、仓位管理、回撤控制）
* 数据处理（基本面数据、特殊日期处理、自定义指标）
* 代码优化技巧
* 调试与日志记录

### [第四部分：完整策略案例](hitrader_comprehensive_manual_part4.md)

* 单均线策略
* 双均线策略
* MACD策略
* 布林带策略
* RSI策略
* 跟踪止损策略
* 网格交易策略
* 多因子策略
* 基于市值的选股策略
* 定投策略

## 使用指南

本手册既可以作为学习教程，也可以作为查询参考。建议按照以下方式使用：

1. 初学者：按照第一部分到第四部分的顺序阅读，逐步掌握HiTrader平台的使用
2. 进阶用户：直接查阅第二部分和第三部分，了解技术指标使用和高级功能
3. 实战应用：参考第四部分的完整策略案例，结合自身需求进行修改和优化

## 关键语法速查

### 基本框架

```python
def choose_stock(context):
    """标的"""
    # 设置交易标的
    context.symbol_list = ["600000.XSHG"]

def indicators(context):
    """指标"""
    # 计算技术指标
    context.sma = SMA(context.data.close, period=20)
    # 设置参数
    context.stop_loss = 0.05

def timing(context):
    """择时"""
    # 买入逻辑
    if not context.position:
        if context.data.close[0] > context.sma[0]:
            context.buy(data=context.data, size=100)
    # 卖出逻辑
    else:
        if context.data.close[0] < context.sma[0]:
            context.close(data=context.data)

def control_risk(context):
    """风控"""
    # 止损逻辑
    if context.position.size > 0:
        if context.data.close[0] < (1 - context.stop_loss) * context.position.price:
            context.close(data=context.data)
```

### 常用函数

```python
# 获取当前日期
current_date = context.data.datetime.date(0)

# 输出日志
context.log("当前价格: {}".format(context.data.close[0]))

# 获取持仓
position = context.getposition(data)

# 交易操作
context.buy(data=data, size=100)
context.sell(data=data, size=100)
context.close(data=data)

# 获取账户信息
total_value = context.broker.getvalue()
cash = context.broker.cash
```

## 版本信息

本手册基于HiTrader最新版本编写，涵盖了所有主要功能和API。随着平台的更新，部分功能可能会有变化，请以官方文档为准。 