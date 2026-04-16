#!/usr/bin/env python3
"""合并 agent_core 分片文件"""

parts = []

# 读取所有分片
for i in range(1, 4):
    path = f"C:\\Users\\17533\\Desktop\\self-evo-baby\\core\\agent_core_p{i}.py"
    try:
        with open(path, 'r', encoding='utf-8') as f:
            parts.append(f.read())
        print(f"读取部分 {i} 成功")
    except FileNotFoundError:
        print(f"部分 {i} 不存在，跳过")

# 合并
content = '\n'.join(parts)

# 写入完整文件
output_path = "C:\\Users\\17533\\Desktop\\self-evo-baby\\core\\agent_core.py"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"合并完成：{output_path}")
print(f"总大小：{len(content)} 字节")
