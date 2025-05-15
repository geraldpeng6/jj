# MCP项目一键配置指南

本文档提供了使用一键配置脚本在Ubuntu服务器上部署MCP项目的说明。

## 前提条件

- Ubuntu 18.04/20.04/22.04 服务器
- 具有sudo权限的用户
- 如果需要SSL，需要一个指向服务器的域名

## 使用方法

### 1. 克隆项目

首先，将项目克隆到服务器上：

```bash
# 克隆项目
git clone <your-repository-url> quant_mcp
cd quant_mcp
```

### 2. 设置脚本权限

```bash
# 设置脚本可执行权限
chmod +x deploy/setup_server.sh
```

### 3. 运行一键配置脚本

#### 基本用法（使用IP地址，HTTP）

```bash
sudo bash deploy/setup_server.sh
```

这将使用服务器的IP地址和HTTP协议配置MCP项目。

#### 使用域名（HTTP）

```bash
sudo bash deploy/setup_server.sh --domain your-domain.com
```

#### 使用域名和SSL（HTTPS）

```bash
sudo bash deploy/setup_server.sh --domain your-domain.com --ssl --ssl-email your-email@example.com
```

#### 完整选项

```bash
sudo bash deploy/setup_server.sh --domain your-domain.com --ip 192.168.1.100 --port 80 --ssl --ssl-email your-email@example.com --project-dir /path/to/quant_mcp
```

### 4. 脚本选项说明

- `--domain DOMAIN`: 服务器域名（如果有）
- `--ip IP`: 服务器IP地址（默认：自动检测）
- `--port PORT`: HTTP端口（默认：80）
- `--ssl`: 启用SSL/HTTPS
- `--ssl-email EMAIL`: 用于Let's Encrypt的邮箱地址
- `--project-dir DIR`: 项目目录（默认：当前目录）
- `--help`: 显示帮助信息

## 配置完成后

脚本执行完成后，将显示以下信息：

1. 服务器信息（API URL、静态文件URL等）
2. VSCode配置（用于连接到MCP服务器）
3. 服务管理命令
4. 测试命令

## VSCode配置

在您的本地VSCode中，配置MCP服务器连接：

1. 打开VSCode设置（可以通过按下`Ctrl+,`或`Cmd+,`，或者通过菜单`File > Preferences > Settings`）。

2. 点击右上角的"打开设置（JSON）"图标，或者直接编辑`settings.json`文件。

3. 添加脚本输出的VSCode配置。例如：

```json
{
    "mcpServers": {
        "量化交易助手": {
            "url": "http://your-server-ip-or-domain/mcp",
            "transportType": "streamable_http"
        }
    }
}
```

## 服务管理

### 查看服务状态

```bash
sudo systemctl status mcp
```

### 重启服务

```bash
sudo systemctl restart mcp
```

### 停止服务

```bash
sudo systemctl stop mcp
```

### 查看日志

```bash
sudo journalctl -u mcp.service
```

## 测试

### 测试MCP服务

```bash
curl http://localhost:8000/health
```

### 测试Nginx代理

```bash
curl http://your-server-ip-or-domain/health
```

### 测试K线图生成

```bash
cd /path/to/quant_mcp
source .venv/bin/activate
python -c "from src.tools.kline_tools import get_kline_data; import asyncio; result = asyncio.run(get_kline_data('600000', 'XSHG', http_mode=True)); print(result)"
```

## 故障排除

### 1. Nginx配置错误

如果Nginx配置有错误，可以查看错误日志：

```bash
sudo nginx -t
sudo cat /var/log/nginx/error.log
```

### 2. MCP服务无法启动

检查MCP服务日志：

```bash
sudo journalctl -u mcp.service
```

### 3. 无法访问静态文件

检查Nginx配置中的静态文件路径是否正确，以及文件权限：

```bash
sudo ls -la /path/to/quant_mcp/data/charts
```

确保Nginx用户（通常是www-data）有权限读取静态文件目录：

```bash
sudo chown -R www-data:www-data /path/to/quant_mcp/data/charts
```

### 4. SSL证书问题

如果SSL证书配置有问题，可以尝试重新运行certbot：

```bash
sudo certbot --nginx -d your-domain.com
```

## 安全注意事项

1. 定期更新系统和依赖：

```bash
sudo apt update && sudo apt upgrade -y
```

2. 监控日志文件，检查异常活动：

```bash
sudo tail -f /var/log/nginx/access.log
```

3. 考虑设置防火墙规则，只允许必要的端口：

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```
