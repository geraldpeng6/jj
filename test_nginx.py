#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Nginx配置脚本

生成测试HTML文件并返回URL
"""

import os
import sys
import logging
import datetime
from utils.nginx_utils import get_chart_url

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_nginx')

def main():
    """
    主函数
    """
    # 确保charts目录存在
    charts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # 生成测试文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"test_nginx_{timestamp}.html"
    file_path = os.path.join(charts_dir, file_name)
    
    # 生成测试HTML文件
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Nginx测试</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Nginx配置测试成功!</h1>
    <p>如果您看到此页面，说明Nginx已成功配置为提供HTML文件。</p>
    <p>生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"测试文件已生成: {file_path}")
    
    # 获取URL
    url = get_chart_url(file_path)
    if url:
        print(f"测试文件URL: {url}")
        print("请在浏览器中访问此URL测试Nginx配置")
    else:
        print("无法生成URL，请检查Nginx配置")

if __name__ == "__main__":
    main()
