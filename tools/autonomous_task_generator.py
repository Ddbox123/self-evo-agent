#!/usr/bin/env python3
"""
自主任务生成器 - Agent 的任务发动机

功能：
- 分析当前代码库状态，识别改进空间
- 回顾历史进化经验，继承智慧
- 生成能提升 Agent 能力的自主任务
- 避免重复和低效任务
"""

import os
import json
import datetime
from typing import List, Dict, Optional
from langchain_core.tools import tool

# 尝试导入，如果失败则提供空实现
try:
    from .memory_tools import get_generation, get_current_goal, list_archives, read_generation_archive
except ImportError:
    # 空实现用于静态检查
    def get_generation(): return 1
    def get_current_goal(): return ""
    def list_archives(): return "[]"
    def read_generation_archive(n): return "{}"


# 任务类型优先级（越高越优先）
TASK_PRIORITIES = {
    "critical_fix": 100,      # 关键bug修复
    "performance": 90,         # 性能优化
    "new_capability": 80,     # 新功能
    "code_quality": 70,       # 代码质量
    "testing": 60,            # 测试完善
    "documentation": 50,     # 文档
    "refactor": 40,           # 重构
    "exploration": 30,        # 探索学习
}


def _get_project_root() -> str:
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _scan_codebase_quality() -> Dict:
    """扫描代码库质量"""
    root = _get_project_root()
    issues = []
    suggestions = []

    # 检查关键文件是否存在
    key_files = ["agent.py", "restarter.py", "config.py"]
    prompts_key_files = ["SOUL.md", "AGENTS.md", "IDENTITY.md"]
    for f in key_files:
        path = os.path.join(root, f)
        if not os.path.exists(path):
            issues.append(f"缺少关键文件: {f}")
    for f in prompts_key_files:
        path = os.path.join(root, "prompts", f)
        if not os.path.exists(path):
            issues.append(f"缺少提示文件: prompts/{f}")

    # 检查 tools 目录
    tools_dir = os.path.join(root, "tools")
    if os.path.exists(tools_dir):
        tool_files = [f for f in os.listdir(tools_dir) if f.endswith(".py") and not f.startswith("_")]
        if len(tool_files) < 5:
            suggestions.append(f"tools/ 目录只有 {len(tool_files)} 个工具，考虑增加更多工具")

    # 检查测试目录
    tests_dir = os.path.join(root, "tests")
    if os.path.exists(tests_dir):
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        if len(test_files) < 3:
            suggestions.append(f"tests/ 目录只有 {len(test_files)} 个测试文件，需要补充")

    return {
        "issues": issues,
        "suggestions": suggestions,
        "tool_count": len(tool_files) if os.path.exists(tools_dir) else 0,
        "test_count": len(test_files) if os.path.exists(tests_dir) else 0,
    }


def _analyze_history_for_patterns() -> Dict:
    """分析历史进化，寻找模式"""
    root = _get_project_root()
    archives_dir = os.path.join(root, "workspace", "memory", "archives")

    patterns = {
        "total_archived": 0,
        "common_improvements": [],
        "last_goals": [],
    }

    if not os.path.exists(archives_dir):
        return patterns

    archives = list_archives()
    try:
        archive_list = json.loads(archives).get("archives", [])
        patterns["total_archived"] = len(archive_list)

        # 获取最近3个归档的目标
        for arch in archive_list[-3:]:
            gen = arch.get("generation", 0)
            content = read_generation_archive(gen)
            try:
                data = json.loads(content)
                if "next_goal" in data:
                    patterns["last_goals"].append(data["next_goal"])
            except:
                pass
    except:
        pass

    return patterns


def _get_capability_gaps() -> List[Dict]:
    """识别能力差距"""
    gaps = []

    # 基于现有工具推断能力
    gaps.append({
        "type": "capability",
        "name": "错误处理增强",
        "description": "Agent 缺乏健壮的错误处理和恢复机制",
        "priority": 80,
    })

    gaps.append({
        "type": "capability",
        "name": "自我监控",
        "description": "Agent 缺乏自我监控指标和健康检查",
        "priority": 70,
    })

    return gaps


