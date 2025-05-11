#!/bin/bash

# 激活虚拟环境
source .venv/bin/activate

# 运行服务器
python server.py $@
