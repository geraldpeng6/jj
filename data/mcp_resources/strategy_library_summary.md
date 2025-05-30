# HiTrader 策略库总结

## 策略分类

HiTrader策略库包含多种类型的交易策略，可以分为以下几个主要类别：

## 1. 趋势跟踪策略

### 均线类策略

#### 单均线策略
**核心机制**: 利用价格与均线的交叉关系判断买卖时机
- 买入信号: 价格上穿均线
- 卖出信号: 价格下穿均线
- 代表策略: `单均线策略`

```python
# 核心代码
context.sma = SMA(period=15)
if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:
    context.buy(price=context.data.close[0]*1.1)
elif context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
    context.sell(price=context.data.close[0]*0.9)
```

#### 双均线策略
**核心机制**: 利用短期均线与长期均线的交叉关系判断买卖时机
- 买入信号: 短期均线上穿长期均线
- 卖出信号: 短期均线下穿长期均线
- 代表策略: `双均线策略`

```python
# 核心代码
context.short_sma = SMA(period=15)
context.long_sma = SMA(period=30)
if context.short_sma[-1] < context.long_sma[-1] and context.short_sma[0] > context.long_sma[0]:
    context.buy(price=context.data.close[0]*1.1)
elif context.short_sma[-1] > context.long_sma[-1] and context.short_sma[0] < context.long_sma[0]:
    context.sell(price=context.data.close[0]*0.9)
```

### 通道类策略

#### 海龟交易策略
**核心机制**: 基于唐奇安通道和ATR指标的突破策略
- 买入信号: 价格突破上轨
- 加仓条件: 价格超过上次买入价格加上ATR的一定倍数
- 卖出信号: 价格突破下轨或触及止损
- 代表策略: `海龟交易策略`

```python
# 核心代码
dc_high_line = DonchianChannel(context.data, period=dc_high_period).top(-1)
dc_low_line = DonchianChannel(context.data, period=dc_low_period).bot(-1)
context.atr = AverageTrueRange(context.data, period=atr_period)

# 买入逻辑
if context.dc_high_signal[0] == 1.0 and context.buy_count == 0:
    size = context.broker.cash * context.account_risk / context.atr[0] // 10 * 10
    context.buy(data=context.data, size=size, signal='open')
    
# 风控逻辑
scale_price = context.last_buy_price + context.scale_ratio * context.atr[0]
stop_price = context.last_buy_price - context.stop_ratio * context.atr[0]
```

#### 布林带策略
**核心机制**: 利用价格在布林带上下轨之间的波动特性
- 买入信号: 价格触及下轨
- 卖出信号: 价格触及上轨
- 代表策略: `布林带策略`

```python
# 核心代码
bb = BollingerBands(context.data.close, period=60)
context.top = bb.top
context.bot = bb.bot

if not context.position and context.data.close[0] <= context.bot[0]:
    context.buy(price=context.data.close[0]*1.1)
elif context.position and context.data.close[0] >= context.top[0]:
    context.sell(price=context.data.close[0]*1.1)
```

#### 肯特纳通道策略
**核心机制**: 结合价格与肯特纳通道的关系判断趋势
- 多头信号: 价格突破上轨且中轨向上
- 空头信号: 价格突破下轨且中轨向下
- 平仓信号: 价格突破中轨
- 代表策略: `肯特纳通道策略`

```python
# 核心代码
kc = KeltnerChannel(context.data, period=context.period, devfactor=context.multi)
context.middle_line = kc.mid
context.upper_line = kc.top
context.lower_line = kc.bot
context.upper_signal = CrossOver(context.data.close, context.upper_line)
context.lower_signal = CrossOver(context.data.close, context.lower_line)

if position == 0 and context.upper_signal[0] > 0 and context.middle_line[0] > context.middle_line[-1]:
    context.buy()
elif position == 0 and context.lower_signal[0] < 0 and context.middle_line[0] < context.middle_line[-1]:
    context.sell()
```

