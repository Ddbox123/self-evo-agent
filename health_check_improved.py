import sys
import os
import time
from pathlib import Path


def check_file_readability(file_path: str) -> dict:
    """检查文件可读性并返回详细信息"""
    result = {
        'path': file_path,
        'exists': False,
        'readable': False,
        'size': 0,
        'encoding_issues': False,
        'error': None
    }
    
    try:
        path = Path(file_path)
        result['exists'] = path.exists()
        if not result['exists']:
            result['error'] = 'File does not exist'
            return result
        
        result['size'] = path.stat().st_size
        
        # 尝试多种编码读取
        encodings = ['utf-8', 'gbk', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(100)  # 只读前100字符
                result['readable'] = True
                result['encoding'] = encoding
                break
            except (UnicodeDecodeError, OSError):
                continue
        else:
            result['encoding_issues'] = True
            result['error'] = f'Could not read with any encoding: {encodings}'
            
    except Exception as e:
        result['error'] = str(e)
        
    return result


def run_health_check():
    """运行全面的健康检查"""
    print('=== Agent 健康检查 ===')
    print(f'时间: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    
    # 关键文件检查
    critical_files = [
        'agent.py',
        'config.py',
        'restarter.py',
        'tools/__init__.py',
        'README.md'
    ]
    
    print('\n📁 关键文件检查:')
    for file_path in critical_files:
        result = check_file_readability(file_path)
        status = '✅' if result['readable'] else '❌'
        size_info = f' ({result["size"]} bytes)' if result['size'] > 0 else ''
        print(f'  {status} {file_path}{size_info}')
        if not result['readable']:
            print(f'     错误: {result["error"]}')
    
    # 工具目录检查
    print('\n🔧 工具模块检查:')
    tools_dir = Path('tools')
    if tools_dir.exists() and tools_dir.is_dir():
        tool_files = list(tools_dir.glob('*.py'))
        print(f'  ✅ 工具目录存在，包含 {len(tool_files)} 个 Python 文件')
        
        # 检查 __init__.py 导入
        init_file = tools_dir / '__init__.py'
        if init_file.exists():
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                print('  ✅ tools/__init__.py 可读')
            except Exception as e:
                print(f'  ❌ tools/__init__.py 读取失败: {e}')
    else:
        print('  ❌ 工具目录不存在')
    
    print('\n✅ 健康检查完成')

if __name__ == '__main__':
    run_health_check()