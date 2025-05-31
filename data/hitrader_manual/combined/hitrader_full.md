# HiTrader 量化交易平台全面指南

## HiTrader 量化交易平台全面指南 - 第一部分：基础架构与核心语法

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


---


## HiTrader 量化交易平台全面指南 - 第二部分：技术指标全解

## 1. 技术指标概述

HiTrader提供了丰富的技术指标库，覆盖了动量指标、趋势指标、波动指标、量价指标等多种类型。本部分将详细介绍平台支持的所有技术指标的用法、参数和返回值。

### 1.1 指标使用规则

在HiTrader中使用技术指标时，需要注意以下几点：

1. 所有指标通常在`indicators`函数中初始化
2. 指标计算结果以时间序列形式返回，可使用索引访问历史值
3. 大多数指标需要标的价格或成交量作为输入参数
4. 某些指标会返回多个数值，通常以对象属性形式访问

### 1.2 指标访问约定

技术指标返回的是序列对象，访问规则与价格数据相同：

- `[0]` 代表当前值
- `[-1]` 代表前一个值
- `[-2]` 代表前两个值，以此类推

## 2. 趋势指标

### 2.1 移动平均线 (MA)

#### 2.1.1 简单移动平均线 (SMA)

**函数名**: `SMA`, `MovingAverageSimple`

**用途**: 计算周期内的算术平均值，是最基础的趋势指标

**调用方式**:
```python
sma = SMA(data.close, period=20)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 必填 |

**返回值**:
- `sma`: 移动平均值序列

**使用示例**:
```python
def indicators(context):
    # 计算20日简单移动平均线
    context.sma = SMA(context.data.close, period=20)
    
def timing(context):
    # 使用移动平均线判断买卖信号
    if context.data.close[0] > context.sma[0] and context.data.close[-1] < context.sma[-1]:
        # 价格上穿均线，买入信号
        context.buy(data=context.data, size=100)
    elif context.data.close[0] < context.sma[0] and context.data.close[-1] > context.sma[-1]:
        # 价格下穿均线，卖出信号
        context.close(data=context.data)
```

#### 2.1.2 指数移动平均线 (EMA)

**函数名**: `EMA`, `MovingAverageExponential`

**用途**: 赋予近期数据更高的权重，对价格变化的反应更敏感

**调用方式**:
```python
ema = EMA(data.close, period=20)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 必填 |

**返回值**:
- `ema`: 指数移动平均值序列

**使用示例**:
```python
def indicators(context):
    # 计算快慢两条指数移动平均线
    context.ema_fast = EMA(context.data.close, period=12)
    context.ema_slow = EMA(context.data.close, period=26)
    
def timing(context):
    # 使用EMA交叉判断买卖信号
    if context.ema_fast[0] > context.ema_slow[0] and context.ema_fast[-1] < context.ema_slow[-1]:
        # 快线上穿慢线，买入信号
        context.buy(data=context.data, size=100)
    elif context.ema_fast[0] < context.ema_slow[0] and context.ema_fast[-1] > context.ema_slow[-1]:
        # 快线下穿慢线，卖出信号
        context.close(data=context.data)
```

#### 2.1.3 加权移动平均线 (WMA)

**函数名**: `WMA`, `MovingAverageWeighted`

**用途**: 按时间顺序加权，最近的数据具有最大权重

**调用方式**:
```python
wma = WMA(data.close, period=20)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 必填 |

**返回值**:
- `wma`: 加权移动平均值序列

### 2.2 MACD (移动平均线收敛发散)

**函数名**: `MACD`

**用途**: 通过两条不同周期的EMA之差及其平均值，判断价格趋势的强弱和可能的转变

**调用方式**:
```python
macd = MACD(data.close, period_me1=12, period_me2=26, period_signal=9)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period_me1 | 快线周期 | 整数 | 12 |
| period_me2 | 慢线周期 | 整数 | 26 |
| period_signal | 信号线周期 | 整数 | 9 |

**返回值**:
- `macd.macd`: DIF值序列 (快线-慢线)
- `macd.signal`: DEA值序列 (DIF的移动平均)
- `macd.histo`: MACD柱状图值序列 (DIF-DEA)

**使用示例**:
```python
def indicators(context):
    # 计算MACD指标
    macd_indicator = MACD(context.data.close, period_me1=12, period_me2=26, period_signal=9)
    context.dif = macd_indicator.macd       # DIF线
    context.dea = macd_indicator.signal     # DEA线
    context.macd = macd_indicator.histo     # MACD柱

def timing(context):
    # 判断金叉死叉信号
    if context.dif[0] > context.dea[0] and context.dif[-1] < context.dea[-1]:
        # DIF上穿DEA，金叉信号，买入
        context.buy(data=context.data, size=100)
    elif context.dif[0] < context.dea[0] and context.dif[-1] > context.dea[-1]:
        # DIF下穿DEA，死叉信号，卖出
        context.close(data=context.data)
```

### 2.3 布林带 (Bollinger Bands)

**函数名**: `BollingerBands`

**用途**: 通过计算价格的标准差，形成价格通道，评估价格波动性及可能的反转点

**调用方式**:
```python
bb = BollingerBands(data.close, period=20, devfactor=2.0)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 20 |
| devfactor | 标准差倍数 | 浮点数 | 2.0 |

**返回值**:
- `bb.top`: 上轨线序列 (中轨+标准差*倍数)
- `bb.mid`: 中轨线序列 (SMA)
- `bb.bot`: 下轨线序列 (中轨-标准差*倍数)

**使用示例**:
```python
def indicators(context):
    # 计算布林带指标
    bb = BollingerBands(context.data.close, period=20, devfactor=2.0)
    context.bb_top = bb.top      # 上轨
    context.bb_mid = bb.mid      # 中轨
    context.bb_bot = bb.bot      # 下轨
    
def timing(context):
    # 使用布林带判断买卖信号
    if context.data.close[0] <= context.bb_bot[0]:
        # 价格触及下轨，买入信号
        context.buy(data=context.data, size=100)
    elif context.data.close[0] >= context.bb_top[0]:
        # 价格触及上轨，卖出信号
        context.close(data=context.data)
```

### 2.4 肯特纳通道 (Keltner Channel)

**函数名**: `KeltnerChannel`

**用途**: 结合ATR和EMA形成的价格通道，用于识别趋势和超买超卖区域

**调用方式**:
```python
kc = KeltnerChannel(data, period=20, devfactor=2.0)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 20 |
| devfactor | ATR倍数 | 浮点数 | 2.0 |

**返回值**:
- `kc.top`: 上轨线序列
- `kc.mid`: 中轨线序列
- `kc.bot`: 下轨线序列

**使用示例**:
```python
def indicators(context):
    # 计算肯特纳通道指标
    kc = KeltnerChannel(context.data, period=20, devfactor=2.0)
    context.kc_top = kc.top
    context.kc_mid = kc.mid
    context.kc_bot = kc.bot
    
def timing(context):
    # 使用肯特纳通道判断买卖信号
    if context.data.close[0] <= context.kc_bot[0]:
        # 价格触及下轨，买入信号
        context.buy(data=context.data, size=100)
    elif context.data.close[0] >= context.kc_top[0]:
        # 价格触及上轨，卖出信号
        context.close(data=context.data)
```

### 2.5 唐奇安通道 (Donchian Channel)

**函数名**: `DonchianChannel`

**用途**: 通过计算周期内的最高价和最低价形成的价格通道，用于判断突破信号

