#!/usr/bin/env python3
"""Fix test_tool_executor.py parameter names"""

path = r"C:\Users\17533\Desktop\self-evo-baby\tests\test_tool_executor.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences
content = content.replace('"directory": str(', '"path": str(')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] Fixed parameter names in test_tool_executor.py")
