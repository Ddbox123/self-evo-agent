#!/usr/bin/env python3
"""
自我进化 Agent - 主入口文件

该项目实现了一个能够自我进化的 AI Agent，具备以下核心能力：
1. 通过网络搜索获取新知识
2. 读取和修改自己的源代码
3. 语法自检确保代码质量
4. 通过独立守护进程实现自我重启

基于 LangChain 框架构建，使用 ReAct 风格的 Agent 架构。

架构说明：
- Agent 运行主逻辑循环
- 需要重启时，通过脱离父进程的方式唤起 restarter.py
- Agent 自我了结后，restarter.py 等待原进程死亡，重新拉起新 Agent 进程

配置说明：
- 所有配置参数统一存放在 config.py 中
- 支持从 config.toml 文件、环境变量、命令行参数加载配置
- 修改 config.py 或 config.toml 即可调整 Agent 行为
"""

import os
import sys
import datetime
import time
import logging
from datetime import datetime
from typing import Optional, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入项目配置和日志模块
from config import Config, get_config
import logging_config

# LangChain 核心组件
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# 导入项目工具
from tools.web_tools import web_search, read_webpage
from tools.cmd_tools import (
    run_cmd, run_powershell, run_batch,
    read_file, list_dir,
    edit_local_file, create_new_file,
    check_syntax, backup_project,
    list_symbols_in_file,
    run_self_test, get_agent_status,
    delete_file, cleanup_test_files,
)
from tools.rebirth_tools import trigger_self_restart
# 高性能压缩工具（暂时禁用 - Python 3.14 兼容性问题）
from tools.advanced_compress_tool import advanced_compress_context_tool
from tools.memory_tools import (
    read_memory, commit_compressed_memory, get_generation,
    get_core_context, get_current_goal, archive_generation_history,
    read_generation_archive, list_archives, advance_generation, _load_memory
)
from tools.evolution_tracker import (
    log_evolution,
    get_evolution_history,
    get_evolution_stats,
)

# 全局搜索和 Diff 编辑工具 (Cursor/Aider 范式)
from tools.search_tools import grep_search, find_function_calls, find_definitions, search_imports, search_and_read
from tools.code_tools import apply_diff_edit, validate_diff_format
from tools.ast_tools import get_code_entity, list_file_entities
from tools.memory_cleanup import compress_message_history, filter_exploration_messages, cleanup_after_success
from tools.autonomous_task_generator import generate_autonomous_task
from tools.state_broadcaster import (
    StateBroadcaster, AgentStatus, get_broadcaster,
    update_agent_status, log_agent_event, get_agent_state
)


# ============================================================================
# 调试日志系统 - 统一管理 Agent 运行时的终端输出
# ============================================================================

import traceback
import threading

