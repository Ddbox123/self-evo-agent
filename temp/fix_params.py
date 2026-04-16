#!/usr/bin/env python3
"""
批量修复测试文件中的参数名不匹配问题
"""

import re

file_path = r'tests\test_shell_tools.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 edit_file 的旧参数名为新参数名
content = content.replace('edit_file(file_path=file_path, old_str=', 
                          'edit_file(file_path=file_path, search_string=')
content = content.replace(', new_str=', ', replace_string=')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed edit_file parameter names')
