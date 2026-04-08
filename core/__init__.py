"""
core - 核心模块包
"""

from core.prompt_builder import build_system_prompt, build_simple_system_prompt
from core.workspace_manager import get_workspace, workspace_root, workspace_db

__all__ = [
    'build_system_prompt',
    'build_simple_system_prompt',
    'get_workspace',
    'workspace_root',
    'workspace_db',
]
