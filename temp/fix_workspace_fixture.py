#!/usr/bin/env python3
"""
修复 test_memory_tools.py 中的 isolate_memory_workspace fixture

问题：WorkspaceManager 是单例，其 __new__ 不接受参数。
解决方案：使用 monkeypatch 临时替换 get_workspace 返回临时路径的 mock 对象。
"""

import sys
import os
from pathlib import Path

# 读取文件
file_path = r'tests\test_memory_tools.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换整个 fixture
old_fixture = '''@pytest.fixture(autouse=True)
def isolate_memory_workspace(monkeypatch, tmp_path):
    """隔离工作区，避免测试污染真实数据"""
    # 临时修改工作区
    from core.workspace_manager import WorkspaceManager
    
    # 保存原始工作区
    original_ws = getattr(isolate_memory_workspace, '_original_ws', None)
    
    # 创建临时工作区
    temp_ws = tmp_path / "test_workspace"
    temp_ws.mkdir(parents=True)
    
    # 创建必要的子目录
    (temp_ws / "memory").mkdir(exist_ok=True)
    (temp_ws / "archives").mkdir(exist_ok=True)
    (temp_ws / "prompts").mkdir(exist_ok=True)
    
    # 临时替换全局工作区
    from core import workspace_manager
    old_ws = getattr(workspace_manager, '_global_workspace', None)
    workspace_manager._global_workspace = WorkspaceManager(str(temp_ws))
    
    yield temp_ws
    
    # 恢复
    if old_ws is not None:
        workspace_manager._global_workspace = old_ws'''

new_fixture = '''@pytest.fixture(autouse=True)
def isolate_memory_workspace(monkeypatch, tmp_path):
    """隔离工作区，避免测试污染真实数据"""
    # 创建临时工作区
    temp_ws = tmp_path / "test_workspace"
    temp_ws.mkdir(parents=True)
    
    # 创建必要的子目录
    (temp_ws / "memory").mkdir(exist_ok=True)
    (temp_ws / "archives").mkdir(exist_ok=True)
    (temp_ws / "prompts").mkdir(exist_ok=True)
    
    # 创建轻量级 mock 工作区对象
    class MockWorkspace:
        def __init__(self, base_path):
            self.memory_index = Path(base_path) / "memory" / "memory.json"
            self.archives_dir = Path(base_path) / "archives"
            self.prompts_dir = Path(base_path) / "prompts"
            # 确保目录存在
            self.archives_dir.mkdir(parents=True, exist_ok=True)
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        def get_prompt_path(self, name):
            return self.prompts_dir / name
    
    # 替换 get_workspace 函数返回 mock 对象
    from core import workspace_manager
    mock_ws = MockWorkspace(str(temp_ws))
    monkeypatch.setattr(workspace_manager, 'get_workspace', lambda: mock_ws)
    
    yield temp_ws'''

content = content.replace(old_fixture, new_fixture)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed isolate_memory_workspace fixture')
