# 量化交易助手MCP服务器云部署指南

本文档提供了在各种云服务器上部署量化交易助手MCP服务器的详细指南。

## 目录

- [前提条件](#前提条件)
- [部署选项](#部署选项)
- [基本部署](#基本部署)
- [生产环境部署](#生产环境部署)
- [云服务提供商特定指南](#云服务提供商特定指南)
  - [阿里云](#阿里云)
  - [腾讯云](#腾讯云)
  - [AWS](#aws)
  - [Google Cloud](#google-cloud)
- [安全配置](#安全配置)
- [负载均衡](#负载均衡)
- [故障排除](#故障排除)

## 前提条件

在开始部署之前，请确保您的云服务器满足以下要求：

- Python 3.10 或更高版本
- 至少 2GB RAM（推荐 4GB 或更多）
- 至少 10GB 可用磁盘空间
- 可访问互联网（用于安装依赖）
- 开放的端口（默认为 8000）

## 部署选项

量化交易助手MCP服务器支持两种主要的部署选项：

1. **基本部署**：适用于开发和测试环境
2. **生产环境部署**：使用 Gunicorn 作为 WSGI 服务器，适用于生产环境

## 基本部署

### 1. 获取代码

首先，将代码克隆或上传到您的云服务器：

```bash
git clone <repository-url>
cd quant_mcp
```

或者使用 SCP 等工具上传代码：

```bash
scp -r /path/to/local/quant_mcp user@your-server-ip:~/
ssh user@your-server-ip
cd quant_mcp
```

### 2. 设置环境变量（可选）

创建 `.env` 文件并设置必要的环境变量：

```bash
touch .env
```

编辑 `.env` 文件，添加以下内容：

```
# MCP服务器配置
MCP_HOST=0.0.0.0
MCP_PORT=8000

# 其他配置
# ...
```

### 3. 运行部署脚本

使用提供的部署脚本启动服务器：

```bash
chmod +x deploy.sh
./deploy.sh
```

这将自动创建虚拟环境、安装依赖并启动服务器。

### 4. 自定义部署选项

您可以通过命令行参数自定义部署选项：

```bash
./deploy.sh --port 9000 --host 127.0.0.1 --no-stateless
```

查看所有可用选项：

```bash
./deploy.sh --help
```

## 生产环境部署

对于生产环境，我们建议使用 Gunicorn 作为 WSGI 服务器，以提高性能和可靠性。

### 1. 使用生产环境部署脚本

```bash
chmod +x deploy_prod.sh
./deploy_prod.sh start
```

### 2. 管理服务器

启动服务器：

```bash
./deploy_prod.sh start
```

停止服务器：

```bash
./deploy_prod.sh stop
```

重启服务器：

```bash
./deploy_prod.sh restart
```

查看服务器状态：

```bash
./deploy_prod.sh status
```

### 3. 配置为系统服务

为了确保服务器在系统重启后自动启动，您可以将其配置为系统服务。

对于使用 systemd 的系统（如 Ubuntu 16.04+、CentOS 7+）：

```bash
sudo nano /etc/systemd/system/mcp-server.service
```

添加以下内容：

```
[Unit]
Description=量化交易助手MCP服务器
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/quant_mcp
ExecStart=/path/to/quant_mcp/deploy_prod.sh start
ExecStop=/path/to/quant_mcp/deploy_prod.sh stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
```

## 云服务提供商特定指南

### 阿里云

1. 创建 ECS 实例（推荐 2 核 4GB 或更高配置）
2. 开放安全组入站规则，允许 TCP 端口 8000（或您配置的端口）
3. 按照基本部署或生产环境部署步骤进行部署
4. 考虑使用阿里云 SLB（负载均衡）实现高可用性

### 腾讯云

1. 创建云服务器实例（推荐 2 核 4GB 或更高配置）
2. 在安全组中开放端口 8000（或您配置的端口）
3. 按照基本部署或生产环境部署步骤进行部署
4. 考虑使用腾讯云 CLB（负载均衡）实现高可用性

### AWS

1. 创建 EC2 实例（推荐 t3.medium 或更高配置）
2. 在安全组中开放端口 8000（或您配置的端口）
3. 按照基本部署或生产环境部署步骤进行部署
4. 考虑使用 AWS ELB（弹性负载均衡）实现高可用性

### Google Cloud

1. 创建 Compute Engine 实例（推荐 e2-medium 或更高配置）
2. 在防火墙规则中开放端口 8000（或您配置的端口）
3. 按照基本部署或生产环境部署步骤进行部署
4. 考虑使用 Google Cloud Load Balancing 实现高可用性

## 安全配置

为了确保您的 MCP 服务器安全，请考虑以下配置：

1. **使用 HTTPS**：在生产环境中，强烈建议使用 HTTPS。您可以使用 Nginx 或 Apache 作为反向代理，并配置 SSL 证书。

2. **限制 IP 访问**：配置防火墙规则，只允许特定 IP 地址访问您的服务器。

3. **使用认证**：确保 `data/config/auth.json` 文件正确配置，以启用认证功能。

4. **定期更新**：定期更新服务器和依赖项，以修复安全漏洞。

## 负载均衡

对于高流量场景，您可以部署多个 MCP 服务器实例，并使用负载均衡器分发流量。

1. 在多台服务器上部署 MCP 服务器
2. 配置负载均衡器（如 Nginx、HAProxy 或云服务提供商的负载均衡服务）
3. 确保使用无状态模式（`--stateless` 选项）以支持水平扩展

## 故障排除

如果您在部署过程中遇到问题，请检查以下内容：

1. **日志文件**：检查 `logs/` 目录中的日志文件，了解详细的错误信息。

2. **端口冲突**：确保指定的端口未被其他服务占用。

3. **防火墙规则**：确保云服务器的防火墙允许指定端口的流量。

4. **依赖问题**：如果遇到依赖安装问题，尝试手动安装：
   ```bash
   pip install -r requirements.txt
   ```

5. **权限问题**：确保脚本具有执行权限：
   ```bash
   chmod +x deploy.sh deploy_prod.sh
   ```

如果问题仍然存在，请查看项目文档或联系支持团队。
