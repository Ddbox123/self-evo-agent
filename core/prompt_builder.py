"""
core/prompt_builder.py - 动态系统提示词组装器

从 prompts/ 目录读取 Markdown 文件，动态组装系统提示词。
支持模板变量替换和 docs/tools_manual.md 索引注入。
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any


# Prompt 文件路径
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
SOUL_FILE = os.path.join(PROMPTS_DIR, "SOUL.md")
IDENTITY_FILE = os.path.join(PROMPTS_DIR, "IDENTITY.md")
AGENTS_FILE = os.path.join(PROMPTS_DIR, "AGENTS.md")
USER_FILE = os.path.join(PROMPTS_DIR, "USER.md")
TOOLS_MANUAL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "tools_manual.md")


def _load_prompt_file(file_path: str) -> str:
    """加载单个 Prompt 文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"[警告: 找不到 {file_path}]"
    except Exception as e:
        return f"[错误: 无法读取 {file_path}: {e}]"


def _extract_tools_manual_index() -> str:
    """从 tools_manual.md 提取精简索引"""
    try:
        if not os.path.exists(TOOLS_MANUAL):
            return ""

        with open(TOOLS_MANUAL, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取工具列表部分（简化版）
        lines = content.split("\n")
        index_lines = ["\n## 工具手册索引 (docs/tools_manual.md)", ""]

        for line in lines:
            # 提取工具名称（格式：| `tool_name` |）
            if "`" in line and "|" in line:
                parts = line.split("`")
                if len(parts) >= 2:
                    tool_name = parts[1].strip()
                    if tool_name and not tool_name.startswith("#"):
                        index_lines.append(f"- `{tool_name}`")

        return "\n".join(index_lines[:20])  # 最多显示 20 个工具

    except Exception:
        return ""


def _load_memory_context() -> Dict[str, Any]:
    """加载记忆上下文"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from tools.memory_tools import read_memory

        memory = read_memory()
        return {
            "generation": memory.get("generation", 1),
            "total_generations": memory.get("total_generations", 1),
            "core_context": memory.get("core_context", ""),
            "current_goal": memory.get("current_goal", ""),
        }
    except Exception as e:
        return {
            "generation": 1,
            "total_generations": 1,
            "core_context": "",
            "current_goal": "",
            "error": str(e),
        }


def build_system_prompt(
    generation: Optional[int] = None,
    total_generations: Optional[int] = None,
    core_context: Optional[str] = None,
    current_goal: Optional[str] = None,
) -> str:
    """
    构建动态系统提示词。

    Args:
        generation: 当前世代数
        total_generations: 总世代数
        core_context: 跨代核心记忆
        current_goal: 本世代目标

    Returns:
        组装完成的系统提示词字符串
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 如果没有传入记忆，则从 memory_tools 加载
    if generation is None:
        memory_data = _load_memory_context()
        generation = memory_data.get("generation", 1)
        total_generations = memory_data.get("total_generations", 1)
        core_context = memory_data.get("core_context", "")
        current_goal = memory_data.get("current_goal", "")

    # 加载各模块 Prompt
    soul = _load_prompt_file(SOUL_FILE)
    identity = _load_prompt_file(IDENTITY_FILE)
    agents = _load_prompt_file(AGENTS_FILE)
    user = _load_prompt_file(USER_FILE)
    tools_index = _extract_tools_manual_index()

    # 组装完整提示词
    prompt_parts = [
        soul,
        "\n---\n",
        identity,
        "\n---\n",
        agents,
        "\n---\n",
        user,
    ]

    # 添加记忆上下文
    if core_context or current_goal:
        memory_section = [
            "\n---\n",
            "## 你的记忆与状态\n",
            f"- 当前世代: G{generation}（共{total_generations}代）\n",
        ]
        if core_context:
            memory_section.append(f"- 核心智慧摘要: {core_context}\n")
        if current_goal:
            memory_section.append(f"- 本世代核心目标: {current_goal}\n")
        prompt_parts.extend(memory_section)

    # 添加工具手册索引
    if tools_index:
        prompt_parts.append("\n---\n")
        prompt_parts.append(tools_index)

    # 添加环境信息
    env_section = [
        "\n---\n",
        "## 当前环境\n",
        f"- 当前时间: {current_time}\n",
        f"- 项目根目录: {project_root}\n",
    ]
    prompt_parts.extend(env_section)

    # 拼接并返回
    return "".join(prompt_parts)


def build_simple_system_prompt() -> str:
    """
    简化版系统提示词（不加载记忆，仅用于初始化）。
    用于 Agent 启动时快速生成提示词。
    """
    return build_system_prompt(
        generation=1,
        total_generations=1,
        core_context="",
        current_goal="",
    )


if __name__ == "__main__":
    # 测试用
    print(build_system_prompt())
