#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTML服务器诊断工具

用于诊断HTML服务器无法通过公网访问的问题
"""

import os
import sys
import socket
import requests
import subprocess
import argparse
import logging
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('diagnose_server')

def is_running_on_ec2() -> bool:
    """检测是否在EC2实例上运行"""
    # 首先检查环境变量
    env_ec2 = os.environ.get('EC2_INSTANCE')
    if env_ec2 is not None:
        if env_ec2.lower() == 'true':
            return True
        elif env_ec2.lower() == 'false':
            return False
    
    # 尝试访问EC2元数据服务
    try:
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id', timeout=0.5)
        if response.status_code == 200:
            return True
    except:
        pass
    
    # 检查系统文件
    ec2_files = [
        '/sys/hypervisor/uuid',
        '/sys/devices/virtual/dmi/id/product_uuid',
        '/etc/ec2_version',
        '/etc/amazon/ssm/seelog.xml',
        '/var/lib/amazon',
        '/var/log/amazon'
    ]
    for file_path in ec2_files:
        if os.path.exists(file_path):
            return True
    
    return False

def get_public_ip() -> Optional[str]:
    """获取公网IP地址"""
    apis = [
        'https://api.ipify.org',
        'https://ifconfig.me/ip',
        'https://icanhazip.com',
        'https://ident.me',
        'https://ipecho.net/plain'
    ]

    for api in apis:
        try:
            response = requests.get(api, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            continue

    return None

def get_local_ip() -> Optional[str]:
    """获取本地IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return None

