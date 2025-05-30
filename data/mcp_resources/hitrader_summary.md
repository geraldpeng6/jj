# HiTrader 量化交易平台总结

## 平台基础概念

HiTrader是一个量化交易平台，允许用户编写、回测和部署交易策略。平台提供了完整的代码框架和API，支持多种市场和标的。

## 代码框架结构

HiTrader的策略代码分为四个主要模块：

1. **选股模块 (choose_stock)**：定义交易标的
2. **指标模块 (indicators)**：计算交易指标和设置参数
3. **择时模块 (timing)**：实现买卖逻辑
4. **风控模块 (control_risk)**：实现风险控制逻辑

每个模块有自己的职责，分离了交易策略的不同方面，使代码更易于维护和理解。

## 核心概念和API

### Context对象

`context`是全局对象，在策略的各个模块间共享数据：

- `context.log()` - 输出日志信息（替代print）
- `context.broker` - 访问账户信息（`getvalue()`获取总资产，`cash`获取可用现金）
- `context.symbol_list` - 设置标的池
- `context.benchmark` - 设置基准标的
- `context.parse_index` - 设置是否解析指数成分股

### 标的数据访问

- `context.data` - 当标的池只有一个标的时，直接访问该标的
- `context.datas` - 访问所有标的的列表
- `context.getdatabyname(symbol)` - 通过代码获取特定标的

### 标的数据结构

标的数据包含多种属性：

- `data.close` - 收盘价
- `data.open` - 开盘价
- `data.high` - 最高价
- `data.low` - 最低价
- `data.volume` - 成交量
- `data._name` - 标的代码
- `data.datetime.date()` - 获取当前日期

数据索引约定：`[0]`代表当前值，`[-1]`代表前一个值，依此类推。

### 持仓管理

- `context.position` - 单标的情况下的持仓
- `context.getposition(data)` - 获取特定标的的持仓
- `position.size` - 持仓数量
- `position.price` - 持仓均价

### 交易操作

- `context.buy(data, size, price)` - 买入操作
- `context.sell(data, size, price)` - 卖出操作
- `context.close(data, price)` - 平仓操作
- `context.order_target_value(target, price)` - 调整持仓至目标市值

## 常用指标

HiTrader内置了丰富的技术指标，包括但不限于：

- SMA - 简单移动平均
- EMA - 指数移动平均
- MACD - 移动平均收敛散度
- RSI - 相对强弱指数
- BollingerBands - 布林带
- KDJ - 随机指标
- CommodityChannelIndex - 顺势指标(CCI)
- DonchianChannel - 唐奇安通道
- CrossOver - 交叉检测

## 策略实现模式

### 1. 选股模块
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

### 2. 指标模块
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

### 3. 择时模块
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

### 4. 风控模块
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

## 常见策略类型

HiTrader支持多种类型的策略，常见的包括：

1. **趋势跟踪策略**
   - 单均线/双均线突破
   - 海龟交易法
   - 唐奇安通道

2. **震荡指标策略**
   - RSI超买超卖
   - KDJ交叉
   - CCI反转

3. **综合指标策略**
   - MACD+KDJ结合
   - 布林带+均线
   - 一阳穿三线

4. **基本面选股策略**
   - 小市值选股
   - 市净率筛选
   - 净利润增长率筛选

5. **投资组合策略**
   - 多因子策略
   - FOF策略（基金中的基金）

6. **定投策略**
   - 移动平均成本法
   - 目标市值法
   - 目标止盈法

## 策略优化与风控方法

### 策略优化
- 参数优化（如均线周期、指标阈值）
- 标的选择优化
- 交易时机优化

### 风控方法
1. **固定止盈止损**：根据持仓均价设定固定比例的止盈止损点
2. **跟踪止损**：随着盈利增加动态调整止损点
3. **时间风控**：基于持仓时间的风控
4. **资金管理**：
   - 单日资金使用限制
   - 总资金使用比例控制
   - 单个标的资金分配

## 策略评估指标

评估交易策略的常用指标：

- 总收益率
- 年化收益率
- 最大回撤
- 夏普比率
- 胜率
- 盈亏比
- 卡玛比率
- 交易次数

## 常见策略框架模式

### 基础框架
将策略逻辑清晰地分为四个模块，使代码结构清晰。

### 带信号字典的框架
使用信号字典记录每个标的的交易信号，便于管理多标的策略。
```python
def timing(context):
    trade_dict = {'需买入的标的对象': [], '需卖出的标的对象': []}
    
    # 计算信号并填充字典
    for data in context.datas:
        # 信号计算...
        if 买入信号:
            trade_dict['需买入的标的对象'].append(data)
        elif 卖出信号:
            trade_dict['需卖出的标的对象'].append(data)
    
    # 执行交易
    for sell_data in trade_dict['需卖出的标的对象']:
        context.close(data=sell_data)
    
    for buy_data in trade_dict['需买入的标的对象']:
        context.buy(data=buy_data, size=context.trade_size)
```

### 资金管理框架
增加资金管理和订单管理功能的框架。
```python
def timing(context):
    # 计算当日已使用资金
    day_buy_value = 0
    for order in context.get_orders(status='submitted'):
        if order.ordtype == 0:  # 买入订单
            day_buy_value += order.created.price * order.created.size
    
    # 资金控制逻辑...
    if day_buy_percent < context.day_max_percent:
        # 执行买入...
```

## 策略规划建议

策略开发前应明确：
1. 策略名称和目标
2. 各模块具体内容：指标选择、标的范围、择时逻辑、风控方法
3. 回测设置：资金量、交易频率、回测周期、手续费等
4. 评估标准：预期表现、目标指标、可能的失效情形

以上内容提供了HiTrader量化交易平台的核心概念和使用方法，适合作为开发和优化交易策略的参考。 