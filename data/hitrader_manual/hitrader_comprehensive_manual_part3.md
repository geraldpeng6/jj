# HiTrader 量化交易平台全面指南 - 第三部分：高级功能与风险管理

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