# HiTrader 量化交易平台全面指南 - 第二部分：技术指标全解

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