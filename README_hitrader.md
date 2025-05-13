# HiTrader策略生成器

本项目提供了一个自动生成HiTrader交易策略代码的工具，可以根据用户指定的参数生成完整的HiTrader策略代码，并支持回测功能。

## 功能特点

- 自动生成完整的HiTrader策略代码，包括indicators、choose_stock、timing和control_risk四个函数
- 支持多种策略类型，如趋势跟踪、均值回归、突破、动量等
- 支持多种技术指标，如MA、MACD、RSI、KDJ、BOLL等
- 支持多种仓位管理和止损方式
- 支持回测功能，可以直接对生成的策略进行回测

## 使用方法

### 通过MCP服务器使用

1. 启动MCP服务器：

```bash
uv run server.py
```

2. 使用MCP客户端连接服务器，然后可以使用以下提示模板：

- `generate_hitrader_strategy`: 生成HiTrader交易策略代码
- `optimize_hitrader_strategy`: 优化现有的HiTrader交易策略代码
- `generate_backtest_code`: 生成HiTrader策略的回测代码

或者使用以下工具：

- `generate_hitrader_strategy`: 生成HiTrader策略代码并保存为文件
- `backtest_hitrader_strategy`: 回测HiTrader策略

### 通过脚本使用

可以使用提供的示例脚本来生成HiTrader策略代码：

```bash
uv run scripts/generate_hitrader_strategy.py --strategy_type dual_ma --timeframe daily --risk_level medium --specific_stocks 600000.XSHG --backtest
```

参数说明：

- `--strategy_type`: 策略类型，可选值包括trend_following, mean_reversion, breakout, momentum, dual_ma, macd, rsi, kdj, boll
- `--timeframe`: 交易时间框架，可选值包括daily, weekly, 60min, 30min, 15min
- `--risk_level`: 风险水平，可选值包括low, medium, high
- `--stock_selection`: 选股方式，可选值包括single, multiple, index, sector
- `--specific_stocks`: 指定股票代码，多个股票用&分隔，如600000.XSHG&000001.XSHE
- `--indicators_required`: 需要的技术指标，可选值包括ma, macd, rsi, kdj, boll, all
- `--position_sizing`: 仓位管理方式，可选值包括fixed, dynamic, risk_based
- `--stop_loss`: 止损方式，可选值包括fixed, trailing, atr, none
- `--backtest`: 是否进行回测
- `--start_date`: 回测开始日期，格式为YYYY-MM-DD
- `--end_date`: 回测结束日期，格式为YYYY-MM-DD

## HiTrader策略代码结构

HiTrader策略代码通常包含四个主要函数：

1. `indicators(context)`: 计算技术指标
2. `choose_stock(context)`: 选择交易标的
3. `timing(context)`: 实现交易信号和执行交易
4. `control_risk(context)`: 实现风险控制逻辑

### 示例代码

以下是一个简单的双均线策略示例：

```python
def indicators(context):
    """指标"""
    # 计算短期均线和长期均线
    context.short_ma = SMA(period=5)
    context.long_ma = SMA(period=20)

def choose_stock(context):
    """选股"""
    context.symbol_list = ["600000.XSHG"]

def timing(context):
    """择时"""
    # 判断是否持仓，如果不持仓，则判断是否出现买入信号
    if not context.position:
        # 当短期均线上穿长期均线时，出现买入信号
        if context.short_ma[-1] < context.long_ma[-1] and context.short_ma[0] > context.long_ma[0]:
            # 买入信号出现时，发送买入指令，系统自动执行买入交易
            context.order = context.buy(price=context.data.close[0]*1.01)

    # 如果持仓，则判断是否出现卖出信号
    else:
        # 当短期均线下穿长期均线时，出现卖出信号
        if context.short_ma[-1] > context.long_ma[-1] and context.short_ma[0] < context.long_ma[0]:
            # 卖出信号出现时，发送卖出指令，系统自动执行卖出交易
            context.order = context.sell(price=context.data.close[0]*0.99)

def control_risk(context):
    """风控"""
    # 如果持仓，并且当前价格低于买入价格的95%，则止损卖出
    if context.position and context.data.close[0] < context.position.avg_cost * 0.95:
        context.order = context.sell(price=context.data.close[0]*0.99)
```

## 常用技术指标

HiTrader支持多种技术指标，包括：

- `SMA(period)`: 简单移动平均线
- `EMA(period)`: 指数移动平均线
- `MACD(fast_period, slow_period, signal_period)`: MACD指标
- `RSI(period)`: 相对强弱指数
- `BOLL(period, std_dev)`: 布林带
- `KDJ(period)`: KDJ随机指标
- `ATR(period)`: 平均真实波幅

## 注意事项

- 生成的策略代码仅供参考，实际使用前请进行充分测试
- 回测结果不代表未来表现，投资有风险，请谨慎操作
- 建议在实盘交易前，先进行模拟交易测试