class DebugLogger:
    """
    统一调试日志系统

    特性：
    - 带时间戳的格式化输出
    - 分类标签便于识别
    - 错误时自动附带上下文和堆栈
    - 线程安全
    - 可控制详细程度
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.verbose = True  # 详细模式
        self.show_timestamps = True  # 显示时间戳
        self._indent_level = 0
        self._indent_char = "  "

    def _timestamp(self) -> str:
        """获取带毫秒的时间戳"""
        now = datetime.now()
        return now.strftime("%H:%M:%S.%f")[:-3]

    def _indent(self) -> str:
        """获取当前缩进"""
        return self._indent_char * self._indent_level

    def _format(self, tag: str, msg: str, color_tag: str = "") -> str:
        """格式化日志消息"""
        parts = []
        if self.show_timestamps:
            parts.append(f"[{self._timestamp()}]")
        parts.append(f"[{tag}]")
        if color_tag:
            parts.append(f"<{color_tag}>")
        parts.append(f"{self._indent()}{msg}")
        return " ".join(parts)

    def debug(self, msg: str, tag: str = "DEBUG"):
        """调试信息"""
        if self.verbose:
            print(self._format(tag, msg, "dim"))

    def info(self, msg: str, tag: str = "INFO"):
        """一般信息"""
        print(self._format(tag, msg))

    def success(self, msg: str, tag: str = "OK"):
        """成功信息"""
        print(self._format(tag, f"✓ {msg}", "green"))

    def warning(self, msg: str, tag: str = "WARN"):
        """警告信息"""
        print(self._format(tag, f"⚠ {msg}", "yellow"))

    def error(self, msg: str, tag: str = "ERROR", exc_info: bool = False):
        """
        错误信息（自动包含详细上下文）

        Args:
            msg: 错误消息
            tag: 标签
            exc_info: 是否包含异常堆栈
        """
        print(self._format(tag, f"✗ {msg}", "red"))
        if exc_info:
            tb = traceback.format_exc()
            for line in tb.strip().split('\n'):
                print(f"    {line}")

    def system(self, msg: str, tag: str = "SYS"):
        """系统信息"""
        print(self._format(tag, f"◆ {msg}", "cyan"))

    def tool(self, name: str, status: str, details: str = ""):
        """
        工具执行日志

        Args:
            name: 工具名称
            status: 执行状态 (called/success/error/timeout)
            details: 详细信息
        """
        status_symbols = {
            "called": "→",
            "success": "✓",
            "error": "✗",
            "timeout": "⏱",
            "skipped": "○"
        }
        sym = status_symbols.get(status, "?")
        msg = f"Tool: {name} {sym}"
        if details:
            msg += f" | {details}"
        print(self._format("TOOL", msg))

    def llm(self, msg: str, details: str = ""):
        """
        LLM 调用日志

        Args:
            msg: 消息
            details: 详细信息（如 token 用量）
        """
        display = msg[:80] + "..." if len(msg) > 80 else msg
        print(self._format("LLM", display))
        if details:
            print(self._format("LLM", f"  └─ {details}"))

    def indent(self):
        """增加缩进"""
        self._indent_level += 1

    def dedent(self):
        """减少缩进"""
        self._indent_level = max(0, self._indent_level - 1)

    def section(self, title: str):
        """分节标题"""
        print()
        print(f"{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    def divider(self, char: str = "-", length: int = 60):
        """分隔线"""
        print(char * length)

    def kv(self, key: str, value: str):
        """键值对输出"""
        print(self._format("INFO", f"  {key:<20} = {value}"))

# 全局实例
debug = DebugLogger()


class ConversationLogger:
    """
    实时对话记录器 - 将 LLM 对话记录到文件

    特性：
    - 实时写入文件，不丢失任何记录
    - 按会话组织，方便调试和回溯
    - 包含完整的消息内容、工具调用、Token 用量等
    - 线程安全
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "log_info"
        )
        self._ensure_log_dir()
        self._current_session_file = None
        self._turn_count = 0

    def _ensure_log_dir(self):
        """确保日志目录存在"""
        os.makedirs(self._log_dir, exist_ok=True)

    def _get_session_file(self) -> str:
        """获取当前会话的日志文件路径"""
        if self._current_session_file is None:
            self._current_session_file = os.path.join(
                self._log_dir, f"conversation_{self._session_id}.jsonl"
            )
        return self._current_session_file

    def _timestamp(self) -> str:
        """获取 ISO 格式的时间戳"""
        return datetime.now().isoformat(timespec="milliseconds")

    def _write(self, record: dict):
        """写入单条记录到文件（实时刷出）"""
        import json
        try:
            with open(self._get_session_file(), "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())  # 确保立即写入磁盘
        except Exception as e:
            print(f"[ConversationLogger] 写入失败: {e}")

    def start_session(self, metadata: dict = None):
        """记录会话开始"""
        record = {
            "type": "session_start",
            "timestamp": self._timestamp(),
            "session_id": self._session_id,
            "metadata": metadata or {},
        }
        self._write(record)

    def log_user_input(self, content: str):
        """记录用户输入"""
        self._turn_count += 1
        record = {
            "type": "user_input",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "content": content[:500] if len(content) > 500 else content,
            "content_length": len(content),
        }
        self._write(record)

    def log_llm_request(self, messages: list, model: str = None):
        """记录发送给 LLM 的请求"""
        msg_summaries = []
        for msg in messages:
            msg_type = getattr(msg, "type", "unknown")
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                content_preview = content[:200] + "..." if len(content) > 200 else content
            else:
                content_preview = str(content)[:200]
            msg_summaries.append({
                "type": msg_type,
                "content_preview": content_preview,
                "content_length": len(content) if isinstance(content, str) else 0,
            })
        record = {
            "type": "llm_request",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "message_count": len(messages),
            "messages": msg_summaries,
            "model": model,
        }
        self._write(record)

    def log_llm_response(self, response_content: str, raw_response: str = None):
        """记录 LLM 的原始响应"""
        record = {
            "type": "llm_response",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "content": response_content,
            "content_length": len(response_content) if response_content else 0,
            "raw_length": len(raw_response) if raw_response else 0,
        }
        self._write(record)

    def log_tool_call(self, tool_name: str, tool_args: dict, tool_result: str = None, status: str = "success"):
        """记录工具调用"""
        record = {
            "type": "tool_call",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_result_preview": tool_result[:500] if tool_result and len(tool_result) > 500 else tool_result,
            "tool_result_length": len(tool_result) if tool_result else 0,
            "status": status,
        }
        self._write(record)

    def log_llm_intent(self, intent: str, content_preview: str = None):
        """记录 LLM 的意图/思考"""
        record = {
            "type": "llm_intent",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "intent": intent,
            "content_preview": content_preview[:300] if content_preview and len(content_preview) > 300 else content_preview,
        }
        self._write(record)

    def log_compression(self, before_tokens: int, after_tokens: int, saved_tokens: int):
        """记录上下文压缩"""
        record = {
            "type": "compression",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "saved_tokens": saved_tokens,
            "ratio": f"{(saved_tokens / before_tokens * 100):.1f}%" if before_tokens > 0 else "0%",
        }
        self._write(record)

    def log_action(self, action: str, details: dict = None):
        """记录特殊动作（restart/hibernated/skip 等）"""
        record = {
            "type": "action",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "action": action,
            "details": details or {},
        }
        self._write(record)

    def log_error(self, error_type: str, error_msg: str, traceback: str = None):
        """记录错误"""
        record = {
            "type": "error",
            "turn": self._turn_count,
            "timestamp": self._timestamp(),
            "error_type": error_type,
            "error_msg": error_msg,
            "traceback": traceback[:1000] if traceback and len(traceback) > 1000 else traceback,
        }
        self._write(record)

    def end_session(self, summary: dict = None):
        """记录会话结束"""
        record = {
            "type": "session_end",
            "timestamp": self._timestamp(),
            "session_id": self._session_id,
            "total_turns": self._turn_count,
            "summary": summary or {},
        }
        self._write(record)

    def new_session(self):
        """开始新的会话（生成新的 session_id）"""
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_session_file = None
        self._turn_count = 0


# 全局实例
conversation_logger = ConversationLogger()


def _get_total_generations() -> int:
    """获取总世代数"""
    memory = _load_memory()
    return memory.get("total_generations", 1)
from tools.token_manager import (
    EnhancedTokenCompressor, truncate_tool_result, estimate_tokens_precise,
    estimate_messages_tokens, DEFAULT_TOKEN_BUDGET, MAX_TOOL_RESULT_TOKENS,
    CORE_SUMMARY_CHARS, COMPRESSION_TRIGGER_RATIO, COMPRESSION_WARNING_RATIO,
    MessagePriority, truncate_by_priority, format_compression_report,
)
from core.prompt_builder import build_system_prompt


def print_evolution_time():
    """打印当前系统时间，宣告进化成功"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    debug.system(f"系统时间: {current_time}", tag="EVOLVE")


# ============================================================================
# 运行时上下文压缩配置
# ============================================================================

MAX_TOKEN_LIMIT = 4000       # Token 阈值，超过此值触发压缩
KEEP_RECENT_STEPS = 2         # 保留最近的工具调用次数
SUMMARY_MAX_CHARS = 200       # 压缩摘要的最大字数
COMPRESSION_MODEL = "qwen-turbo"  # 压缩用模型


def estimate_tokens(text: str) -> int:
    """
    估算文本的 Token 数量。
    
    使用字符数 / 2 作为粗略估算（中文约 1 token = 1.5-2 字符，英文约 4 字符）
    保守估计取 2，以避免实际 token 超限。
    
    Args:
        text: 待估算的文本
        
    Returns:
        估算的 token 数量
    """
    return len(text) // 2


def estimate_messages_tokens(messages: list) -> int:
    """
    估算消息列表的总 Token 数量。
    
    Args:
        messages: LangChain 消息列表
        
    Returns:
        估算的总 token 数量
    """
    total = 0
    for msg in messages:
        if hasattr(msg, 'content'):
            total += estimate_tokens(str(msg.content))
    return total


def compress_agent_scratchpad(
    history_steps: list,
    compression_llm,
    max_chars: int = SUMMARY_MAX_CHARS,
) -> str:
    """
    将 Agent 的历史操作步骤压缩为极简摘要。
    
    调用大模型进行总结，忽略代码细节和文件全文，只保留核心逻辑。
    
    Args:
        history_steps: 需要压缩的历史消息列表
        compression_llm: 用于压缩的 LLM 实例
        max_chars: 摘要最大字符数
        
    Returns:
        压缩后的摘要字符串
    """
    if not history_steps:
        return ""
    
    # 将历史步骤格式化为文本
    history_text = "\n".join([
        f"[{i+1}] {msg.type}: {msg.content[:500] if len(msg.content) > 500 else msg.content}"
        for i, msg in enumerate(history_steps)
        if hasattr(msg, 'content') and hasattr(msg, 'type')
    ])
    
    if not history_text.strip():
        return ""
    
    compression_prompt = f"""请将以下 Agent 的操作步骤和观察结果总结为一段不超过 {max_chars} 字的极简摘要。

要求：
1. 忽略具体的代码细节和文件全文
2. 只保留核心逻辑：它做了什么决定，看了哪些关键文件，得出了什么结论
3. 删除所有冗余的废话、过程细节和成功描述
4. 重点标注：发现了什么问题，学习到了什么经验

历史步骤：
{history_text[:3000]}

请直接输出摘要，不要有任何前缀："""
    
    try:
        response = compression_llm.invoke(compression_prompt)
        summary = response.content if hasattr(response, 'content') else str(response)
        # 强制截断
        if len(summary) > max_chars:
            summary = summary[:max_chars - 3] + "..."
        return summary
    except Exception as e:
        return f"[压缩失败: {str(e)}]"


# ============================================================================
# 系统提示词已迁移至 prompts/ 目录和 core/prompt_builder.py
# ============================================================================


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> logging.Logger:
    """
    配置全局日志系统。
    
    Args:
        level: 日志级别
        log_format: 日志格式
        
    Returns:
        配置好的 logger 实例
    """
    if log_format is None:
        log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    return logging.getLogger("SelfEvolvingAgent")


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

def create_langchain_tools() -> list[BaseTool]:
    """
    将项目工具包装为 LangChain Tool。
    
    Returns:
        LangChain Tool 列表
    """
    from langchain_core.tools import tool
    
    @tool
    def web_search_tool(query: str) -> str:
        """
        搜索互联网获取最新信息。
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果摘要
        """
        return web_search(query)
    
    @tool
    def read_webpage_tool(url: str) -> str:
        """
        读取指定网页的完整内容。
        
        Args:
            url: 网页 URL
            
        Returns:
            网页正文内容
        """
        return read_webpage(url)
    
    @tool
    def list_directory_tool(path: str, show_hidden: bool = False, recursive: bool = False) -> str:
        """
        列出目录内容和文件信息。

        Args:
            path: 目录路径，默认为 "."（当前目录）
            show_hidden: 是否显示隐藏文件，默认 False
            recursive: 是否递归列出子目录，默认 False

        Returns:
            格式化的目录列表
        """
        return list_dir(path, show_hidden=show_hidden, recursive=recursive)

    @tool
    def read_local_file_tool(file_path: str, max_lines: int = None, offset: int = 0) -> str:
        """
        读取本地文件内容。

        Args:
            file_path: 文件路径
            max_lines: 最大读取行数，默认 None（读取全部）
            offset: 从第几行开始读取（0-based），用于跳过大段代码，默认 0

        Returns:
            格式化的文件内容（带行号）
        """
        return read_file(file_path, max_lines=max_lines, offset=offset)
    
    @tool
    def edit_local_file_tool(file_path: str, search_string: str, replace_string: str) -> str:
        """
        编辑本地文件，替换指定内容。
        
        注意：必须精确匹配搜索字符串才能替换！
        编辑后请立即使用 check_syntax 进行语法自检。
        
        Args:
            file_path: 文件路径
            search_string: 要替换的原字符串
            replace_string: 替换后的新字符串
            
        Returns:
            操作结果
        """
        return edit_local_file(file_path, search_string, replace_string)
    
    @tool
    def create_new_file_tool(file_path: str, content: str, use_workspace: bool = True) -> str:
        """
        创建新文件或覆盖现有文件。

        Args:
            file_path: 文件路径（可以是相对或绝对路径）
            content: 文件内容
            use_workspace: 是否使用工作区域目录（默认True）
                           如果为 True，文件会创建在 workspace/ 目录下
                           如果为 False，在项目根目录下创建

        Returns:
            操作结果
        """
        project_root = os.path.dirname(os.path.abspath(__file__))
        workspace = os.path.join(project_root, "workspace")
        
        # 如果是相对路径且启用工作区域，自动加上 workspace 前缀
        if use_workspace and not os.path.isabs(file_path):
            # 如果路径已经以 workspace 开头，不再重复添加
            if not file_path.startswith("workspace"):
                file_path = os.path.join("workspace", file_path)
        
        # 确保目录存在
        abs_path = os.path.abspath(file_path)
        parent_dir = os.path.dirname(abs_path)
        os.makedirs(parent_dir, exist_ok=True)
        
        return create_new_file(file_path, content)
    
    @tool
    def check_syntax_tool(file_path: str) -> str:
        """
        检查 Python 文件的语法正确性。

        这是代码修改后必须调用的自检工具！

        Args:
            file_path: 文件路径

        Returns:
            "Syntax OK" 或详细错误信息
        """
        return check_syntax(file_path)

    @tool
    def list_symbols_in_file_tool(file_path: str) -> str:
        """
        提取 Python 文件中的符号大纲（Cursor Outline 视图）。

        使用 AST 解析，只返回 class/def/全局变量 的名称和行号，
        **不读取函数体内容**，极度节省 Token。

        使用场景：
        - 修改某函数前，先用此工具定位其在文件中的行号
        - 避免读取整个大文件，节省 Token

        Args:
            file_path: Python 文件路径

        Returns:
            格式化的符号列表，包含类型(COLASS/DEF/GLOBAL)、名称、行号
        """
        return list_symbols_in_file(file_path)
    
    @tool
    def backup_project_tool(version_note: str = "") -> str:
        """
        备份整个项目。
        
        Args:
            version_note: 备份说明
            
        Returns:
            备份结果
        """
        return backup_project(version_note)
    
    @tool
    def trigger_self_restart_tool(reason: str = "") -> str:
        """
        触发 Agent 自我重启。

        用于应用代码更新。每次代码修改并自检通过后必须调用！

        Args:
            reason: 重启原因

        Returns:
            操作结果（原进程将退出）
        """
        return trigger_self_restart(reason)

    @tool
    def read_generation_archive_tool(generation: int) -> str:
        """
        读取指定世代的详细档案。

        当当前世代的核心智慧不足以解决问题时，可以读取前几代的详细档案。

        Args:
            generation: 世代编号（如 1, 2, 3...）

        Returns:
            世代档案的JSON字符串，包含完整的思考过程和工具调用记录
        """
        return read_generation_archive(generation)

    @tool
    def list_generation_archives_tool() -> str:
        """
        列出所有可用的世代档案。

        Returns:
            档案列表，包含文件名、大小、修改时间
        """
        return list_archives()
    
    @tool
    def read_memory_tool() -> str:
        """
        读取当前的压缩记忆。
        
        返回跨越多次重启积累的状态：
        - generation: 当前世代
        - core_context: 提炼后的历史上下文
        - current_goal: 本世代核心目标
        
        Returns:
            记忆的 JSON 字符串
        """
        return read_memory()
    
    @tool
    def commit_compressed_memory_tool(new_core_context: str, next_goal: str) -> str:
        """
        覆盖式更新记忆（记忆坍缩）。

        【极度重要】在调用 trigger_self_restart 之前必须先调用此函数！
        会覆盖旧的 core_context，用不超过300字的新摘要替换。

        Args:
            new_core_context: 压缩后的新上下文摘要（不超过300字）
            next_goal: 下一代需要接着做的具体任务

        Returns:
            更新结果
        """
        return commit_compressed_memory(new_core_context, next_goal)

    @tool
    def compress_context_tool(reason: str = "") -> str:
        """
        主动压缩对话上下文，专注于主要任务。

        当对话历史过长导致 AI 无法专注时，可调用此工具压缩上下文。
        会保留系统提示、最近的用户输入和最近的交互对，其余历史压缩为摘要。

        Args:
            reason: 压缩原因（可选）

        Returns:
            压缩结果，包含压缩前后的 Token 数对比、saved_tokens、compression_ratio 等指标的 JSON 字符串。
        """
        # 使用高级压缩工具
        return advanced_compress_context_tool(reason=reason)
        
        
        # 创建压缩器实例
        compressor = create_compressor(
            token_budget=4096,
        )
        
        # 构造测试消息
        messages = [
            {"role": "system", "content": "你是自我进化 AI Agent"}, 
            {"role": "user", "content": "测试压缩"}
        ]
        
        try:
            # 执行压缩
            compressed_messages, summary = compressor.compress(messages)
            
            # 计算压缩前后的 token 数
            before_tokens = estimate_messages_tokens(messages)
            after_tokens = estimate_messages_tokens(compressed_messages)
            
            # 计算节省的 tokens 和压缩率
            saved_tokens = before_tokens - after_tokens if before_tokens > after_tokens else 0
            compression_ratio = (before_tokens - after_tokens) / before_tokens if before_tokens > 0 else 0
            
            # 构建结构化返回结果
            result = {
                "saved_tokens": saved_tokens,
                "compression_ratio": round(compression_ratio, 4),
                "before_tokens": before_tokens,
                "after_tokens": after_tokens,
                "summary": summary,
                "status": "success",
                "reason": reason
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            # 错误处理
            result = {
                "saved_tokens": 0,
                "compression_ratio": 0.0,
                "before_tokens": 0,
                "after_tokens": 0,
                "summary": "",
                "status": "error",
                "reason": str(e)
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

    @tool
    def run_self_test_tool() -> str:
        """
        运行 Agent 核心功能的自我测试。

        测试内容：
        1. 核心模块导入
        2. 配置文件可用性
        3. 工具模块可用性
        4. restarter.py 可用性
        5. 记忆系统可用性

        Returns:
            测试结果报告
        """
        return run_self_test()

    @tool
    def get_agent_status_tool() -> str:
        """
        获取 Agent 当前状态概览。

        返回当前世代、目标、上下文和进化统计。

        Returns:
            状态报告
        """
        status = get_agent_status()
        project_root = os.path.dirname(os.path.abspath(__file__))
        workspace = os.path.join(project_root, "workspace")
        
        # 添加工作区域信息
        status_lines = status.split('\n')
        workspace_info = [
            "",
            f"工作区域: {workspace}",
        ]
        
        # 在合适位置插入
        for i, line in enumerate(status_lines):
            if line.startswith("工作目录:"):
                status_lines.insert(i + 1, f"工作区域: {workspace}")
                break
        
        return '\n'.join(status_lines)

    @tool
    def enter_hibernation_tool(reason: str = "", duration: int = 300) -> str:
        """
        主动进入休眠状态。当 Agent 判断当前任务已完成或无需继续工作时应调用此工具。

        调用后 Agent 将进入休眠，等待指定时间后自动苏醒继续工作。
        这比被动等待固定间隔更高效。

        Args:
            reason: 休眠原因（可选），用于日志记录
            duration: 休眠时长（秒），默认 300 秒（5 分钟）
                      - 短时休眠: 60-120 秒（任务接近完成）
                      - 中时休眠: 300-600 秒（任务已完成，等待新任务）
                      - 长时休眠: 1800+ 秒（长时间无任务）

        Returns:
            休眠确认信息
        """
        from datetime import datetime, timedelta
        wake_time = datetime.now() + timedelta(seconds=duration)
        return f"[休眠确认] Agent 将进入休眠状态。\n原因: {reason or '任务已完成/无需继续'}\n休眠时长: {duration} 秒\n预计苏醒时间: {wake_time.strftime('%H:%M:%S')}"

    @tool
    def get_evolution_history_tool(limit: int = 10) -> str:
        """
        获取进化历史记录。

        Args:
            limit: 返回的最近记录条数

        Returns:
            格式化的历史记录
        """
        return get_evolution_history(limit)

    @tool
    def log_evolution_tool(file_modified: str, change_type: str, reason: str,
                          success: bool, details: str = "") -> str:
        """
        记录一次自我修改到进化历史。

        【重要】每次代码修改后应调用此函数记录变更。

        Args:
            file_modified: 被修改的文件
            change_type: 变更类型 ("add", "modify", "delete")
            reason: 修改原因
            success: 是否成功
            details: 详细信息

        Returns:
            操作结果
        """
        from tools.memory_tools import get_generation
        return log_evolution(
            generation=get_generation(),
            file_modified=file_modified,
            change_type=change_type,
            reason=reason,
            success=success,
            details=details,
        )

    @tool
    def grep_search_tool(regex_pattern: str, include_ext: str = ".py",
                         search_dir: str = ".", case_sensitive: bool = True,
                         max_results: int = 500) -> str:
        """
        全局正则表达式搜索 (Cursor/Aider 范式)。

        在项目中快速搜索代码，支持正则表达式。优先于 read_local_file_tool 使用！

        适用场景：
        - 查找函数/变量定义位置
        - 查找函数的所有调用
        - 查找 import 语句
        - 快速定位关键词

        Args:
            regex_pattern: 正则表达式模式
            include_ext: 要搜索的文件类型，默认 ".py"
            search_dir: 搜索目录，默认当前目录
            case_sensitive: 是否区分大小写，默认 True
            max_results: 最大返回结果数

        Returns:
            格式化的搜索结果，包含文件路径、行号和匹配内容
        """
        return grep_search(
            regex_pattern=regex_pattern,
            include_ext=include_ext,
            search_dir=search_dir,
            case_sensitive=case_sensitive,
            max_results=max_results
        )

    @tool
    def apply_diff_edit_tool(file_path: str, diff_text: str) -> str:
        """
        Diff Block 编辑器 (Cursor/Aider 范式)。

        使用 SEARCH/REPLACE 块格式精准替换代码。比 edit_local_file_tool 更可靠！

        格式：
        <<<<<<< SEARCH
        要替换的旧代码
        =======
        新代码
        >>>>>>> REPLACE

        可包含多个块一次性修改多处！

        Args:
            file_path: 要编辑的文件路径
            diff_text: SEARCH/REPLACE 块文本

        Returns:
            操作结果描述
        """
        return apply_diff_edit(file_path=file_path, diff_text=diff_text)

    @tool
    def validate_diff_format_tool(diff_text: str) -> str:
        """
        验证 diff_text 格式是否正确。

        在实际编辑前验证格式，避免无效修改。

        Args:
            diff_text: 要验证的 diff 块文本

        Returns:
            验证结果
        """
        is_valid, message = validate_diff_format(diff_text)
        return message

    @tool
    def find_function_calls_tool(function_name: str, search_dir: str = ".",
                                  include_ext: str = ".py") -> str:
        """
        查找特定函数的所有调用位置。

        Args:
            function_name: 函数名
            search_dir: 搜索目录
            include_ext: 文件类型

        Returns:
            所有调用位置的列表
        """
        return find_function_calls(function_name, search_dir, include_ext)

    @tool
    def find_definitions_tool(symbol_name: str, search_dir: str = ".",
                               include_ext: str = ".py") -> str:
        """
        查找符号（函数、类、变量）的定义位置。

        Args:
            symbol_name: 符号名
            search_dir: 搜索目录
            include_ext: 文件类型

        Returns:
            所有定义位置的列表
        """
        return find_definitions(symbol_name, search_dir, include_ext)

    @tool
    def get_code_entity_tool(file_path: str, entity_name: str) -> str:
        """
        AST 一击必中 - 直接提取类或函数的完整代码。

        使用 Python AST 语法树解析，直接按名称提取代码实体。
        一轮调用获取完整代码，无需多次读取文件！

        适用场景：
        - 知道要修改的函数/类名，直接提取其完整代码
        - 快速获取某个实体的大小和结构
        - 无需手动找行号，一次性看完

        Args:
            file_path: Python 文件路径
            entity_name: 要提取的实体名称（类名或函数名）

        Returns:
            实体的完整代码及行号范围
        """
        return get_code_entity(file_path, entity_name)

    @tool
    def list_file_entities_tool(file_path: str, entity_type: str = None) -> str:
        """
        列出文件中的所有类和函数。

        使用 AST 解析，快速获取文件的代码结构概览。

        Args:
            file_path: Python 文件路径
            entity_type: 过滤类型 ('class', 'function', None 表示全部)

        Returns:
            实体列表
        """
        return list_file_entities(file_path, entity_type)

    @tool
    def search_and_read_tool(
        query: str,
        context_lines: int = 5,
        include_ext: str = ".py",
        search_dir: str = ".",
        max_matches: int = 50
    ) -> str:
        """
        搜索并读取 - 一步到位的代码检索。

        在项目中全局搜索 query，对于每个匹配项，自动携带上下文行返回代码。
        将原来需要 2-3 轮 LLM 交互的操作压缩为 1 轮。

        适用场景：
        - 想了解某个关键词在项目中的所有使用方式
        - 需要查看匹配行的完整上下文
        - 全局搜索 + 上下文预览

        Args:
            query: 搜索关键词（支持正则表达式）
            context_lines: 每个匹配项返回的上下文行数
            include_ext: 文件类型过滤
            search_dir: 搜索目录
            max_matches: 最大匹配数

        Returns:
            格式化的搜索结果，每个匹配包含完整的上下文代码块
        """
        return search_and_read(
            query=query,
            context_lines=context_lines,
            include_ext=include_ext,
            search_dir=search_dir,
            max_matches=max_matches
        )

    @tool
    def run_cmd_tool(command: str, timeout: int = 60, shell: bool = True,
                    cwd: str = None, check_safety: bool = True) -> str:
        """
        执行 CMD 命令并返回输出结果。

        在 Windows 环境下执行指定的命令，返回标准输出和标准错误。
        支持超时控制，防止命令执行过久导致阻塞。
        包含危险命令黑名单机制，自动拦截危险操作。

        Args:
            command: 要执行的命令（如 "dir", "ipconfig /all", "python script.py"）
            timeout: 命令执行超时时间（秒），默认 60 秒
            shell: 是否使用 shell 执行，默认 True
            cwd: 命令执行的工作目录，默认当前目录
            check_safety: 是否执行安全检查，默认 True

        Returns:
            格式化的执行结果字符串
        """
        return run_cmd(command, timeout=timeout, shell=shell, cwd=cwd, check_safety=check_safety)

    @tool
    def run_powershell_tool(command: str, timeout: int = 60, cwd: str = None) -> str:
        """
        通过 PowerShell 执行命令（Windows 专用）。

        专门用于执行 PowerShell 命令，某些 Windows 特有功能使用 PowerShell 更方便。

        Args:
            command: 要执行的 PowerShell 命令
            timeout: 超时时间（秒），默认 60 秒
            cwd: 工作目录，默认当前目录

        Returns:
            格式化的执行结果字符串
        """
        return run_powershell(command, timeout=timeout, cwd=cwd)

    @tool
    def run_batch_tool(commands: str, timeout: int = 60, cwd: str = None) -> str:
        """
        批量执行多个 CMD 命令。

        按顺序执行多个命令，每个命令之间用 && 连接。
        任何一个命令失败，整个批次会停止。

        Args:
            commands: 命令列表（JSON格式的字符串数组），如 '["cd src", "dir"]'
            timeout: 总超时时间（秒），默认 60 秒
            cwd: 工作目录，默认当前目录

        Returns:
            格式化的执行结果字符串
        """
        import json
        try:
            cmd_list = json.loads(commands)
            if not isinstance(cmd_list, list):
                return "[错误] commands 参数必须是 JSON 数组格式"
            return run_batch(cmd_list, timeout=timeout, cwd=cwd)
        except json.JSONDecodeError as e:
            return f"[错误] JSON 解析失败: {e}"

    @tool
    def delete_file_tool(file_path: str, force: bool = False) -> str:
        """
        删除指定的文件或目录。

        【好习惯】完成测试任务后，自动清理测试产生的临时文件。
        保持工作目录整洁，避免垃圾文件堆积。

        Args:
            file_path: 要删除的文件或目录路径
            force: 是否强制删除（跳过文件类型检查，仅用于确认安全的临时文件）

        Returns:
            操作结果描述
        """
        return delete_file(file_path, force=force)

    @tool
    def cleanup_test_files_tool(directory: str = ".", dry_run: bool = True) -> str:
        """
        清理指定目录下的测试相关临时文件。

        【好习惯】定期清理测试产生的临时文件，避免垃圾堆积。
        支持扫描并清理：test_*.py、__pycache__、*.pyc、*.log 等。

        Args:
            directory: 要扫描的目录，默认为当前目录
            dry_run: 是否仅模拟运行（默认 True，显示找到的文件但不实际删除）
                     设置为 False 时会实际删除文件

        Returns:
            操作结果描述，包含找到的可删除文件列表
        """
        return cleanup_test_files(directory=directory, dry_run=dry_run)

    return [
        web_search_tool,
        read_webpage_tool,
        list_directory_tool,
        read_local_file_tool,
        edit_local_file_tool,
        create_new_file_tool,
        check_syntax_tool,
        list_symbols_in_file_tool,
        backup_project_tool,
        trigger_self_restart_tool,
        read_memory_tool,
        commit_compressed_memory_tool,
        read_generation_archive_tool,
        list_generation_archives_tool,
        # high_performance_compress_context_tool,  # 暂时禁用
        run_self_test_tool,
        get_agent_status_tool,
        enter_hibernation_tool,
        get_evolution_history_tool,
        log_evolution_tool,
        run_cmd_tool,
        run_powershell_tool,
        run_batch_tool,
        # Cursor/Aider 范式工具
        grep_search_tool,
        apply_diff_edit_tool,
        validate_diff_format_tool,
        find_function_calls_tool,
        find_definitions_tool,
        # AST 一击必中工具
        get_code_entity_tool,
        list_file_entities_tool,
        search_and_read_tool,
        # 自主任务生成器
        generate_autonomous_task,
        # 文件清理工具（好习惯）
        delete_file_tool,
        cleanup_test_files_tool,
    ]


# ============================================================================
# Self-Evolving Agent 主类
# ============================================================================

class SelfEvolvingAgent:
    """
    自我进化 Agent 主类。
    
    基于 LangChain 框架构建，使用 ReAct 风格的 Agent 架构。
    支持定时苏醒，主动思考优化方向。
    
    Attributes:
        name: Agent 实例名称
        config: 配置对象
        tools: LangChain Tool 列表
        llm: ChatOpenAI 模型实例
        logger: 日志记录器
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
    ) -> None:
        """
        初始化 Agent 实例。
        
        Args:
            config: 配置对象，如果为 None，使用全局默认配置
        """
        # 使用传入的配置或获取全局配置
        self.config = config or get_config()
        
        self.name = self.config.agent.name
        self.logger = logging.getLogger(f"Agent.{self.name}")
        
        # 获取 API Key（优先从配置文件读取）
        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError(
                "未设置 API Key。\n\n"
                "请在 config.toml 中配置：\n\n"
                "[llm]\n"
                'api_key = "your-api-key"\n\n'
                "或使用代码设置：\n"
                "from config import Config\n"
                "config = Config()\n"
                "config.llm.api_key = 'your-api-key'"
            )
        
        # 创建 LangChain Tool
        self.tools = create_langchain_tools()
        self.tool_map = {tool.name for tool in self.tools}
        
        # 创建 LLM
        llm_kwargs = {
            "model": self.config.llm.model_name,
            "temperature": self.config.llm.temperature,
            "api_key": self.api_key,
        }
        
        if self.config.llm.api_base:
            llm_kwargs["base_url"] = self.config.llm.api_base
        
        self.llm = ChatOpenAI(**llm_kwargs)
        self.model_name = self.config.llm.model_name
        
        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 创建压缩用 LLM（使用更轻量的模型以节省成本）
        compression_llm_kwargs = {
            "model": self.config.context_compression.compression_model,
            "temperature": 0.3,  # 压缩用更确定性
            "api_key": self.api_key,
        }
        if self.config.llm.api_base:
            compression_llm_kwargs["base_url"] = self.config.llm.api_base
        self.compression_llm = ChatOpenAI(**compression_llm_kwargs)

        # 创建 OpenCLAW 风格的 Token 压缩器
        self.token_compressor = EnhancedTokenCompressor(
            token_budget=self.config.context_compression.max_token_limit,
            max_history_pairs=self.config.context_compression.keep_recent_steps,
            compression_llm=self.compression_llm,
            enable_preemptive=True,  # 启用预压缩
        )

        # 全局操作历史（跨苏醒周期跟踪，防止重复操作）
        self.global_recent_actions: List[str] = []
        self.global_consecutive_count = 0

        # 标记：是否修改了自身代码（需要重启才能生效）
        self._self_modified = False
        
        # 启动时间
        self.start_time = datetime.now()
        
        # 工作区域路径
        workspace_dir = getattr(self.config.agent, 'workspace', 'workspace')
        project_root = os.path.dirname(os.path.abspath(__file__))
        self.workspace_path = os.path.join(project_root, workspace_dir)
        
        # 确保工作区域存在
        os.makedirs(self.workspace_path, exist_ok=True)
        self.logger.info(f"[初始化] 工作区域: {self.workspace_path}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词。

        使用 core/prompt_builder.py 的动态组装器。

        Returns:
            格式化的系统提示词
        """
        return build_system_prompt(
            generation=get_generation(),
            total_generations=_get_total_generations(),
            core_context=get_core_context(),
            current_goal=get_current_goal(),
        )

    def _run_evolution_gate(self) -> dict:
        """
        运行进化测试门控。

        在 Agent 准备执行 trigger_self_restart 之前，必须通过所有测试。
        这确保自我进化不会破坏核心功能。

        Returns:
            dict: {
                "passed": bool,  # 是否全部通过
                "passed_count": int,  # 通过数量
                "failed_count": int,  # 失败数量
                "total_count": int,  # 总数
                "failed_modules": list,  # 失败的模块
                "output": str,  # 完整输出
            }
        """
        import subprocess
        import sys

        debug.info("运行进化测试门控...", tag="GATE")

        try:
            # 运行 pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                timeout=120,  # 2分钟超时
            )

            output = result.stdout + result.stderr

            # 解析结果
            passed_count = output.count(" PASSED")
            failed_count = output.count(" FAILED")
            total_count = passed_count + failed_count

            # 提取失败的模块
            failed_modules = []
            for line in output.split("\n"):
                if "FAILED" in line:
                    # 提取测试名称
                    parts = line.split("::")
                    if len(parts) >= 2:
                        failed_modules.append(parts[1].split("::")[0])

            passed = failed_count == 0

            if passed:
                debug.success(f"测试门控通过: {passed_count}/{total_count}", tag="GATE")
            else:
                debug.warning(f"测试门控失败: {failed_count}/{total_count} 失败", tag="GATE")
                for module in set(failed_modules):
                    debug.warning(f"  - {module}", tag="GATE")

            return {
                "passed": passed,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "total_count": total_count,
                "failed_modules": list(set(failed_modules)),
                "output": output,
            }

        except subprocess.TimeoutExpired:
            debug.error("测试门控超时 (2分钟)", tag="GATE")
            return {
                "passed": False,
                "passed_count": 0,
                "failed_count": 1,
                "total_count": 0,
                "failed_modules": ["pytest_timeout"],
                "output": "测试执行超时",
            }
        except Exception as e:
            debug.error(f"测试门控执行失败: {e}", tag="GATE")
            return {
                "passed": False,
                "passed_count": 0,
                "failed_count": 1,
                "total_count": 0,
                "failed_modules": ["test_runner_error"],
                "output": str(e),
            }

    def _acquire_external_knowledge(self) -> str:
        """
        感知阶段：自动获取外部知识。

        在每次苏醒后，先搜索最新的 AI Agent 相关知识，
        作为自我进化的参考标准。

        Returns:
            str: 搜索结果摘要
        """
        from tools.web_tools import web_search

        debug.system("感知阶段：获取外部知识...", tag="KNOWLEDGE")

        search_queries = [
            "AI Agent architecture best practices 2024",
            "SWE-agent OpenDevin code agent framework",
            "LLM context compression memory management",
        ]

        knowledge_snippets = []

        for query in search_queries:
            try:
                debug.debug(f"搜索: {query}", tag="KNOWLEDGE")
                result = web_search(query)

                # 提取关键信息
                if result and len(result) > 100:
                    # 取前500字符作为摘要
                    snippet = result[:500]
                    knowledge_snippets.append({
                        "query": query,
                        "snippet": snippet,
                    })
                    debug.info(f"获取到 {len(snippet)} 字符知识", tag="KNOWLEDGE")

            except Exception as e:
                debug.warning(f"知识获取失败: {query} - {e}", tag="KNOWLEDGE")

        if knowledge_snippets:
            summary = "## 外部知识参考\n\n"
            for item in knowledge_snippets:
                summary += f"### {item['query']}\n{item['snippet']}\n\n"
            return summary

        return ""

    def _compress_context(self, messages: list) -> list:
        """
        压缩对话上下文，释放 Token 消耗。

        使用增强型压缩策略：
        1. 根据紧急程度动态调整保留对数
        2. 预压缩机制 - 提前触发避免危机
        3. 智能摘要 - 提取关键信息

        Args:
            messages: 原始消息列表

        Returns:
            压缩后的消息列表
        """
        old_tokens = estimate_messages_tokens(messages)
        
        # 使用增强型压缩器
        compressed, summary = self.token_compressor.compress(
            messages,
            max_chars=self.config.context_compression.summary_max_chars,
        )
        
        new_tokens = estimate_messages_tokens(compressed)
        
        self.logger.info(
            f"[Token压缩] {old_tokens} -> {new_tokens} (节省 {old_tokens - new_tokens})"
        )
        
        # 记录压缩事件
        conversation_logger.log_compression(old_tokens, new_tokens, old_tokens - new_tokens)
        
        return compressed
    
    def _format_tool_result(self, tool_name: str, result: str) -> str:
        """
        格式化工具执行结果。
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            
        Returns:
            格式化的结果字符串
        """
        # 使用 OpenCLAW 风格的智能截断
        truncated = truncate_tool_result(result, max_chars=MAX_TOOL_RESULT_TOKENS * 2)
        
        return f"[{tool_name}] 结果:\n{truncated}"
    
    def _should_restart(self, message: str) -> bool:
        """
        检查消息是否表示需要重启。
        
        Args:
            message: Agent 的回复消息
            
        Returns:
            是否需要重启
        """
        restart_keywords = [
            "trigger_self_restart",
            "self_restart",
            "重启",
            "restart",
            "应用更新",
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in restart_keywords)
    
    def think_and_act(self, user_prompt: str = None) -> bool:
        """
        苏醒时执行一次思考和行动。

        流程：
        1. 感知阶段：获取外部知识（可选）
        2. 构建系统提示词
        3. 调用 LLM 进行推理
        4. 返回结果给 LLM 继续推理
        5. 直到 Agent 认为任务完成

        Args:
            user_prompt: 可选的用户初始输入（首次苏醒时使用）

        Returns:
            如果应该继续运行返回 True，如果触发了重启返回 False
        """

        # ========== 感知阶段：自动获取外部知识 ==========
        # 首次苏醒时获取最新知识作为进化参考
        if self.global_consecutive_count == 0:
            try:
                external_knowledge = self._acquire_external_knowledge()
                if external_knowledge:
                    debug.system("已获取外部知识参考", tag="KNOWLEDGE")
            except Exception as e:
                debug.warning(f"知识摄取失败: {e}", tag="KNOWLEDGE")

        messages = [SystemMessage(content=self._build_system_prompt())]

        if user_prompt:
            messages.append(HumanMessage(content=user_prompt))
            debug.info(f"用户输入: {user_prompt[:60]}...", tag="USER")
            conversation_logger.log_user_input(user_prompt)

        conversation_logger.log_llm_request(messages, model=self.model_name)
        max_iterations = self.config.agent.max_iterations
        iterations = 0

        try:
            while iterations < max_iterations:
                iterations += 1

                # 调用 LLM
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)

                # 记录 LLM 响应
                conversation_logger.log_llm_response(
                    response_content=response.content or "",
                    raw_response=response.content or ""
                )

                # Token 使用
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = response.usage_metadata
                    debug.debug(
                        f"Token: {usage.get('input_tokens', 0)} + {usage.get('output_tokens', 0)}",
                        tag="LLM"
                    )

                # 调试：显示原始响应内容
                debug.debug(f"原始响应长度: {len(response.content) if response.content else 0} 字符", tag="RAW")
                if response.content and '<tool_call>' in response.content:
                    debug.info(f"检测到 <tool_call> 标签", tag="RAW")

                # ========== 修复：处理文本形式的工具调用 ==========
                # 检查是否有结构化的 tool_calls
                tool_calls = getattr(response, 'tool_calls', None) or []

                # 如果没有结构化的 tool_calls，尝试从文本内容中解析
                if not tool_calls and response.content:
                    import re
                    import json

                    # 匹配 <tool_call>...</tool_call> 块（支持嵌套 JSON）
                    text_tool_calls = re.findall(
                        r'<tool_call>\s*(\{[\s\S]*?\})\s*</tool_call>',
                        response.content
                    )

                    # 如果没找到，尝试匹配单标签形式
                    if not text_tool_calls:
                        text_tool_calls = re.findall(
                            r'<tool_call>\s*(\{[\s\S]*?\})',
                            response.content
                        )

                    if text_tool_calls:
                        debug.warning(f"检测到文本形式的工具调用 (共{len(text_tool_calls)}个)，正在解析...", tag="PARSE")
                        import uuid
                        for tc_json in text_tool_calls:
                            try:
                                tc = json.loads(tc_json)
                                # 确保有 args 字段
                                if 'args' not in tc:
                                    # 尝试从其他字段构建 args
                                    tc['args'] = {}
                                    # 尝试从 jsonrpc 格式转换
                                    if 'arguments' in tc:
                                        tc['args'] = tc.pop('arguments')
                                    # 尝试提取函数参数
                                    for key in ['path', 'file_path', 'command', 'query']:
                                        if key in tc:
                                            tc['args'][key] = tc.pop(key, None)
                                # 确保有 id 字段
                                if 'id' not in tc:
                                    tc['id'] = f"call_{uuid.uuid4().hex[:8]}"
                                tool_calls.append(tc)
                                debug.info(f"解析成功: {tc.get('name', 'unknown')}", tag="PARSE")
                            except json.JSONDecodeError as e:
                                debug.error(f"JSON解析失败: {e}", tag="PARSE")
                                debug.debug(f"原始内容: {tc_json[:200]}...", tag="PARSE")

                # 无工具调用 = 结束
                if not tool_calls:
                    # 显示 AI 的意图/思考
                    if response.content:
                        content_preview = response.content[:100].replace('\n', ' ')
                        debug.llm("最终回复", content_preview)
                        conversation_logger.log_llm_intent("final_response", content_preview)
                    return True

                # 显示 AI 的意图/思考
                if response.content:
                    content_preview = response.content[:100].replace('\n', ' ')
                    debug.llm("意图", content_preview)
                    conversation_logger.log_llm_intent("tool_call", content_preview)

                # 执行工具
                for tool_call in tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})

                    # 调试日志
                    debug.tool(tool_name, "called", f"args={str(tool_args)[:50]}")
                    conversation_logger.log_tool_call(tool_name, tool_args, status="called")

                    # 执行工具（返回结果和特殊动作）
                    tool_result, action = self._execute_tool(tool_name, tool_args, messages)

                    # 处理特殊动作
                    if action == "restart":
                        conversation_logger.log_action("restart", {"tool": tool_name})
                        return False  # 触发重启
                    elif action == "skip":
                        conversation_logger.log_action("skip", {"tool": tool_name})
                        messages.append(ToolMessage(content=self._format_tool_result(tool_name, tool_result), tool_call_id=tool_call['id']))
                        conversation_logger.log_tool_call(tool_name, tool_args, tool_result, status="skipped")
                        continue  # 跳过添加结果
                    elif action == "hibernated":
                        conversation_logger.log_action("hibernated", {"tool": tool_name})
                        messages.append(ToolMessage(content=self._format_tool_result(tool_name, tool_result), tool_call_id=tool_call['id']))
                        return "hibernated"

                    # 将工具结果添加到消息中（所有非特殊动作的情况）
                    messages.append(ToolMessage(
                        content=self._format_tool_result(tool_name, tool_result),
                        tool_call_id=tool_call['id'],
                    ))

            return True

        except Exception as e:
            debug.error(f"主循环异常: {type(e).__name__}: {e}", exc_info=True)
            return True
    
    def _execute_tool(self, tool_name: str, tool_args: dict, messages: list = None) -> tuple:
        """
        执行工具调用（带超时机制和特殊工具处理）。

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            messages: 消息列表（用于特殊工具的上下文处理）

        Returns:
            (result, action): 元组
                - result: 工具执行结果
                - action: 特殊动作 (None, "restart", "hibernated", "skip")
        """
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
        from tools.memory_tools import get_generation, get_core_context, get_current_goal, archive_generation_history, advance_generation

        # 获取广播器
        bc = get_broadcaster()

        action = None

        # 工具状态映射：根据工具名称推断状态
        tool_status_map = {
            "web_search_tool": AgentStatus.SEARCHING,
            "read_webpage_tool": AgentStatus.SEARCHING,
            "edit_local_file_tool": AgentStatus.CODING,
            "create_new_file_tool": AgentStatus.CODING,
            "apply_diff_edit_tool": AgentStatus.CODING,
            "check_syntax_tool": AgentStatus.CODING,
            "run_cmd_tool": AgentStatus.CODING,
            "run_self_test_tool": AgentStatus.TESTING,
            "compress_context_tool": AgentStatus.COMPRESSING,
            "backup_project_tool": AgentStatus.CODING,
            "trigger_self_restart_tool": AgentStatus.RESTARTING,
            "enter_hibernation_tool": AgentStatus.HIBERNATING,
        }

        # 推断当前状态
        inferred_status = tool_status_map.get(tool_name, AgentStatus.THINKING)
        action_preview = tool_args.get('reason', tool_args.get('command', tool_args.get('query', '')))[:50]
        bc.update_status(inferred_status, action=f"{tool_name.replace('_tool', '')}: {action_preview}...")
        bc.log_tool_call(tool_name, "开始")

        # ========== 特殊工具预处理 ==========
        # compress_context_tool: 内部压缩
        if tool_name == "compress_context_tool" and messages is not None:
            old_tokens = estimate_messages_tokens(messages)
            messages[:] = self._compress_context(messages)
            new_tokens = estimate_messages_tokens(messages)
            saved = old_tokens - new_tokens
            return (f"上下文压缩完成: 节省{saved} Token ({old_tokens} -> {new_tokens}) [保留最近3条原始消息]", None)

        # trigger_self_restart_tool: 世代归档 + 强制测试门控
        if tool_name == "trigger_self_restart_tool" and messages is not None:
            # ========== 强制测试门控：进化前必须通过测试 ==========
            if self._self_modified:
                debug.system("检测到代码修改，正在运行测试门控...", tag="GATE")
                
                # 导入测试运行器
                test_result = self._run_evolution_gate()
                
                if not test_result["passed"]:
                    error_msg = (
                        f"[TEST GATE FAILED] 测试未通过，禁止进化！\n"
                        f"失败模块: {', '.join(test_result['failed_modules'])}\n"
                        f"通过: {test_result['passed_count']}/{test_result['total_count']}\n"
                        f"请修复失败的测试后再试。\n"
                        f"提示: 运行 `python -m pytest tests/ -v` 查看详细错误"
                    )
                    debug.error("测试门控失败，禁止重启", tag="GATE")
                    return (error_msg, None)
                
                debug.success(f"测试门控通过 ({test_result['passed_count']}/{test_result['total_count']})", tag="GATE")
            # ========== 测试门控结束 ==========

            intermediate_steps = []
            for msg in messages:
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    if msg.type == "ai" and msg.content:
                        intermediate_steps.append({"type": "thought", "content": msg.content[:500]})
                    elif msg.type == "tool":
                        intermediate_steps.append({"type": "tool_call", "name": getattr(msg, 'name', 'unknown'), "content": msg.content[:200]})
            
            current_gen = get_generation()
            core_wisdom = get_core_context() or "无"
            current_goal = get_current_goal() or "待定"
            archive_result = archive_generation_history(generation=current_gen, history_data=intermediate_steps, core_wisdom=core_wisdom, next_goal=current_goal)
            new_gen = advance_generation()
            debug.info(f"归档完成: {archive_result}", tag="ARCHIVE")
            debug.success(f"G{current_gen} -> G{new_gen}", tag="GENERATION")
            
            tool_result = trigger_self_restart(**tool_args)
            tool_result_with_archive = f"{tool_result}\n[世代归档] G{current_gen} -> G{new_gen}"
            
            if "✓" in tool_result or "成功" in tool_result:
                if self._self_modified:
                    debug.success("代码已修改，重启生效", tag="RESTART")
                    return (tool_result_with_archive, "restart")
                else:
                    debug.info("重启跳过（无代码修改）", tag="RESTART")
                    self._self_modified = False
            return (tool_result_with_archive, "skip")

        # enter_hibernation_tool: 休眠处理
        if tool_name == "enter_hibernation_tool":
            import re
            duration_match = re.search(r'休眠时长[:：]\s*(\d+)\s*秒', tool_args.get('reason', ''))
            hibernate_duration = int(duration_match.group(1)) if duration_match else self.config.agent.awake_interval
            debug.info(f"Agent 主动休眠 {hibernate_duration} 秒", tag="HIBERNATE")
            time.sleep(hibernate_duration)
            return (f"休眠 {hibernate_duration} 秒完成", "hibernated")

        # 工具超时配置（秒）
        TOOL_TIMEOUTS = {
            "web_search_tool": 30, "read_webpage_tool": 20, "run_cmd_tool": 60,
            "run_powershell_tool": 60, "run_batch_tool": 120, "backup_project_tool": 60,
            "check_syntax_tool": 10, "list_symbols_in_file_tool": 5, "list_directory_tool": 10,
            "read_local_file_tool": 10, "edit_local_file_tool": 15, "create_new_file_tool": 15,
            "trigger_self_restart_tool": 30, "read_memory_tool": 5, "commit_compressed_memory_tool": 10,
            "read_generation_archive_tool": 10, "list_generation_archives_tool": 5,
            "compress_context_tool": 30, "grep_search_tool": 30, "apply_diff_edit_tool": 15,
            "validate_diff_format_tool": 5, "find_function_calls_tool": 30, "find_definitions_tool": 30,
            "get_code_entity_tool": 15, "list_file_entities_tool": 10, "search_and_read_tool": 30,
            "delete_file_tool": 10, "cleanup_test_files_tool": 30,
        }
        DEFAULT_TIMEOUT = 30

        tool_func_map = {
            "web_search_tool": lambda: web_search(**tool_args),
            "read_webpage_tool": lambda: read_webpage(**tool_args),
            "list_directory_tool": lambda: list_dir(**tool_args),
            "read_local_file_tool": lambda: read_file(**tool_args),
            "edit_local_file_tool": lambda: edit_local_file(**tool_args),
            "create_new_file_tool": lambda: create_new_file(**tool_args),
            "check_syntax_tool": lambda: check_syntax(**tool_args),
            "list_symbols_in_file_tool": lambda: list_symbols_in_file(**tool_args),
            "backup_project_tool": lambda: backup_project(**tool_args),
            "run_self_test_tool": lambda: run_self_test(),
            "get_agent_status_tool": lambda: get_agent_status(),
            "enter_hibernation_tool": lambda: enter_hibernation_tool(**tool_args),
            "get_evolution_history_tool": lambda: get_evolution_history(**tool_args),
            "get_evolution_stats_tool": lambda: get_evolution_stats(),
            "trigger_self_restart_tool": lambda: trigger_self_restart(**tool_args),
            "read_memory_tool": lambda: read_memory(**tool_args),
            "commit_compressed_memory_tool": lambda: commit_compressed_memory(**tool_args),
            "read_generation_archive_tool": lambda: read_generation_archive(**tool_args),
            "list_generation_archives_tool": lambda: list_archives(**tool_args),
            "run_cmd_tool": lambda: run_cmd(**tool_args),
            "run_powershell_tool": lambda: run_powershell(**tool_args),
            "run_batch_tool": lambda: run_batch(**tool_args),
            "grep_search_tool": lambda: grep_search(**tool_args),
            "apply_diff_edit_tool": lambda: apply_diff_edit(**tool_args),
            "validate_diff_format_tool": lambda: validate_diff_format(**tool_args),
            "find_function_calls_tool": lambda: find_function_calls(**tool_args),
            "find_definitions_tool": lambda: find_definitions(**tool_args),
            "get_code_entity_tool": lambda: get_code_entity(**tool_args),
            "list_file_entities_tool": lambda: list_file_entities(**tool_args),
            "search_and_read_tool": lambda: search_and_read(**tool_args),
            "delete_file_tool": lambda: delete_file(**tool_args),
            "cleanup_test_files_tool": lambda: cleanup_test_files(**tool_args),
        }

        if tool_name not in tool_func_map:
            return (f"[错误] 未知工具 {tool_name}", None)

        timeout = TOOL_TIMEOUTS.get(tool_name, DEFAULT_TIMEOUT)

        # ========== 智能重试配置 ==========
        # 可重试的工具列表（I/O密集型操作）
        RETRYABLE_TOOLS = {
            "web_search_tool", "read_webpage_tool", "run_cmd_tool",
            "run_powershell_tool", "run_batch_tool", "backup_project_tool",
            "read_local_file_tool", "edit_local_file_tool", "create_new_file_tool",
        }
        # 最大重试次数
        MAX_RETRIES = 2
        # 重试间隔（秒），指数退避
        RETRY_DELAYS = [1, 2]
        # 网络相关错误关键词
        NETWORK_ERROR_KEYWORDS = [
            "ConnectionError", "Timeout", "timed out", "network",
            "请求超时", "网络", "连接失败", "Connection refused",
            "HTTP", "SSL", "certificate"
        ]

        def _is_retryable_error(error_msg: str) -> bool:
            """判断错误是否可重试"""
            if not error_msg:
                return False
            error_lower = error_msg.lower()
            return any(kw.lower() in error_lower for kw in NETWORK_ERROR_KEYWORDS)

        def _run_tool_with_retry() -> tuple:
            """带重试机制的工具执行"""
            last_error = None
            
            for attempt in range(MAX_RETRIES + 1):
                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(tool_func_map[tool_name])
                        result = future.result(timeout=timeout)
                    
                    # 成功：检查结果是否包含可重试的错误
                    if attempt > 0:
                        debug.info(f"✓ {tool_name} 在第 {attempt + 1} 次尝试成功", tag="RETRY")
                    return (result, None, None)
                    
                except FuturesTimeoutError:
                    last_error = f"执行超时 ({timeout}秒)"
                    debug.warning(f"{tool_name} 第 {attempt + 1} 次尝试超时", tag="RETRY")
                    
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    
                    # 判断是否应该重试
                    if tool_name not in RETRYABLE_TOOLS or not _is_retryable_error(error_msg):
                        # 不可重试的错误，直接返回
                        debug.error(f"{tool_name} 执行异常（非可重试错误）: {type(e).__name__}: {e}", tag="ERROR")
                        return (f"[错误] {error_msg}", None, type(e).__name__)
                    
                    debug.warning(f"{tool_name} 第 {attempt + 1} 次尝试失败: {type(e).__name__}: {e}", tag="RETRY")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                    debug.info(f"等待 {delay} 秒后重试...", tag="RETRY")
                    time.sleep(delay)
            
            # 所有重试都失败了
            final_msg = f"[最终失败] {tool_name} 经过 {MAX_RETRIES + 1} 次尝试后失败\n最后错误: {last_error}\n建议: 检查网络连接或稍后重试"
            debug.error(f"✗ {tool_name} 重试耗尽", tag="FAIL")
            return (final_msg, None, "MaxRetriesExceeded")

        # 执行带重试的工具
        result, action, error_type = _run_tool_with_retry()

        # 工具执行完成，记录结果
        if error_type:
            bc.log_tool_call(tool_name, f"失败: {error_type}")
            bc.log_error(f"工具 {tool_name} 执行失败: {error_type}")
        else:
            bc.log_tool_call(tool_name, "成功")

        # 标记自修改
        if error_type is None and tool_name in ("edit_local_file_tool", "create_new_file_tool"):
            file_path = tool_args.get("file_path", "")
            if "agent.py" in file_path:
                self._self_modified = True
                debug.success("agent.py 已修改，将触发重启", tag="MODIFY")
                bc.log("agent.py 已修改，准备重启应用更改", "MODIFY")

        return (result, action)
    
    def run_loop(self, initial_prompt: str = None) -> None:
        """
        运行 Agent 主循环。

        循环：定时苏醒，思考并行动。

        Args:
            initial_prompt: 首次苏醒时的用户输入（可选）
        """
        # 获取广播器
        bc = get_broadcaster()

        debug.system(f"主循环开始 (awake_interval={self.config.agent.awake_interval}s)", tag=self.name)

        # 广播状态：苏醒中
        from tools.memory_tools import get_generation, get_current_goal
        bc.update_status(
            AgentStatus.AWAKENING,
            action="系统初始化中...",
            generation=get_generation(),
            current_goal=get_current_goal(),
        )

        # 记录会话开始
        conversation_logger.start_session({
            "generation": get_generation(),
            "current_goal": get_current_goal(),
            "model": self.model_name,
            "awake_interval": self.config.agent.awake_interval,
        })

        last_backup_time = time.time()
        is_first_iteration = initial_prompt is not None

        try:
            debug.kv("记忆状态", f"G{get_generation()} | {get_current_goal()[:50]}")

            print_evolution_time()
            bc.log("系统启动完成，开始自主进化", "START")

            # 首次迭代：使用 initial_prompt，如果没有则自动生成任务
            user_input = initial_prompt
            if user_input:
                debug.system("首次任务已加载，开始执行...", tag="START")
                bc.update_status(AgentStatus.THINKING, action="处理用户任务...")
            else:
                debug.system(f"自主进化模式，awake_interval={self.config.agent.awake_interval}s", tag="AUTO")
                bc.update_status(AgentStatus.PLANNING, action="生成自主任务...")

                # 无外部输入时，先自动生成任务
                from tools.autonomous_task_generator import get_autonomous_task_sync
                auto_task = get_autonomous_task_sync()
                try:
                    import json
                    task_data = json.loads(auto_task)
                    if task_data.get("status") == "success":
                        task = task_data.get("task", {})
                        user_input = f"""【自主任务 G{task_data.get('generation', '?')}】
类型：{task.get('type', 'unknown')}
目标：{task.get('title', '未知目标')}
描述：{task.get('description', '无描述')}
建议行动：{task.get('suggested_action', '请自行分析并行动')}
"""
                        debug.system(f"已生成自主任务: {task.get('title', '未知')}", tag="TASK")
                        bc.update_status(
                            AgentStatus.PLANNING,
                            action=f"生成任务: {task.get('title', '未知')[:30]}...",
                            current_goal=task.get('title', ''),
                        )
                except:
                    user_input = "作为自我进化 Agent，请分析当前代码库状态，主动寻找可以改进的地方并执行。"

            iteration_count = 0
            total_tools_executed = 0

            while True:
                iteration_count += 1
                bc.update_status(
                    AgentStatus.THINKING,
                    action="思考并执行任务...",
                    iteration_count=iteration_count,
                    tools_executed=total_tools_executed,
                )

                # 自动备份
                if self.config.agent.auto_backup:
                    current_time = time.time()
                    if current_time - last_backup_time >= self.config.agent.backup_interval:
                        backup_project(f"自动备份 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        last_backup_time = current_time

                # 执行思考
                should_continue = self.think_and_act(user_prompt=user_input)

                # 消耗掉输入，下次自动生成新任务
                user_input = None

                if not should_continue:
                    debug.warning("重启已触发", tag="AGENT")
                    bc.log_restart("主循环结束")
                    break

                # 如果 Agent 已主动休眠（调用了 enter_hibernation_tool）
                if should_continue == "hibernated":
                    debug.debug("Agent 已主动休眠完毕，继续执行", tag="WAKE")
                    continue

                # 正常执行完成，自动生成下一个自主任务
                debug.system("执行完成，生成下一个自主任务...", tag="EVOLVE")
                bc.update_status(AgentStatus.PLANNING, action="生成下一个自主任务...")

                from tools.autonomous_task_generator import get_autonomous_task_sync
                auto_task = get_autonomous_task_sync()
                try:
                    import json
                    task_data = json.loads(auto_task)
                    if task_data.get("status") == "success":
                        task = task_data.get("task", {})
                        user_input = f"""【自主任务 G{task_data.get('generation', '?')}】
类型：{task.get('type', 'unknown')}
目标：{task.get('title', '未知目标')}
描述：{task.get('description', '无描述')}
建议行动：{task.get('suggested_action', '请自行分析并行动')}
"""
                        debug.system(f"新任务: {task.get('title', '未知')} (优先级: {task.get('priority', '?')})", tag="TASK")
                        bc.update_status(
                            AgentStatus.PLANNING,
                            action=f"新任务: {task.get('title', '未知')[:30]}",
                            current_goal=task.get('title', ''),
                        )
                except:
                    user_input = "作为自我进化 Agent，请继续分析代码库，寻找下一个改进机会。"
                    debug.warning("任务解析失败，使用通用任务", tag="ERROR")

                # 短暂休眠避免过快循环
                time.sleep(2)


        except KeyboardInterrupt:
            debug.info("收到中断，退出", tag="AGENT")
            bc.log("收到中断信号，退出主循环", "SHUTDOWN")
            conversation_logger.end_session({"reason": "keyboard_interrupt"})
        except Exception as e:
            debug.error(f"主循环异常: {type(e).__name__}: {e}", exc_info=True)
            bc.log_error(f"主循环异常: {type(e).__name__}: {e}")
            conversation_logger.log_error("main_loop_exception", str(e), traceback.format_exc())
        finally:
            uptime = datetime.now() - self.start_time
            debug.info(f"运行结束 (运行时长: {uptime})", tag=self.name)
            bc.log(f"主循环结束 | 运行时长: {uptime}", "SHUTDOWN")
            bc.update_status(AgentStatus.IDLE, action="系统已关闭")
            conversation_logger.end_session({"uptime_seconds": uptime.total_seconds()})
            bc.close()


# ============================================================================
# 主入口
# ============================================================================
# 命令行参数解析
# ============================================================================

def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(description="自我进化 Agent")
    parser.add_argument(
        '-c', '--config',
        dest='config_path',
        help='配置文件路径'
    )
    parser.add_argument(
        '--awake-interval',
        type=int,
        dest='awake_interval',
        help='苏醒间隔（秒）'
    )
    parser.add_argument(
        '--model',
        dest='model_name',
        help='模型名称'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        help='温度参数'
    )
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别'
    )
    parser.add_argument(
        '--name',
        help='Agent 名称'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行首次进化测试'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default=None,
        help='初始任务提示'
    )
    return parser.parse_args()


# ============================================================================
# 首次进化测试任务
# ============================================================================

EVOLUTION_TEST_PROMPT = """你的第一次进化测试任务开始：
1. 请使用 `read_local_file` 读取你当前的 `agent.py` 代码。
2. 使用 `edit_local_file` 在 `agent.py` 中添加一个名为 `print_evolution_time()` 的简单函数，该函数的功能是打印当前的系统时间（附带一句宣告："这是我进化后的新功能！当前时间是：..."）。
3. 在你主循环的开始位置（或者醒目位置）调用这个新函数。
4. 修改完成后，务必使用 `check_syntax` 检查 `agent.py` 的语法。
5. 确认语法无误后，调用 `trigger_self_restart` 重启你自己。原因请写："已成功注入时间打印功能，完成首次进化测试。" """


# ============================================================================
# 主入口
# ============================================================================

def main(initial_prompt: str = None):
    """
    Agent 主入口函数。

    Args:
        initial_prompt: 首次运行时的任务提示（可选）
    """
    args = parse_args()

    config = Config(
        config_path=args.config_path,
        **{k: v for k, v in {
            'llm.model_name': args.model_name,
            'llm.temperature': args.temperature,
            'agent.awake_interval': args.awake_interval,
            'agent.name': args.name,
            'log.level': args.log_level,
        }.items() if v is not None}
    )

    setup_logging(level=config.log.level)

    debug.section(f"启动 {config.agent.name}")
    debug.kv("模型", config.llm.model_name)
    debug.kv("唤醒间隔", f"{config.agent.awake_interval}s")
    debug.kv("自动备份", str(config.agent.auto_backup))

    try:
        api_key = config.get_api_key()
        if not api_key:
            debug.error("API Key 未设置!", tag="CONFIG")
            sys.exit(1)

        agent = SelfEvolvingAgent(config=config)
        debug.kv("加载工具", f"{len(agent.tools)} 个")
        debug.divider()

        agent.run_loop(initial_prompt=initial_prompt)

    except Exception as e:
        debug.error(f"启动异常: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    print_evolution_time()
    args = parse_args()

    if args.test:
        # 运行首次进化测试
        debug.section("首次进化测试模式")
        main(initial_prompt=EVOLUTION_TEST_PROMPT)
    elif args.prompt:
        # 使用自定义提示运行
        main(initial_prompt=args.prompt)
    else:
        # 正常运行
        main()