**调用方式**:
```python
dc = DonchianChannel(data, period=20)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 20 |

**返回值**:
- `dc.top`: 上轨线序列（最高价）
- `dc.mid`: 中轨线序列（中值）
- `dc.bot`: 下轨线序列（最低价）

**使用示例**:
```python
def indicators(context):
    # 计算唐奇安通道指标
    dc = DonchianChannel(context.data, period=20)
    context.dc_top = dc.top
    context.dc_mid = dc.mid
    context.dc_bot = dc.bot
    # 计算价格与通道上下轨的交叉信号
    context.dc_top_cross = CrossOver(context.data.close, context.dc_top)
    context.dc_bot_cross = CrossOver(context.data.close, context.dc_bot)
    
def timing(context):
    # 使用唐奇安通道判断买卖信号
    if context.dc_top_cross[0] > 0:  # 价格上穿上轨
        # 突破上轨，买入信号
        context.buy(data=context.data, size=100)
    elif context.dc_bot_cross[0] < 0:  # 价格下穿下轨
        # 突破下轨，卖出信号
        context.close(data=context.data)
```

## 3. 震荡指标

### 3.1 相对强弱指数 (RSI)

**函数名**: `RSI`, `RelativeStrengthIndex`

**用途**: 通过计算上涨与下跌幅度的比值，衡量价格超买超卖状态

**调用方式**:
```python
rsi = RSI(data.close, period=14, safediv=True)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 14 |
| safediv | 是否保护除法 | 布尔值 | True |

**返回值**:
- `rsi`: RSI值序列 (取值范围0-100)

**使用示例**:
```python
def indicators(context):
    # 计算RSI指标
    context.rsi = RSI(context.data.close, period=14)
    # 设置超买超卖阈值
    context.rsi_upper = 70  # 超买阈值
    context.rsi_lower = 30  # 超卖阈值
    
def timing(context):
    # 使用RSI判断买卖信号
    if context.rsi[0] < context.rsi_lower:
        # RSI低于30，超卖信号，买入
        context.buy(data=context.data, size=100)
    elif context.rsi[0] > context.rsi_upper:
        # RSI高于70，超买信号，卖出
        context.close(data=context.data)
```

### 3.2 随机指标 (KDJ)

**函数名**: `KDJ`, `StochasticFast`

**用途**: 通过计算收盘价在一段时间内最高价与最低价之间的位置，判断超买超卖状态

**调用方式**:
```python
kdj = KDJ(data, period=14, period_dfast=3, period_dslow=3)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 14 |
| period_dfast | K值周期 | 整数 | 3 |
| period_dslow | D值周期 | 整数 | 3 |
| movav | 移动平均类型 | 函数 | SMA |

**返回值**:
- `kdj.percK`: K值序列
- `kdj.percD`: D值序列
- `kdj.percJ`: J值序列 (3*K-2*D)

**使用示例**:
```python
def indicators(context):
    # 计算KDJ指标
    kdj = KDJ(context.data, period=14, period_dfast=3, period_dslow=3)
    context.k = kdj.percK
    context.d = kdj.percD
    context.j = kdj.percJ
    
def timing(context):
    # 使用KDJ判断买卖信号
    if context.k[0] > context.d[0] and context.k[-1] < context.d[-1]:
        # K线上穿D线，金叉信号，买入
        context.buy(data=context.data, size=100)
    elif context.k[0] < context.d[0] and context.k[-1] > context.d[-1]:
        # K线下穿D线，死叉信号，卖出
        context.close(data=context.data)
```

### 3.3 顺势指标 (CCI)

**函数名**: `CommodityChannelIndex`, `CCI`

**用途**: 测量价格偏离其平均值的程度，判断价格超买超卖状态和可能的反转点

**调用方式**:
```python
cci = CommodityChannelIndex(data.close, period=20)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 20 |

**返回值**:
- `cci`: CCI值序列

**使用示例**:
```python
def indicators(context):
    # 计算CCI指标
    context.cci = CommodityChannelIndex(context.data.close, period=20)
    # 设置超买超卖阈值
    context.cci_upper = 100   # 超买阈值
    context.cci_lower = -100  # 超卖阈值
    
def timing(context):
    # 使用CCI判断买卖信号
    if context.cci[-1] < context.cci_lower and context.cci[0] > context.cci_lower:
        # CCI从下向上穿过-100，买入信号
        context.buy(data=context.data, size=100)
    elif context.cci[-1] > context.cci_upper and context.cci[0] < context.cci_upper:
        # CCI从上向下穿过+100，卖出信号
        context.close(data=context.data)
```

### 3.4 Williams %R

**函数名**: `WilliamsR`, `PercentR`

**用途**: 类似随机指标，测量收盘价与最高最低价的位置关系，判断超买超卖状态

**调用方式**:
```python
percentr = WilliamsR(data, period=14)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 14 |

**返回值**:
- `percentr`: %R值序列 (取值范围-100到0)

**使用示例**:
```python
def indicators(context):
    # 计算Williams %R指标
    context.percentr = WilliamsR(context.data, period=14)
    
def timing(context):
    # 使用Williams %R判断买卖信号
    if context.percentr[0] < -80:
        # %R低于-80，超卖信号，买入
        context.buy(data=context.data, size=100)
    elif context.percentr[0] > -20:
        # %R高于-20，超买信号，卖出
        context.close(data=context.data)
```

## 4. 量价指标

### 4.1 平均真实波幅 (ATR)

**函数名**: `AverageTrueRange`, `ATR`

**用途**: 测量价格波动性，常用于设置止损点和头寸规模

**调用方式**:
```python
atr = AverageTrueRange(data, period=14)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 14 |
| movav | 移动平均类型 | 函数 | EMA |

**返回值**:
- `atr`: ATR值序列

**使用示例**:
```python
def indicators(context):
    # 计算ATR指标
    context.atr = AverageTrueRange(context.data, period=14)
    # 设置止损倍数
    context.atr_multiple = 3.0
    
def control_risk(context):
    # 使用ATR实现动态止损
    if context.position.size > 0:
        # 计算止损价格
        stop_price = context.position.price - context.atr[0] * context.atr_multiple
        if context.data.close[0] < stop_price:
            # 触发止损，平仓
            context.close(data=context.data)
```

### 4.2 能量潮 (OBV)

**函数名**: `OnBalanceVolume`, `OBV`

**用途**: 通过成交量的累积反映价格趋势强度

**调用方式**:
```python
obv = OnBalanceVolume(data)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |

**返回值**:
- `obv`: OBV值序列

**使用示例**:
```python
def indicators(context):
    # 计算OBV指标
    context.obv = OnBalanceVolume(context.data)
    # 计算OBV的移动平均线
    context.obv_ma = SMA(context.obv, period=20)
    
def timing(context):
    # 使用OBV判断买卖信号
    if context.obv[0] > context.obv_ma[0] and context.obv[-1] < context.obv_ma[-1]:
        # OBV上穿其移动平均线，买入信号
        context.buy(data=context.data, size=100)
    elif context.obv[0] < context.obv_ma[0] and context.obv[-1] > context.obv_ma[-1]:
        # OBV下穿其移动平均线，卖出信号
        context.close(data=context.data)
```

## 5. 辅助指标

### 5.1 交叉检测 (CrossOver)

**函数名**: `CrossOver`

**用途**: 检测两个序列的交叉情况，简化交叉判断逻辑

**调用方式**:
```python
cross = CrossOver(data1, data2)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data1 | 第一个数据序列 | 序列 | 必填 |
| data2 | 第二个数据序列 | 序列 | 必填 |

