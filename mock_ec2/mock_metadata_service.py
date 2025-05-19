#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模拟EC2元数据服务

此脚本模拟EC2元数据服务，返回指定的公网IP
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# 模拟的EC2公网IP
MOCK_IP = "123.45.67.89"

class MetadataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/latest/meta-data/public-ipv4":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(MOCK_IP.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        # 禁止输出HTTP请求日志
        pass

def run(server_class=HTTPServer, handler_class=MetadataHandler, port=80):
    server_address = ("127.0.0.1", port)
    httpd = server_class(server_address, handler_class)
    print(f"模拟EC2元数据服务已启动，监听端口: {port}")
    print(f"模拟的EC2公网IP: {MOCK_IP}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("模拟EC2元数据服务已停止")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8169  # 默认端口
    run(port=port)
