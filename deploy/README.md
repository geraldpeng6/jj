# MCP服务器部署指南

本文档提供了将MCP（量化交易助手）部署到服务器的详细步骤，并说明如何让用户通过HTTP获取生成的HTML内容（K线图和回测结果）。

## 目录

- [系统要求](#系统要求)
- [部署步骤](#部署步骤)
  - [1. 准备服务器](#1-准备服务器)
  - [2. 安装依赖](#2-安装依赖)
  - [3. 配置环境](#3-配置环境)
  - [4. 部署MCP](#4-部署mcp)
  - [5. 配置Nginx](#5-配置nginx)
  - [6. 启动服务](#6-启动服务)
- [使用说明](#使用说明)
  - [获取K线图](#获取k线图)
  - [获取回测结果](#获取回测结果)
- [故障排除](#故障排除)

## 系统要求

- 操作系统：Ubuntu 20.04 LTS或更高版本（推荐）
- Python：3.8或更高版本
- Nginx：1.18或更高版本
- 内存：至少2GB RAM
- 存储：至少20GB可用空间

## 部署步骤

### 1. 准备服务器

1. 登录到您的服务器：

```bash
ssh username@your-server-ip
```

2. 更新系统包：

```bash
sudo apt update
sudo apt upgrade -y
```

3. 安装必要的系统依赖：

```bash
sudo apt install -y python3 python3-pip python3-venv nginx
```

### 2. 安装依赖

1. 克隆或上传MCP代码到服务器：

```bash
# 如果使用Git
git clone <your-repository-url> /path/to/quant_mcp
cd /path/to/quant_mcp

# 或者，上传代码后
cd /path/to/quant_mcp
```

2. 确保部署脚本可执行：

```bash
chmod +x deploy/deploy.sh
chmod +x deploy/start.sh
```

### 3. 配置环境

1. 创建环境配置文件：

```bash
cp deploy/.env.example deploy/.env
```

2. 编辑环境配置文件，设置服务器URL和其他配置：

```bash
nano deploy/.env
```

修改以下配置：

```
MCP_SERVER_HOST=your-server-domain-or-ip
MCP_SERVER_PORT=80
MCP_SERVER_PROTOCOL=http
```

如果使用HTTPS，则设置：

```
MCP_SERVER_PROTOCOL=https
MCP_SERVER_PORT=443
```

**重要说明**：
- 在本地开发环境中，我们使用`file://`协议直接打开HTML文件
- 在服务器环境中，需要修改`utils/static_server.py`文件中的URL生成逻辑，使用HTTP/HTTPS协议而不是`file://`协议
- 修改方法：将`url = f"file://{os.path.abspath(file_path)}"`改为`url = f"{server_url}/static/{rel_path}"`

### 4. 部署MCP

运行部署脚本：

```bash
./deploy/deploy.sh --server-name your-server-domain-or-ip
```

如果需要使用SSL，可以添加`--ssl`选项并提供证书和密钥路径：

```bash
./deploy/deploy.sh --server-name your-server-domain-or-ip --ssl --ssl-cert /path/to/cert.pem --ssl-key /path/to/key.pem
```

部署脚本会创建Python虚拟环境、安装依赖、创建Nginx配置文件和systemd服务文件。

### 5. 配置Nginx

按照部署脚本输出的指令，以root权限执行以下命令：

```bash
sudo cp /path/to/quant_mcp/deploy/nginx.conf /etc/nginx/sites-available/mcp
sudo ln -sf /etc/nginx/sites-available/mcp /etc/nginx/sites-enabled/mcp
sudo cp /path/to/quant_mcp/deploy/mcp.service /etc/systemd/system/mcp.service
sudo systemctl daemon-reload
sudo systemctl enable mcp
sudo systemctl start mcp
sudo systemctl restart nginx
```

### 6. 启动服务

服务应该已经通过systemd启动。您可以检查服务状态：

```bash
sudo systemctl status mcp
```

如果需要手动启动服务，可以使用启动脚本：

```bash
cd /path/to/quant_mcp
./deploy/start.sh
```

## 使用说明

### 获取K线图

要获取K线图，使用`get_kline_data`函数并设置`http_mode=True`：

```python
result = await get_kline_data(
    symbol="600000",
    exchange="XSHG",
    resolution="1D",
    http_mode=True
)
```

返回的结果中将包含一个URL，用户可以通过该URL访问K线图：

```
K线图表已生成并可通过以下URL访问:
http://your-server-domain-or-ip/static/klines/600000_XSHG_1D_post_1234567890.html
```

### 获取回测结果

要获取回测结果，使用`run_strategy_backtest`函数并设置`http_mode=True`：

```python
result = await run_strategy_backtest(
    strategy_id="your-strategy-id",
    http_mode=True
)
```

返回的结果中将包含一个URL，用户可以通过该URL访问回测结果：

```
回测结果图表已生成并可通过以下URL访问:
http://your-server-domain-or-ip/static/backtests/backtest_your-strategy-id_1234567890.html
```

## 故障排除

### 1. 无法访问静态文件

检查Nginx配置和权限：

```bash
sudo nginx -t
sudo ls -la /path/to/quant_mcp/data/charts
```

确保Nginx用户（通常是www-data）有权限读取静态文件目录：

```bash
sudo chown -R www-data:www-data /path/to/quant_mcp/data/charts
```

### 2. MCP服务无法启动

检查日志：

```bash
sudo journalctl -u mcp.service
```

确保Python虚拟环境和依赖安装正确：

```bash
cd /path/to/quant_mcp
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. URL生成不正确

检查环境配置文件中的服务器URL设置：

```bash
cat deploy/.env
```

确保`MCP_SERVER_HOST`、`MCP_SERVER_PORT`和`MCP_SERVER_PROTOCOL`设置正确。