**返回值**:
- `cross`: 交叉值序列
  - `1.0`: data1从下向上穿过data2
  - `-1.0`: data1从上向下穿过data2
  - `0.0`: 没有交叉

**使用示例**:
```python
def indicators(context):
    # 计算短期和长期移动平均线
    context.sma_short = SMA(context.data.close, period=5)
    context.sma_long = SMA(context.data.close, period=20)
    # 计算均线交叉信号
    context.cross = CrossOver(context.sma_short, context.sma_long)
    
def timing(context):
    # 使用均线交叉判断买卖信号
    if context.cross[0] > 0:
        # 短期均线上穿长期均线，金叉信号，买入
        context.buy(data=context.data, size=100)
    elif context.cross[0] < 0:
        # 短期均线下穿长期均线，死叉信号，卖出
        context.close(data=context.data)
```

### 5.2 标准差 (StdDev)

**函数名**: `StdDev`, `StandardDeviation`

**用途**: 测量数据的波动性，常用于布林带等技术指标的计算

**调用方式**:
```python
stddev = StdDev(data.close, period=20, movav=SMA)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 必填 |
| movav | 移动平均类型 | 函数 | SMA |

**返回值**:
- `stddev`: 标准差序列

### 5.3 涨跌幅 (ROC)

**函数名**: `ROC`, `RateOfChange`

**用途**: 计算价格变动的百分比

**调用方式**:
```python
roc = ROC(data.close, period=10)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 数据序列 | 序列 | 必填 |
| period | 计算周期 | 整数 | 必填 |

**返回值**:
- `roc`: 涨跌幅序列 (百分比形式)

**使用示例**:
```python
def indicators(context):
    # 计算10日涨跌幅
    context.roc = ROC(context.data.close, period=10)
    
def timing(context):
    # 使用涨跌幅判断买卖信号
    if context.roc[0] < -10:
        # 10日跌幅超过10%，买入信号
        context.buy(data=context.data, size=100)
    elif context.roc[0] > 10:
        # 10日涨幅超过10%，卖出信号
        context.close(data=context.data)
```

### 5.4 最大回撤 (MaxDrawDown)

**函数名**: `MaxDrawDown`, `MaxDrawDownN`

**用途**: 计算价格的最大回撤比例，评估风险

**调用方式**:
```python
mdd = MaxDrawDownN(data, period=252)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 必填 |

**返回值**:
- `mdd`: 最大回撤序列 (百分比形式)

**使用示例**:
```python
def indicators(context):
    # 计算252日(一年)最大回撤
    context.mdd = MaxDrawDownN(context.data, period=252)
    
def control_risk(context):
    # 使用最大回撤控制风险
    if context.mdd[0] > 0.2:  # 回撤超过20%
        # 减仓或平仓
        if context.position.size > 0:
            # 平掉一半仓位
            context.sell(data=context.data, size=context.position.size//2)
```

### 5.5 夏普比率 (SharpeRatio)

**函数名**: `SharpeRatio`

**用途**: 计算投资收益与风险的比率，评估策略质量

**调用方式**:
```python
sharpe = SharpeRatio(data, period=252, riskfreerate=0.0)
```

**参数说明**:

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| data | 标的数据对象 | 对象 | 必填 |
| period | 计算周期 | 整数 | 必填 |
| riskfreerate | 无风险利率 | 浮点数 | 0.0 |

**返回值**:
- `sharpe`: 夏普比率序列

## 6. 复合指标使用示例

### 6.1 MACD + KDJ 综合信号

```python
def indicators(context):
    """指标计算"""
    # 计算MACD指标
    macd = MACD(context.data.close, period_me1=12, period_me2=26, period_signal=9)
    context.dif = macd.macd
    context.dea = macd.signal
    context.macd_hist = macd.histo
    
    # 计算KDJ指标
    kdj = KDJ(context.data, period=14, period_dfast=3, period_dslow=3)
    context.k = kdj.percK
    context.d = kdj.percD
    context.j = kdj.percJ
    
def timing(context):
    """择时信号"""
    # 未持仓时，使用MACD金叉作为买入信号
    if not context.position:
        if context.dif[0] > context.dea[0] and context.dif[-1] < context.dea[-1]:
            # MACD金叉，买入
            context.buy(data=context.data, size=100)
    else:
        # 持仓时，使用KDJ死叉作为卖出信号
        if context.k[0] < context.d[0] and context.k[-1] > context.d[-1]:
            # KDJ死叉，卖出
            context.close(data=context.data)
```

### 6.2 均线系统 + RSI过滤

```python
def indicators(context):
    """指标计算"""
    # 计算均线系统
    context.sma5 = SMA(context.data.close, period=5)
    context.sma10 = SMA(context.data.close, period=10)
    context.sma20 = SMA(context.data.close, period=20)
    
    # 计算RSI指标
    context.rsi = RSI(context.data.close, period=14)
    
def timing(context):
    """择时信号"""
    # 均线多头排列且RSI处于合理区间时买入
    if not context.position:
        # 检查均线多头排列
        if context.sma5[0] > context.sma10[0] > context.sma20[0]:
            # 检查RSI不在超买区间
            if context.rsi[0] < 70:
                # 买入信号
                context.buy(data=context.data, size=100)
    else:
        # 均线死叉或RSI超买时卖出
        if (context.sma5[0] < context.sma10[0] or context.rsi[0] > 70):
            # 卖出信号
            context.close(data=context.data)
```

### 6.3 布林带 + 成交量确认

```python
def indicators(context):
    """指标计算"""
    # 计算布林带
    bb = BollingerBands(context.data.close, period=20, devfactor=2.0)
    context.bb_top = bb.top
    context.bb_mid = bb.mid
    context.bb_bot = bb.bot
    
    # 计算成交量移动平均
    context.volume_ma = SMA(context.data.volume, period=20)
    
def timing(context):
    """择时信号"""
    # 未持仓时
    if not context.position:
        # 价格触及下轨且成交量放大
        if context.data.close[0] <= context.bb_bot[0] and context.data.volume[0] > 1.5 * context.volume_ma[0]:
            # 买入信号
            context.buy(data=context.data, size=100)
    else:
        # 价格触及上轨或突破中轨且成交量放大
        if (context.data.close[0] >= context.bb_top[0] or 
            (context.data.close[0] < context.bb_mid[0] and context.data.close[-1] > context.bb_mid[-1] and
             context.data.volume[0] > 1.5 * context.volume_ma[0])):
            # 卖出信号
            context.close(data=context.data)
``` 


---


## HiTrader 量化交易平台全面指南 - 第三部分：高级功能与风险管理

## 1. 高级功能

### 1.1 订单管理

#### 1.1.1 取消订单功能

在使用量化交易时，为避免长时间未成交的订单最终在不满足策略条件的情况下成交，可以使用取消订单功能。

**功能实现**:

在指标模块中设置订单取消的时间间隔：
```python
def indicators(context):
    # 其他代码...
    
    # 设置订单取消间隔时间为1800秒(30分钟)
    context.cancel_interval = 1800
```

在择时模块中实现订单取消逻辑：
```python
def timing(context):
    # 取消超时订单
    canceled_value = 0
    current_datetime = context.datetime.datetime()
    
    # 获取所有已委托的订单
    submitted_orders = context.get_orders(status='submitted')
    for order in submitted_orders:
        # 获取委托创建时间
        created_time = order.created_at
        # 获取当前距离委托时的间隔秒数
        interval_now = (current_datetime - created_time).seconds
        
        # 如果订单为买入且超过设定的取消时间
        if order.ordtype == 0 and interval_now >= context.cancel_interval:
            # 取消订单
            context.cancel(order)
            # 计算订单金额
            order_value = order.created.price * order.created.size
            # 累加已取消订单的金额
            canceled_value += order_value
            context.log(f"已取消超时订单: {order.created.price} x {order.created.size}")
    
    # 其他择时逻辑...
```

#### 1.1.2 T+1 交易限制

股票市场的T+1规则要求当日买入的股票不能在当天卖出，只能在下一交易日卖出。在HiTrader中可以通过以下方式实现T+1限制：

**功能实现**:

在择时模块中，使用标的的可交易数量进行卖出操作：
```python
def timing(context):
    # 其他择时逻辑...
    
    # 遍历需要卖出的标的
    for sell_data in trade_dict['需卖出的标的对象']:
        # 获取当天可交易的数量
        salable_size = context.getposition(sell_data).available
        
        # 如果可交易数量大于0
        if salable_size > 0:
            # 卖出可交易数量，而不是全部持仓
            context.sell(data=sell_data, size=salable_size, price=sell_data.close[0]*0.9)
```

在风控模块中也需要相应调整：
```python
def control_risk(context):
    # 遍历所有标的
    for data in context.datas:
        # 获取当天可交易的数量
        salable_size = context.getposition(data).available
        
        # 如果有可交易持仓
        if salable_size > 0:
            # 获取持仓均价
            hold_price = context.getposition(data).price
            # 计算止损价
            stop_price = (1 - context.stop_loss) * hold_price
            
            # 如果当前价格达到了止损价
            if data.close[0] < stop_price:
                # 执行平仓，但只平掉可交易的部分
                context.sell(data=data, size=salable_size, price=data.close[0]*0.9)
```

### 1.2 资金管理

#### 1.2.1 总资金风控

总资金风控确保投入交易的资金不超过账户总资产的特定比例，降低整体风险。

**功能实现**:

在指标模块中设置最大资金使用比例：
```python
def indicators(context):
    # 其他代码...
    
    # 设置最大使用资金比例为80%
    context.max_percent = 0.8
```

在择时模块中实现资金控制：
```python
def timing(context):
    # 其他代码...
    
    # 计算当前买入所需的资金
    buy_value = buy_data.close[0] * context.trade_size
    
    # 计算剩余的现金比例
    remaining_cash_percent = (context.broker.cash - buy_value) / context.broker.getvalue()
    
    # 如果投入的总资金不超过最大资金使用比例
    if remaining_cash_percent > (1 - context.max_percent):
        # 执行买入
        context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0]*1.1)
