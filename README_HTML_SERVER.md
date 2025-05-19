# HTML服务器配置指南

本文档提供了如何配置HTML服务器以提供K线图表和回测结果HTML文件的访问的说明。

## 概述

量化交易助手生成的K线图表和回测结果HTML文件可以通过两种方式访问：

1. **本地模式**：直接在本地浏览器中打开HTML文件
2. **服务器模式**：通过Web服务器（如Nginx）提供HTML文件的访问

服务器模式特别适用于在远程服务器（如AWS EC2）上部署量化交易助手，并希望通过网络访问生成的图表。

## 配置服务器模式

### 1. 创建服务器配置文件

在`data/config`目录下创建`server.json`文件，可以复制`server.json.example`作为模板：

```bash
cp data/config/server.json.example data/config/server.json
```

然后编辑`server.json`文件，设置适当的配置：

```json
{
  "enabled": true,
  "host": "your-server-ip-or-domain",
  "port": 80,
  "base_url": "",
  "charts_dir": "data/charts",
  "use_https": false
}
```

参数说明：
- `enabled`: 是否启用服务器模式
- `host`: 服务器的IP地址或域名
- `port`: 服务器端口，通常为80（HTTP）或443（HTTPS）
- `base_url`: 基础URL，如果为空则自动构建为`http(s)://host:port`
- `charts_dir`: 图表目录，相对于项目根目录
- `use_https`: 是否使用HTTPS

### 2. 配置Nginx服务器

在AWS EC2或其他服务器上，需要配置Nginx来提供HTML文件的访问。

#### 安装Nginx（如果尚未安装）

```bash
# 在Ubuntu/Debian上
sudo apt update
sudo apt install nginx

# 在CentOS/RHEL上
sudo yum install epel-release
sudo yum install nginx
```

#### 创建Nginx配置文件

可以使用项目提供的示例配置文件：

```bash
sudo cp data/config/nginx.conf.example /etc/nginx/conf.d/quant_mcp.conf
```

然后编辑配置文件，将`/path/to/quant_mcp-1/data/charts`替换为实际的charts目录路径：

```bash
sudo nano /etc/nginx/conf.d/quant_mcp.conf
```

#### 重启Nginx

```bash
sudo systemctl restart nginx
```

### 3. 测试配置

启动量化交易助手，生成一些K线图表或回测结果，然后尝试通过浏览器访问：

```
http://your-server-ip-or-domain/some_chart.html
```

## 安全注意事项

1. 配置只允许访问HTML文件，防止目录列表和其他文件的访问
2. 考虑添加基本的HTTP认证以限制访问
3. 如果需要更高的安全性，配置HTTPS

## 自动生成Nginx配置

量化交易助手提供了一个工具函数来自动生成Nginx配置文件：

```python
from utils.html_server import create_nginx_config

# 生成配置文件
create_nginx_config('path/to/output/nginx.conf')
```

## 故障排除

1. **无法访问HTML文件**
   - 检查Nginx是否正在运行：`sudo systemctl status nginx`
   - 检查Nginx错误日志：`sudo tail -f /var/log/nginx/error.log`
   - 确保防火墙允许80端口的访问

2. **权限问题**
   - 确保Nginx用户（通常是www-data或nginx）有权限读取charts目录
   - 可以使用以下命令修改权限：`sudo chmod -R 755 /path/to/quant_mcp-1/data/charts`

3. **URL构建问题**
   - 如果URL不正确，检查`server.json`中的配置，特别是`host`和`port`设置

## 在EC2上的完整部署步骤

1. 安装必要的软件包
   ```bash
   sudo apt update
   sudo apt install nginx python3 python3-pip git
   ```

2. 克隆项目
   ```bash
   git clone https://your-repository-url/quant_mcp-1.git
   cd quant_mcp-1
   ```

3. 安装Python依赖
   ```bash
   pip3 install -r requirements.txt
   ```

4. 配置服务器
   ```bash
   cp data/config/server.json.example data/config/server.json
   # 编辑server.json设置正确的host
   ```

5. 配置Nginx
   ```bash
   sudo cp data/config/nginx.conf.example /etc/nginx/conf.d/quant_mcp.conf
   # 编辑配置文件设置正确的路径
   sudo systemctl restart nginx
   ```

6. 启动量化交易助手
   ```bash
   ./start.sh
   ```

现在，当量化交易助手生成K线图表或回测结果时，它将返回可通过网络访问的URL，而不是本地文件路径。