def check_port_open(host: str, port: int) -> bool:
    """检查指定主机的端口是否开放"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False

def check_ec2_security_group() -> Dict[str, Any]:
    """检查EC2安全组配置"""
    result = {
        "http_allowed": False,
        "https_allowed": False,
        "error": None
    }
    
    try:
        # 获取实例ID
        try:
            instance_id_cmd = "curl -s http://169.254.169.254/latest/meta-data/instance-id"
            instance_id = subprocess.check_output(instance_id_cmd, shell=True, timeout=2).decode('utf-8').strip()
            print(f"获取到EC2实例ID: {instance_id}")
            
            # 获取安全组ID
            sg_cmd = f"aws ec2 describe-instances --instance-ids {instance_id} --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' --output text"
            security_groups = subprocess.check_output(sg_cmd, shell=True, timeout=5).decode('utf-8').strip().split()
            
            if not security_groups:
                result["error"] = "无法获取安全组信息"
                return result
                
            print(f"获取到安全组: {security_groups}")
            
            # 检查安全组规则
            for sg_id in security_groups:
                rules_cmd = f"aws ec2 describe-security-groups --group-ids {sg_id} --query 'SecurityGroups[0].IpPermissions[*]'"
                rules_output = subprocess.check_output(rules_cmd, shell=True, timeout=5).decode('utf-8')
                
                # 检查是否允许HTTP流量（端口80）
                if '"FromPort": 80' in rules_output or '"ToPort": 80' in rules_output:
                    result["http_allowed"] = True
                    print(f"安全组 {sg_id} 允许HTTP流量（端口80）")
                
                # 检查是否允许HTTPS流量（端口443）
                if '"FromPort": 443' in rules_output or '"ToPort": 443' in rules_output:
                    result["https_allowed"] = True
                    print(f"安全组 {sg_id} 允许HTTPS流量（端口443）")
        except subprocess.SubprocessError as e:
            result["error"] = f"执行AWS CLI命令失败: {e}"
        except Exception as e:
            result["error"] = f"检查安全组时出错: {e}"
    except ImportError:
        result["error"] = "无法导入subprocess模块，跳过安全组检查"
    
    return result

def check_processes() -> Dict[str, Any]:
    """检查占用端口80的进程"""
    result = {
        "port_80_used": False,
        "processes": [],
        "error": None
    }
    
    try:
        # 检查端口80是否被占用
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', 80))
            s.close()
            # 如果能绑定成功，说明端口未被占用
            result["port_80_used"] = False
        except:
            # 端口被占用
            result["port_80_used"] = True
            
            # 查找占用端口的进程
            try:
                # 使用lsof命令查找占用端口的进程
                cmd = "lsof -i :80 -n -P"
                output = subprocess.check_output(cmd, shell=True, timeout=5).decode('utf-8')
                
                # 解析输出
                lines = output.strip().split('\n')
                if len(lines) > 1:  # 第一行是标题
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 2:
                            result["processes"].append({
                                "command": parts[0],
                                "pid": parts[1]
                            })
            except subprocess.SubprocessError as e:
                # 如果lsof命令失败，尝试使用netstat
                try:
                    cmd = "netstat -tulpn | grep :80"
                    output = subprocess.check_output(cmd, shell=True, timeout=5).decode('utf-8')
                    
                    # 解析输出
                    lines = output.strip().split('\n')
                    for line in lines:
                        if ':80 ' in line:
                            parts = line.split()
                            if len(parts) >= 7:
                                pid_program = parts[6].split('/')
                                if len(pid_program) >= 2:
                                    result["processes"].append({
                                        "command": pid_program[1],
                                        "pid": pid_program[0]
                                    })
                except:
                    result["error"] = "无法确定占用端口80的进程"
    except Exception as e:
        result["error"] = f"检查进程时出错: {e}"
    
    return result

def diagnose_server(port: int = 80) -> None:
    """诊断服务器问题"""
    print("===== HTML服务器诊断工具 =====")
    
    # 检查是否在EC2上运行
    on_ec2 = is_running_on_ec2()
    print(f"在EC2上运行: {'是' if on_ec2 else '否'}")
    
    # 获取IP地址
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    print(f"本地IP: {local_ip or '无法获取'}")
    print(f"公网IP: {public_ip or '无法获取'}")
    
    # 检查端口是否开放
    if local_ip:
        local_port_open = check_port_open(local_ip, port)
        print(f"本地端口{port}开放: {'是' if local_port_open else '否'}")
    
    if public_ip:
        public_port_open = check_port_open(public_ip, port)
        print(f"公网端口{port}开放: {'是' if public_port_open else '否'}")
    
    # 如果在EC2上运行，检查安全组配置
    if on_ec2:
        print("\n===== EC2安全组配置 =====")
        sg_result = check_ec2_security_group()
        
        if sg_result.get("error"):
            print(f"检查安全组时出错: {sg_result['error']}")
        else:
            print(f"安全组允许HTTP流量（端口80）: {'是' if sg_result.get('http_allowed', False) else '否'}")
            print(f"安全组允许HTTPS流量（端口443）: {'是' if sg_result.get('https_allowed', False) else '否'}")
    
    # 检查端口占用情况
    print("\n===== 端口占用情况 =====")
    proc_result = check_processes()
    
    if proc_result.get("error"):
        print(f"检查进程时出错: {proc_result['error']}")
    else:
        print(f"端口80被占用: {'是' if proc_result.get('port_80_used', False) else '否'}")
        
        if proc_result.get('port_80_used', False) and proc_result.get('processes'):
            print("占用端口80的进程:")
            for proc in proc_result.get('processes', []):
                print(f"  - 命令: {proc.get('command')}, PID: {proc.get('pid')}")
    
    # 提供诊断建议
    print("\n===== 诊断建议 =====")
    
    if not public_ip:
        print("1. 无法获取公网IP，请检查网络连接")
    
    if on_ec2:
        if not sg_result.get('http_allowed', False):
            print("2. EC2安全组未配置允许HTTP流量（端口80），请在AWS控制台中修改安全组设置，添加入站规则允许TCP端口80")
        
        if proc_result.get('port_80_used', False):
            print("3. 端口80已被其他进程占用，请停止这些进程或使用其他端口")
            print("   可以使用以下命令停止占用端口80的进程:")
            for proc in proc_result.get('processes', []):
                print(f"   sudo kill {proc.get('pid')}")
        
        if not public_port_open and sg_result.get('http_allowed', False) and not proc_result.get('port_80_used', False):
            print("4. 安全组已配置允许HTTP流量，但公网端口80仍不可访问，可能的原因:")
            print("   - 网络ACL设置：确保允许入站TCP端口80")
            print("   - 实例状态：确保实例正在运行且网络接口正常")
            print("   - 公网IP：确保实例有公网IP或弹性IP")
            print("   - 路由表：确保子网的路由表配置正确")
            print("   - 服务器绑定：确保服务器绑定到0.0.0.0而不是localhost")
    else:
        print("2. 未检测到在EC2实例上运行，如果您确实在EC2上运行，可以设置环境变量EC2_INSTANCE=true")
        print("   export EC2_INSTANCE=true")
        
        if proc_result.get('port_80_used', False):
            print("3. 端口80已被其他进程占用，请停止这些进程或使用其他端口")
    
    print("\n===== 解决方案 =====")
    print("1. 如果在EC2上运行，请使用提供的start_ec2.sh脚本以root权限启动服务器:")
    print("   sudo ./start_ec2.sh")
    print("2. 确保EC2安全组允许入站TCP端口80")
    print("3. 如果端口80被占用，请停止占用的进程或使用其他端口")
    print("4. 如果仍然无法访问，请检查网络ACL、路由表和实例状态")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HTML服务器诊断工具')
    parser.add_argument('--port', type=int, default=80, help='要检查的端口号，默认为80')
    args = parser.parse_args()
    
    diagnose_server(args.port)