```

#### 1.2.2 单日资金风控

单日资金风控限制每个交易日内买入标的使用的资金比例，避免单日过度交易。

**功能实现**:

在指标模块中设置单日最大资金使用比例：
```python
def indicators(context):
    # 其他代码...
    
    # 设置最大使用资金比例
    context.max_percent = 0.8
    # 设置每天最大使用资金比例
    context.day_max_percent = 0.4
```

在择时模块中实现单日资金控制：
```python
def timing(context):
    # 设置记录当天买入资金为0
    day_buy_value = 0
    
    # 计算已提交订单的资金
    submitted_orders = context.get_orders(status='submitted')
    for order in submitted_orders:
        if order.ordtype == 0:  # 买入订单
            day_buy_value += order.created.price * order.created.size
    
    # 计算已成交订单的资金
    completed_orders = context.get_orders(status='completed')
    for order in completed_orders:
        if order.ordtype == 0:  # 买入订单
            day_buy_value += order.executed.value
    
    # 遍历需要买入的标的
    for buy_data in trade_dict['需买入的标的对象']:
        # 计算当前买入所需的资金
        buy_value = buy_data.close[0] * context.trade_size
        
        # 计算当天用于买入的资金比例
        day_buy_percent = (day_buy_value + buy_value) / context.broker.getvalue()
        
        # 计算剩余的现金比例
        remaining_cash_percent = (context.broker.cash - buy_value) / context.broker.getvalue()
        
        # 检查资金使用是否符合限制
        if day_buy_percent < context.day_max_percent and remaining_cash_percent > (1 - context.max_percent):
            # 执行买入
            order = context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0]*1.1)
            
            # 如果订单创建成功
            if order:
                # 累加当日买入资金
                day_buy_value += buy_value
```

### 1.3 时间管理

#### 1.3.1 时间风控（交易日计数）

时间风控限制持仓的最长时间，超过特定交易日数量后强制平仓。

**功能实现**:

在指标模块中初始化相关参数：
```python
def indicators(context):
    # 其他代码...
    
    # 设置最长持有天数
    context.max_hold_days = 10
    # 初始化存储买入时间的字典
    context.buy_date_dict = {}
```

在择时模块记录买入时间：
```python
def timing(context):
    # 其他代码...
    
    # 执行买入后记录买入时间
    if order:
        # 记录买入日期
        context.buy_date_dict[buy_data._name] = context.data.datetime.date(0)
```

在风控模块实现时间风控：
```python
def control_risk(context):
    # 获取当前日期
    current_date = context.data.datetime.date(0)
    
    # 遍历所有标的
    for data in context.datas:
        # 获取当天可交易的数量
        salable_size = context.getposition(data).available
        
        # 如果有可交易持仓且有买入记录
        if salable_size > 0 and data._name in context.buy_date_dict:
            # 获取买入日期
            buy_date = context.buy_date_dict[data._name]
            
            # 计算持仓交易日数量（这里假设有交易日历函数）
            hold_days = context.trading_days_between(buy_date, current_date)
            
            # 如果持仓天数超过最长持有天数
            if hold_days >= context.max_hold_days:
                # 执行平仓
                context.sell(data=data, size=salable_size, price=data.close[0]*0.9)
                # 移除买入记录
                del context.buy_date_dict[data._name]
```

## 2. 风险管理

### 2.1 止损策略

#### 2.1.1 固定止盈止损

最基本的风险管理方式，根据持仓成本设定固定比例的止盈止损点。

```python
def control_risk(context):
    # 遍历所有标的
    for data in context.datas:
        position = context.getposition(data)
        # 如果有持仓
        if position.size > 0:
            # 获取持仓均价
            hold_price = position.price
            # 计算止损价
            stop_price = (1 - context.stop_loss) * hold_price
            # 计算止盈价
            profit_price = (1 + context.take_profit) * hold_price
            
            # 当前价格触及止损或止盈价时，平仓
            if data.close[0] < stop_price or data.close[0] > profit_price:
                context.close(data=data, price=data.close[0]*0.9)
```

#### 2.1.2 跟踪止损

动态调整止损点位，保护盈利，锁定收益。

```python
def indicators(context):
    # 其他代码...
    
    # 设置止损比例
    context.stop_rate = 0.05
    # 设置最高价为0
    context.h_price = 0
```

```python
def control_risk(context):
    # 如果当前已持仓
    if context.position.size != 0:
        # 更新最高价
        context.h_price = max(context.h_price, context.position.price, context.data.close[0])
        
        # 计算止损价
        stop_price = (1 - context.stop_rate) * context.h_price
        
        # 如果当前股价小于止损价
        if context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data, price=context.data.close[0]*0.9)
            # 重置最高价
            context.h_price = 0
```

#### 2.1.3 ATR动态止损

基于波动性指标ATR设置动态止损点，适应市场波动。

```python
def indicators(context):
    # 其他代码...
    
    # 计算ATR指标
    context.atr = AverageTrueRange(context.data, period=14)
    # 设置ATR倍数
    context.atr_multiple = 3.0