## 2. 振荡指标策略

### RSI策略
**核心机制**: 利用RSI指标的超买超卖特性
- 买入信号: RSI低于下限阈值
- 卖出信号: RSI高于上限阈值
- 代表策略: `RSI-标的池-分钟回测V6`、`框架代码（RSI指标）`

```python
# 核心代码
rsi = RSI(data.close, period=rsi_period, safediv=True)
if rsi[0] < context.bot:  # RSI低于下限，买入信号
    trade_dict['需买入的标的对象'].append(data)
elif rsi[0] > context.top:  # RSI高于上限，卖出信号
    trade_dict['需卖出的标的对象'].append(data)
```

### CCI策略
**核心机制**: 利用CCI指标的反转特性
- 买入信号: CCI从超卖区域向上突破
- 卖出信号: CCI从超买区域向下突破
- 代表策略: `关卡6-CCI指标择时示例`

```python
# 核心代码
context.cci = CommodityChannelIndex(period=20)
if context.cci[-1] < context.min_cci and context.cci[0] > context.min_cci:
    context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)
elif context.cci[-1] > context.max_cci and context.cci[0] < context.max_cci:
    context.close(data=context.data, price=context.data.close[0]*0.9)
```

### MACD策略
**核心机制**: 利用MACD指标的趋势判断和信号线交叉
- 买入信号: DIF和MACD均大于0，且DIF上穿MACD
- 卖出信号: DIF和MACD均小于0，且DIF下穿MACD
- 代表策略: `MACD策略`

```python
# 核心代码
macd = MACD(period_me1=12, period_me2=26, period_signal=9)
context.dif = macd.macd
context.macd = macd.signal
context.histo = context.dif - context.macd

if context.dif > 0 and context.macd > 0 and context.histo[0] > 0 and context.histo[-1] < 0:
    context.buy(price=context.data.close[0]*1.1)
elif context.dif < 0 and context.macd < 0 and context.histo[0] < 0 and context.histo[-1] > 0:
    context.sell(price=context.data.close[0]*0.9)
```

## 3. 组合指标策略

### MACD+KDJ策略
**核心机制**: 结合MACD和KDJ两种指标判断买卖时机
- 买入信号: MACD指标条件
- 卖出信号: KDJ的J线下穿D线
- 代表策略: `MACD+KDJ策略`

```python
# 核心代码
# 买入使用MACD指标
if context.dif > 0 and context.macd > 0 and context.histo[0] > 0 and context.histo[-1] < 0:
    context.buy(price=context.data.close[0]*1.1)
# 卖出使用KDJ指标
elif context.J[-1] > context.D[-1] and context.J[0] < context.D[0]:
    context.sell(price=context.data.close[0]*0.9)
```

### CCI+SMA策略
**核心机制**: 结合CCI和均线判断买卖点
- 买入信号: CCI从超卖区域向上突破
- 卖出信号: 价格下穿长期均线
- 代表策略: `关卡5-CCI+SMA择时示例`

```python
# 核心代码
if context.cci[-1] < context.min_cci and context.cci[0] > context.min_cci:
    context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)
elif context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:
    context.close(data=context.data, price=context.data.close[0]*0.9)
```

### 一阳穿三线策略
**核心机制**: 结合K线形态和多条均线关系
- 买入信号: 阳线穿过短、中、长三条均线，且成交量放大
- 代表策略: `关卡2-一阳穿三线示例`

```python
# 核心代码
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

## 4. 择时与止盈止损策略

### 抄底策略
**核心机制**: 利用连续下跌的反转机会
- 买入信号: 价格连续下跌一定天数
- 卖出信号: 价格连续上涨一定天数或达到止盈止损点
- 代表策略: `关卡7-抄底止损示例`、`关卡7-抄底止盈止损示例`

```python
# 核心代码
# 价格趋势判断函数
def price_trend(times, trend_type):
    # 判断价格是否连续上涨或下跌
    # ...

