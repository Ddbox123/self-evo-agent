#!/usr/bin/env python3
"""
任务工具 - 向大模型暴露任务管理能力

提供 set_plan 和 tick_subtask 工具，
并包含重启前的任务完成度强制检查。
"""

from typing import List, Dict, Any, Optional
from core.task_manager import get_task_manager


def set_plan_tool(goal: str, tasks: List[str]) -> str:
    """
    【计划制定工具】设置本轮任务清单

    每次苏醒确定本轮目标后，第一步必须调用此工具将大目标拆解为具体小任务。

    ⚠️ 重要：调用此工具会覆盖之前的任务清单！

    Args:
        goal: 本轮的总目标描述（如 "重构错误重试逻辑"）
        tasks: 子任务列表（3-5个），每个任务描述要具体可执行

    Returns:
        JSON 格式的执行结果，包含任务列表和当前状态

    示例:
        set_plan_tool(
            goal="优化 Agent 的内存管理",
            tasks=[
                "分析当前内存泄漏问题",
                "实现内存监控工具",
                "添加自动清理机制",
                "编写测试验证"
            ]
        )
    """
    result = get_task_manager().set_plan(goal, tasks)
    
    lines = [
        f"[✅ 任务清单已设置]",
        f"",
        f"🎯 目标: {result['goal']}",
        f"",
        f"📋 子任务 ({result['pending_count']} 项):",
    ]
    
    for task in result.get("tasks", []):
        lines.append(f"  ⏳ [ ] {task['id']}. {task['description']}")
    
    lines.append("")
    lines.append("请开始执行，完成后用 tick_subtask 逐个打勾！")
    
    return "\n".join(lines)


def tick_subtask_tool(task_id: int, summary: str) -> str:
    """
    【任务打勾工具】标记任务完成并记录结论

    每完成一个小任务，必须立刻调用此工具打勾。
    你的 System Prompt 会随之动态更新进度。

    Args:
        task_id: 任务编号（从 set_plan 返回的任务列表中获取）
        summary: 该任务完成后的核心结论/成果（一句话总结）

    Returns:
        JSON 格式结果，包含完成进度和剩余任务

    示例:
        tick_subtask_tool(
            task_id=1,
            summary="发现内存泄漏在 memory_tools.py 第 89 行"
        )
    """
    result = get_task_manager().tick_subtask(task_id, summary)
    
    if result["status"] != "success":
        return f"[❌ 错误] {result.get('message', '未知错误')}"
    
    completed = result["completed_count"]
    total = result["total"]
    remaining = result["remaining"]
    all_done = result.get("all_done", False)
    
    lines = [
        f"[✅ 任务 #{task_id} 已完成]",
        f"",
        f"📝 结论: {summary}",
        f"",
        f"📊 进度: {completed}/{total}",
    ]
    
    if all_done:
        lines.extend([
            "",
            "🎉 【全部任务完成！】",
            "你现在可以调用 trigger_self_restart 结束本轮了！",
        ])
    else:
        lines.extend([
            "",
            f"⏳ 还剩 {remaining} 个任务，继续加油！",
        ])
    
    return "\n".join(lines)


def modify_task_tool(task_id: int, new_description: str) -> str:
    """
    【任务修改工具】修改任务描述

    如果发现任务描述不准确或需要调整，可以使用此工具修改。

    Args:
        task_id: 任务编号
        new_description: 新的任务描述

    Returns:
        修改结果
    """
    result = get_task_manager().modify_task(task_id, new_description)
    
    if result["status"] == "success":
        return f"[✅ 任务 #{task_id} 已修改]: {new_description}"
    return f"[❌ 错误] {result.get('message', '未知错误')}"


def add_task_tool(description: str) -> str:
    """
    【任务追加工具】添加新的子任务

    如果执行过程中发现需要新增任务，使用此工具追加。

    Args:
        description: 新任务描述

    Returns:
        添加结果
    """
    result = get_task_manager().add_task(description)
    
    if result["status"] == "success":
        return f"[✅ 新任务已添加] #{result['task_id']}: {description}"
    return f"[❌ 错误] {result.get('message', '未知错误')}"


def remove_task_tool(task_id: int) -> str:
    """
    【任务删除工具】删除不需要的任务

    如果某个任务不再需要，可以删除它。

    Args:
        task_id: 要删除的任务编号

    Returns:
        删除结果
    """
    result = get_task_manager().remove_task(task_id)
    
    if result["status"] == "success":
        return f"[✅ 任务 #{task_id} 已删除]，剩余 {result['remaining']} 个任务"
    return f"[❌ 错误] {result.get('message', '未知错误')}"


def check_restart_block() -> tuple[bool, str]:
    """
    【系统内部】检查是否允许重启

    在调用 trigger_self_restart 之前必须调用此检查。
    如果有未完成的任务，阻止重启并返回错误信息。

    Returns:
        (is_blocked: bool, message: str)
        - is_blocked=True 时，message 包含拦截原因
        - is_blocked=False 时，可以继续执行重启
    """
    tm = get_task_manager()
    
    # 如果没有任何任务，不拦截（允许无任务重启）
    if not tm.subtasks:
        return False, ""
    
    # 检查是否有未完成的任务
    if not tm.is_all_completed:
        pending_tasks = [t for t in tm.subtasks if not t["is_completed"]]
        pending_list = "\n".join([
            f"  ⏳ [ ] {t['id']}. {t['description']}"
            for t in pending_tasks
        ])
        
        message = (
            f"\n"
            f"[系统拦截] 你的任务清单中还有未完成的项目，禁止重启！\n"
            f"\n"
            f"📋 未完成任务 ({len(pending_tasks)} 项):\n"
            f"{pending_list}\n"
            f"\n"
            f"请继续执行剩余任务，或使用 modify_task / remove_task 调整计划。\n"
            f"禁止调用 trigger_self_restart 直到所有任务都打勾！\n"
        )
        return True, message
    
    return False, ""


def get_task_status() -> str:
    """
    【状态查询工具】查看当前任务状态

    Returns:
        当前任务清单的状态摘要
    """
    tm = get_task_manager()
    
    lines = [
        "[任务状态]",
        "",
        f"🎯 目标: {tm.generation_goal or '(未设置)'}",
        f"📊 进度: {tm.completion_rate:.0%}",
    ]
    
    if tm.subtasks:
        completed = sum(1 for t in tm.subtasks if t["is_completed"])
        lines.append(f"📋 任务: {completed}/{len(tm.subtasks)} 完成")
    else:
        lines.append("📋 任务: (空)")
    
    return "\n".join(lines)