```

```python
def control_risk(context):
    # 如果持仓
    if context.position.size > 0:
        # 计算止损价格 = 持仓均价 - ATR值 * 倍数
        stop_price = context.position.price - context.atr[0] * context.atr_multiple
        
        # 如果当前价格低于止损价
        if context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data, price=context.data.close[0]*0.9)
```

### 2.2 仓位管理

#### 2.2.1 等比例资金分配

将账户资金平均分配给各个交易标的。

```python
def timing(context):
    # 计算每个标的可使用的资金
    per_stock_value = context.broker.getvalue() * context.max_percent / len(context.stock_pool)
    
    # 遍历标的池
    for symbol in context.stock_pool:
        data = context.getdatabyname(symbol)
        
        # 计算可买入的数量
        size = per_stock_value / data.close[0] // 100 * 100  # 确保是100的整数倍
        
        # 执行买入
        context.buy(data=data, size=size)
```

#### 2.2.2 基于波动性的资金分配

根据标的波动性分配资金，波动性大的标的分配较少资金。

```python
def indicators(context):
    # 其他代码...
    
    # 计算各标的的波动性
    context.volatility = {}
    for data in context.datas:
        # 计算20日ATR
        atr = AverageTrueRange(data, period=20)
        # 计算相对波动性（ATR/价格）
        context.volatility[data._name] = atr[0] / data.close[0]
```

```python
def timing(context):
    # 计算总波动性
    total_volatility = sum(1/vol for vol in context.volatility.values())
    
    # 遍历标的池
    for symbol in context.stock_pool:
        data = context.getdatabyname(symbol)
        
        # 计算资金分配比例（波动性小的分配更多资金）
        weight = (1/context.volatility[symbol]) / total_volatility
        
        # 计算可用资金
        available_value = context.broker.getvalue() * context.max_percent * weight
        
        # 计算可买入的数量
        size = available_value / data.close[0] // 100 * 100
        
        # 执行买入
        context.buy(data=data, size=size)
```

### 2.3 回撤控制

监控策略回撤，在回撤超过特定阈值时采取措施。

```python
def indicators(context):
    # 其他代码...
    
    # 计算252日(一年)最大回撤
    context.mdd = MaxDrawDownN(context.data, period=252)
    # 设置回撤阈值
    context.max_drawdown_limit = 0.2  # 20%的回撤阈值
```

```python
def control_risk(context):
    # 如果当前回撤超过阈值
    if context.mdd[0] > context.max_drawdown_limit:
        # 减仓操作
        for data in context.datas:
            position = context.getposition(data)
            if position.size > 0:
                # 卖出一半持仓
                context.sell(data=data, size=position.size//2)
```

## 3. 数据处理

### 3.1 基本面数据获取

HiTrader提供了获取基本面数据的功能，可以用于选股和策略决策。

```python
def choose_stock(context):
    # 获取当前日期
    current_date = context.data.datetime.date()
    
    # 获取市值数据
    valuation_data = context.get_fundamentals(date=current_date, type="valuation")
    # 筛选出市值小于特定值的标的
    filtered_data = valuation_data[valuation_data['market_cap'] < 10000]  # 市值小于100亿
    
    # 获取财务指标数据
    indicator_data = context.get_fundamentals(date=current_date, type="indicator")
    # 筛选出净利润增长率大于特定值的标的
    filtered_data = indicator_data[indicator_data['inc_net_profit_year_on_year'] > 20]  # 净利润同比增长大于20%
    
    # 提取筛选后的标的代码
    context.stock_pool = filtered_data['symbol_exchange'].to_list()
```

### 3.2 特殊日期处理

处理特定日期的逻辑，如月初、季度初等。

```python
def timing(context):
    # 获取当前日期
    current_date = context.data.datetime.date(0)
    # 获取前一交易日日期
    previous_date = context.data.datetime.date(-1)
    
    # 判断是否为月初第一个交易日
    if current_date.month != previous_date.month:
        # 月初调仓逻辑
        context.log("月初调仓")
        # 调仓代码...
    
    # 判断是否为季度初第一个交易日
    if current_date.month in [1, 4, 7, 10] and previous_date.month not in [1, 4, 7, 10]:
        # 季度初调仓逻辑
        context.log("季度初调仓")
        # 调仓代码...
```

### 3.3 自定义指标计算

创建自定义指标进行策略优化。

```python
def indicators(context):
    # 其他代码...
    
    # 自定义复合指标：价格动量 * 成交量变化率
    context.price_momentum = ROC(context.data.close, period=20)  # 20日价格动量
    context.volume_change = ROC(context.data.volume, period=20)  # 20日成交量变化率
    
    # 计算复合指标
    context.composite_indicator = []
    for i in range(len(context.price_momentum)):
        # 复合指标 = 价格动量 * 成交量变化率
        value = context.price_momentum[i] * context.volume_change[i]
        context.composite_indicator.append(value)
```

## 4. 代码优化技巧

### 4.1 高效的信号计算

在处理多标的策略时，使用信号字典提高代码效率和可读性。

```python
def timing(context):
    # 创建信号字典
    trade_dict = {'需买入的标的对象': [], '需卖出的标的对象': []}
    
    # 遍历所有标的，计算信号
    for data in context.datas:
        # 计算信号
        buy_signal = False
        sell_signal = False
        
        # 判断买入信号
        if context.sma_short[data._name][0] > context.sma_long[data._name][0] and \
           context.sma_short[data._name][-1] < context.sma_long[data._name][-1]:
            buy_signal = True
        
        # 判断卖出信号
        if context.sma_short[data._name][0] < context.sma_long[data._name][0] and \
           context.sma_short[data._name][-1] > context.sma_long[data._name][-1]:
            sell_signal = True
        
        # 更新信号字典
        position = context.getposition(data)
        if not position and buy_signal:
            trade_dict['需买入的标的对象'].append(data)
        elif position.size > 0 and sell_signal:
            trade_dict['需卖出的标的对象'].append(data)
    
    # 执行交易
    for sell_data in trade_dict['需卖出的标的对象']:
        context.close(data=sell_data)
    
    for buy_data in trade_dict['需买入的标的对象']:
        context.buy(data=buy_data, size=context.trade_size)
```

### 4.2 优化指标计算

在多标的策略中优化指标计算，避免重复计算。

```python
def indicators(context):
    # 创建指标字典，按标的分别存储
    context.indicator_dict = {}
    
    # 遍历所有标的
    for data in context.datas:
        # 为每个标的计算指标
        sma_short = SMA(data.close, period=10)
        sma_long = SMA(data.close, period=30)
        rsi = RSI(data.close, period=14)
        
        # 存储到字典中
        context.indicator_dict[data._name] = {
            'sma_short': sma_short,
            'sma_long': sma_long,
            'rsi': rsi
        }
```

### 4.3 动态参数优化

根据市场状态动态调整策略参数。

```python
def indicators(context):
    # 基础参数设置
    context.base_period = 20
    
    # 计算市场波动性
    context.market_volatility = StdDev(context.data.close, period=20)
    
    # 动态调整参数
    def update_parameters():
        # 如果市场波动性高于阈值，使用更长的周期
        if context.market_volatility[0] > 0.02:  # 2%的日波动
            context.sma_period = context.base_period * 1.5
        else:
            context.sma_period = context.base_period
        
        # 计算动态参数的均线
        context.dynamic_sma = SMA(context.data.close, period=int(context.sma_period))
    
    # 初始化时调用一次
    update_parameters()
    
    # 存储更新参数的函数以便在择时中调用
    context.update_parameters = update_parameters
```

```python
def timing(context):
    # 每次调用择时函数时更新参数
    context.update_parameters()
    
    # 使用动态参数的指标进行交易决策
    if context.data.close[0] > context.dynamic_sma[0] and context.data.close[-1] < context.dynamic_sma[-1]:
        context.buy(data=context.data, size=context.trade_size)
    elif context.data.close[0] < context.dynamic_sma[0] and context.data.close[-1] > context.dynamic_sma[-1]:
        context.close(data=context.data)
```

## 5. 调试与日志记录

### 5.1 策略调试技巧

在策略开发过程中使用日志输出关键信息，辅助调试。

```python
def timing(context):
    # 记录当前资产状态
    context.log(f"当前总资产: {context.broker.getvalue()}, 可用现金: {context.broker.cash}")
    
    # 记录指标值
    context.log(f"当前SMA(10)值: {context.sma_short[0]}, SMA(30)值: {context.sma_long[0]}")
    context.log(f"当前RSI值: {context.rsi[0]}")
    
    # 记录交易信号
    if context.sma_short[0] > context.sma_long[0] and context.sma_short[-1] < context.sma_long[-1]:
        context.log("生成买入信号")
        context.buy(data=context.data, size=context.trade_size)
```

### 5.2 高级日志格式化

使用结构化日志提高可读性和分析效率。

```python
def timing(context):
    # 记录状态信息
    status_info = {
        "日期": context.data.datetime.date(0),
        "总资产": context.broker.getvalue(),
        "可用现金": context.broker.cash,
        "持仓标的": [data._name for data in context.datas if context.getposition(data).size > 0],
        "技术指标": {
            "SMA(10)": context.sma_short[0],
            "SMA(30)": context.sma_long[0],
            "RSI": context.rsi[0]
        }
    }
    
    # 使用JSON格式输出日志
    import json
    context.log(f"状态信息: {json.dumps(status_info, indent=2)}")
```

### 5.3 性能监控

监控策略运行性能，识别潜在的优化点。

```python
def indicators(context):
    # 其他代码...
    
    # 初始化性能监控指标
    context.execution_times = {
        "计算指标时间": [],
        "信号生成时间": [],
        "交易执行时间": []
    }
```

```python
def timing(context):
    import time
    
    # 记录指标计算开始时间
    start_time = time.time()
    
    # 计算指标
    # ...指标计算代码...
    
    # 记录指标计算时间
    context.execution_times["计算指标时间"].append(time.time() - start_time)
    
    # 记录信号生成开始时间
    start_time = time.time()
    
    # 生成交易信号
    # ...信号生成代码...
    
    # 记录信号生成时间
    context.execution_times["信号生成时间"].append(time.time() - start_time)
    
    # 记录交易执行开始时间
    start_time = time.time()
    
    # 执行交易
    # ...交易执行代码...
    
    # 记录交易执行时间
    context.execution_times["交易执行时间"].append(time.time() - start_time)
    
    # 定期输出性能数据
    if len(context.execution_times["计算指标时间"]) % 20 == 0:
        for key, times in context.execution_times.items():
            avg_time = sum(times[-20:]) / 20
            context.log(f"{key}平均耗时: {avg_time:.6f}秒")
``` 


---


## HiTrader 量化交易平台全面指南 - 第四部分：完整策略案例

本部分提供完整的策略实现案例，从简单到复杂，展示HiTrader的各种功能和应用场景。

## 1. 单均线策略

最基础的趋势跟踪策略，使用单一均线判断买卖时机。

```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600000.XSHG"]  # 浦发银行

def indicators(context):
    """指标"""
    # 计算15日的均价
    context.sma = SMA(period=15)
    # 设置止盈比例为0.1
    context.p_takeprofit = 0.1
    # 设置止损比例为0.05
    context.p_stoploss = 0.05

def timing(context):
    """择时"""
    # 如果未持仓
    if context.position.size == 0:
        # 如果当天收盘价在15日均线之上
        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:
            # 执行买入
            context.buy(data=context.data, price=context.data.close[0]*1.1)
    # 如果当天收盘价在15日均线之下
    elif context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
        # 执行平仓
        context.close(data=context.data, price=context.data.close[0]*0.9)

def control_risk(context):
    """风控"""
    # 如果持仓
    if context.position.size != 0:
        # 计算止盈价
        limit_price = (1 + context.p_takeprofit) * context.position.price
        # 计算止损价
        stop_price = (1 - context.p_stoploss) * context.position.price

        # 如果当前收盘价大于止盈价或小于止损价
        if context.data.close[0] > limit_price or context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data, price=context.data.close[0]*0.9)
