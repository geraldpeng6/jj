#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生成测试HTML文件

此脚本用于生成测试HTML文件，并打印出访问URL
"""

import os
import datetime
import socket
import requests
from pathlib import Path

def get_public_ip():
    """
    获取公网IP
    
    Returns:
        str: 公网IP，如果获取失败则返回None
    """
    try:
        # 尝试从EC2元数据服务获取公网IP
        response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=0.5)
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    try:
        # 尝试从ipify获取公网IP
        response = requests.get('https://api.ipify.org', timeout=2)
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    return None

def get_local_ip():
    """
    获取本地IP
    
    Returns:
        str: 本地IP，如果获取失败则返回localhost
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return 'localhost'

def main():
    """
    主函数
    """
    # 确保charts目录存在
    charts_dir = Path('data/charts')
    charts_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成测试文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"test_{timestamp}.html"
    file_path = charts_dir / file_name
    
    # 生成测试HTML内容
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>测试HTML文件</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>测试HTML文件</h1>
    <p>如果您能看到此页面，说明Nginx配置成功！</p>
    <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"测试HTML文件已生成: {file_path}")
    
    # 获取IP地址
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    
    # 打印访问URL
    if public_ip:
        print(f"公网访问URL: http://{public_ip}/{file_name}")
    
    print(f"本地访问URL: http://{local_ip}/{file_name}")
    print(f"内网访问URL: http://172.31.27.244/{file_name}")
    print(f"请在浏览器中访问以上URL，验证配置是否成功")

if __name__ == "__main__":
    main()
