# MCP 服务器传输协议说明

本文档介绍了 MCP 服务器支持的不同传输协议及其使用方法。

## 支持的传输协议

MCP 服务器支持以下三种传输协议：

1. **STDIO (标准输入输出)**
   - 默认传输协议
   - 适用于本地工具和命令行脚本
   - 通过标准输入输出流进行通信

2. **SSE (Server-Sent Events)**
   - 基于 HTTP 的单向通信协议
   - 适用于与 Web 应用集成
   - 允许服务器向客户端推送实时更新

3. **Streamable HTTP**
   - 推荐用于生产环境部署
   - 基于 HTTP 的双向通信协议
   - 提供更好的性能和可靠性

## 启动服务器

### 一键启动脚本（推荐）

我们提供了一键启动脚本 `start.sh`，它会自动检查环境，安装依赖，并启动服务器。这个脚本适用于新环境，无需手动设置。

```bash
# 使用默认设置启动（SSE传输协议，监听0.0.0.0:8000）
./start.sh

# 指定传输协议
./start.sh --transport stdio                # 使用STDIO传输协议
./start.sh --transport sse                  # 使用SSE传输协议
./start.sh --transport streamable-http      # 使用Streamable HTTP传输协议

# 指定主机和端口
./start.sh --host 127.0.0.1 --port 9000
```

这个脚本会自动：
- 检查并安装 uv（如果需要）
- 创建虚拟环境（如果不存在）
- 安装所需依赖
- 启动服务器

### 使用 STDIO 传输协议

```bash
# 使用一键启动脚本
./start.sh --transport stdio

# 使用开发脚本启动（需要先激活虚拟环境）
./scripts/run.sh --transport stdio

# 或直接使用 Python（需要先激活虚拟环境）
python server.py --transport stdio
```

### 使用 SSE 传输协议

```bash
# 使用一键启动脚本（默认就是SSE传输协议）
./start.sh

# 指定主机和端口
./start.sh --host 127.0.0.1 --port 9000

# 使用run.sh脚本启动（需要先激活虚拟环境）
./scripts/run.sh --transport sse --host 127.0.0.1 --port 9000

# 或直接使用 Python（需要先激活虚拟环境）
python server.py --transport sse --host 127.0.0.1 --port 9000
```

### 使用 Streamable HTTP 传输协议

```bash
# 使用一键启动脚本
./start.sh --transport streamable-http

# 指定主机和端口
./start.sh --transport streamable-http --host 127.0.0.1 --port 9000

# 使用run.sh脚本启动（需要先激活虚拟环境）
./scripts/run.sh --transport streamable-http --host 127.0.0.1 --port 9000

# 或直接使用 Python（需要先激活虚拟环境）
python server.py --transport streamable-http --host 127.0.0.1 --port 9000
```

## 客户端连接

### 连接到 STDIO 服务器

STDIO 传输协议通常用于本地进程间通信，客户端需要启动服务器进程并通过标准输入输出流进行通信。

### 连接到 SSE 服务器

SSE 服务器的 URL 格式为：`http://<host>:<port>/sse`

例如：`http://127.0.0.1:8000/sse`

### 连接到 Streamable HTTP 服务器

Streamable HTTP 服务器的 URL 格式为：`http://<host>:<port>/mcp`

例如：`http://127.0.0.1:8000/mcp`

## 选择合适的传输协议

- **开发和测试**：使用 STDIO 传输协议，简单直接
- **与 Web 应用集成**：使用 SSE 传输协议，便于在浏览器中使用
- **生产环境部署**：使用 Streamable HTTP 传输协议，提供更好的性能和可靠性

## 注意事项

1. 使用 SSE 或 Streamable HTTP 传输协议时，服务器需要能够接受来自网络的连接，可能需要配置防火墙规则。
2. 默认情况下，服务器监听所有网络接口 (0.0.0.0)，如果只需要本地访问，可以将主机设置为 127.0.0.1。
3. 确保选择的端口未被其他应用占用。