```

## 2. 双均线策略

使用两条不同周期的均线交叉判断买卖时机。

```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600158.XSHG"]  # 中体产业

def indicators(context):
    """指标"""
    # 计算15日的均价，赋值给变量context.short_sma
    context.short_sma = SMA(period=15)
    # 计算30日的均价，赋值给变量context.long_sma
    context.long_sma = SMA(period=30)
    # 设置止损比例
    context.stop_loss = 0.05
    # 设置止盈比例
    context.take_profit = 0.10

def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当15日均价上升并且交叉穿过30日均价时，出现买入信号
        if context.short_sma[-1] < context.long_sma[-1] and context.short_sma[0] > context.long_sma[0]:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.1)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当15日均价下降并且交叉穿过30日均价时，出现卖出信号
        if context.short_sma[-1] > context.long_sma[-1] and context.short_sma[0] < context.long_sma[0]:
            # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)

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

## 3. MACD策略

使用MACD指标判断买卖时机，利用DIF与DEA的交叉产生信号。

```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600360.XSHG"]  # 华微电子

def indicators(context):
    """指标"""
    # 计算MACD指标
    # 快速EMA周期 period_me1
    # 慢速EMA周期 period_me2
    # DIFF平滑周期 period_signal
    macd = MACD(period_me1=12, period_me2=26, period_signal=9)
    # 计算DIF值
    context.dif = macd.macd
    # 计算MACD值
    context.macd = macd.signal
    # 计算Histo值
    context.histo = context.dif - context.macd

def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当DIF和MACD均大于0，并且DIF向上突破MACD时，出现买入信号
        if context.dif > 0 and context.macd > 0 and context.histo[0] > 0 and context.histo[-1] < 0:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.1)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当DIF和MACD均小于等于0，并且DIF向下突破MACD时，出现卖出信号
        if context.dif < 0 and context.macd < 0 and context.histo[0] < 0 and context.histo[-1] > 0:
            # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)

def control_risk(context):
    """风控"""
    pass
```

## 4. 布林带策略

利用布林带通道的上下轨判断超买超卖信号。

```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600000.XSHG"]  # 浦发银行

def indicators(context):
    """指标"""
    # 计算布林带指标，period周期修改为60
    bb = BollingerBands(context.data.close, period=60)
    # 计算阻力线
    context.top = bb.top
    # 计算支撑线
    context.bot = bb.bot
    # 设置止损比例
    context.stop_loss = 0.05

def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当股价触及下限支撑线时，出现买入信号
        if context.data.close[0] <= context.bot[0]:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.1)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当股价触及上限阻力线时，出现卖出信号
        if context.data.close[0] >= context.top[0]:
        # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)

def control_risk(context):
    """风控"""
    # 如果持仓
    if context.position.size > 0:
        # 获取持仓均价
        entry_price = context.position.price
        # 计算止损价
        stop_price = entry_price * (1 - context.stop_loss)
        
        # 如果价格低于止损价
        if context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data)
```

## 5. RSI策略

利用RSI指标的超买超卖特性进行交易。

