'''
健康检查工具

提供 Agent 系统健康状态检查功能。
'''

import sys
import os
import platform
from pathlib import Path
from typing import Dict, Any


def check_system_health() -> Dict[str, Any]:
    '''
    检查系统健康状态
    
    Returns:
        包含健康信息的字典
    '''
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'working_directory': str(Path.cwd()),
        'python_path': sys.executable,
        'environment_variables': list(os.environ.keys())[:10],  # 只显示前10个
        'system_health': 'OK'
    }


def check_tools_availability() -> Dict[str, bool]:
    '''
    检查工具模块可用性
    
    Returns:
        工具可用性字典
    '''
    try:
        import requests
        requests_available = True
    except ImportError:
        requests_available = False
    
    try:
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False
    
    return {
        'requests': requests_available,
        'psutil': psutil_available,
        'json': True,
        're': True
    }
