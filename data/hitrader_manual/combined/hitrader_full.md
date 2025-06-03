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

策略详情 - 单均线策略

基本信息:
- ID: RvK9lMrkgjaOxY8m2oJBV3GEb6qmX1eZ
- 名称: 单均线策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600000.XSHG"]

`````

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算15日的均价，赋值给变量context.sma
    context.sma = SMA(period=15)

```

择时代码:
```python
def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当股票收盘价上升并且交叉穿过15日均价时，出现买入信号
        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.1)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当股票收盘价小于15日均价时，出现卖出信号
        if context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
            # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)

```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 双均线策略

基本信息:
- ID: bXw27Vmpqx3enDo9b0PW5jNBaY1KLGZl
- 名称: 双均线策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600158.XSHG"]

```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算15日的均价，赋值给变量context.short_sma
    context.short_sma = SMA(period=15)
    # 计算30日的均价，赋值给变量context.long_sma
    context.long_sma = SMA(period=30)

```

择时代码:
```python
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

```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 海龟交易策略

基本信息:
- ID: 1dKPJgRbWyxjO3oJxAGNmLnVpqQ2a5vE
- 名称: 海龟交易策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["FU2205.XSGE"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置唐奇安通道相关参数
    # 设置唐奇安通道上轨周期
    dc_high_period = 20
    # 设置唐奇安通道下轨周期
    dc_low_period = 10
    # 获取唐奇安通道上轨
    dc_high_line = DonchianChannel(context.data, period=dc_high_period).top(-1)
    # 获取唐奇安通道下轨
    dc_low_line = DonchianChannel(context.data, period=dc_low_period).bot(-1)

    # 获取收盘价与唐奇安通道上轨突破信号
    context.dc_high_signal = CrossOver(context.data.close, dc_high_line)
    # 获取收盘价与唐奇安通道下轨突破信号
    context.dc_low_signal = CrossOver(context.data.close, dc_low_line)

    # 设置 ATR 相关参数
    # 设置平均真实波幅周期
    atr_period = 20
    # 获取平均真实波幅 ATR
    context.atr = AverageTrueRange(context.data, period=atr_period)

    # 设置其他与交易相关的常量
    # 设置加仓波幅系数
    context.scale_ratio = 0.5
    # 设置买入次数上限
    context.scale_number = 4
    # 设置止损波幅系数
    context.stop_ratio = 2
    # 设置账户风险比例
    context.account_risk = 0.01
    # 初始化累计买入次数
    context.buy_count = 0
    # 初始化上一次买入价格
    context.last_buy_price = 0
```

择时代码:
```python
def timing(context):
    """择时"""
    # 标的收盘价向上突破唐奇安通道上轨，且当前未持仓时，出现入市信号
    if context.dc_high_signal[0] == 1.0 and context.buy_count == 0:
        # 计算买入数量
        size = context.broker.cash * context.account_risk / context.atr[0] // 10 * 10
        # 发送买入指令
        context.buy(data=context.data, size=size, signal='open')
        # 更新买入次数
        context.buy_count = 1
        # 以当前收盘价作为买入价格
        context.last_buy_price = context.data.close[0]
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 获取多仓数量
    long_size = context.getposition(context.data, side='long').size
    # 如果当前未持多仓
    if long_size == 0:
        # 跳出该函数
        return

    # 计算加仓价
    scale_price = context.last_buy_price + context.scale_ratio * context.atr[0]
    # 计算止损价
    stop_price = context.last_buy_price - context.stop_ratio * context.atr[0]

    # 如果标的收盘价向下突破唐奇安通道下轨，或收盘价小于止损价
    if context.dc_low_signal[0] == -1.0 or context.data.close[0] < stop_price:
        # 发送平仓指令
        context.close(data=context.data, side='long')
        # 更新买入次数
        context.buy_count = 0
        
    # 如果标的收盘价大于加仓价，并且累计加仓次数小于加仓次数上限时
    elif context.data.close[0] > scale_price and context.buy_count < context.scale_number:
        # 计算加仓数量
        size = context.broker.cash * context.account_risk / context.atr[0] // 10 * 10
        # 发送加仓指令
        context.buy(data=context.data, size=size, side='long')
        # 更新累计买入次数
        context.buy_count += 1
        # 以当前收盘价作为买入价格
        context.last_buy_price = context.data.close[0]

```
---
策略详情 - 多因子策略

基本信息:
- ID: Bk4bMeJnL7Em6D0ZR0Y1PdlxaK2jpRNW
- 名称: 多因子策略
- 类型: 策略库策略

策略代码:

选股代码:
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
```

指标代码:
```python
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
```

择时代码:
```python
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
                context.buy(data=data, size=size,price=data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 遍历所有股票
    for data in context.datas:
        # 获取每只股票的仓位
        position = context.getposition(data).size
        # 如果该股票已持仓，但不在股票池中，或当前交易日收盘价小于其15日均价,出现卖出信号
        if position != 0 and data._name not in context.stock_pool or context.sma[data._name][0] > data.close[0]:
            # 平仓
            context.close(data=data,price=data.close[0]*0.9)
```
---
策略详情 - 移动平均成本法定投策略

基本信息:
- ID: kLElZMDVnY3JvX87BAmd4yqQW9rxa67g
- 名称: 移动平均成本法定投策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["513500.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 定投日期, 每月20号定投
    context.buy_day = 20
    # 定投金额, 每次定投10000元
    context.buy_money = 10000  
    # 偏离上界限
    context.up_bound = 1.2
    # 偏离下界限
    context.down_bound = 0.8
    # 向上突破上界限时的定投倍数  
    context.up_multiple = 0.5
    # 向下突破下界限时的定投倍数  
    context.down_multiple = 2.5
```

择时代码:
```python
def timing(context):
    """择时"""
    # 获取当前交易日的日期
    current_date = context.data.datetime.date(0)
    # 获取上一个交易日的日期
    previous_date = context.data.datetime.date(-1)
    # 判断当前交易日是否是定投日期
    if context.buy_day == int(str(current_date)[-2:]) or int(str(previous_date)[-2:]) < context.buy_day < int(str(current_date)[-2:]):
        # 获取标的的仓位
        position = context.getposition(context.data).size
        
        # 判断是否持仓
        if position > 0:
            # 如果持仓，获取平均持有成本
            per_value = context.getposition(context.data).price
        else:
            # 如果未持仓，记标的的收盘价为平均持有成本
            per_value = context.data.close
        # 获取定投的费率
        taker = context.get_taker(context.buy_money)
        # 基于定投金额和费率计算申购份额
        size = context.buy_money / (context.data.close * (1 + taker))
        
        # 计算当前标的价格与平均持有成本的比值
        ratio = context.data.close[-1] / per_value
        
        # 判断是否偏离下界限
        if ratio < context.down_bound:
            # 当当前价格低于平均持有成本时，则多买
            size = size * context.down_multiple
            
        # 判断是否偏离上界限
        if ratio >= context.up_bound:
            # 当当前价格高于平均持有成本时，则少买
            size = size * context.up_multiple
            
		# 发送申购指令
        context.order = context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
      """风控"""
      pass
```
---
策略详情 - 均线偏离法定投策略

基本信息:
- ID: Ew9DBX7a6mNjlr0LP0JGVynbQqOM25dR
- 名称: 均线偏离法定投策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "000001.XSHG"  
    # 输入组合标的
    context.symbol_list = ["000001.XSHG", "510300.XSHG"]
```

指标代码:
```python
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
```

择时代码:
```python
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
                context.order = context.buy(data=data, size=size,price=context.data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 目标止盈法定投策略

基本信息:
- ID: 1YzLpkbN5qGKaJ0gNogVQlZew34WRj7v
- 名称: 目标止盈法定投策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["502048.XSHG"]

```

指标代码:
```python
def indicators(context):
    context.buy_day = 9  # 定投日期
    context.buy_money = 2000  # 定投金额
    context.target_profit = 0.4  # 止盈盈利目标
    context.min_term = 12  # 最小持有期数

    context.term_buy = 0  # 记录投资期数
    context.finish = False  # 是否达到止盈

```

择时代码:
```python
def timing(context):
    """择时"""
    current_date = context.datas[0].datetime.date(0)
    pre_date = context.datas[0].datetime.date(-1)

    # 计算当前收益率，达到止盈条件则全部赎回
    if context.position:
        profit_percent = context.datas[0].close[0] / context.position.price - 1
        if profit_percent >= context.target_profit and context.term_buy >= context.min_term:
            context.order = context.order_target_value(value=0)
            context.finish = True

    # 定投
    if context.buy_day == int(str(current_date)[-2:]) or \
            int(str(pre_date)[-2:]) < context.buy_day < int(str(current_date)[-2:]):

        if not context.finish:
            price = context.datas[0].close[0]
            taker = context.get_taker(context.buy_money)
            size = context.buy_money / (price * (1 + taker))

            context.order = context.buy(size=size,price=context.data.close[0]*1.1)
            context.term_buy += 1

```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 目标市值法定投策略

基本信息:
- ID: jyqPOGLv5z4YN784GAQ6ZlJpnWgKXx9d
- 名称: 目标市值法定投策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["502048.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 定投日期
    context.buy_day = 9  
    # 定投金额
    context.buy_money = 5000  
    # 目标市值
    context.target_value = 50000
```

择时代码:
```python
def timing(context):
    """择时"""
    # 获取当前交易日的日期
    current_date = context.data.datetime.date(0)
    # 获取上一个交易日的日期
    previous_date = context.data.datetime.date(-1)
    # 判断当前交易日是否是定投日期
    if context.buy_day == int(str(current_date)[-2:]) or int(str(previous_date)[-2:]) < context.buy_day < int(str(current_date)[-2:]):

        # 获取当前市值
        current_value = context.position.size * context.datas[0].close[0]
        # 计算买入金额
        diff_value = context.target_value - current_value

        # 如果买入金额为0，表示当前市值已经等于目标市值，则不定投
        if diff_value == 0:
            return

        # 如果买入金额大于0，表示当前市值没有达到目标市值，则追加定投
        elif diff_value > 0:
            # 确定买入金额
            buy_money = min(context.buy_money, diff_value)
            # 获取定投的费率
            taker = context.get_taker(buy_money)
            # 基于定投金额和费率计算申购份额
            size = buy_money / (context.datas[0].close[0] * (1 + taker))
		    # 发送申购指令
            context.order = context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)

        # 如果买入金额小于0，表示当前市值超出目标市值，则卖出超出部分
        else:
            context.order = context.order_target_value(target=context.target_value,price=context.data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 跨品种套利策略

基本信息:
- ID: LVpRPwBvOeGZWQ8WO8E34mXMrjxzyn7d
- 名称: 跨品种套利策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置基准标的
    context.benchmark = "RB2201.XSGE"
    # 设置标的
    context.symbol_list = ["RB2201.XSGE", "J2201.XDCE"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置布林带时间窗口
    period = 20
    # 设置开仓阈值
    open_devfactor = 1.5
    # 设置止损阈值
    stop_devfactor = 2

    # 遍历所有标的
    for data in context.datas:
        # 如果标的为螺纹钢
        if data._name == "RB2201.XSGE":
            # 记录标的对象
            context.rb_data = data
        # 如果标的为焦炭
        elif data._name == "J2201.XDCE":
            # 记录标的对象
            context.j_data = data

    # 获取两个标的的价差序列
    context.diff_close = context.rb_data.close - context.j_data.close
    # 计算套利区间上下限
    open_boll_band = BollingerBands(context.diff_close,
                                            period=period,
                                            devfactor=open_devfactor)

    # 获取套利区间的上轨、下轨、中轨
    open_top = open_boll_band.top
    open_bot = open_boll_band.bot
    context.open_mid = open_boll_band.mid

    # 获取价差分别突破上轨、下轨的信号
    context.cross_top_signal = CrossOver(context.diff_close, open_top)
    context.cross_bot_signal = CrossOver(context.diff_close, open_bot)

    # 计算止损区间上下限
    stop_boll_band = BollingerBands(context.diff_close,
                                            period=period,
                                            devfactor=stop_devfactor)
    # 获取止损区间的上下轨
    context.stop_top = stop_boll_band.top
    context.stop_bot = stop_boll_band.bot
```

择时代码:
```python
def timing(context):
    """择时"""
    # 获取焦炭多仓数量
    long_size = context.getposition(context.j_data, side='long').size
    # 获取焦炭空仓数量
    short_size = context.getposition(context.j_data, side='short').size

    # 如果未持有空仓和多仓
    if long_size == 0 and short_size == 0:

        # 当价差上穿上轨
        if context.cross_top_signal[0] == 1.0:
            # 做空螺纹钢
            context.sell(data=context.rb_data, signal='open')
            # 做多焦炭
            context.buy(data=context.j_data, signal='open')

        # 当价差下穿下轨
        elif context.cross_bot_signal[0] == -1.0:
            # 做多螺纹钢
            context.buy(data=context.rb_data, signal='open')
            # 做空焦炭
            context.sell(data=context.j_data, signal='open')

    # 如果对焦炭持多仓并且价差小于等于中轨
    elif long_size > 0 and context.diff_close[0] <= context.open_mid[0]:
        # 对两个合约进行平仓
        context.close(data=context.j_data, side='long')
        context.close(data=context.rb_data, side='short')

    # 如果对焦炭持空仓并且价差大于等于中轨
    elif short_size < 0 and context.diff_close[0] >= context.open_mid[0]:
        # 对两个合约进行平仓
        context.close(data=context.j_data, side='short')
        context.close(data=context.rb_data, side='long')
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 获取焦炭多仓数量
    long_size = context.getposition(context.j_data, side='long').size
    # 获取焦炭空仓数量
    short_size = context.getposition(context.j_data, side='short').size

    # 如果对焦炭持多仓并且价差大于上轨
    if long_size > 0 and context.diff_close[0] > context.stop_top[0]:
        # 对两个合约进行平仓
        context.close(data=context.j_data, side='long')
        context.close(data=context.rb_data, side='short')

    # 如果对焦炭持空仓并且价差小于下轨
    elif short_size < 0 and context.diff_close[0] < context.stop_bot[0]:
        # 对两个合约进行平仓
        context.close(data=context.j_data, side='short')
        context.close(data=context.rb_data, side='long')
```
---
策略详情 - MACD策略

基本信息:
- ID: RnOL6bxqG5lKpVArZADgJ1MazmXrWB9v
- 名称: MACD策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600360.XSHG"]

```

指标代码:
```python
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

```

择时代码:
```python
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

```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - MACD+KDJ策略

基本信息:
- ID: 9mdpEgqwNaBJ25oOMAQe7lR6xbKr3GPV
- 名称: MACD+KDJ策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600360.XSHG"]

```

指标代码:
```python
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

    # 计算KDJ指标
    kdj = KDJ(context.data,
              period=14,
              period_dfast=3,
              period_dslow=3,
              safediv=False,
              safezero=0.0,
              movav=SMA)

    context.J = kdj.percJ
    context.percK = kdj.percK
    context.D = kdj.percD


```

择时代码:
```python
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
   	# 当J向下突破D时，出现卖出信号
    	if context.J[-1] > context.D[-1] and context.J[0] < context.D[0]:
	    # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.9)

```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 关卡1-均线突破策略示例

基本信息:
- ID: 5dZbPzBk7VORjvARLogQ46rKNwaEGMJX
- 名称: 关卡1-均线突破策略示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的为中国石油
    context.symbol_list = ['601857.XSHG']
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算15日平均线
    context.sma = SMA(context.data.close, period=15)
    # 设置止盈比例为0.1
    context.p_takeprofit = 0.1
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果未持仓
    if context.position.size == 0:
        # 如果当天收盘价在15日均线之上
        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:

            # 执行买入
            context.buy(data=context.data,price=context.data.close[0]*1.1)

    # 如果当天收盘价在15日均线之下
    elif context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:

        # 执行平仓
        context.close(data=context.data,price=context.data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 如果持仓
    if context.position.size != 0:
        # 计算止盈价
        limit_price = (1 + context.p_takeprofit) * context.position.price

        # 如果当前收盘价大于止盈价
        if context.data.close[0] > limit_price:
            # 执行平仓
            context.close(data=context.data,price=context.data.close[0]*0.9)
```
---
策略详情 - 关卡2-一阳穿三线示例

基本信息:
- ID: YWRakGqPDlvKjx0D1A9LN41QyVwOp6r7
- 名称: 关卡2-一阳穿三线示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的及基准
    context.benchmark = "000300.XSHG"
    context.symbol_list = ["000300.XSHG"]
    context.parse_index = True

    # 确定标的池
    context.buy_list = []
    for data in context.datas:
        short_sma = context.stock_sma[data._name]['short_sma']
        medium_sma = context.stock_sma[data._name]['medium_sma']
        long_sma = context.stock_sma[data._name]['long_sma']
        volume_sma = context.stock_sma[data._name]['volume_sma']

        # 判断是否符合一阳穿三线条件
        if data.open[0] < data.close[0] and \
                data.volume[0] > 2 * volume_sma[-1] and \
                data.low[0] < short_sma[0] and \
                data.low[0] < medium_sma[0] and \
                data.low[0] < long_sma[0] and \
                data.close[0] > short_sma[0] and \
                data.close[0] > medium_sma[0] and \
                data.close[0] > long_sma[0]:
            context.buy_list.append(data._name)
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置短期均线周期为 5 日
    context.short_period = 5
    # 设置中期均线周期为 10 日
    context.medium_period = 10
    # 设置长期均线周期为 30 日
    context.long_period = 30
    # 设置放量周期为 15 日
    context.volume_period = 15
    # 设定止盈、止损涨跌幅为 5%
    context.down_tr = 0.05

    # 创建空字典
    context.stock_sma = {}

    for data in context.datas:
        context.stock_sma[data._name] = {
            'short_sma': SMA(data.close, period=context.short_period), # 计算短期均价
            'medium_sma' : SMA(data.close, period=context.medium_period), # 计算中期均价
            'long_sma' : SMA(data.close, period=context.long_period), # 计算长期均价
            'volume_sma' : SMA(data.volume, period=context.volume_period) # 计算成交量均值
        }

```

择时代码:
```python
def timing(context):
    """择时"""
    # 立即买入
    for name in context.buy_list:
        data = context.getdatabyname(name)
        context.buy(data=data,price=data.close[0]*1.1)
            
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 当持有股涨跌幅大于 5%，就全部卖出
    for data in context.datas:
        position = context.getposition(data).size
        if position!= 0 and abs((data.close[0] - data.close[-1])/data.close[-1]) >= context.down_tr:
            context.close(data=data,price=data.close[0]*0.9)
```
---
策略详情 - 关卡3-指标选取示例

基本信息:
- ID: E6yMYPqWlQDNB4oNxAwb1e3ZLm7VrxkJ
- 名称: 关卡3-指标选取示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置基准标的：上证50
    context.benchmark = '000300.XSHG'
    # 设置组合标的，上证50里面的所有成分股
    context.symbol_list = ["000300.XSHG"]
    # 设置解析成分股
    context.parse_index = True

    # 创建列表，用来储存合格标的
    context.stock_list = []

    # 遍历初始标的池中的所有标的
    for data in context.datas:
        
        # 如果当前标的历史交易天数小于计算周期
        if len(data.volume) < context.volume_days:
            # 跳过本次循环
            continue

        # 创建成交量累加变量
        count_volume = 0            
        # 计算总成交量，将指定时间内的每日成交量累加求和
        for i in range(context.volume_days):
            count_volume += data.volume[-i]
        # 计算历史成交量均值
        volume_avg = count_volume/context.volume_days
        
        # 计算当日涨幅
        daily_increase = (data.close[0]-data.close[-1])/data.close[-1]

        # 判断当日涨幅是否超过目标当日涨幅，并且当日成交量超过历史成交量均值
        if daily_increase > context.target_increase and data.volume[0]>volume_avg:
            # 将通过判断的标的添加到合格标的池
            context.stock_list.append(data._name)
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置历史成交量均值的计算周期
    context.volume_days = 120
    # 设置目标当日涨幅
    context.target_increase = 0.02
    # 设置止损比例
    context.loss_ratio = 0.05

    # 创建MACD指标字典
    context.stock_info = {}

    # 遍历所有标的
    for data in context.datas:

        # MACD类的实例化，快的EMA周期为12，慢的EMA周期为26，差离值计算周期为9
        macd_instance = MACD(data.close, period_me1=12, period_me2=26, period_signal=9)

        # 将对应的值写入到MACD指标字典中
        context.stock_info[data._name] = {
            'DIF值': macd_instance.macd,
            'DEA值': macd_instance.signal,
            'MACD值':macd_instance.macd-macd_instance.signal,
        }

```

择时代码:
```python
def timing(context):
    """择时"""
    # 遍历初始标的池中的所有标的
    for data in context.datas:

        # 获取MACD指标数据和持仓信息
        macd_info = context.stock_info[data._name]
        position = context.getposition(data)

        # 如果标的在合格标的池中且当前未持仓
        if data._name in context.stock_list and position.size == 0:

            # 如果DIF值和DEA值均大于0，并且MACD值由负变正
            if macd_info['DIF值'][0] > 0 and macd_info['DEA值'][0] > 0 and macd_info['MACD值'][-1] < 0 and macd_info['MACD值'][0] > 0:
                # 发送买入指令，系统自动执行买入交易
                context.buy(data=data,price=data.close[0]*1.1)

        # 如果当前已持仓        
        elif position.size != 0:
            # 如果DIF值和DEA值均小于0，并且MACD值由正变负
            if macd_info['DIF值'][0] < 0 and macd_info['DEA值'][0] < 0 and macd_info['MACD值'][-1] > 0 and macd_info['MACD值'][0] < 0 :
                # 执行平仓
                context.close(data=data,price=data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 遍历初始标的中的所有标的
    for data in context.datas:
        # 获取标的持仓信息
        position = context.getposition(data)

        # 如果当前已持仓
        if position.size != 0:
            # 计算止损价格
            stop_price = (1 - context.loss_ratio) * position.price

            # 如果当日收盘价低于止损价格
            if data.close[0] < stop_price:
                # 执行平仓
                context.close(data=data,price=data.close[0]*0.9)   
```
---
策略详情 - 关卡4-筛选总市值选股示例

基本信息:
- ID: lbgKWjdQGe4vXV8X60YLD9pR6m1ON5yk
- 名称: 关卡4-筛选总市值选股示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "000016.XSHG"
    # 输入组合标的
    context.symbol_list = ['000016.XSHG']
    context.parse_index = True
    
    # 获取当前以及前一天的日期
    context.current_date = context.data.datetime.date()
    context.previous_date = context.data.datetime.date(-1)
    # 判断当前交易日是否是每个季度的第一个交易日，判断标的池的更新次数，若满足其中一个条件，更新标的池
    if context.current_date.month in [1, 4, 7, 10] and context.previous_date.month not in [1, 4, 7, 10]:
        # 获取估值指标数据
        indicator_data = context.get_fundamentals(context.current_date, type="valuation")
        # 筛选出总市值大于最小总市值的数据
        filted_data = indicator_data[indicator_data['market_cap'] > context.min_market_cap]
        
        # 查看筛选后的标的代码
        context.log('筛选后的标的为：\n{}'.format(filted_data['symbol_exchange']))
```

指标代码:
```python
def indicators(context):
    """指标初始化"""
    # 设置最小总市值
    context.min_market_cap = 15000
```

择时代码:
```python
def timing(context):
    """择时"""
    pass
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 关卡5-筛选中长期上涨股票示例

基本信息:
- ID: JNMK5br6azDm97AjBAgwE4X13nGZVOyq
- 名称: 关卡5-筛选中长期上涨股票示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置基准标的
    context.benchmark = "000016.XSHG"
    # 设置标的池
    context.symbol_list = ["000016.XSHG"]
    # 设置解析成分股
    context.parse_index = True

    # 获取当前的日期
    context.current_date = context.data.datetime.date()    
    # 获取昨天的日期
    context.previous_date = context.data.datetime.date(-1)


    # 如果当前交易日为每个季度的第一个交易日
    if context.current_date.month in [1, 4, 7, 10] and context.previous_date.month not in [1, 4, 7, 10]:
        # 保存上一次筛选后的标的名称列表
        context.last_stock_pool = context.stock_pool

        # 获取财务指标数据
        indicator_data = context.get_fundamentals(pub_date=context.current_date, type='indicator')

        # 筛选出营业收入同比增长率大于最小营业收入同比增长率的数据
        filted_data = indicator_data[indicator_data['inc_revenue_year_on_year']>context.min_income_raise]
        # 进一步筛选出净利润同比增长率大于最小净利润同比增长率的数据
        filted_data = filted_data[filted_data['inc_net_profit_year_on_year']>context.min_margin]
        # 进一步筛选出销售净利率大于最小销售净利率的数据
        filted_data = filted_data[filted_data['net_profit_margin']>context.min_sales_margin]
        # 进一步筛选出销售毛利率大于最小销售毛利率的数据
        filted_data = filted_data[filted_data['gross_profit_margin']>context.min_gross_margin]
        # 进一步筛选出净资产收益率大于最小净资产收益率的数据
        filted_data = filted_data[filted_data['roe']>context.min_roe]

        # 查看筛选后的标的代码
        context.log('筛选后的标的为：\n{}'.format(filted_data['symbol_exchange']))
        # 将标的代码保存到标的池中
        context.stock_pool = filted_data['symbol_exchange'].to_list()
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置最小营业收入同比增长率
    context.min_income_raise = 10
    # 设置最小净利润同比增长率
    context.min_margin = 22
    # 设置最小销售净利率
    context.min_sales_margin = 2
    # 设置最小销售毛利率
    context.min_gross_margin = 9
    # 设置最小净资产收益率
    context.min_roe = 5
    # 设置账户最大使用资金
    context.max_percent = 0.9

    # 初始化上一次标的名称列表
    context.last_stock_pool = []
    # 初始化当前标的名称列表
    context.stock_pool = []
 
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果当前交易日为每个季度的第一个交易日
    if context.current_date.month in [1, 4, 7, 10] and context.previous_date.month not in [1, 4, 7, 10]: 
        
        # 创建买入列表
        buy_list = []
        # 遍历上一次标的池数据
        for name in context.last_stock_pool:
            # 根据标的名称，获取标的数据
            data = context.getdatabyname(name)

            # 遍历当前标的池中的标的名称
            if name in context.stock_pool:
                
                # 计算单个标的能使用的资金
                stock_value = context.broker.getvalue() * context.max_percent/len(context.stock_pool)
                # 计算单个标的所需购买的数量
                size = stock_value / data.close[0] // 100*100
                # 获取标的成交数据
                position = context.getposition(data)

                # 如果需购买的数量小于当前持仓数量
                if size < position.size:
                    # 执行卖出，减少持仓数量
                    context.sell(data=data, size=position.size - size,price=data.close[0]*0.9)
                # 如果需购买的数量大于当前持仓数量
                elif size > position.size:
                    # 将标的和购买数量添加到购买列表中
                    buy_list.append((data, size - position.size))

            # 其他情况
            else:
                # 执行平仓
                context.close(data=data,price=data.close[0]*0.9)
   
        # 遍历买入列表
        for data, size in buy_list:
            # 执行买入
            context.buy(data=data, size=size,price=data.close[0]*1.1)

    # 遍历当前标的池
    for name in context.stock_pool:
        # 根据标的名称，获取标的数据
        data = context.getdatabyname(name)

        # 如果该标的当前没有持仓
        if not context.getposition(data):
            # 计算单个标的能使用的资金
            stock_value = context.broker.getvalue() * context.max_percent/len(context.stock_pool)
            # 计算购买数量
            size = stock_value / data.close[0] // 100*100
            # 执行购买
            context.buy(data=data, size=size,price=data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 关卡6-CCI指标择时示例

基本信息:
- ID: payN3jJvkP5z7q8BkoZGE9rdYO6BmVbR
- 名称: 关卡6-CCI指标择时示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的为康泰生物
    context.symbol_list = ["300601.XSHE"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算周期为20日的CCI指标
    context.cci = CommodityChannelIndex(period=20)

    # 设置最小CCI值
    context.min_cci = -100
    # 设置最大CCI值
    context.max_cci = 100
    # 设置账户最大使用资金
    context.max_percent = 0.9
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果未持有该标的
    if context.position.size == 0:
        # 如果 CCI 值向上突破最小 CCI 值
        if context.cci[-1] < context.min_cci and context.cci[0] > context.min_cci:
            # 计算购买数量
            size = context.broker.cash*context.max_percent/context.data.close[0]//100*100
            # 执行买入
            context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)
    
    # 如果 CCI 值向下突破最大 CCI 值
    elif context.cci[-1] > context.max_cci and context.cci[0] < context.max_cci:
            # 执行平仓
            context.close(data=context.data,price=context.data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 关卡6-布林带择时示例

基本信息:
- ID: RYKkG1ebvWDV9q8518y42gBMJxzawpP3
- 名称: 关卡6-布林带择时示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的为中体产业
    context.symbol_list = ["600158.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算布林带指标，周期为20天
    bb = BollingerBands(context.data.close, period=20)
    # 计算阻力线
    context.top = bb.top
    # 计算支撑线
    context.bot = bb.bot
    # 设置账户最大使用资金
    context.max_percent = 0.9
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果未持有该标的
    if context.position.size == 0:
        # 如果价格触及下限支撑线
        if context.data.close[0] <= context.bot[0]:
            # 计算购买数量
            size = context.broker.cash*context.max_percent/context.data.close[0]//100*100
            # 执行买入
            context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)
    
    # 如果价格触及上限阻力线
    elif context.data.close[0] >= context.top[0]:
            # 执行平仓
            context.close(data=context.data,price=context.data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 关卡5-CCI+SMA择时示例

基本信息:
- ID: jLMGWdzRy51DgPA3wAb4xENYa37Opmek
- 名称: 关卡5-CCI+SMA择时示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    # 设置标的为康泰生物
    context.symbol_list = ["300601.XSHE"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算120日均线
    context.sma = SMA(context.data.close, period=120)
    # 计算周期为40日的CCI指标
    context.cci = CommodityChannelIndex(period=40)
    # 设置最小CCI值
    context.min_cci = -100

```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果未持有该标的
    if context.position.size == 0:
        # 如果 CCI 值向上突破最小 CCI 值
        if context.cci[-1] < context.min_cci and context.cci[0] > context.min_cci:
            # 计算购买数量
            size = context.broker.cash/context.data.close[0]//100*100
            # 执行买入
            context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)

    # 如果股价向下突破 120 日均线
    elif context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
        # 执行平仓
        context.close(data=context.data,price=context.data.close[0]*0.9)

```

风控代码:
```python
def control_risk(context):
    pass

```
---
策略详情 - 关卡7-抄底止损示例

基本信息:
- ID: MbKgYj19d2eNynok9ADJVLvrXGEZ6OkP
- 名称: 关卡7-抄底止损示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的
    context.symbol_list = ["300761.XSHE"]

```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置止损比例
    context.p_stoploss = 0.05
    # 设置连续下跌天数
    context.p_downdays = 4
    # 设置连续上涨天数
    context.p_updays = 3
    # 设置账户最大使用资金
    context.max_percent = 0.9
```

择时代码:
```python
def timing(context):
    """择时"""
    # 定义价格趋势判断函数
    def price_trend(times, trend_type):
        # 如果当前次数小于0，或趋势类型不为up或down，则返回True
        if times < 0 or trend_type not in ['up', 'down']:
            return False
        # 如果当前次数为0，则返回True
        elif times == 0:
            return True
        # 如果趋势类型为down，且出现前一天小于等于当天，则返回False
        elif trend_type == 'down' and context.data[-times] <= context.data[1-times]:
            return False
        # 如果趋势类型为up，且出现前一天大于等于当天，则返回False
        elif trend_type == 'up' and context.data[-times] >= context.data[1-times]:
            return False
        # 其他情况则调用函数本身，并次数减一
        else:
            return price_trend(times-1, trend_type)
    
    # 判断是否持仓，如果没有持仓，则开仓
    if context.position.size == 0:
        # 判断是否在指定天数连续下跌
        if price_trend(context.p_downdays, 'down'):
            # 计算购买数量
            size = context.broker.cash * context.max_percent / context.data.close[0] // 100 * 100
            # 执行买入
            context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)
    
    # 判断是否在指定天数连续上涨
    elif price_trend(context.p_updays, 'up'):
            # 执行平仓
            context.close(data=context.data,price=context.data.close[0]*0.9)
```

风控代码:
```python
def control_risk(context):
    """风控"""

    # 判断是否持仓
    if context.position.size != 0:
        # 计算止损价
        stop_price = (1 - context.p_stoploss) * context.position.price

        # 如果价格下跌到了止损价，则进行平仓
        if context.data.close[0] <= stop_price :
            context.close(data=context.data)
```
---
策略详情 - 关卡7-抄底止盈止损示例

基本信息:
- ID: Nnb52gZJDPReBw8qg0akKVLyp9Ymj34E
- 名称: 关卡7-抄底止盈止损示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的为浦发银行
    context.symbol_list = ["600000.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置连续下跌天数
    context.p_downdays = 3
    # 设置止损比例
    context.p_stoploss = 0.05
    # 设置止盈比例
    context.p_takeprofit = 0.15
    # 设置账户最大使用资金
    context.max_percent = 0.9
```

择时代码:
```python
def timing(context):
    """择时"""
    # 定义连续下跌判断函数
    def slumped(times):
        # 如果次数为0，则返回True
        if times == 0:
            return True
        # 如果出现前一天收盘价小于等于当天
        elif context.data.close[-times] <= context.data.close[1-times] or times < 0:
            return False
        # 其他情况则调用函数本身，并次数减一
        else:
            return slumped(times-1)

    # 如果未持仓，且在指定天数连续下跌
    if context.position.size == 0 and slumped(context.p_downdays):
        # 计算买入数量
        size = context.broker.cash * context.max_percent / context.data.close[0] // 100 * 100
        # 执行买入
        context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 如果持仓
    if context.position.size != 0:
        # 计算止损价
        stop_price = (1 - context.p_stoploss) * context.position.price
        # 计算止盈价
        limit_price = (1 + context.p_takeprofit) * context.position.price
 
        # 如果当前收盘价大于止盈价或当前收盘价小于止损价
        if context.data.close[0] > limit_price or context.data.close[0] < stop_price:
            # 执行平仓
            context.close(data=context.data,price=context.data.close[0]*0.9)
```
---
策略详情 - 关卡8-跟踪止损示例

基本信息:
- ID: Xw2Mn7YDaBVgPb0b9o6dWOlrmjERQLeG
- 名称: 关卡8-跟踪止损示例
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    #  设置标的为北信源
    context.symbol_list = ["300352.XSHE"]
```

指标代码:
```python
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
```

择时代码:
```python
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
            context.buy(data=context.data, size=size,price=context.data.close[0]*1.1)

    # 如果5日均价下跌并且穿过30日均价时
    elif context.short_sma[-1] > context.long_sma[-1] and context.short_sma[0] < context.long_sma[0]:

        # 执行平仓
        context.close(data=context.data,price=context.data.close[0]*0.9)
        # 重置最高价
        context.h_price = 0
        # 将死叉信号设置为True
        context.d_cross_sign = True
```

风控代码:
```python
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
            context.close(data=context.data,price=context.data.close[0]*1.1)
            # 重置最高价
            context.h_price = 0
```
---
策略详情 - 布林带策略

基本信息:
- ID: nla9wGYjv71mkO0ENAbzBPM4rRNWQdqJ
- 名称: 布林带策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["600000.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 计算布林带指标，period周期修改为60
    bb = BollingerBands(context.data.close, period = 60)
    # 计算阻力线
    context.top = bb.top
    # 计算支撑线
    context.bot = bb.bot
```

择时代码:
```python
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
            context.order = context.sell(price=context.data.close[0]*1.1)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - Hilbert策略

基本信息:
- ID: aKWZlLvVjnk4BQ8zmAPqzDNMmX9xd5p6
- 名称: Hilbert策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["601398.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置均价周期
    context.sma_period = 20
    # 设置 Hilbert 变换的周期
    context.hilbert_period = 30

    # 计算均价
    context.sma = SMA(context.data.close, period=context.sma_period)
    # 计算均价的差分
    context.sma_diff = context.sma(0) - context.sma(-1)
```

择时代码:
```python
def timing(context):
    """择时"""
    import numpy as np
    from scipy.signal import hilbert

    # 获取差分序列
    context.history_data = context.sma_diff.get(ago=0, size=context.hilbert_period)

    # 判断差分序列是否为空
    if context.history_data:
        # 基于差分序列进行Hilbert变换
        context.hilbert = np.imag(hilbert(list(context.history_data)))

        # 判断是否持仓，如果不持仓，则判断是否出现买入信号
        if not context.position:
            # △(n)大于0，出现买入信号
            if context.hilbert[-1] > 0:
                # 发送买入指令
                context.order = context.buy()
            
        # 如果持仓，则判断是否出现卖出信号
        else:
            # △(n)小于0，出现卖出信号
            if context.hilbert[-1] < 0:
                # 发送卖出指令
                context.order = context.sell()
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 激进型FOF

基本信息:
- ID: 6RzYKdQ791Gyrj0GY8pgkaJWN2mw5vBn
- 名称: 激进型FOF
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "000300.XSHG"
    # 输入组合标的
    context.symbol_list = ["160632.XSHE", "161029.XSHE", "161121.XSHE", "161725.XSHE", "159916.XSHE", "159933.XSHE", "160222.XSHE", "160421.XSHE", "165516.XSHE", "161115.XSHE"]
    # 获取当前的日期
    context.current_date = context.data.datetime.date()    
    # 获取昨天的日期
    context.previous_date = context.data.datetime.date(-1)

    # 如果当天月份与昨天月份不同
    if context.current_date.month != context.previous_date.month:
        # 记录上一次筛选的标的
        context.last_stock_pool = context.stock_pool

        # 设置标的得分空列表
        score_list = []
        # 遍历所有标的
        for data in context.datas:
            # 计算得分
            score = context.returns[data._name][0] + context.sharpe_ratio[data._name][0] - context.max_draw_down[data._name][0]
            # 添加标的代码和得分到标的得分列表
            score_list.append([data._name, score])
        # 按照得分降序排列
        sorted_rate = sorted(score_list, key=lambda x: x[1], reverse=True)

        # 计算筛选标的数量
        context.stock_num = int(context.ratio * len(context.symbol_list))
        # 重置标的池空列表
        context.stock_pool = []
        # 获取指定数量的标的
        for i in sorted_rate[:context.stock_num]:
            # 将筛选的标的添加到标的池
            context.stock_pool.append(i[0])
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置需要考虑最近 N 个交易日标的表现
    period = 5
    # 设置筛选标的的比例
    context.ratio = 0.2
    # 设置用于购买股票的资金比例
    context.max_percent = 0.9

    # 初始化历史 N 个交易日净值增长率
    context.returns = {}
    # 初始化历史 N 个交易日的波动率
    context.volatility = {}
    # 初始化夏普比率
    context.sharpe_ratio = {}
    # 初始化历史 N 个交易日的最大回撤
    context.max_draw_down = {}

    # 设置本次标的名称列表
    context.stock_pool = []

    # 遍历所有标的
    for data in context.datas:
        # 计算最近 N 个交易日的总收益率
        context.returns[data._name] = ROC(data, period=period)

        # 计算最近 N 个交易日的波动率
        growth_rate = ROC(data, period=1)
        context.volatility[data._name] = StdDev(growth_rate, period=period)

        # 计算最近 N 个交易日的夏普比率
        context.sharpe_ratio[data._name] = SharpeRatio(data, period=period)

        # 计算最近 N 个交易日的最大回撤率
        context.max_draw_down[data._name] = MaxDrawDownN(data, period=period)
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果当天月份与昨天月份不同
    if context.current_date.month != context.previous_date.month:
        
        # 遍历上一次标的池数据
        for name in context.last_stock_pool:
            # 根据标的名称，获取标的数据
            data = context.getdatabyname(name)

            # 如果标的名称在不在本次标的池中
            if name not in context.stock_pool:
                # 对标的进行平仓
                context.close(data=data)

        # 遍历当前标的池
        for name in context.stock_pool:
            # 根据标的名称，获取标的数据
            data = context.getdatabyname(name)

            # 如果该标的当前没有持仓
            if context.getposition(data).size == 0:
                # 计算单个标的能使用的资金
                stock_value = context.broker.getvalue() * context.max_percent / context.stock_num
                # 计算购买数量
                size = stock_value / data.close[0] // 100 * 100
                # 执行购买
                context.buy(data=data, size=size)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 成长型FOF

基本信息:
- ID: 95YNkRq7wLlebgoMp8vG42djMKyVQ3DP
- 名称: 成长型FOF
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 输入基准标的
    context.benchmark = "000300.XSHG"
    # 输入组合标的
    context.symbol_list = ["160632.XSHE", "161029.XSHE", "161121.XSHE", "161725.XSHE", "159916.XSHE", "160421.XSHE", "165516.XSHE", "161115.XSHE", "164208.XSHE", "160513.XSHE"]
    
    # 获取当前的日期
    context.current_date = context.data.datetime.date()    
    # 获取昨天的日期
    context.previous_date = context.data.datetime.date(-1)

    # 如果当天月份与昨天月份不同
    if context.current_date.month != context.previous_date.month:
        # 记录上一次筛选的标的
        context.last_stock_pool = context.stock_pool

        # 设置标的得分空列表
        score_list = []
        # 遍历所有标的
        for data in context.datas:
            # 计算得分
            score = context.returns[data._name][0] - context.max_draw_down[data._name][0] + context.volatility[data._name][0] 
            # 添加标的代码和得分到标的得分列表
            score_list.append([data._name, score])
        # 按照得分降序排列
        sorted_rate = sorted(score_list, key=lambda x: x[1], reverse=True)

        # 计算筛选标的数量
        context.stock_num = int(context.ratio * len(context.symbol_list))
        # 重置标的池空列表
        context.stock_pool = []
        # 获取指定数量的标的
        for i in sorted_rate[:context.stock_num]:
            # 将筛选的标的添加到标的池
            context.stock_pool.append(i[0])
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置需要考虑最近 N 个交易日标的表现
    period = 10
    # 设置筛选标的的比例
    context.ratio = 0.2
    # 设置用于购买股票的资金比例
    context.max_percent = 0.9

    # 初始化历史 N 个交易日净值增长率
    context.returns = {}
    # 初始化历史 N 个交易日的波动率
    context.volatility = {}
    # 初始化夏普比率
    context.sharpe_ratio = {}
    # 初始化历史 N 个交易日的最大回撤
    context.max_draw_down = {}

    # 设置本次标的名称列表
    context.stock_pool = []

    # 遍历所有标的
    for data in context.datas:
        # 计算最近 N 个交易日的总收益率
        context.returns[data._name] = ROC(data, period=period)

        # 计算最近 N 个交易日的波动率
        growth_rate = ROC(data, period=1)
        context.volatility[data._name] = StdDev(growth_rate, period=period)

        # 计算最近 N 个交易日的夏普比率
        context.sharpe_ratio[data._name] = SharpeRatio(data, period=period)

        # 计算最近 N 个交易日的最大回撤率
        context.max_draw_down[data._name] = MaxDrawDownN(data, period=period)
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果当天月份与昨天月份不同
    if context.current_date.month != context.previous_date.month:
        
        # 遍历上一次标的池数据
        for name in context.last_stock_pool:
            # 根据标的名称，获取标的数据
            data = context.getdatabyname(name)

            # 如果标的名称不在本次标的池中
            if name not in context.stock_pool:
                # 对标的进行平仓
                context.close(data=data)

        # 遍历本次标的池
        for name in context.stock_pool:
            # 根据标的名称，获取标的数据
            data = context.getdatabyname(name)

            # 如果该标的当前没有持仓
            if context.getposition(data).size == 0:
                # 计算单个标的能使用的资金
                stock_value = context.broker.getvalue() * context.max_percent / context.stock_num
                # 计算购买数量
                size = stock_value / data.close[0] // 100 * 100
                # 执行购买
                context.buy(data=data, size=size)
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 肯特纳通道策略

基本信息:
- ID: kB2dqbZ3xvNanyolQ0OlgJYR4DKeQ1r5
- 名称: 肯特纳通道策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    context.symbol_list = ["JD2212.XDCE"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置周期
    context.period = 10
    # 设置倍数
    context.multi = 2

    # 计算肯特纳通道相关指标
    kc = KeltnerChannel(context.data, period=context.period, devfactor=context.multi)
    # 获取肯特纳通道的中轨
    context.middle_line = kc.mid
    # 获取肯特纳通道的上轨
    context.upper_line = kc.top
    # 获取肯特纳通道的下轨
    context.lower_line = kc.bot

    # 计算收盘价与上轨的交叉信号
    context.upper_signal = CrossOver(context.data.close, context.upper_line)
    # 计算收盘价与下轨的交叉信号
    context.lower_signal = CrossOver(context.data.close, context.lower_line)

```

择时代码:
```python
def timing(context):
    """择时"""
    # 获取当前仓位
    position = context.getposition(context.data).size

    # 如果当前交易日无持仓，且收盘价向上突破上轨，且中轨向上，出现做多信号
    if position == 0 and context.upper_signal[0] > 0 and context.middle_line[0] > context.middle_line[-1]:
        # 发送做多指令
        context.order = context.buy()

    # 如果当前交易日无持仓，且收盘价向下突破下轨，且中轨向下，出现做空信号
    elif position == 0 and context.lower_signal[0] < 0 and context.middle_line[0] < context.middle_line[-1]:
        # 发送做空指令
        context.order = context.sell()

    # 如果当前交易日持多仓，且收盘价向下突破中轨，出现平多信号
    elif position > 0 and context.data.close[0] < context.middle_line[0]:
        # 发送平多指令
        context.order = context.close()

    # 如果当前交易日持空仓，且收盘价向上突破中轨，出现平空信号
    elif position < 0 and context.data.close[0] > context.middle_line[0]:
        # 发送平空指令
        context.order = context.close()
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass
```
---
策略详情 - 网格交易策略

基本信息:
- ID: jJp3Onk2bLBd7QoKWom6e49gyZMxDRNY
- 名称: 网格交易策略
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置标的：华夏中小企业100ETF
    context.symbol_list = ["159902.XSHE"]
```

指标代码:
```python
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

```

择时代码:
```python
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

```

风控代码:
```python
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
            context.buy(data=context.data, size=change_index*context.per_size)
        
        # 更新前一日挡位
        context.last_index = index

    context.log("当前持仓规模:{}".format(context.getposition(context.data).size))

```
---
策略详情 - 小市值选股

基本信息:
- ID: aWnv1PqONRYK4g0vn0xmEQX6LkJrZebB
- 名称: 小市值选股
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """标的"""
    # 设置基准标的
    context.benchmark = "000852.XSHG"
    # 设置指数
    context.symbol_list = ["000852.XSHG"]
    # 打开解析成分股参数
    context.parse_index = True

    # 如果入选标的列表为空
    if context.stock_pool == []:
        # 获取当前日期
        current_date = context.data.datetime.date()

        # 获取市值数据
        valuation = context.get_fundamentals(date=current_date, type="valuation")
        # 提取标的代码和市值数据
        valuation = valuation[["symbol_exchange", "market_cap"]]
        # 将数据按照市值从小到大进行排序
        sorted_valuation = valuation.sort_values(by="market_cap")
        # 取出标的名称
        name_list = sorted_valuation["symbol_exchange"].to_list()

        # 提取小市值标的
        context.stock_pool = name_list[context.select_start:context.select_end]
        # 打印筛选出来的标的
        context.log("筛选出来的标的有:{}".format(context.stock_pool))
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置账户最大使用资金比例
    context.max_percent = 0.9

    # 将买入状态设置为 False，表示未执行过买入操作
    context.have_bought = False
    # 初始化入选标的列表
    context.stock_pool = []
    # 设置小市值的筛选标准
    context.select_start = 3
    context.select_end = 33
```

择时代码:
```python
def timing(context):
    """择时"""
    # 如果入选标的列表不为空且尚未买入过标的
    if context.stock_pool != [] and not context.have_bought:
        # 计算单个标的的可用资金
        stock_value = context.broker.getvalue() * context.max_percent / len(context.stock_pool)

        # 遍历入选标的列表
        for name in context.stock_pool:
            # 获取入选标的对象
            data = context.getdatabyname(name)

            # 计算标的的买入数量
            size = stock_value / data.close[0] // 100 * 100
            # 执行买入操作
            context.buy(data=data, size=size, price=data.close[0]*1.1)

        # 将买入状态设置为 True，表示已执行过买入操作
        context.have_bought = True
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 市值+市净率 选股

基本信息:
- ID: bQjv2nDEkmrg7LA6q0KeaJNxRqlBYWV4
- 名称: 市值+市净率 选股
- 类型: 策略库策略

策略代码:

选股代码:
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
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置账户最大使用资金
    context.max_percent = 0.9

    # 将买入状态设置为 False，表示未执行过买入操作
    context.have_bought = False
    # 初始化入选标的列表
    context.stock_pool = []
```

择时代码:
```python
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
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 市值+净利润同比增长率 选股

基本信息:
- ID: PwQ17ky2JjEzYW0Pv8gnMl3aNGVKpd4L
- 名称: 市值+净利润同比增长率 选股
- 类型: 策略库策略

策略代码:

选股代码:
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
        # 取出标的代码、市净率数据
        valuation_data = valuation_data[['symbol_exchange', 'pb_ratio']]

        # 获取分数数据，从1开始
        rank_list = []
        for i in range(1, len(valuation_data)+1):
            rank_list.append(i)

        # 根据市净率按大到小进行排序
        valuation_data = valuation_data.sort_values(by='pb_ratio', ascending=False)
        # 将市净率得分写入到市值数据中
        valuation_data['pb_rank'] = rank_list

        # 获取财务指标数据
        indicator_data = context.get_fundamentals(date=current_date, type="indicator")
        # 取出标的代码、净利润同比增长率数据
        indicator_data = indicator_data[['symbol_exchange', 'inc_net_profit_year_on_year']]

        # 按净利润增长率小到大进行排序
        indicator_data = indicator_data.sort_values(by='inc_net_profit_year_on_year')
        # 将净利润增长率得分写入到财务指标数据中
        indicator_data['inc_net_profit_rank'] = rank_list

        # 合并市值数据和财务指标数据
        total_data = valuation_data.merge(indicator_data, on='symbol_exchange')

        # 计算分数，并写入到总数据中
        total_data['score'] = total_data['pb_rank'] + total_data['inc_net_profit_rank']

        # 根据分数对总数据按大到小进行排序
        total_data = total_data.sort_values(by='score', ascending=False)

        # 获取前10个股票名称
        context.stock_pool = total_data['symbol_exchange'].to_list()[:10]

        context.log('\n筛选出来的标的{}'.format(context.stock_pool))
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置账户最大使用资金
    context.max_percent = 0.9

    # 将买入状态设置为 False，表示未执行过买入操作
    context.have_bought = False
    # 初始化入选标的列表
    context.stock_pool = []
```

择时代码:
```python
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
```

风控代码:
```python
def control_risk(context):
    """风控"""
    pass

```
---
策略详情 - 框架代码（RSI指标）

基本信息:
- ID: lONjwgvzb5BWryoV189eLXJd1VqDZKQ3
- 名称: 框架代码（RSI指标）
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """选股"""
    # 设置基准标的
    context.benchmark = "000016.XSHG"
    # 设置标的列表
    context.symbol_list = ["000016.XSHG"]
    context.parse_index = True
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置每次买卖的数量
    context.trade_size = 100
    # 设置止盈比例
    context.take_profit = 0.15
    # 设置止损比例
    context.stop_loss = 0.08

    # 以上为每个策略都会用到的常用参数设置部分
    # 接下来针对具体的策略，可以计算一些针对性的参数
    # ------------------------------------------------------------------

    # 初始化RSI指标上限
    context.top = 70
    # 初始化RSI指标下限
    context.bot = 25
    # 设置信号字典
    context.rsi_dict = {}
    # 设置RSI的计算周期
    rsi_period = 6
    # 遍历所有标的
    for data in context.datas:
        # 计算周期为6的RSI指标
        rsi = RSI(data.close, period=rsi_period, safediv=True)
        # 记录标的对应的RSI指标 
        context.rsi_dict[data] = {'rsi': rsi}
```

择时代码:
```python
def timing(context):
    """择时"""
    # 设置交易字典
    trade_dict = {'需买入的标的对象': [], '需买入标的的代码': [], '需卖出的标的对象': [], '需卖出的标的代码': []}
    # 遍历所有标的
    for data in context.datas:
        # 获取RSI
        rsi = context.rsi_dict[data]['rsi']

        # 当RSI值低于其下限时
        if rsi[0] < context.bot:
            # 记录需要买入的标的对象
            trade_dict['需买入的标的对象'].append(data)
            # 记录需要买入标的对象的代码
            trade_dict['需买入标的的代码'].append(data._name)
        # 当RSI值高于其上限时
        elif rsi[0] > context.top:
            # 记录需要卖出的标的对象
            trade_dict['需卖出的标的对象'].append(data)
            # 记录需要卖出标的对象的代码
            trade_dict['需卖出的标的代码'].append(data._name)

    # 如果需买入标的的代码列表或需卖出的标的代码不为空：
    if trade_dict['需买入标的的代码'] or trade_dict['需卖出的标的代码']:
        # 打印列表中的信息
        context.log('\n 需卖出的标的为：{} \n 需买入的标的为：{}'.format(trade_dict['需卖出的标的代码'], trade_dict['需买入标的的代码']))

    # 择时到此，将输出所有标的需要操作的状态，新的策略只需要在这之前根据策略内容输出对应的状态即可
    # 接下来执行交易

    # 遍历需要卖出的标的
    for sell_data in trade_dict['需卖出的标的对象']:
        # 获取持仓数量
        hold_size = context.getposition(sell_data).size
        # 如果持仓数量大于0
        if hold_size > 0:
            # 执行平仓，订单类型为市价单
            context.close(data=sell_data, price=sell_data.close[0]*0.9)
            # # 执行平仓，订单类型为限价单
            # context.sell(data=sell_data, size=hold_size, price=sell_data.close[0], exectype=Order.Limit)

    # 遍历需要买入的标的
    for buy_data in trade_dict['需买入的标的对象']:
        # 执行买入，订单类型为市价单
        context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0]*1.1)
        # # 执行买入，订单类型为限价单
        # context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0], exectype=Order.Limit)

```

风控代码:
```python
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
                context.log("执行了止盈或止损")
```
---
策略详情 - 框架代码+单日资金和总资金风控

基本信息:
- ID: rkxdaDLRbPmwqyAwP8lz4e6MXpEWN7YO
- 名称: 框架代码+单日资金和总资金风控
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """选股"""
    # 设置基准标的
    context.benchmark = "000300.XSHG"
    # 设置标的列表
    context.symbol_list = ["000300.XSHG"]
    context.parse_index = True
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置每次买卖的数量
    context.trade_size = 100
    # 设置止盈比例
    context.take_profit = 0.15
    # 设置止损比例
    context.stop_loss = 0.08

    # 以上为每个策略都会用到的常用参数设置部分
    # 接下来针对具体的策略，可以计算一些针对性的参数
    # ------------------------------------------------------------------

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

    # 设置最大使用资金比例
    context.max_percent = 0.8
    # 设置每天最大使用资金比例
    context.day_max_percent = 0.4
```

择时代码:
```python
def timing(context):
    """择时"""
    # 设置信号字典
    trade_dict = {'需买入的标的对象': [], '需买入标的的代码': [], '需卖出的标的对象': [], '需卖出的标的代码': []}
    # 遍历所有标的
    for data in context.datas:
        # 获取RSI
        rsi = context.rsi_dict[data]['rsi']

        # 当RSI值低于其下限时
        if rsi[0] < context.bot:
            # 记录需要买入的标的对象
            trade_dict['需买入的标的对象'].append(data)
            # 记录需要买入标的对象的代码
            trade_dict['需买入标的的代码'].append(data._name)
        # 当RSI值高于其上限时
        elif rsi[0] > context.top:
            # 记录需要卖出的标的对象
            trade_dict['需卖出的标的对象'].append(data)
            # 记录需要卖出标的对象的代码
            trade_dict['需卖出的标的代码'].append(data._name)

    # 如果需买入标的的代码列表或需卖出的标的代码不为空：
    if trade_dict['需买入标的的代码'] or trade_dict['需卖出的标的代码']:
        # 打印列表中的信息
        context.log('\n 需卖出的标的为：{} \n 需买入的标的为：{}'.format(trade_dict['需卖出的标的代码'], trade_dict['需买入标的的代码']))

    # 择时到此，将输出所有标的需要操作的状态，新的策略只需要在这之前根据策略内容输出对应的状态即可

    # 设置记录当天买入资金为0
    day_buy_value = 0
    # 获取所有已委托的订单
    submitted_orders = context.get_orders(status='submitted')
    # 遍历所有已委托的订单
    for order in submitted_orders:
        # 如果该委托单为买入
        if order.ordtype == 0:
            # 计算订单金额
            order_value = order.created.price * order.created.size
            # 将订单金额累加到当天买入资金变量中
            day_buy_value += order_value

    # 获取所有已成交的订单
    completed_orders = context.get_orders(status='completed')
    # 遍历所有已成交的订单
    for order in completed_orders:
        # 如果该成交单为买入
        if order.ordtype == 0:
            # 获取订单金额，并累加到当天买入资金变量中
            day_buy_value += order.executed.value

    # 当天买入资金需要减去取消的订单金额
    day_buy_value -= canceled_value

    # 接下来执行交易

    # 遍历需要卖出的标的
    for sell_data in trade_dict['需卖出的标的对象']:
        # 获取持仓数量
        hold_size = context.getposition(sell_data).size
        # 如果持仓数量大于0
        if hold_size > 0:
            # 执行平仓，订单类型为市价单
            context.close(data=sell_data, price=sell_data.close[0]*0.9)
            # # 执行平仓，订单类型为限价单
            # context.sell(data=sell_data, size=hold_size, price=sell_data.close[0], exectype=Order.Limit)

    # 遍历需要买入的标的
    for buy_data in trade_dict['需买入的标的对象']:
        # 计算当前买入所需的资金
        buy_value = buy_data.close[0] * context.trade_size
        # 计算当天用于买入的资金比例
        day_buy_percent = (day_buy_value + buy_value) / context.broker.getvalue()
        # 计算剩余的现金比例
        remaining_cash_percent = (context.broker.cash - buy_value) / context.broker.getvalue()

        # 如果当天用于买入的资金比例小于每天最大买入资金比例，并且投入的总资金不超过最大资金使用比例
        if day_buy_percent < context.day_max_percent and remaining_cash_percent > (1 - context.max_percent):
            # 执行买入，订单类型为市价单
            order = context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0]*1.1)
            # # 执行买入，订单类型为限价单
            # order = context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0], exectype=Order.Limit)

            # 如果order的值不为None
            if order:
                # 将本次买入金额累加到当天买入资金变量中
                day_buy_value += buy_value
```

风控代码:
```python
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
                context.log("执行了止盈或止损")
```
---
策略详情 - RSI-标的池-分钟回测V6

基本信息:
- ID: QYgmqJZNkRvDzb0Yy0lxWO9PpXGKaM2L
- 名称: RSI-标的池-分钟回测V6
- 类型: 策略库策略

策略代码:

选股代码:
```python
def choose_stock(context):
    """选股"""
    # 设置基准标的
    context.benchmark = "510360.XSHG"
    # 设置标的列表
    context.symbol_list = ["601398.XSHG", "000725.XSHE", "002717.XSHE", "600028.XSHG", "510360.XSHG"]
```

指标代码:
```python
def indicators(context):
    """指标"""
    # 设置每次买卖的数量
    context.trade_size = 100
    # 设置止盈比例
    context.take_profit = 0.15
    # 设置止损比例
    context.stop_loss = 0.08

    # 以上为每个策略都会用到的常用参数设置部分
    # 接下来针对具体的策略，可以计算一些针对性的参数
    # ------------------------------------------------------------------

    # 初始化RSI指标上限
    context.top = 75
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

    # ------------------资金风控
    # 设置最大使用资金比例
    context.max_percent = 0.8
    # 设置每天最大使用资金比例
    context.day_max_percent = 0.3

    # ------------------取消订单
    # 设置订单取消间隔时间为1800秒
    context.cancel_interval = 1800
```

择时代码:
```python
def timing(context):
    """择时"""
    # 设置信号字典
    trade_dict = {'需买入的标的对象': [], '需买入标的的代码': [], '需卖出的标的对象': [], '需卖出的标的代码': []}
    # 遍历所有标的
    for data in context.datas:
        # 获取RSI
        rsi = context.rsi_dict[data]['rsi']

        # 当RSI值低于其下限时
        if rsi[0] < context.bot:
            # 记录需要买入的标的对象
            trade_dict['需买入的标的对象'].append(data)
            # 记录需要买入标的对象的代码
            trade_dict['需买入标的的代码'].append(data._name)
        # 当RSI值高于其上限时
        elif rsi[0] > context.top:
            # 记录需要卖出的标的对象
            trade_dict['需卖出的标的对象'].append(data)
            # 记录需要卖出标的对象的代码
            trade_dict['需卖出的标的代码'].append(data._name)

    # 如果需买入标的的代码列表或需卖出的标的代码不为空：
    if trade_dict['需买入标的的代码'] or trade_dict['需卖出的标的代码']:
        # 打印列表中的信息
        context.log('\n 需卖出的标的为：{} \n 需买入的标的为：{}'.format(trade_dict['需卖出的标的代码'], trade_dict['需买入标的的代码']))

    # 择时到此，将输出所有标的需要操作的状态，新的策略只需要在这之前根据策略内容输出对应的状态即可

    # -------------------取消订单
    # 设置取消订单金额为0
    canceled_value = 0
    # 获取当前日期时间
    current_datetime = context.datetime.datetime()

    # 获取所有已委托的订单
    submitted_orders = context.get_orders(status='submitted')
    # 遍历所有已委托的订单
    for order in submitted_orders:
        # 获取委托创建时间
        created_time = order.created_at
        # 获取当前距离委托时，间隔的秒数
        interval_now = (current_datetime - created_time).seconds

        # 如果该委托单为买入并且当前距离委托的间隔时间达到订单取消间隔时间
        if order.ordtype == 0 and interval_now >= context.cancel_interval:
            # 取消订单
            context.cancel(order)
            # 计算订单金额
            order_value = order.created.price * order.created.size
            # 将订单金额累加到取消清单金额中
            canceled_value += order_value

    # -------------------资金风控--计算今天花费总资金(不包含现在)
    # 设置记录当天买入资金为0
    day_buy_value = 0
    # 遍历所有已委托的订单
    for order in submitted_orders:
        # 如果该委托单为买入
        if order.ordtype == 0:
            # 计算订单金额
            order_value = order.created.price * order.created.size
            # 将订单金额累加到当天买入资金变量中
            day_buy_value += order_value

    # 当天买入资金需要减去取消的订单金额
    day_buy_value -= canceled_value

    # 获取所有已成交的订单
    completed_orders = context.get_orders(status='completed')
    # 遍历所有已成交的订单
    for order in completed_orders:
        # 如果该成交单为买入
        if order.ordtype == 0:
            # 获取订单金额，并累加到当天买入资金变量中
            day_buy_value += order.executed.value

    # 接下来执行交易

    # 遍历需要卖出的标的
    for sell_data in trade_dict['需卖出的标的对象']:
        # 获取当天可交易的数量
        salable_size = context.getposition(sell_data).available

        # 如果可交易数量大于0
        if salable_size > 0:
            # 卖出所有持仓数量，订单类型为市价单
            context.sell(data=sell_data, size=salable_size,price=sell_data.close[0])
            # # 执行卖出，订单类型为限价单
            # context.sell(data=sell_data, size=salable_size, price=sell_data.close[0], exectype=Order.Limit)

    # 遍历需要买入的标的
    for buy_data in trade_dict['需买入的标的对象']:

        # -------------------资金风控--计算今天花费总资金(包含现在)

        # 计算当前买入所需的资金
        buy_value = buy_data.close[0] * context.trade_size
        # 计算当天用于买入的资金比例
        day_buy_percent = (day_buy_value + buy_value) / context.broker.getvalue()
        # 计算剩余的现金比例
        remaining_cash_percent = (context.broker.cash - buy_value) / context.broker.getvalue()

        # 如果当天用于买入的资金比例小于每天最大买入资金比例，并且投入的总资金不超过最大资金使用比例
        if day_buy_percent < context.day_max_percent and remaining_cash_percent > (1 - context.max_percent):
            # # 执行买入，订单类型为市价单
            # order = context.buy(data=buy_data, size=context.trade_size)
            # 执行买入，订单类型为限价单
            order = context.buy(data=buy_data, size=context.trade_size, price=buy_data.close[0], exectype=Order.Limit)

            # 如果order不为None
            if order:
                # 将本次买入金额累加到当天买入资金变量中
                day_buy_value += buy_value
```

风控代码:
```python
def control_risk(context):
    """风控"""
    # 遍历所有标的
    for data in context.datas:
        # # 获取标的当前持仓数量
        # hold_size = context.getposition(data).size
        # 获取当天可交易的数量
        salable_size = context.getposition(data).available
        # 如果有持仓
        if salable_size > 0:
            # 获取持仓均价
            hold_price = context.getposition(data).price
            # 计算止损价
            stop_price = (1 - context.stop_loss) * hold_price
            # 计算止盈价
            profit_price = (1 + context.take_profit) * hold_price
            
            # 如果当前价格达到了止盈或止损价
            if data.close[0] < stop_price or data.close[0] > profit_price:
                # 执行平仓
                context.sell(data=data, size=salable_size,price=data.close[0])
                context.log("执行了止盈或止损")

---------------------------------------------
