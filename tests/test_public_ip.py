#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试获取公网IP的功能
"""

import unittest
import os
import sys
import logging
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.html_server import get_public_ip, get_server_host, load_config

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_public_ip')


class TestPublicIP(unittest.TestCase):
    """
    测试获取公网IP的功能
    """
    
    def setUp(self):
        """
        测试前的准备工作
        """
        # 保存原始配置
        self.original_config_exists = os.path.exists('data/config/html_server.json')
        if self.original_config_exists:
            with open('data/config/html_server.json', 'r') as f:
                self.original_config = f.read()
        
        # 清除环境变量
        if 'MCP_SERVER_HOST' in os.environ:
            self.original_env = os.environ['MCP_SERVER_HOST']
            del os.environ['MCP_SERVER_HOST']
        else:
            self.original_env = None

    def tearDown(self):
        """
        测试后的清理工作
        """
        # 恢复原始配置
        if self.original_config_exists:
            with open('data/config/html_server.json', 'w') as f:
                f.write(self.original_config)
        elif os.path.exists('data/config/html_server.json'):
            os.remove('data/config/html_server.json')
        
        # 恢复环境变量
        if self.original_env is not None:
            os.environ['MCP_SERVER_HOST'] = self.original_env

    def test_get_public_ip(self):
        """
        测试从公网IP服务获取公网IP的功能
        """
        ip = get_public_ip()
        print(f"获取到的公网IP: {ip}")
        
        # 检查IP格式
        self.assertIsNotNone(ip, "未能获取到公网IP")
        self.assertRegex(ip, r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', "IP格式不正确")
        
        # 检查IP不是保留的私有IP地址
        parts = [int(p) for p in ip.split('.')]
        self.assertFalse(
            parts[0] == 10 or
            (parts[0] == 172 and 16 <= parts[1] <= 31) or
            (parts[0] == 192 and parts[1] == 168) or
            parts[0] == 127,
            f"获取到的IP {ip} 是私有IP地址"
        )
        
        # 确保不是硬编码的测试IP
        self.assertNotEqual(ip, "123.45.67.89", "获取到的IP是硬编码的测试IP")

    def test_get_server_host_without_config(self):
        """
        测试在没有配置文件的情况下获取服务器主机地址
        """
        # 临时移除配置文件
        if os.path.exists('data/config/html_server.json'):
            os.rename('data/config/html_server.json', 'data/config/html_server.json.bak')
        
        try:
            # 获取服务器主机地址
            host = get_server_host()
            print(f"没有配置文件时获取到的服务器主机地址: {host}")
            
            # 检查不是硬编码的测试IP
            self.assertNotEqual(host, "123.45.67.89", "获取到的主机地址是硬编码的测试IP")
            
            # 验证是有效的IP地址或主机名
            if host != "localhost":
                # 如果是IP地址，验证格式
                if all(c.isdigit() or c == '.' for c in host):
                    self.assertRegex(host, r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', "IP格式不正确")
        
        finally:
            # 恢复配置文件
            if os.path.exists('data/config/html_server.json.bak'):
                os.rename('data/config/html_server.json.bak', 'data/config/html_server.json')
    
    def test_get_server_host_with_env(self):
        """
        测试在设置了环境变量的情况下获取服务器主机地址
        """
        # 设置环境变量
        os.environ['MCP_SERVER_HOST'] = '192.168.1.100'
        
        # 获取服务器主机地址
        host = get_server_host()
        print(f"设置了环境变量时获取到的服务器主机地址: {host}")
        
        # 检查是否使用了环境变量的值
        self.assertEqual(host, '192.168.1.100', "未使用环境变量中的主机地址")
    
    def test_get_server_host_with_config(self):
        """
        测试在有配置文件的情况下获取服务器主机地址
        """
        # 创建配置文件
        os.makedirs('data/config', exist_ok=True)
        config = {
            "server_host": "8.8.8.8",
            "server_port": 8081,
            "charts_dir": "data/charts",
            "use_ec2_metadata": False,
            "use_public_ip": False
        }
        with open('data/config/html_server.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # 获取服务器主机地址
        host = get_server_host()
        print(f"有配置文件时获取到的服务器主机地址: {host}")
        
        # 检查是否使用了配置文件的值
        self.assertEqual(host, '8.8.8.8', "未使用配置文件中的主机地址")


if __name__ == '__main__':
    unittest.main() 