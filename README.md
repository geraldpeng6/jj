# Quant MCP Backtest Tools

量化交易策略回测工具，支持多种参数定制的量化策略回测。

## 回测参数说明

回测工具提供以下可定制参数：

### 资金设置

- **初始资金 (capital)**: 回测起始可用资金，默认值为200000元。
- **订单数量 (order)**: 每笔交易的股票数量，默认值为500股。

### 时间范围

- **开始日期 (start_date)**: 回测开始日期，格式为 "YYYY-MM-DD"，默认为一年前。
- **结束日期 (end_date)**: 回测结束日期，格式为 "YYYY-MM-DD"，默认为当前日期。

### 数据频次 (resolution)

回测支持以下数据频次：

| 参数值 | 说明 |
|-------|-----|
| 1s, 3s, 5s | 秒级数据 |
| 1m, 5m, 15m, 30m | 分钟级数据 |
| 1h, 2h | 小时级数据 |
| 1d, 2d, 3d | 日级数据 |
| 1w, 3w | 周级数据 |
| 1m, 6m | 月级数据 |

默认值为 "1d" (日线数据)。

### 复权方式 (fq)

回测支持以下复权设置：

- **post**: 后复权（默认）
- **pre**: 前复权
- **none**: 不复权

### 交易参数

- **手续费率 (commission)**: 交易手续费率，默认为0.0003（0.03%）
- **保证金比率 (margin)**: 保证金比率，默认为0.05（5%）
- **无风险利率 (riskfreerate)**: 无风险利率，默认为0.01（1%）
- **金字塔加仓次数 (pyramiding)**: 允许的加仓次数，默认为1次

## 使用示例

```python
from utils.backtest_utils import run_backtest

# 运行回测
result = run_backtest(
    strategy_id="your_strategy_id",
    start_date="2023-01-01",
    end_date="2023-12-31",
    capital=100000,            # 10万初始资金
    order=200,                 # 每笔200股
    resolution="15m",          # 15分钟线
    fq="pre",                  # 前复权
    commission=0.0005,         # 0.05%手续费
    margin=0.1,                # 10%保证金
    riskfreerate=0.03          # 3%无风险利率
)

# 输出回测结果
if result.get('success'):
    print(f"回测成功，共收到 {result.get('position_count', 0)} 条数据")
    print(f"图表路径: {result.get('chart_path')}")
else:
    print(f"回测失败: {result.get('error')}")
```

## 测试脚本

项目包含测试脚本 `src/scripts/test_backtest_params.py`，可用于测试不同参数组合的回测效果。

## 命令行工具

项目提供了命令行工具 `src/scripts/run_backtest_cli.py` 用于快速运行回测并配置参数：

### 基本用法

```bash
# 使用策略ID运行回测
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id

# 使用指定股票代码运行回测
python src/scripts/run_backtest_cli.py --symbol 600000.XSHG

# 多只股票
python src/scripts/run_backtest_cli.py --symbol "600000.XSHG&000001.XSHE"
```

### 配置参数示例

```bash
# 设置回测时间范围和数据频率
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id \
  --start_date 2023-01-01 --end_date 2023-12-31 --resolution 15m

# 设置初始资金和交易参数
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id \
  --capital 100000 --order 200 --commission 0.0005 --margin 0.1

# 使用前复权数据
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id --fq pre

# 自动打开回测结果图表
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id --open_chart
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--strategy_id` | 策略ID | - |
| `--symbol` | 股票代码，多个用&分隔 | - |
| `--start_date` | 回测开始日期，格式 YYYY-MM-DD | 一年前 |
| `--end_date` | 回测结束日期，格式 YYYY-MM-DD | 当前日期 |
| `--capital` | 初始资金 | 200000 |
| `--order` | 每笔交易数量 | 500 |
| `--resolution` | 数据频次，如 1s, 5m, 15m, 1h, 1d 等 | 1D |
| `--fq` | 复权方式: post, pre, none | post |
| `--commission` | 手续费率 | 0.0003 |
| `--margin` | 保证金比率 | 0.05 |
| `--riskfreerate` | 无风险利率 | 0.01 |
| `--pyramiding` | 金字塔加仓次数 | 1 |
| `--listen_time` | 监听回测结果时间（秒） | 60 |
| `--open_chart` | 自动打开回测图表 | 否 |

### 使用自定义策略代码

```bash
# 使用自定义指标代码文件
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id \
  --indicator_file path/to/indicator.py

# 使用自定义择时代码文件
python src/scripts/run_backtest_cli.py --strategy_id your_strategy_id \
  --timing_file path/to/timing.py
``` 