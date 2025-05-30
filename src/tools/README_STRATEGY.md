# 策略工具 (Strategy Tools)

策略工具模块提供了对量化交易策略进行管理的功能，包括创建、查询、更新和删除策略。本文档介绍了相关功能和使用方法。

## 功能概述

策略工具模块提供以下功能：

1. **查询策略列表** - 获取用户策略或策略库列表
2. **查询策略详情** - 查看特定策略的详细信息
3. **创建用户策略** - 创建新的用户策略
4. **更新用户策略** - 更新现有用户策略
5. **删除用户策略** - 删除现有用户策略

所有策略均在远程服务器管理，不进行本地存储。

## 工具说明

### 查询策略列表 (list_strategies)

```python
async def list_strategies(strategy_group: str = "library") -> str:
```

- **参数**：
  - `strategy_group`: 策略组类型，"user"表示用户策略，"library"表示策略库策略，默认为"library"
- **返回值**：格式化的策略列表信息，或错误信息

### 查询策略详情 (get_strategy)

```python
async def get_strategy(strategy_id: str) -> str:
```

- **参数**：
  - `strategy_id`: 策略ID
- **返回值**：格式化的策略详情信息，或错误信息

### 创建用户策略 (create_strategy)

```python
async def create_strategy(strategy_name: str, choose_stock: str, indicator: str, timing: str, control_risk: str = "def control_risk(context):\n    pass\n") -> str:
```

- **参数**：
  - `strategy_name`: 策略名称
  - `choose_stock`: 选股代码
  - `indicator`: 指标代码
  - `timing`: 择时代码
  - `control_risk`: 风控代码，默认为空实现
- **返回值**：创建结果信息，或错误信息

### 更新用户策略 (update_strategy)

```python
async def update_strategy(strategy_id: str, strategy_name: str, choose_stock: str, indicator: str, timing: str, control_risk: str = "def control_risk(context):\n    pass\n") -> str:
```

- **参数**：
  - `strategy_id`: 策略ID
  - `strategy_name`: 策略名称
  - `choose_stock`: 选股代码
  - `indicator`: 指标代码
  - `timing`: 择时代码
  - `control_risk`: 风控代码，默认为空实现
- **返回值**：更新结果信息，或错误信息

### 删除用户策略 (delete_user_strategy)

```python
async def delete_user_strategy(strategy_id: str) -> str:
```

- **参数**：
  - `strategy_id`: 策略ID
- **返回值**：删除结果信息，或错误信息

## 使用示例

### 创建用户策略

```python
# 创建单均线策略
result = await create_strategy(
    strategy_name="单均线策略",
    choose_stock='def choose_stock(context):\n    context.symbol_list = ["600000.XSHG"]\n',
    indicator='def indicators(context):\n    context.sma = SMA(period=20)\n',
    timing='def timing(context):\n    if not context.position:\n        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:\n            context.order = context.buy(price=context.data.close[0]*1.1)\n    else:\n        if context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:\n            context.order = context.sell(price=context.data.close[0]*0.9)\n'
)
print(result)
```

### 更新用户策略

```python
# 更新单均线策略
result = await update_strategy(
    strategy_id="Qjv2nDEkmrg7LA61yJ0KeaJNxRqlBYWV",
    strategy_name="改进的单均线策略",
    choose_stock='def choose_stock(context):\n    context.symbol_list = ["600000.XSHG"]\n',
    indicator='def indicators(context):\n    context.sma = SMA(period=15)\n',  # 修改了周期
    timing='def timing(context):\n    if not context.position:\n        if context.data.close[-1] < context.sma[-1] and context.data.close[0] > context.sma[0]:\n            context.order = context.buy(price=context.data.close[0]*1.1)\n    else:\n        if context.data.close[-1] > context.sma[-1] and context.data.close[0] < context.sma[0]:\n            context.order = context.sell(price=context.data.close[0]*0.9)\n'
)
print(result)
```

## 注意事项

1. **策略ID**：更新策略时必须提供有效的策略ID，系统会检查策略是否存在
2. **策略类型**：只能更新用户策略，不能更新策略库中的策略
3. **错误处理**：所有操作都有完善的错误处理和日志记录
4. **权限**：所有操作都需要有效的认证信息

## 实现细节

- 所有策略操作都通过 API 请求与远程服务器交互
- 更新策略前会先检查策略是否存在以及是否为用户策略
- 所有响应都有格式化处理，便于用户阅读
- 所有操作都有日志记录，便于排查问题 