# Nginx 配置指南

本文档介绍如何使用 `setup_nginx.sh` 脚本在 EC2 服务器上配置 Nginx，以提供静态 HTML 图表文件服务。

## 功能概述

`setup_nginx.sh` 脚本会自动完成以下任务：

1. 检查并安装 Nginx（如果尚未安装）
2. 创建 Nginx 配置文件，配置为提供 `data/charts` 目录中的 HTML 文件
3. 限制只能访问 HTML 文件，防止目录列表和其他文件类型的访问
4. 配置 Nginx 使用端口 80 提供服务
5. 设置适当的文件权限
6. 重启 Nginx 应用配置
7. 创建测试文件并提供测试 URL

## 使用方法

### 在 EC2 服务器上

1. 将项目代码上传到 EC2 服务器
2. 确保 `setup_nginx.sh` 脚本具有执行权限：

```bash
chmod +x setup_nginx.sh
```

3. 以 root 权限运行脚本：

```bash
sudo ./setup_nginx.sh
```

4. 脚本执行完成后，会提供一个测试 URL，可以在浏览器中访问该 URL 测试配置是否成功

### 自定义图表目录

如果您的图表文件不在默认的 `data/charts` 目录中，可以使用 `-d` 或 `--charts-dir` 选项指定自定义目录：

```bash
sudo ./setup_nginx.sh -d /path/to/your/charts
```

## 访问图表文件

配置完成后，可以通过以下 URL 格式访问图表文件：

```
http://服务器IP/文件名.html
```

例如，如果您的 EC2 服务器 IP 是 `12.34.56.78`，且有一个名为 `backtest_result.html` 的图表文件，则可以通过以下 URL 访问：

```
http://12.34.56.78/backtest_result.html
```

## 安全性说明

此配置具有以下安全特性：

1. 只允许访问 HTML 文件，其他文件类型将返回 403 错误
2. 禁止目录列表，防止泄露目录结构
3. 禁止访问隐藏文件（以 `.` 开头的文件）
4. 添加了适当的 CORS 头，允许从其他域名访问图表文件

## 故障排除

如果遇到问题，可以检查以下日志文件：

- Nginx 错误日志：`/var/log/nginx/quant_charts_error.log`
- Nginx 访问日志：`/var/log/nginx/quant_charts_access.log`

常见问题：

1. **无法访问图表文件**
   - 检查 EC2 安全组设置，确保允许入站 TCP 端口 80
   - 检查 Nginx 是否正在运行：`systemctl status nginx`
   - 检查 Nginx 配置是否有效：`nginx -t`

2. **权限问题**
   - 确保 Nginx 用户对图表目录有读取权限
   - 重新运行脚本，它会自动设置正确的权限

3. **配置文件问题**
   - 检查 `/etc/nginx/conf.d/quant_charts.conf` 文件是否存在
   - 检查配置文件中的路径是否正确

## 与项目集成

在您的 Python 代码中，当生成 HTML 图表文件时，只需将文件保存到 `data/charts` 目录中，然后可以构建 URL 返回给用户：

```python
def generate_chart_url(file_name):
    """
    生成图表文件的URL
    
    Args:
        file_name: HTML文件名
        
    Returns:
        str: 图表文件的URL
    """
    # 获取EC2实例的公网IP
    try:
        # 尝试从EC2元数据服务获取公网IP
        response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=0.5)
        if response.status_code == 200:
            server_ip = response.text
        else:
            # 如果无法获取公网IP，使用本地IP
            server_ip = socket.gethostbyname(socket.gethostname())
    except:
        # 如果不在EC2上运行，使用本地IP
        server_ip = socket.gethostbyname(socket.gethostname())
    
    # 构建URL
    return f"http://{server_ip}/{file_name}"
```

## 注意事项

1. 此脚本主要为 EC2 环境设计，在其他环境中可能需要手动调整
2. 脚本需要 root 权限运行，因为它需要安装软件包和修改系统配置
3. 如果您的 EC2 实例有多个 IP 地址，脚本会尝试使用公网 IP
4. 此配置不包含 HTTPS 支持，如果需要 HTTPS，请考虑使用 AWS Certificate Manager 和 Application Load Balancer，或手动配置 Let's Encrypt