```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600158.XSHG", "600000.XSHG", "600036.XSHG"]

def indicators(context):
    """指标"""
    # 设置每次买卖的数量
    context.trade_size = 100
    # 设置止盈比例
    context.take_profit = 0.15
    # 设置止损比例
    context.stop_loss = 0.08

    # 初始化RSI指标上限
    context.top = 70
    # 初始化RSI指标下限
    context.bot = 25
    # 设置指标字典
    context.rsi_dict = {}
    # 设置RSI的计算周期
    rsi_period = 6
    # 遍历所有标的
    for data in context.datas:
        # 计算周期为6的RSI指标
        rsi = RSI(data.close, period=rsi_period, safediv=True)
        # 记录标的对应的RSI指标 
        context.rsi_dict[data] = {'rsi': rsi}

def timing(context):
    """择时"""
    # 设置信号字典
    trade_dict = {'需买入的标的对象': [], '需卖出的标的对象': []}
    # 遍历所有标的
    for data in context.datas:
        # 获取RSI
        rsi = context.rsi_dict[data]['rsi']

        # 当RSI值低于其下限时
        if rsi[0] < context.bot:
            # 记录需要买入的标的对象
            trade_dict['需买入的标的对象'].append(data)
        # 当RSI值高于其上限时
        elif rsi[0] > context.top:
            # 记录需要卖出的标的对象
            trade_dict['需卖出的标的对象'].append(data)
    
    # 执行交易
    for sell_data in trade_dict['需卖出的标的对象']:
        # 获取持仓数量
        hold_size = context.getposition(sell_data).size
        # 如果持仓数量大于0
        if hold_size > 0:
            # 执行平仓
            context.close(data=sell_data, price=sell_data.close[0]*0.9)

    for buy_data in trade_dict['需买入的标的对象']:
        # 执行买入
        context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0]*1.1)

def control_risk(context):
    """风控"""
    # 遍历所有标的
    for data in context.datas:
        # 获取标的当前持仓数量
        hold_size = context.getposition(data).size
        # 如果有持仓
        if hold_size > 0:
            # 获取持仓均价
            hold_price = context.getposition(data).price
            # 计算止损价
            stop_price = (1 - context.stop_loss) * hold_price
            # 计算止盈价
            profit_price = (1 + context.take_profit) * hold_price
            
            # 如果当前价格达到了止盈或止损价
            if data.close[0] < stop_price or data.close[0] > profit_price:
                # 执行平仓
                context.close(data=data, price=data.close[0]*0.9)
```

## 6. 跟踪止损策略

使用移动止损点保护利润，结合均线交叉产生交易信号。

```python
def choose_stock(context):
    """标的"""
    #  设置标的为北信源
    context.symbol_list = ["300352.XSHE"]

def indicators(context):
    """指标"""
    # 计算5日的均价，赋值给变量context.short_sma
    context.short_sma = SMA(context.data.close, period=5)
    # 计算30日的均价，赋值给变量context.long_sma
    context.long_sma = SMA(context.data.close, period=30)

    # 设置止损比例
    context.stop_rate = 0.05
    # 设置最高价为0
    context.h_price = 0
    # 设置账户最大使用资金
    context.max_percent = 0.9

def timing(context):
    """择时"""
    # 设置死叉信号为False
    context.d_cross_sign = False

    # 如果未持仓
    if context.position.size == 0:
        # 当5日均价上升并且交叉穿过30日均价时，出现买入信号
        if context.short_sma[-1] < context.long_sma[-1] and context.short_sma[0] > context.long_sma[0]:
            # 计算买入数量
            size = context.broker.cash * context.max_percent / context.data.close[0] // 100 * 100
            # 执行买入
            context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)

    # 如果5日均价下跌并且穿过30日均价时
    elif context.short_sma[-1] > context.long_sma[-1] and context.short_sma[0] < context.long_sma[0]:
        # 执行平仓
        context.close(data=context.data, price=context.data.close[0]*0.9)
        # 重置最高价
        context.h_price = 0
        # 将死叉信号设置为True
        context.d_cross_sign = True

def control_risk(context):
    """风控"""
    # 如果当前已持仓并且未出现死叉
    if context.position.size != 0 and not context.d_cross_sign:
        # 获取最高价
        context.h_price = max(
            context.h_price, context.position.price, context.data.close[0])

        # 计算止损价
        stop_price = (1 - context.stop_rate) * context.h_price

        # 如果当前股价小于止损价
        if context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data, price=context.data.close[0]*0.9)
            # 重置最高价
            context.h_price = 0
```

## 7. 网格交易策略

在预设的价格区间内，价格上涨时卖出，价格下跌时买入。

```python
def choose_stock(context):
    """标的"""
    # 设置标的：华夏中小企业100ETF
    context.symbol_list = ["159902.XSHE"]

def indicators(context):
    """指标"""
    # 设置档位总数
    context.number = 10
    # 设置初始仓位
    context.open_percent = 0.5
    # 设置挡位间距
    context.distance = 0.05

    # 设置初始订单状态
    context.open_number = False

def timing(context):
    """择时"""
    # 判断是否已买入初始订单
    if not context.open_number:
        # 记录基准价格
        context.base_price = context.data.close[0]

        # 计算所需买入的初始订单数量
        buy_size = context.broker.getvalue() / context.data.close[0] * context.open_percent // 100 * 100
        # 执行买入
        context.buy(data=context.data, size=buy_size)

        # 记录前一交易日的挡位，初始挡位是0
        context.last_index = 0
        # 计算每变化一挡对应的订单数量
        context.per_size = context.broker.getvalue() / context.data.close[0] / context.number // 100 * 100
        # 计算档位的上边界
        context.max_index = round(context.number * context.open_percent)
        # 计算档位的下边界，由于在初始挡位的下方，所以结果是负数
        context.min_index = context.max_index - context.number 

        # 更新初始订单状态
        context.open_number = True
        context.log('已买入初始订单')

def control_risk(context):
    """风控"""
    # 判断是否已买入初始订单
    if context.open_number:
        # 计算今日挡位
        index = (context.data.close[0] - context.base_price) // context.distance

        # 如果今日挡位低于下边界
        if index < context.min_index:
            # 用下边界替代今日挡位
            index = context.min_index
        # 如果当前挡位高于上边界
        elif index > context.max_index:
            # 用上边界替代今日挡位
            index = context.max_index

        context.log("上一交易日挡位:{}".format(context.last_index))
        context.log("当前交易日挡位:{}".format(index))

        # 计算挡位变化数
        change_index = index - context.last_index
        # 如果挡位变化数大于0
        if change_index > 0:
            # 执行卖出
            context.sell(data=context.data, size=change_index*context.per_size)
        # 如果挡位变化数小于0
        elif change_index < 0:
            # 执行买入
            context.buy(data=context.data, size=-change_index*context.per_size)
        
        # 更新前一日挡位
        context.last_index = index
```

## 8. 多因子策略

结合多个指标和因子进行标的选择和交易决策。

