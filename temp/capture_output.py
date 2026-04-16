#!/usr/bin/env python3
"""捕获实际返回值以修复测试断言"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.shell_tools import run_batch

# 测试 run_batch 返回值
result = run_batch(commands=["echo Command1", "pwd", "dir"])
print("=== run_batch result ===")
print(repr(result))
print("Contains 'Command1'?", "Command1" in result)

# 测试空列表
result2 = run_batch(commands=[])
print("\n=== run_batch empty ===")
print(repr(result2))
