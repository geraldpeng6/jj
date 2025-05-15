#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gunicorn配置文件
用于在生产环境中部署MCP服务器
"""

import multiprocessing
import os

# 绑定的地址和端口
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# 工作进程数
# 建议设置为CPU核心数的2-4倍
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# 工作模式
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")

# 超时时间（秒）
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))

# 保持连接的最大请求数
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))

# 随机化最大请求数，避免所有工作进程同时重启
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 50))

# 日志级别
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# 访问日志格式
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")

# 错误日志
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")

# 进程名
proc_name = os.getenv("GUNICORN_PROC_NAME", "mcp_server")

# 守护进程模式
daemon = os.getenv("GUNICORN_DAEMON", "false").lower() == "true"

# 预加载应用
preload_app = os.getenv("GUNICORN_PRELOAD", "true").lower() == "true"

# 优雅重启超时时间
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))

# 保持连接
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 2))

# 工作进程启动超时时间
timeout = int(os.getenv("GUNICORN_TIMEOUT", 30))

# 工作进程重启策略
worker_exit = lambda server, worker: server.respawn_worker()

# 启动前执行的函数
def on_starting(server):
    print("MCP服务器正在启动...")

# 启动后执行的函数
def when_ready(server):
    print(f"MCP服务器已启动，监听地址: {bind}")
