#!/usr/bin/env python3
"""
层级化记忆模块 - 跨生命周期状态管理

采用"层级记忆"机制：
1. 世代索引 (memory.json) - 保留当前世代号、核心智慧摘要、当前目标
2. 世代档案 (archives/gen_{N}_history.json) - 完整保留每一世代的对话记录和思考过程

存储位置 (统一在 workspace/ 下):
- workspace/memory/memory.json - 世代索引
- workspace/memory/archives/ - 世代详细档案
- workspace/prompts/DYNAMIC.md - 动态提示词

设计原则：详细档案只在 Agent 主动读取时才加载，不增加常规运行的 Token 负担。
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# 导入统一工作区管理器
from core.workspace_manager import get_workspace


def _get_memory_index_path() -> str:
    """获取记忆索引文件路径"""
    ws = get_workspace()
    return str(ws.memory_index)


def _get_archives_path() -> str:
    """获取档案库路径"""
    ws = get_workspace()
    archives = ws.archives_dir
    archives.mkdir(parents=True, exist_ok=True)
    return str(archives)


def _get_dynamic_prompt_path() -> str:
    """获取动态提示词文件路径"""
    ws = get_workspace()
    return str(ws.get_prompt_path("DYNAMIC.md"))


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
    memory_file = _get_memory_index_path()
    if not os.path.exists(memory_file):
        memory = _get_default_memory()
        _save_memory(memory)
        return memory

    try:
        with open(memory_file, 'r', encoding='utf-8') as f:
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
    import logging
    logger = logging.getLogger(__name__)

    memory_file = _get_memory_index_path()
    try:
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        logger.info(f"[记忆保存] 成功: {memory_file}")
        return True
    except IOError as e:
        logger.error(f"[ERROR] 记忆保存失败 (IOError): {e}")
        return False
    except TypeError as e:
        logger.error(f"[ERROR] 记忆保存失败 (序列化错误): {e}")
        return False
    except Exception as e:
        logger.error(f"[ERROR] 记忆保存失败 (未知错误): {e}")
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


def force_save_current_state(core_wisdom: str = "", next_goal: str = "", generation: int = None) -> str:
    """
    【强制记忆快照】在重启前自动调用，确保记忆被保存。

    此函数作为最后一道防线，确保即使 Agent 没有主动调用 commit_compressed_memory，
    在触发重启时系统也会自动保存当前状态。

    Args:
        core_wisdom: 核心智慧摘要（可选，如果为空则保留原有值）
        next_goal: 下一世代目标（可选，如果为空则保留原有值）
        generation: 当前世代（可选，如果为空则读取原有值）

    Returns:
        保存结果
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        memory = _load_memory()

        # 如果没有提供新值，保留原有值
        if not core_wisdom:
            core_wisdom = memory.get("core_wisdom", "无")
        if not next_goal:
            next_goal = memory.get("current_goal", "待定")
        if generation is None:
            generation = memory.get("current_generation", 1)

        # 强制截断
        if len(core_wisdom) > 300:
            core_wisdom = core_wisdom[:297] + "..."

        # 更新记忆
        memory["core_wisdom"] = core_wisdom
        memory["current_goal"] = next_goal
        memory["current_generation"] = generation
        memory["last_archive_time"] = datetime.now().isoformat()

        if _save_memory(memory):
            logger.warning(f"[强制快照] 记忆已保存: G{generation}")
            return json.dumps({
                "status": "success",
                "message": f"强制记忆快照完成: G{generation}",
                "core_wisdom": core_wisdom,
                "next_goal": next_goal
            }, ensure_ascii=False)
        else:
            logger.error("[ERROR] 强制记忆快照失败")
            return json.dumps({
                "status": "error",
                "message": "强制记忆快照失败"
            }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"[ERROR] 强制记忆快照异常: {e}")
        return json.dumps({
            "status": "error",
            "message": f"强制记忆快照异常: {str(e)}"
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


# ============================================================================
# 动态提示词管理
# ============================================================================

def read_dynamic_prompt() -> str:
    """
    读取当前的动态提示词内容。
    
    Returns:
        动态提示词的原始文本
    """
    try:
        if os.path.exists(_get_dynamic_prompt_path()):
            with open(_get_dynamic_prompt_path(), 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception as e:
        return f"[错误: 无法读取动态提示词: {e}]"


def update_generation_task(task: str) -> str:
    """
    更新当前世代的任务到动态提示词区域。
    
    模型在每个世代开始时调用此函数，将自己制定的任务写入系统提示词。
    该任务在整个世代中有效，直到下个世代重新生成。
    
    Args:
        task: 当前世代的任务描述（建议使用 Markdown 格式）
        
    Returns:
        更新结果
    """
    try:
        current_gen = _load_memory().get("current_generation", 1)
        
        # 读取现有内容
        if os.path.exists(_get_dynamic_prompt_path()):
            with open(_get_dynamic_prompt_path(), 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = "# 动态提示词区域\n\n*此区域由模型在每个世代开始时动态生成*\n\n---\n\n"
        
        # 提取累积的洞察（保留世代积累的智慧）
        insights = ""
        if "## 积累的洞察" in existing_content:
            import re
            match = re.search(r"(## 积累的洞察.*)", existing_content, re.DOTALL)
            if match:
                insights = match.group(1).strip()
        
        # 构建新内容
        new_content = f"""# 动态提示词区域

*此区域由模型在每个世代开始时动态生成，会自动加载到系统提示词中。*

---

## G{current_gen} 世代任务

{task}
"""
        
        # 如果有累积洞察，添加回去
        if insights:
            new_content += f"\n---\n\n{insights}\n"
        
        # 写入文件
        with open(_get_dynamic_prompt_path(), 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return json.dumps({
            "status": "success",
            "message": f"G{current_gen} 世代任务已更新",
            "generation": current_gen,
            "task_preview": task[:100] + "..." if len(task) > 100 else task,
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"更新世代任务失败: {str(e)}"
        }, ensure_ascii=False)


def add_insight_to_dynamic(insight: str) -> str:
    """
    将洞察追加到动态提示词的积累区域。
    
    模型可以在进化过程中随时追加洞察，这些洞察会跨世代保留。
    
    Args:
        insight: 要追加的洞察内容
        
    Returns:
        更新结果
    """
    try:
        current_gen = _load_memory().get("current_generation", 1)
        
        # 读取现有内容
        if os.path.exists(_get_dynamic_prompt_path()):
            with open(_get_dynamic_prompt_path(), 'r', encoding='utf-8') as f:
                existing_content = f.read()
        else:
            existing_content = ""
        
        # 检查是否有积累洞察区域
        if "## 积累的洞察" in existing_content:
            # 追加到现有洞察
            import re
            # 在洞察区域追加新内容
            pattern = r"(## 积累的洞察\n\n)"
            replacement = rf"\1**G{current_gen}**: {insight}\n\n"
            updated_content = re.sub(pattern, replacement, existing_content)
        else:
            # 创建新的洞察区域
            if existing_content.strip():
                updated_content = existing_content.rstrip() + f"\n\n---\n\n## 积累的洞察\n\n**G{current_gen}**: {insight}\n"
            else:
                updated_content = f"""# 动态提示词区域

*此区域由模型在每个世代开始时动态生成*\n\n---\n\n## 积累的洞察\n\n**G{current_gen}**: {insight}\n"""
        
        # 写入文件
        with open(_get_dynamic_prompt_path(), 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return json.dumps({
            "status": "success",
            "message": "洞察已追加到动态提示词",
            "generation": current_gen,
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"追加洞察失败: {str(e)}"
        }, ensure_ascii=False)


def clear_generation_task() -> str:
    """
    清除世代任务区域，为下一世代做准备。
    
    在重启时调用，保留积累的洞察，但清除任务区域。
    
    Returns:
        操作结果
    """
    try:
        if not os.path.exists(_get_dynamic_prompt_path()):
            return "无需清除（DYNAMIC.md 不存在）"
        
        with open(_get_dynamic_prompt_path(), 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # 提取累积的洞察（保留）
        insights = ""
        if "## 积累的洞察" in existing_content:
            import re
            match = re.search(r"(## 积累的洞察.*)", existing_content, re.DOTALL)
            if match:
                insights = match.group(1).strip()
        
        next_gen = _load_memory().get("current_generation", 1) + 1
        
        # 构建新内容（只保留洞察，清除任务）
        if insights:
            new_content = f"""# 动态提示词区域

*此区域由模型在每个世代开始时动态生成*\n\n---\n\n## G{next_gen} 世代任务

<!-- 模型将在此区域生成当前世代的任务 -->\n\n---\n\n{insights}\n"""
        else:
            new_content = f"""# 动态提示词区域

*此区域由模型在每个世代开始时动态生成*\n\n---\n\n## G{next_gen} 世代任务

<!-- 模型将在此区域生成当前世代的任务 -->\n"""
        
        with open(_get_dynamic_prompt_path(), 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"G{next_gen} 世代任务区域已准备"
        
    except Exception as e:
        return f"清除任务区域失败: {str(e)}"


# 保持向后兼容
update_dynamic_prompt = update_generation_task


# ==================== 代码库认知地图工具 ====================

def record_codebase_insight(module_path: str, insight: str) -> str:
    """
    刻印代码库认知到数据库

    当 Agent 分析完某个代码模块后，调用此工具将结论刻入数据库，
    供下一代 Agent 继承。

    Args:
        module_path: 模块路径，如 'tools/ast_tools.py' 或 '整体架构'
        insight: 该模块的核心作用、已知问题或最佳调用方式

    Returns:
        操作结果
    """
    try:
        from core.workspace_manager import get_workspace
        from tools.memory_tools import get_generation

        ws = get_workspace()
        current_gen = get_generation()

        success = ws.record_codebase_insight(module_path, insight, current_gen)

        if success:
            return f"✅ 已刻印到数据库: [{module_path}] G{current_gen}\n\n认知摘要: {insight[:100]}..."
        else:
            return f"❌ 刻印失败: {module_path}"

    except Exception as e:
        return f"❌ 刻印异常: {str(e)}"


def get_global_codebase_map() -> str:
    """
    获取全局代码库认知地图

    查询数据库中所有模块的认知摘要，拼接成一段 Markdown 文本，
    供 Agent 在制定计划前阅读。

    Returns:
        Markdown 格式的认知地图
    """
    try:
        from core.workspace_manager import get_workspace

        ws = get_workspace()
        return ws.generate_codebase_map()

    except Exception as e:
        return f"[警告] 获取认知地图失败: {str(e)}"