# 买入逻辑
if context.position.size == 0 and price_trend(context.p_downdays, 'down'):
    context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)

# 卖出逻辑
elif price_trend(context.p_updays, 'up'):
    context.close(data=context.data, price=context.data.close[0]*0.9)
```

### 跟踪止损策略
**核心机制**: 动态调整止损点位，锁定利润
- 买入信号: 均线金叉
- 卖出信号: 均线死叉或价格跌破动态止损线
- 代表策略: `关卡8-跟踪止损示例`

```python
# 核心代码
# 买入逻辑
if context.short_sma[-1] < context.long_sma[-1] and context.short_sma[0] > context.long_sma[0]:
    context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)

# 风控逻辑
context.h_price = max(context.h_price, context.position.price, context.data.close[0])
stop_price = (1 - context.stop_rate) * context.h_price
if context.data.close[0] < stop_price:
    context.close(data=context.data, price=context.data.close[0]*1.1)
```

## 5. 定投策略

### 移动平均成本法定投策略
**核心机制**: 根据当前价格与平均持有成本的关系调整定投金额
- 定投条件: 特定日期定投
- 定投金额调整: 价格低于平均成本时增加定投量，高于时减少定投量
- 代表策略: `移动平均成本法定投策略`

```python
# 核心代码
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
```

### 均线偏离法定投策略
**核心机制**: 根据基金净值与指数均线的关系调整定投金额
- 代表策略: `均线偏离法定投策略`

```python
# 核心代码
# 计算基金净值与指标均价的比值
ratio = data.close[-1] / context.sma
                
# 获取定投的费率
taker = context.get_taker(context.buy_money)
# 基于定投金额和费率计算申购份额
size = context.buy_money / (data.close[0] * (1 + taker))

# 判断是否偏离下界限
if ratio < context.down_bound:
    size = size * context.down_multiple
    
# 判断是否偏离上界限
if ratio >= context.up_bound:
    size = size * context.up_multiple
```

### 目标市值法定投策略
**核心机制**: 定期调整持仓市值至目标市值
- 代表策略: `目标市值法定投策略`

```python
# 核心代码
# 获取当前市值
current_value = context.position.size * context.datas[0].close[0]
# 计算买入金额
diff_value = context.target_value - current_value

# 如果买入金额大于0，表示当前市值没有达到目标市值，则追加定投
if diff_value > 0:
    buy_money = min(context.buy_money, diff_value)
    size = buy_money / (context.datas[0].close[0] * (1 + taker))
    context.buy(data=context.data, size=size, price=context.data.close[0]*1.1)
# 如果买入金额小于0，表示当前市值超出目标市值，则卖出超出部分
elif diff_value < 0:
    context.order_target_value(target=context.target_value, price=context.data.close[0]*0.9)
```

### 目标止盈法定投策略
**核心机制**: 定期定投直到达到目标盈利率
- 代表策略: `目标止盈法定投策略`

```python
# 核心代码
# 计算当前收益率，达到止盈条件则全部赎回
if context.position:
    profit_percent = context.datas[0].close[0] / context.position.price - 1
    if profit_percent >= context.target_profit and context.term_buy >= context.min_term:
        context.order = context.order_target_value(value=0)
        context.finish = True
```

## 6. 多标的策略

### 多因子策略
**核心机制**: 结合多个因子选择标的并进行投资组合构建
- 代表策略: `多因子策略`

```python
# 核心代码
# 选股因子
rate = context.rate[data._name][0]  # 截面收益率
if rate > context.threshold:
    rate_list.append([data._name, rate])

# 择时因子
position = context.getposition(data).size
if not position and data._name in context.stock_pool and data.close[0] > context.sma[data._name][0]:
    # 计算用于购买该标的的金额
    rate = fibo[context.stock_pool.index(data._name)] / sum(fibo)
    per_value = rate * total_value * context.max_value_percent
    size = int(per_value / 100 / data.close[0]) * 100
    context.buy(data=data, size=size, price=data.close[0]*1.1)
