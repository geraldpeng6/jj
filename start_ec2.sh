#!/bin/bash

# EC2服务器启动脚本
# 此脚本用于在EC2服务器上启动MCP服务器，并确保HTML服务器可以通过公网访问

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -h, --help                显示此帮助信息"
    echo "  -t, --transport TRANSPORT 指定传输协议 (stdio, sse, streamable-http) (默认: sse)"
    echo "  -H, --host HOST           指定主机地址 (默认: 0.0.0.0)"
    echo "  -p, --port PORT           指定端口号 (默认: 8000)"
    echo ""
    echo "示例:"
    echo "  $0                        # 使用默认设置启动 (SSE, 0.0.0.0:8000)"
    echo "  $0 -t stdio               # 使用STDIO传输协议启动"
    echo "  $0 -t streamable-http     # 使用Streamable HTTP传输协议启动"
    echo "  $0 -H 127.0.0.1 -p 9000   # 在127.0.0.1:9000上启动"
    exit 0
}

# 默认参数
TRANSPORT="sse"  # 默认使用SSE传输协议
HOST="0.0.0.0"
PORT=8000

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            ;;
        -t|--transport)
            TRANSPORT="$2"
            shift
            shift
            ;;
        -H|--host)
            HOST="$2"
            shift
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            show_help
            ;;
    esac
done

# 检查是否为root用户
check_root() {
    if [ "$(id -u)" != "0" ]; then
        echo -e "${RED}错误: 此脚本需要以root权限运行，以便绑定到端口80${NC}"
        echo -e "${YELLOW}请使用sudo运行此脚本: sudo $0${NC}"
        exit 1
    fi
}

# 检查AWS CLI是否安装
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${YELLOW}AWS CLI未安装，将无法自动检查安全组配置${NC}"
        echo -e "${YELLOW}建议安装AWS CLI: pip install awscli${NC}"
    else
        echo -e "${GREEN}AWS CLI已安装${NC}"
        
        # 检查AWS CLI配置
        if ! aws configure list &> /dev/null; then
            echo -e "${YELLOW}AWS CLI未配置，将无法自动检查安全组配置${NC}"
            echo -e "${YELLOW}建议配置AWS CLI: aws configure${NC}"
        else
            echo -e "${GREEN}AWS CLI已配置${NC}"
        fi
    fi
}

# 检查安全组配置
check_security_group() {
    echo -e "${YELLOW}检查EC2安全组配置...${NC}"
    
    # 获取实例ID
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    if [ -z "$INSTANCE_ID" ]; then
        echo -e "${RED}无法获取实例ID，跳过安全组检查${NC}"
        return
    fi
    
    echo -e "${GREEN}实例ID: $INSTANCE_ID${NC}"
    
    # 获取安全组ID
    SECURITY_GROUPS=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[*].GroupId' --output text 2>/dev/null)
    if [ -z "$SECURITY_GROUPS" ]; then
        echo -e "${RED}无法获取安全组信息，请确保AWS CLI已正确配置${NC}"
        return
    fi
    
    echo -e "${GREEN}安全组: $SECURITY_GROUPS${NC}"
    
    # 检查安全组规则
    HTTP_ALLOWED=false
    HTTPS_ALLOWED=false
    
    for SG_ID in $SECURITY_GROUPS; do
        echo -e "${YELLOW}检查安全组 $SG_ID...${NC}"
        
        # 检查入站规则
        RULES=$(aws ec2 describe-security-groups --group-ids $SG_ID --query 'SecurityGroups[0].IpPermissions[*]' --output json 2>/dev/null)
        
        # 检查是否允许HTTP流量（端口80）
        if echo "$RULES" | grep -q '"FromPort": 80' || echo "$RULES" | grep -q '"ToPort": 80'; then
            HTTP_ALLOWED=true
            echo -e "${GREEN}安全组允许HTTP流量（端口80）${NC}"
        else
            echo -e "${RED}安全组不允许HTTP流量（端口80）${NC}"
            echo -e "${YELLOW}请在AWS控制台中修改安全组设置，添加入站规则允许TCP端口80${NC}"
        fi
        
        # 检查是否允许HTTPS流量（端口443）
        if echo "$RULES" | grep -q '"FromPort": 443' || echo "$RULES" | grep -q '"ToPort": 443'; then
            HTTPS_ALLOWED=true
            echo -e "${GREEN}安全组允许HTTPS流量（端口443）${NC}"
        else
            echo -e "${YELLOW}安全组不允许HTTPS流量（端口443），如需使用HTTPS，请添加入站规则允许TCP端口443${NC}"
        fi
    done
    
    if [ "$HTTP_ALLOWED" = false ]; then
        echo -e "${RED}警告: 安全组不允许HTTP流量（端口80），HTML服务器可能无法通过公网访问${NC}"
    fi
}

# 设置环境变量
setup_env() {
    echo -e "${YELLOW}设置环境变量...${NC}"
    
    # 设置EC2_INSTANCE环境变量，强制识别为EC2环境
    export EC2_INSTANCE=true
    echo -e "${GREEN}已设置EC2_INSTANCE=true${NC}"
    
    # 确保必要的目录存在
    mkdir -p data/logs data/klines data/charts data/temp data/config data/backtest data/templates
    echo -e "${GREEN}已创建必要的目录${NC}"
}

# 启动服务器
start_server() {
    echo -e "${YELLOW}准备启动MCP服务器，使用 $TRANSPORT 传输协议...${NC}"
    
    # 根据传输协议选择不同的启动方式
    if [ "$TRANSPORT" == "stdio" ]; then
        echo -e "${GREEN}启动MCP服务器，使用STDIO传输协议${NC}"
        python server.py --transport stdio
    elif [ "$TRANSPORT" == "sse" ]; then
        echo -e "${GREEN}启动MCP服务器，使用SSE传输协议，地址: http://$HOST:$PORT/sse${NC}"
        python server.py --transport sse --host "$HOST" --port "$PORT"
    elif [ "$TRANSPORT" == "streamable-http" ]; then
        echo -e "${GREEN}启动MCP服务器，使用Streamable HTTP传输协议，地址: http://$HOST:$PORT/mcp${NC}"
        python server.py --transport streamable-http --host "$HOST" --port "$PORT"
    fi
}

# 主函数
main() {
    echo -e "${GREEN}===== EC2服务器启动脚本 =====${NC}"
    
    # 检查root权限
    check_root
    
    # 检查AWS CLI
    check_aws_cli
    
    # 检查安全组配置
    check_security_group
    
    # 设置环境变量
    setup_env
    
    # 启动服务器
    start_server
}

# 执行主函数
main
