# Web服务器配置指南

本文档介绍如何配置Web服务器，以便通过公网IP访问生成的HTML图表文件。

## 功能概述

系统支持两种方式提供HTML图表文件：

1. **Nginx服务器**（推荐）：
   - 使用标准端口80
   - 更好的性能和安全性
   - 支持公网访问
   - 需要root权限安装

2. **内置Web服务器**（备选）：
   - 无需额外安装
   - 自动启动
   - 可能无法使用标准端口
   - 公网访问可能受限

## 安装和配置Nginx

### 自动安装（推荐）

我们提供了自动安装脚本，可以一键安装和配置Nginx：

```bash
# 以root权限运行安装脚本
sudo ./install_nginx.sh
```

脚本会自动完成以下任务：
- 检查并安装Nginx（如果尚未安装）
- 创建配置文件，设置为提供`data/charts`目录中的HTML文件
- 限制只能访问HTML文件，防止目录列表
- 配置使用端口80
- 设置适当的文件权限
- 重启Nginx应用配置
- 创建测试文件并提供测试URL

### 手动安装

如果您希望手动安装和配置Nginx，请按照以下步骤操作：

1. 安装Nginx：
   ```bash
   # Debian/Ubuntu
   sudo apt-get update
   sudo apt-get install -y nginx
   
   # CentOS/RHEL
   sudo yum install -y nginx
   
   # macOS
   brew install nginx
   ```

2. 创建配置文件：
   ```bash
   # Linux
   sudo nano /etc/nginx/conf.d/quant_charts.conf
   
   # macOS
   nano /usr/local/etc/nginx/servers/quant_charts.conf
   ```

3. 添加以下配置内容（替换`/path/to/data/charts`为实际路径）：
   ```nginx
   server {
       listen 80;
       server_name _;
       
       location / {
           root /path/to/data/charts;
           
           # 只允许访问HTML文件
           location ~* \.(html)$ {
               add_header Access-Control-Allow-Origin *;
               add_header Cache-Control "no-cache, must-revalidate";
           }
           
           # 禁止访问非HTML文件
           location ~* \.((?!html).)*$ {
               deny all;
               return 403;
           }
           
           # 禁止目录列表
           autoindex off;
       }
   }
   ```

4. 重启Nginx：
   ```bash
   # Linux
   sudo systemctl restart nginx
   
   # macOS
   brew services restart nginx
   ```

## 设置公网IP

为了生成正确的URL，您需要设置公网IP：

```bash
# 自动获取公网IP
python set_public_ip.py --auto

# 手动设置公网IP
python set_public_ip.py 123.456.789.10

# 查看当前配置的公网IP
python set_public_ip.py --show
```

## 测试配置

运行测试脚本，生成测试HTML文件并获取URL：

```bash
python test_nginx.py
```

如果一切正常，您将看到类似以下输出：

```
测试文件已生成: /path/to/data/charts/test_nginx_20230101_123456.html
测试文件URL: http://123.456.789.10/test_nginx_20230101_123456.html
请在浏览器中访问此URL测试Nginx配置
```

## 使用内置Web服务器

如果您不想安装Nginx，系统会自动使用内置Web服务器。内置服务器会在需要时自动启动，无需手动配置。

您可以使用以下命令诊断内置Web服务器的状态：

```bash
python -c "from utils.web_server import diagnose_network; print(diagnose_network())"
```

## 故障排除

### 无法访问URL

1. **检查Nginx是否正在运行**：
   ```bash
   # Linux
   systemctl status nginx
   
   # macOS
   brew services list | grep nginx
   ```

2. **检查配置文件是否有效**：
   ```bash
   nginx -t
   ```

3. **检查防火墙设置**：
   确保端口80已开放

4. **检查公网IP设置**：
   ```bash
   python set_public_ip.py --show
   ```

5. **检查路由器设置**：
   如果在家庭网络中，可能需要设置端口转发

### 内置Web服务器问题

1. **端口冲突**：
   内置服务器默认使用端口8080，如果该端口被占用，会自动选择其他端口

2. **权限问题**：
   使用标准端口（80/443）需要root权限

## 与项目集成

系统已自动集成了Web服务器功能，当生成HTML图表时，会自动返回可访问的URL。

例如，使用`get_kline_data`工具时，如果设置`generate_chart=True`，将返回图表URL：

```
K线图表已生成
图表URL: http://123.456.789.10/600000_XSHG_1D_post_20230101_123456.html
```

使用`get_kline_data_with_url`工具时，会始终返回图表URL。
