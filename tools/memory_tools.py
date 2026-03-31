#!/usr/bin/env python3
"""
高密度压缩记忆模块 - 跨生命周期状态管理

采用"记忆坍缩"机制：每次重启前将经验压缩为不超过300字的极简摘要，
覆盖旧记忆，确保Token消耗可控。

存储位置: memory.json
"""

import json
import os
from typing import Optional


MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "memory.json"
)


def _get_default_memory() -> dict:
    """获取默认的记忆结构"""
    return {
        "generation": 1,
        "core_context": "初始状态",
        "current_goal": "熟悉环境",
    }


def _load_memory() -> dict:
    """从文件加载记忆，文件不存在则初始化"""
    if not os.path.exists(MEMORY_FILE):
        memory = _get_default_memory()
        _save_memory(memory)
        return memory
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        memory = _get_default_memory()
        _save_memory(memory)
        return memory


def _save_memory(memory: dict) -> bool:
    """保存记忆到文件（覆盖式）"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def read_memory() -> str:
    """
    读取当前的压缩记忆。
    
    采用覆盖式存储，只保留最新、最核心的上下文。
    
    Returns:
        JSON字符串，包含:
        - generation: 当前世代
        - core_context: 提炼后的历史上下文
        - current_goal: 本世代核心目标
        
    Example:
        >>> read_memory()
        '{"generation": 3, "core_context": "...", "current_goal": "..."}'
    """
    memory = _load_memory()
    return json.dumps(memory, ensure_ascii=False, indent=2)


def get_memory_summary() -> str:
    """
    获取人类可读的记忆摘要，用于注入到Prompt中。
    
    Returns:
        格式化的记忆字符串
    """
    memory = _load_memory()
    lines = [
        f"【当前世代】: G{memory.get('generation', 1)}",
        f"【提炼后的历史上下文】: {memory.get('core_context', '无')}",
        f"【本世代核心目标】: {memory.get('current_goal', '待定')}",
    ]
    return "\n".join(lines)


def commit_compressed_memory(new_core_context: str, next_goal: str) -> str:
    """
    覆盖式更新记忆（记忆坍缩）。
    
    【极度重要】在调用 trigger_self_restart 之前必须调用此函数！
    会覆盖旧的core_context，用高度凝练的新摘要替换，同时更新世代和目标。
    
    Args:
        new_core_context: 压缩后的新上下文摘要（建议不超过300字）
        next_goal: 下一代需要接着做的具体任务
        
    Returns:
        更新后的JSON字符串，包含状态和新的generation
        
    Example:
        >>> commit_compressed_memory(
        ...     "修复了datetime模块冲突，核心逻辑在agent.py",
        ...     "继续优化错误处理流程"
        ... )
    """
    # 强制截断到300字
    if len(new_core_context) > 300:
        new_core_context = new_core_context[:297] + "..."
    
    memory = _load_memory()
    memory["generation"] = memory.get("generation", 0) + 1
    memory["core_context"] = new_core_context
    memory["current_goal"] = next_goal
    
    if _save_memory(memory):
        return json.dumps({
            "status": "success",
            "generation": memory["generation"],
            "core_context": new_core_context,
            "next_goal": next_goal,
            "message": f"记忆坍缩完成，当前世代: G{memory['generation']}"
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "error",
            "message": "记忆保存失败，请检查文件权限"
        }, ensure_ascii=False)


def get_generation() -> int:
    """获取当前世代数"""
    return _load_memory().get("generation", 1)


def get_current_goal() -> str:
    """获取当前目标"""
    return _load_memory().get("current_goal", "")


def get_core_context() -> str:
    """获取核心上下文"""
    return _load_memory().get("core_context", "")
