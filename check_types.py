#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查MCP类型
"""

from mcp.types import *

print("Available types in mcp.types:")
for name in dir():
    if not name.startswith('__'):
        print(f"- {name}")
