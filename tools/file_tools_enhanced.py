import os
from pathlib import Path
from typing import Optional, Union


def read_local_file(file_path: str, encoding: str = 'auto') -> dict:
    """
    增强版本地文件读取工具，支持自动编码检测和重试
    
    Args:
        file_path: 文件路径
        encoding: 编码方式，'auto' 表示自动检测
    
    Returns:
        dict: 包含 'success', 'content', 'encoding', 'error' 的字典
    """
    result = {
        'success': False,
        'content': None,
        'encoding': None,
        'error': None,
        'file_path': file_path
    }
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            result['error'] = f'File not found: {file_path}'
            return result
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            result['success'] = True
            result['content'] = ''
            result['encoding'] = 'utf-8'
            return result
        
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'latin-1', 'cp1252', 'utf-8-sig']
        
        if encoding != 'auto':
            encodings = [encoding] + encodings
        
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                result['success'] = True
                result['content'] = content
                result['encoding'] = enc
                return result
            except (UnicodeDecodeError, OSError):
                continue
        
        result['error'] = f'Failed to read file with any encoding: {encodings}'
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def list_directory(path: str = '.') -> dict:
    """
    增强版目录列表工具，包含错误处理
    """
    result = {
        'success': False,
        'files': [],
        'directories': [],
        'error': None,
        'path': path
    }
    
    try:
        p = Path(path)
        if not p.exists():
            result['error'] = f'Directory not found: {path}'
            return result
        
        if not p.is_dir():
            result['error'] = f'Path is not a directory: {path}'
            return result
        
        for item in p.iterdir():
            if item.is_file():
                result['files'].append({
                    'name': item.name,
                    'size': item.stat().st_size,
                    'modified': item.stat().st_mtime
                })
            else:
                result['directories'].append({
                    'name': item.name
                })
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result