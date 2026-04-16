#!/usr/bin/env python3
"""修复 test_code_analysis_tools.py 中的 diff 格式"""

file_path = r'tests\test_code_analysis_tools.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找并替换所有 *** Begin Patch 块
new_lines = []
in_diff_block = False
diff_started = False
new_diff = []

for i, line in enumerate(lines):
    if '*** Begin Patch' in line:
        diff_started = True
        new_diff = []
        continue
    
    if diff_started and '*** End Patch' in line:
        diff_started = False
        # 将 new_diff 中的内容写入新行
        # new_diff 应该包含 *** Update File: 和 @@ 等行
        # 解析为 SEARCH/REPLACE 格式
        file_line = next((l for l in new_diff if 'Update File' in l), None)
        if file_line:
            filename = file_line.split(':', 1)[1].strip()
            # 找到 - 和 + 行
            old_content = ''
            new_content = ''
            for j, dl in enumerate(new_diff):
                if dl.startswith('- ') and old_content == '':
                    old_content = dl[2:].strip()
                elif dl.startswith('+ ') and new_content == '':
                    new_content = dl[2:].strip()
            
            if old_content and new_content:
                new_lines.append(f'<<<<<<< SEARCH\n{old_content}\n=======\n{new_content}\n>>>>>>> REPLACE\n')
        continue
    
    if diff_started:
        new_diff.append(line)
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed diff blocks')
