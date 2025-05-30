# HiTrader 量化交易平台全面指南 - 第四部分：完整策略案例

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