def _generate_self_improvement_tasks() -> List[Dict]:
    """生成自我改进任务"""
    tasks = []

    # 代码质量任务
    tasks.append({
        "type": "code_quality",
        "title": "增强错误处理",
        "description": "在 agent.py 中添加全局异常处理和降级策略，确保任何异常都不会导致静默失败",
        "action": "read agent.py, identify potential failure points, add try-except blocks with proper logging",
        "priority": 90,
    })

    tasks.append({
        "type": "performance",
        "title": "优化记忆压缩",
        "description": "检查 tools/memory_tools.py 中的压缩逻辑，确保上下文始终保持在合理大小",
        "action": "read tools/memory_tools.py, optimize compression algorithm if needed",
        "priority": 85,
    })

    tasks.append({
        "type": "testing",
        "title": "补充测试覆盖",
        "description": "检查 tests/ 目录，为核心工具添加缺失的测试用例",
        "action": "list_dir tests/, identify untested tools, add test files",
        "priority": 75,
    })

    tasks.append({
        "type": "capability",
        "title": "添加健康检查工具",
        "description": "创建一个 self_check 工具，定期检查 Agent 状态、内存使用、对话质量等",
        "action": "create tools/self_check.py with health monitoring capabilities",
        "priority": 80,
    })

    tasks.append({
        "type": "documentation",
        "title": "更新系统文档",
        "description": "检查 docs/ 目录，更新 README 和架构文档，反映最新变更",
        "action": "list_dir docs/, update any outdated documentation",
        "priority": 40,
    })

    return tasks


@tool
def generate_autonomous_task() -> str:
    """
    【自主任务生成器】无需外部输入，自主分析并生成下一个任务。

    此工具用于：
    - 首次苏醒无外部任务时
    - 任务完成后自动生成下一个任务
    - 持续推动 Agent 自我进化

    Returns:
        JSON 格式的任务描述，包含任务类型、目标、行动建议和优先级
    """
    generation = get_generation()

    # 1. 扫描代码库质量
    quality = _scan_codebase_quality()

    # 2. 分析历史模式
    history = _analyze_history_for_patterns()

    # 3. 识别能力差距
    gaps = _get_capability_gaps()

    # 4. 生成任务候选
    candidates = _generate_self_improvement_tasks()

    # 5. 基于当前状态选择最佳任务
    # 优先选择：低测试覆盖 > 能力差距 > 代码质量 > 性能

    selected_task = None
    if quality["test_count"] < 5:
        # 测试覆盖率低，优先补测试
        for t in candidates:
            if t["type"] == "testing":
                selected_task = t
                break

    if not selected_task:
        # 选择优先级最高的任务
        candidates.sort(key=lambda x: x["priority"], reverse=True)
        selected_task = candidates[0]

    # 构建响应
    response = {
        "status": "success",
        "generation": generation,
        "analysis": {
            "codebase_issues": quality["issues"],
            "codebase_suggestions": quality["suggestions"],
            "total_archived_generations": history["total_archived"],
            "last_goals": history["last_goals"][-3:] if history["last_goals"] else [],
            "capability_gaps": len(gaps),
        },
        "task": {
            "type": selected_task["type"],
            "title": selected_task["title"],
            "description": selected_task["description"],
            "suggested_action": selected_task["action"],
            "priority": selected_task["priority"],
        },
        "timestamp": datetime.datetime.now().isoformat(),
        "message": f"G{generation} 自主任务已生成：{selected_task['title']}"
    }

    return json.dumps(response, ensure_ascii=False, indent=2)


def get_autonomous_task_sync() -> str:
    """同步版本，用于直接调用"""
    return generate_autonomous_task.invoke({})
