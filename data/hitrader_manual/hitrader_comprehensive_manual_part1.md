# HiTrader 量化交易平台全面指南 - 第一部分：基础架构与核心语法

## 1. 平台概述

HiTrader是一个完整的量化交易平台，允许用户编写、回测和部署交易策略。平台提供了完整的代码框架和API，支持多种市场和标的，包括股票、期货等。

### 1.1 平台特点

- 完整的策略开发环境
- 高效的回测引擎
- 灵活的代码框架结构
- 丰富的技术指标库
- 多市场和多标的支持
- 实盘交易对接能力

### 1.2 运行环境

HiTrader基于Python语言，通过特定的代码结构来组织交易策略。使用时，需要注意：

- 平台替代了标准Python的部分功能，如日志输出
- 数据访问有特定的语法规则
- 回测和实盘有一致的代码接口

## 2. 代码框架结构

HiTrader的策略代码分为四个主要模块，每个模块有其特定的职责：

### 2.1 选股模块 (choose_stock)

负责定义交易标的，是策略的起点。该模块决定了策略将在哪些证券上执行。

```python
def choose_stock(context):
    """标的"""
    # 设置单个标的
    context.symbol_list = ["600000.XSHG"]
    
    # 或设置多个标的
    # context.symbol_list = ["600000.XSHG", "000001.XSHE"]
    
    # 或使用指数成分股
    # context.benchmark = "000300.XSHG"
    # context.symbol_list = ["000300.XSHG"]
    # context.parse_index = True
```

### 2.2 指标模块 (indicators)

负责计算交易指标和设置参数。在这个模块中：
- 初始化策略所需的各种参数
- 计算技术指标
- 准备择时和风控所需的数据

```python
def indicators(context):
    """指标"""
    # 设置通用参数
    context.trade_size = 100  # 交易量
    context.stop_loss = 0.05  # 止损比例
    context.take_profit = 0.10  # 止盈比例
    
    # 设置策略特有参数和计算指标
    context.sma_short = SMA(context.data.close, period=10)  # 短期均线
    context.sma_long = SMA(context.data.close, period=30)   # 长期均线
```

### 2.3 择时模块 (timing)

实现买卖逻辑，是策略的核心部分。在这个模块中：
- 判断买卖信号
- 执行买卖操作
- 管理持仓

```python
def timing(context):
    """择时"""
    # 判断交易信号
    if not context.position:  # 如果未持仓
        # 当短期均线上穿长期均线，买入信号
        if context.sma_short[-1] < context.sma_long[-1] and context.sma_short[0] > context.sma_long[0]:
            context.buy(data=context.data, size=context.trade_size, price=context.data.close[0]*1.1)
    else:  # 如果已持仓
        # 当短期均线下穿长期均线，卖出信号
        if context.sma_short[-1] > context.sma_long[-1] and context.sma_short[0] < context.sma_long[0]:
            context.close(data=context.data, price=context.data.close[0]*0.9)
```

### 2.4 风控模块 (control_risk)

实现风险控制逻辑，保护策略资金安全。在这个模块中：
- 实现止盈止损
- 实现资金管理规则
- 处理特殊情况（如股票停牌）

```python
def control_risk(context):
    """风控"""
    # 如果有持仓
    if context.position.size > 0:
        # 获取持仓均价
        hold_price = context.position.price
        # 计算止损价
        stop_price = (1 - context.stop_loss) * hold_price
        # 计算止盈价
        profit_price = (1 + context.take_profit) * hold_price
        
        # 当前价格触及止损或止盈价时，平仓
        if context.data.close[0] < stop_price or context.data.close[0] > profit_price:
            context.close(data=context.data, price=context.data.close[0]*0.9)
```

## 3. 核心概念和API

### 3.1 Context对象

`context`是全局对象，在策略的各个模块间共享数据，是数据交互的桥梁：

#### 3.1.1 日志输出

```python
context.log(message)  # 输出日志信息（替代print函数）
```

在 HiTrader 中，`print()` 函数是无效的，必须通过日志功能来输出信息。

**参数说明：**
- `message`: 要输出的日志内容，可以是任何类型

**特别说明：**
日志会自动拼接日期，在指标模块中由于没有日期概念，如需在指标模块打印日志，需加上 `level='DEBUG'` 参数：

```python
context.log("调试信息", level='DEBUG')
```

#### 3.1.2 账户信息访问

```python
context.broker.getvalue()  # 获取总资产（现金+持仓市值）
context.broker.cash       # 获取可用现金
```

**用法示例：**
```python
# 计算可用资金比例
available_cash_percent = context.broker.cash / context.broker.getvalue()
```

#### 3.1.3 标的池管理

```python
context.symbol_list = ["600000.XSHG"]  # 设置标的池
context.benchmark = "000300.XSHG"      # 设置基准标的
context.parse_index = True             # 设置是否解析指数成分股
```

**标的代码格式规则：**
- 上交所股票：代码.XSHG（如：600000.XSHG）
- 深交所股票：代码.XSHE（如：000001.XSHE）
- 上期所期货：代码.XSGE（如：FU2205.XSGE）
- 大商所期货：代码.XDCE（如：J2201.XDCE）

### 3.2 标的数据访问

#### 3.2.1 获取标的数据

```python
context.data              # 当标的池只有一个标的时，直接访问该标的
context.datas             # 访问所有标的的列表
context.getdatabyname(symbol)  # 通过代码获取特定标的
```

**用法示例：**
```python
# 遍历所有标的
for data in context.datas:
    current_price = data.close[0]
    symbol = data._name
    context.log(f"标的 {symbol} 当前价格: {current_price}")
```

#### 3.2.2 标的数据结构

标的数据包含多种属性：

