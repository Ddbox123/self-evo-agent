#!/usr/bin/env python3
"""将测试中的 *** Begin Patch 格式替换为 <<<<<<< SEARCH 格式"""

import re

file_path = r'tests\test_code_analysis_tools.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 diff 格式
old_format = r'\*\*\*\s*Begin Patch\s*\n\*\*\*\s*Update File: (.+?)\n@@\s*\n- (.+?)\n\+ (.+?)\n\*\*\*\s*End Patch'
new_format = r'<<<<<<< SEARCH\n\2\n=======\n\3\n>>>>>>> REPLACE'

# 由于有多处，需要循环替换直到没有匹配
prev_content = None
while content != prev_content:
    prev_content = content
    content = re.sub(old_format, new_format, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed diff format in test_code_analysis_tools.py')
