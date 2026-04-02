#!/usr/bin/env python3
"""
层级化记忆模块 - 跨生命周期状态管理

采用"层级记忆"机制：
1. 世代索引 (memory.json) - 保留当前世代号、核心智慧摘要、当前目标
2. 世代档案 (archives/gen_{N}_history.json) - 完整保留每一世代的对话记录和思考过程

存储位置:
- workspace/memory.json - 世代索引
- workspace/memory/archives/ - 世代详细档案

设计原则：详细档案只在 Agent 主动读取时才加载，不增加常规运行的 Token 负担。
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


def _get_workspace_path() -> str:
    """获取工作区域路径"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace = os.path.join(project_root, "workspace")
    os.makedirs(workspace, exist_ok=True)
    return workspace


def _get_archives_path() -> str:
    """获取档案库路径"""
    archives = os.path.join(_get_workspace_path(), "memory", "archives")
    os.makedirs(archives, exist_ok=True)
    return archives


# 文件路径
MEMORY_FILE = os.path.join(_get_workspace_path(), "memory.json")


def _get_default_memory() -> dict:
    """获取默认的记忆结构"""
    return {
        "current_generation": 1,
        "core_wisdom": "初始状态",
        "current_goal": "熟悉环境",
        "total_generations": 1,
        "last_archive_time": None,
    }


def _load_memory() -> dict:
    """从文件加载记忆，文件不存在则初始化"""
    if not os.path.exists(MEMORY_FILE):
        memory = _get_default_memory()
        _save_memory(memory)
        return memory
    
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            memory = json.load(f)
        
        # 迁移旧结构到新结构
        needs_migration = False
        if "generation" in memory and "current_generation" not in memory:
            memory["current_generation"] = memory.pop("generation")
            needs_migration = True
        if "core_context" in memory and "core_wisdom" not in memory:
            memory["core_wisdom"] = memory.pop("core_context")
            needs_migration = True
        if "total_generations" not in memory:
            memory["total_generations"] = memory.get("current_generation", 1)
            needs_migration = True
        
        if needs_migration:
            _save_memory(memory)
        
        return memory
    except (json.JSONDecodeError, IOError):
        memory = _get_default_memory()
        _save_memory(memory)
        return memory


def _save_memory(memory: dict) -> bool:
    """保存记忆到文件"""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def read_memory() -> str:
    """
    读取当前的世代索引（轻量级，不加载详细档案）。
    
    Returns:
        JSON字符串，包含:
        - current_generation: 当前世代
        - core_wisdom: 核心智慧摘要
        - current_goal: 本世代核心目标
        - total_generations: 总世代数
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
    current_gen = memory.get('current_generation', 1)
    total_gens = memory.get('total_generations', 1)
    core_wisdom = memory.get('core_wisdom', '无')
    current_goal = memory.get('current_goal', '待定')
    
    lines = [
        f"【当前世代】: G{current_gen} (共 {total_gens} 代)",
        f"【核心智慧】: {core_wisdom}",
        f"【本世代目标】: {current_goal}",
        f"【档案库】: memory/archives/ (可按需读取)",
    ]
    return "\n".join(lines)


def get_generation() -> int:
    """获取当前世代数"""
    return _load_memory().get("current_generation", 1)


def get_current_goal() -> str:
    """获取当前目标"""
    return _load_memory().get("current_goal", "")


def get_core_context() -> str:
    """获取核心上下文（兼容旧接口）"""
    return _load_memory().get("core_wisdom", "")


def archive_generation_history(
    generation: int,
    history_data: List[Dict[str, Any]],
    core_wisdom: str,
    next_goal: str,
) -> str:
    """
    将当前世代的完整历史记录归档到磁盘。
    
    Args:
        generation: 当前世代编号
        history_data: 包含本轮所有思考、工具调用和结果的列表
        core_wisdom: 提炼的核心智慧（300字以内）
        next_goal: 下一世代的目标
    
    Returns:
        归档结果，包含文件路径
    """
    archives_path = _get_archives_path()
    
    # 构建世代档案
    archive = {
        "generation": generation,
        "archived_at": datetime.now().isoformat(),
        "core_wisdom": core_wisdom,
        "next_goal": next_goal,
        "total_steps": len(history_data),
        "history": history_data,
    }
    
    # 文件名格式: gen_{N}_history.json
    filename = f"gen_{generation}_history.json"
    filepath = os.path.join(archives_path, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(archive, f, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "status": "success",
            "generation": generation,
            "archive_file": filepath,
            "steps_count": len(history_data),
            "message": f"世代 G{generation} 档案已归档至 {filename}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"归档失败: {str(e)}"
        }, ensure_ascii=False)


def read_generation_archive(generation: int) -> str:
    """
    读取指定世代的详细档案。
    
    Args:
        generation: 世代编号
    
    Returns:
        世代档案的JSON字符串
    """
    archives_path = _get_archives_path()
    filename = f"gen_{generation}_history.json"
    filepath = os.path.join(archives_path, filename)
    
    if not os.path.exists(filepath):
        return json.dumps({
            "status": "error",
            "message": f"世代 G{generation} 的档案不存在"
        }, ensure_ascii=False)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            archive = json.load(f)
        return json.dumps(archive, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"读取档案失败: {str(e)}"
        }, ensure_ascii=False)


def list_archives() -> str:
    """
    列出所有可用的世代档案。
    
    Returns:
        档案列表
    """
    archives_path = _get_archives_path()
    
    if not os.path.exists(archives_path):
        return json.dumps({
            "status": "success",
            "archives": [],
            "message": "暂无档案记录"
        }, ensure_ascii=False)
    
    archives = []
    for filename in sorted(os.listdir(archives_path)):
        if filename.startswith("gen_") and filename.endswith("_history.json"):
            filepath = os.path.join(archives_path, filename)
            try:
                stat = os.stat(filepath)
                archives.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except OSError:
                pass
    
    return json.dumps({
        "status": "success",
        "archives": archives,
        "count": len(archives)
    }, ensure_ascii=False)


def commit_compressed_memory(new_core_context: str, next_goal: str) -> str:
    """
    更新记忆索引（世代号递增由 archive_generation_history 处理）。
    
    【极度重要】在调用 trigger_self_restart 之前必须调用此函数！
    会更新 core_wisdom 和 current_goal，世代号由归档操作递增。
    
    Args:
        new_core_context: 压缩后的新上下文摘要（建议不超过300字）
        next_goal: 下一代需要接着做的具体任务
        
    Returns:
        更新后的JSON字符串，包含状态和世代信息
    """
    # 强制截断到300字
    if len(new_core_context) > 300:
        new_core_context = new_core_context[:297] + "..."
    
    memory = _load_memory()
    memory["core_wisdom"] = new_core_context
    memory["current_goal"] = next_goal
    memory["last_archive_time"] = datetime.now().isoformat()
    
    if _save_memory(memory):
        return json.dumps({
            "status": "success",
            "current_generation": memory["current_generation"],
            "total_generations": memory.get("total_generations", 1),
            "core_wisdom": new_core_context,
            "next_goal": next_goal,
            "message": f"记忆索引已更新"
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "error",
            "message": "记忆保存失败，请检查文件权限"
        }, ensure_ascii=False)


def advance_generation() -> int:
    """
    推进到下一世代（内部使用，由归档操作调用）。
    
    Returns:
        新的世代编号
    """
    memory = _load_memory()
    current = memory.get("current_generation", 1)
    memory["current_generation"] = current + 1
    memory["total_generations"] = max(memory.get("total_generations", 1), current + 1)
    _save_memory(memory)
    return current + 1
