import sys
import os
import platform

print('=== 环境诊断 ===')
print(f'Python 版本: {sys.version}')
print(f'平台: {platform.platform()}')
print(f'系统: {platform.system()}')
print(f'架构: {platform.architecture()}')
print(f'当前工作目录: {os.getcwd()}')

# 检查关键模块
modules_to_check = ['os', 'sys', 'pathlib', 'json', 're']
for module in modules_to_check:
    try:
        __import__(module)
        print(f'✓ {module} 可用')
    except ImportError as e:
        print(f'✗ {module} 不可用: {e}')

print('\n=== 文件系统测试 ===')
try:
    with open('test_read.txt', 'w', encoding='utf-8') as f:
        f.write('test content')
    print('✓ 文件写入测试成功')
    
    with open('test_read.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'✓ 文件读取测试成功: {content}')
    
    os.remove('test_read.txt')
except Exception as e:
    print(f'✗ 文件系统测试失败: {e}')