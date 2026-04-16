#!/usr/bin/env python3
"""
快速测试诊断脚本 - 找出所有失败的测试及其原因
"""

import subprocess
import re

print("🔍 正在运行所有测试并收集失败信息...")
print("=" * 60)

result = subprocess.run(
    ["python", "-m", "pytest",
     "tests/test_shell_tools.py",
     "tests/test_memory_tools.py",
     "tests/test_rebirth_tools.py",
     "tests/test_search_tools.py",
     "tests/test_code_analysis_tools.py",
     "tests/test_token_manager.py",
     "--tb=line", "-q", "--maxfail=50"],
    capture_output=True, text=True, cwd=r"c:\Users\17533\Desktop\self-evo-baby"
)

output = result.stdout + result.stderr

# 提取失败和错误
lines = output.split('\n')
failures = []
current_test = None

for line in lines:
    if '::' in line and ('PASSED' in line or 'FAILED' in line or 'ERROR' in line):
        if 'FAILED' in line or 'ERROR' in line:
            test_name = re.findall(r'::(.+?)\s', line)
            if test_name:
                failures.append(test_name[0])

print(f"❌ 发现 {len(failures)} 个失败的测试:")
for i, f in enumerate(failures, 1):
    print(f"  {i:3d}. {f}")

print(f"\n📊 测试通过率预估: {max(0, 370 - len(failures))}/370")
print("\n💡 建议：逐个修复这些测试的不匹配问题")
