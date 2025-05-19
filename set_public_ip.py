#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设置公网IP脚本

用于手动设置用于生成HTML文件URL的公网IP
"""

import os
import sys
import argparse
import logging
from utils.nginx_utils import set_public_ip, get_public_ip_from_config, get_server_ip

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('set_public_ip')

def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='设置用于生成HTML文件URL的公网IP')
    parser.add_argument('ip', nargs='?', help='公网IP地址，如果不提供则尝试自动获取')
    parser.add_argument('--auto', action='store_true', help='自动获取公网IP')
    parser.add_argument('--show', action='store_true', help='显示当前配置的公网IP')
    
    args = parser.parse_args()
    
    # 显示当前配置的公网IP
    if args.show:
        current_ip = get_public_ip_from_config()
        if current_ip:
            print(f"当前配置的公网IP: {current_ip}")
        else:
            print("当前未配置公网IP")
        return
    
    # 自动获取公网IP
    if args.auto or not args.ip:
        print("正在自动获取公网IP...")
        ip = get_server_ip()
        if ip == "localhost":
            print("无法自动获取公网IP，请手动指定")
            return
        print(f"自动获取到公网IP: {ip}")
    else:
        ip = args.ip
        print(f"使用手动指定的公网IP: {ip}")
    
    # 设置公网IP
    if set_public_ip(ip):
        print(f"公网IP设置成功: {ip}")
        print(f"现在可以通过 http://{ip}/文件名.html 访问图表文件")
    else:
        print("公网IP设置失败")

if __name__ == "__main__":
    main()