```

### FOF策略
**核心机制**: 根据基金的历史表现选择基金进行投资
- 代表策略: `激进型FOF`、`成长型FOF`

```python
# 核心代码
# 计算多种指标评分
score = context.returns[data._name][0] + context.sharpe_ratio[data._name][0] - context.max_draw_down[data._name][0]
score_list.append([data._name, score])

# 按得分排序选择基金
sorted_rate = sorted(score_list, key=lambda x: x[1], reverse=True)
context.stock_num = int(context.ratio * len(context.symbol_list))
context.stock_pool = []
for i in sorted_rate[:context.stock_num]:
    context.stock_pool.append(i[0])
```

## 7. 特殊策略

### 跨品种套利策略
**核心机制**: 利用相关性品种间的价差交易
- 代表策略: `跨品种套利策略`

```python
# 核心代码
# 获取两个标的的价差序列
context.diff_close = context.rb_data.close - context.j_data.close
# 计算套利区间上下限
open_boll_band = BollingerBands(context.diff_close, period=period, devfactor=open_devfactor)

# 当价差上穿上轨
if context.cross_top_signal[0] == 1.0:
    # 做空螺纹钢
    context.sell(data=context.rb_data, signal='open')
    # 做多焦炭
    context.buy(data=context.j_data, signal='open')
```

### 网格交易策略
**核心机制**: 在预设价格区间内设置网格，价格上升卖出，价格下跌买入
- 代表策略: `网格交易策略`

```python
# 核心代码
# 计算今日挡位
index = (context.data.close[0] - context.base_price) // context.distance
# 计算挡位变化数
change_index = index - context.last_index
# 如果挡位变化数大于0，执行卖出
if change_index > 0:
    context.sell(data=context.data, size=change_index*context.per_size)
# 如果挡位变化数小于0，执行买入
elif change_index < 0:
    context.buy(data=context.data, size=change_index*context.per_size)
```

### Hilbert策略
**核心机制**: 利用希尔伯特变换分析价格趋势
- 代表策略: `Hilbert策略`

```python
# 核心代码
# 基于差分序列进行Hilbert变换
context.hilbert = np.imag(hilbert(list(context.history_data)))
# 判断是否持仓，如果不持仓，则判断是否出现买入信号
if not context.position:
    # △(n)大于0，出现买入信号
    if context.hilbert[-1] > 0:
        context.order = context.buy()
# 如果持仓，则判断是否出现卖出信号
else:
    # △(n)小于0，出现卖出信号
    if context.hilbert[-1] < 0:
        context.order = context.sell()
```

## 8. 选股策略

### 市值选股策略
**核心机制**: 基于市值大小选择股票
- 代表策略: `小市值选股`

```python
# 核心代码
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
```

### 基本面选股策略
**核心机制**: 结合多个基本面指标选择股票
- 代表策略: `市值+市净率 选股`、`市值+净利润同比增长率 选股`、`关卡5-筛选中长期上涨股票示例`

```python
# 核心代码
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
```

## 策略总结

HiTrader策略库包含丰富多样的策略类型，涵盖了大多数常见的量化交易方法。每种策略都有其特定的应用场景和优缺点：

1. **趋势跟踪类策略**：适合明显趋势市场，但在震荡市场可能频繁交易导致亏损
2. **振荡指标类策略**：适合震荡市场，在单边趋势市场可能错过大行情
3. **组合指标策略**：通过多指标结合提高信号可靠性，但参数设置更复杂
4. **定投类策略**：长期投资策略，降低择时难度，但收益可能低于成功的择时策略
5. **多标的策略**：通过分散投资降低风险，但需要更复杂的资金管理
6. **特殊策略**：针对特定市场环境或标的特性设计，应用场景可能较为局限

在实际应用中，应根据市场环境、交易标的特性和个人风险偏好选择合适的策略，并通过回测和参数优化来提高策略性能。 