```python
data.close     # 收盘价序列
data.open      # 开盘价序列
data.high      # 最高价序列
data.low       # 最低价序列
data.volume    # 成交量序列
data._name     # 标的代码
data.datetime  # 时间序列
```

**数据索引约定：**
- `[0]` 代表当前值
- `[-1]` 代表前一个值
- `[-2]` 代表前两个值，依此类推

**获取日期示例：**
```python
current_date = data.datetime.date(0)    # 当前日期
previous_date = data.datetime.date(-1)  # 前一个交易日日期
```

#### 3.2.3 处理停牌标的

```python
context.exclude_symbols = ["000001.XSHE"]  # 排除指定标的
context.fill_nan = True                    # 填充停牌数据
```

停牌填充规则：填充后，停牌的开盘价、最高价、最低价和收盘价都为最近一个交易日的收盘价，成交量为0。

### 3.3 持仓管理

#### 3.3.1 获取持仓信息

```python
context.position                     # 单标的情况下的持仓
context.getposition(data)            # 获取特定标的的持仓
context.getposition(data, side='long')  # 获取特定方向的持仓
```

**side参数可选值：**
- `'long'`: 多仓（默认）
- `'short'`: 空仓

#### 3.3.2 持仓数据属性

```python
position.size     # 持仓数量
position.price    # 持仓均价
position.pnl      # 浮动盈亏
position.available  # 可交易数量（考虑T+1规则）
```

**判断是否持仓示例：**
```python
if context.position:  # 或 if position.size > 0:
    # 有持仓的逻辑
else:
    # 无持仓的逻辑
```

### 3.4 交易操作

#### 3.4.1 基本交易指令

```python
context.buy(data=data, size=size, price=price)    # 买入操作
context.sell(data=data, size=size, price=price)   # 卖出操作
context.close(data=data, price=price)             # 平仓操作
```

**完整参数说明：**
- `data`: 标的数据对象
- `size`: 交易数量
- `price`: 交易价格（不设置时使用市价）
- `exectype`: 订单类型，默认为市价单
- `valid`: 订单有效期
- `side`: 交易方向（'long'或'short'）
- `signal`: 信号名称（用于记录）

**买入示例：**
```python
# 以接近收盘价的110%买入100股
context.buy(data=context.data, size=100, price=context.data.close[0]*1.1)
```

#### 3.4.2 高级交易指令

```python
# 调整持仓至目标市值
context.order_target_value(data=data, target=target_value, price=price)

# 按固定金额买入
context.order_value(data=data, value=value, price=price)
```

#### 3.4.3 订单管理

```python
# 获取当日委托单
orders = context.get_orders(status="submitted")  # 获取未成交订单
orders = context.get_orders(status="completed")  # 获取已成交订单
orders = context.get_orders(status="canceled")   # 获取已取消订单
orders = context.get_orders(status="all")        # 获取所有订单

# 取消订单
context.cancel(order)  # 取消指定订单
```

**订单属性：**
- `order.ordtype`: 订单类型（0为买入，1为卖出）
- `order.created_at`: 订单创建时间
- `order.created.price`: 委托价格
- `order.created.size`: 委托数量
- `order.executed.price`: 成交价格
- `order.executed.size`: 成交数量
- `order.executed.value`: 成交金额

## 4. 工具函数

### 4.1 基础数学函数

```python
# 四舍五入
context.round(value, ndigits=None)  # 四舍五入到指定小数位

# 最大最小值
max(a, b)  # 返回最大值
min(a, b)  # 返回最小值
```

### 4.2 日期函数

```python
# 获取交易日日期
current_date = context.data.datetime.date(0)

# 日期比较
if current_date.month != previous_date.month:
    # 月份交替的逻辑
```

### 4.3 交易费用计算

```python
# 获取交易费率
taker = context.get_taker(trade_amount)  # 根据交易金额获取费率
```

## 5. 基础功能代码示例

### 5.1 固定止盈止损

```python
def control_risk(context):
    """固定止盈止损"""
    for data in context.datas:
        position = context.getposition(data)
        if position.size > 0:
            # 获取持仓均价
            hold_price = position.price
            # 计算止损价
            stop_price = (1 - context.stop_loss) * hold_price
            # 计算止盈价
            profit_price = (1 + context.take_profit) * hold_price
            
            # 当前价格触及止损或止盈价时，平仓
            if data.close[0] < stop_price or data.close[0] > profit_price:
                context.close(data=data)
```

### 5.2 跟踪止损

```python
def control_risk(context):
    """跟踪止损"""
    # 如果当前已持仓
    if context.position.size != 0:
        # 更新最高价
        context.h_price = max(context.h_price, context.position.price, context.data.close[0])
        # 计算止损价
        stop_price = (1 - context.stop_rate) * context.h_price
        # 如果当前股价小于止损价
        if context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data)
            # 重置最高价
            context.h_price = 0
```

### 5.3 信号字典框架

```python
def timing(context):
    """使用信号字典的择时模块"""
    trade_dict = {'需买入的标的对象': [], '需卖出的标的对象': []}
    
    # 计算信号并填充字典
    for data in context.datas:
        # 计算指标
        rsi = context.rsi_dict[data]['rsi']
        
        # 买入信号
        if rsi[0] < context.bot:
            trade_dict['需买入的标的对象'].append(data)
        # 卖出信号
        elif rsi[0] > context.top:
            trade_dict['需卖出的标的对象'].append(data)
    
    # 执行交易
    for sell_data in trade_dict['需卖出的标的对象']:
        if context.getposition(sell_data).size > 0:
            context.close(data=sell_data)
    
    for buy_data in trade_dict['需买入的标的对象']:
        if context.getposition(buy_data).size == 0:
            context.buy(data=buy_data, size=context.trade_size)
``` 