```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "600048.XSHG"
    # 股票组合的代码赋值给context.symbol_list 
    context.symbol_list = ["600048.XSHG", "601010.XSHG", "600663.XSHG","600007.XSHG", "600185.XSHG"]

    # 创建一个空列表
    rate_list = []
    # 遍历所有股票
    for data in context.datas:
        # 获取每只股票的截面收益率，存储到列表rate_list中
        rate = context.rate[data._name][0]
        if rate > context.threshold:
            rate_list.append([data._name, rate])

    # 按照收益率进行降序排序，并获取指定数量的股票池
    sorted_rate = sorted(rate_list, key=lambda x: x[1], reverse=True)
    context.stock_pool = [i[0] for i in sorted_rate]
    context.pool_size = len(context.stock_pool)

def indicators(context):
    """指标"""
    # 移动平均时间窗口
    context.period = 15
    # 设置用于购买股票的资金比例
    context.max_value_percent = 0.9  
    # 设置需要考虑收益率的时间窗口
    context.look_back_days = 50  
    # 设置截面收益率的阈值
    context.threshold = 0.2

    # 创建一个空字典
    context.sma = dict()
    context.rate = dict()
    for data in context.datas:
        # 计算所有股票的15日的移动平均价，存储到字典context.sma中
        context.sma[data._name] = SMA(data.close, period=context.period)
        # 计算所有股票的截面收益率，存储到字典context.rate中
        context.rate[data._name] = PctChange(data.close, period=50)

def timing(context):
    """择时"""
    # 提取当前的账户价值
    total_value = context.broker.getvalue()

    if context.pool_size != 0:
        # 计算用于购买标的池中不同标的的金额

        # 构建一个fibonacci数列
        def fibonacci(n):
            if n < 3:
                return 1
            return fibonacci(n - 1) + fibonacci(n - 2)

        fibo = []
        for i in range(context.pool_size + 1):
            if i > 0:
                fibo.append(fibonacci(i))

        fibo = sorted(fibo, reverse=True)
        
        buy_list = []
        # 遍历所有标的
        for data in context.datas:
            # 获取每只股票的仓位
            position = context.getposition(data).size
            # 如果该股票在股票池中，且未持仓，且当前交易日收盘价大于其20日均价,出现买入信号
            if not position and data._name in context.stock_pool and data.close[0] > context.sma[data._name][0]:
                # 统计每次符合买入条件的标的
                buy_list.append(data._name)

                # 计算用于购买该标的的金额
                rate = fibo[context.stock_pool.index(data._name)] / sum(fibo)
                per_value = rate * total_value * context.max_value_percent

                # 计算该标的的买入数量
                size = int(per_value / 100 / data.close[0]) * 100
                # 发送买入指令
                context.buy(data=data, size=size, price=data.close[0]*1.1)

def control_risk(context):
    """风控"""
    # 遍历所有股票
    for data in context.datas:
        # 获取每只股票的仓位
        position = context.getposition(data).size
        # 如果该股票已持仓，但不在股票池中，或当前交易日收盘价小于其15日均价,出现卖出信号
        if position != 0 and data._name not in context.stock_pool or context.sma[data._name][0] > data.close[0]:
            # 平仓
            context.close(data=data, price=data.close[0]*0.9)
```

## 9. 基于市值的选股策略

使用市值等基本面数据进行选股，构建投资组合。

```python
def choose_stock(context):
    """标的"""
    # 设置基准标的
    context.benchmark = "000300.XSHG"
    # 设置标的
    context.symbol_list = ["000300.XSHG"]
    # 打开解析成分股参数
    context.parse_index = True
    
    # 如果入选标的列表为空
    if context.stock_pool == []:
        # 获取当前日期
        current_date = context.data.datetime.date()

        # 获取市值数据
        valuation_data = context.get_fundamentals(date=current_date, type="valuation")
        # 取出标的代码、市净率、市销率数据
        valuation_data = valuation_data[['symbol_exchange', 'pb_ratio', 'ps_ratio']]

        # 获取分数数据，从1开始
        rank_list = []
        for i in range(1, len(valuation_data)+1):
            rank_list.append(i)

        # 根据市净率按大到小进行排序
        valuation_data = valuation_data.sort_values(by='pb_ratio', ascending=False)
        # 将市净率得分写入到市值数据中
        valuation_data['pb_rank'] = rank_list

        # 根据市销率按大到小进行排序
        valuation_data = valuation_data.sort_values(by='ps_ratio', ascending=False)
        # 将市销率得分写入到市值数据中
        valuation_data['ps_rank'] = rank_list

        # 计算总分
        valuation_data['score'] = valuation_data['pb_rank'] + valuation_data['ps_rank']

        # 根据分数从大到小进行排序
        valuation_data = valuation_data.sort_values(by='score', ascending=False)

        # 获取前 10 个股票名称，并添加到入选标的列表中
        context.stock_pool = valuation_data['symbol_exchange'].to_list()[:10]

        context.log('\n筛选出来的标的有{}'.format(context.stock_pool))

def indicators(context):
    """指标"""
    # 设置账户最大使用资金
    context.max_percent = 0.9

    # 将买入状态设置为 False，表示未执行过买入操作
    context.have_bought = False
    # 初始化入选标的列表
    context.stock_pool = []

def timing(context):
    """择时"""
    # 如果未买入并且入选标的列表不为空
    if not context.have_bought and context.stock_pool != []:
        # 计算每个标的所能用的资金
        stock_value = context.broker.getvalue() * context.max_percent / len(context.stock_pool)

        # 遍历入选标的列表
        for name in context.stock_pool:
            # 获取入选的标的对象
            data = context.getdatabyname(name)

            # 计算买入数量
            size = stock_value / data.close[0] // 100 * 100
            # 执行买入操作
            context.buy(data=data, size=size, price=data.close[0]*1.1)

        # 将买入状态设置为 True，表示已执行过买入操作
        context.have_bought = True

def control_risk(context):
    """风控"""
    # 在这里可以添加止损等风控逻辑
    pass
```

## 10. 定投策略

实现基于定期定额的投资策略，结合均线偏离进行调整。

```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "000001.XSHG"  
    # 输入组合标的
    context.symbol_list = ["000001.XSHG", "510300.XSHG"]

def indicators(context):
    """指标"""
    # 定投日期
    context.buy_day = 9
    # 定投金额
    context.buy_money = 5000
    # 指数的均线时间窗口
    context.period = 100  
    # 偏离上界限
    context.up_bound = 1.1
    # 偏离下界限
    context.down_bound = 0.9 
    # 向上突破上界限时的定投倍数 
    context.up_multiple = 0.5 
    # 向下突破下界限时的定投倍数 
    context.down_multiple = 1.5  
    # 计算指数的均价
    for data in context.datas:
        if data._name == context.benchmark:
            context.sma = MovingAverageSimple(data.close, period=context.period)

def timing(context):
    """择时"""
    # 获取当前交易日的日期
    current_date = context.datas[0].datetime.date(0)
    # 获取上一个交易日的日期
    previous_date = context.datas[0].datetime.date(-1)
    # 判断当前交易日是否是定投日期
    if context.buy_day == int(str(current_date)[-2:]) or int(str(previous_date)[-2:]) < context.buy_day < int(str(current_date)[-2:]):
        # 遍历所有标的
        for data in context.datas:
            # 筛选目标标的
            if data._name != context.benchmark:
                # 计算基金净值与指标均价的比值
                ratio = data.close[-1] / context.sma
                
                # 获取定投的费率
                taker = context.get_taker(context.buy_money)
                # 基于定投金额和费率计算申购份额
                size = context.buy_money / (data.close[0] * (1 + taker))

                # 判断是否偏离下界限
                if ratio < context.down_bound:
                    # 当当前价格低于平均持有成本时，则多买
                    size = size * context.down_multiple
                    
                # 判断是否偏离上界限
                if ratio >= context.up_bound:
                    # 当当前价格高于平均持有成本时，则少买
                    size = size * context.up_multiple

                # 发送申购指令
                context.order = context.buy(data=data, size=size, price=context.data.close[0]*1.1)

def control_risk(context):
    """风控"""
    pass
``` 


---

