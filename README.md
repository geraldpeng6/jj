# 量化交易助手 MCP 服务器

基于 Model Context Protocol (MCP) 的量化交易助手服务器，提供股票历史数据查询、K线图表生成等功能。

## 功能特点

- 获取股票历史K线数据
- 保存K线数据到文件
- 生成K线图表并在浏览器中显示

## 目录结构

```
quant_mcp/
├── data/                   # 数据目录
│   ├── charts/             # 图表文件目录
│   ├── config/             # 配置文件目录
│   │   └── auth.json       # 认证配置文件
│   ├── klines/             # K线数据文件目录
│   ├── logs/               # 日志目录
│   └── temp/               # 临时文件目录
├── scripts/                # 脚本目录
│   ├── setup_uv.sh         # uv 安装和环境设置脚本
│   └── update_deps.sh      # 依赖更新脚本
├── src/                    # 源代码目录
│   ├── prompts/            # 提示词模块
│   ├── resources/          # 资源模块
│   └── tools/              # 工具模块
│       └── kline_tools.py  # K线数据工具
├── utils/                  # 工具函数
│   ├── auth_utils.py       # 认证工具
│   ├── chart_generator.py  # 图表生成器
│   ├── kline_utils.py      # K线数据工具
│   └── logging_utils.py    # 日志工具
├── .gitignore              # Git 忽略文件
├── requirements.txt        # 项目依赖
└── server.py               # 服务器入口
```

## 安装依赖

### 使用 uv (推荐)

我们推荐使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理工具，它比传统的 pip 更快、更可靠。

1. 运行安装脚本（会安装 uv 并创建虚拟环境）:

```bash
./scripts/setup_uv.sh
```

2. 激活虚拟环境:

```bash
source .venv/bin/activate
```

3. 使用运行脚本启动服务器:

```bash
./scripts/run.sh
```

### 使用 pip

如果您不想使用 uv，也可以使用传统的 pip 安装依赖:

```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置文件模板并填写认证信息：

```bash
cp data/config/auth.json.example data/config/auth.json
```

2. 编辑 `data/config/auth.json` 文件，填入您的 API 令牌和用户 ID：

```json
{
    "token": "your_api_token_here",
    "user_id": "your_user_id_here"
}
```

## 开发指南

### Git 版本控制

本项目使用 Git 进行版本控制。`.gitignore` 文件已配置为忽略常见的临时文件、日志文件和包含敏感信息的配置文件。

基本 Git 操作：

```bash
# 查看文件状态
git status

# 添加更改
git add .

# 提交更改
git commit -m "描述你的更改"

# 查看提交历史
git log
```

### 启动服务器

```bash
python server.py
```

默认使用 stdio 传输协议，这是与 Claude 桌面应用等客户端通信的标准方式。

### 使用工具

在支持 MCP 的客户端（如 Claude 桌面应用）中，可以使用以下工具：

1. **获取K线数据**：

```
get_kline_data(symbol="600000", exchange="XSHG", resolution="1D")
```

2. **保存K线数据到文件**：

```
save_kline_data(symbol="600000", exchange="XSHG", resolution="1D", file_format="csv")
```

## 参数说明

### 获取K线数据 (get_kline_data)

- `symbol`: 股票代码，例如 "600000"
- `exchange`: 交易所代码，例如 "XSHG"
- `resolution`: 时间周期，例如 "1D"（日线）, "1"（1分钟）
- `from_date`: 开始日期，格式为YYYY-MM-DD，默认为30天前
- `to_date`: 结束日期，格式为YYYY-MM-DD，默认为当前日期
- `fq`: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
- `fq_date`: 复权基准日期，格式为YYYY-MM-DD，默认为当前日期
- `category`: 品种类别，默认为 "stock"（股票）
- `skip_paused`: 是否跳过停牌日期，默认为 False
- `generate_chart`: 是否生成K线图表并在浏览器中显示，默认为 False

### 保存K线数据 (save_kline_data)

- `symbol`: 股票代码，例如 "600000"
- `exchange`: 交易所代码，例如 "XSHG"
- `resolution`: 时间周期，例如 "1D"（日线）, "1"（1分钟）
- `from_date`: 开始日期，格式为YYYY-MM-DD，默认为30天前
- `to_date`: 结束日期，格式为YYYY-MM-DD，默认为当前日期
- `fq`: 复权方式，"post"（后复权）, "pre"（前复权）, "none"（不复权）
- `output_dir`: 输出目录，默认为"data/klines"
- `file_format`: 文件格式，支持"csv"和"excel"，默认为"csv"
