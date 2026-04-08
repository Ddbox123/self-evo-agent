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

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

# 导入项目工具（统一从 tools 包导入）
from tools import (
    create_langchain_tools,  # LangChain 工具工厂
    advanced_compress_context_tool,  # 压缩工具
    EnhancedTokenCompressor,
    estimate_messages_tokens,
)
from tools.task_tools import (
    set_plan_tool,
    tick_subtask_tool,
    modify_task_tool,
    add_task_tool,
    remove_task_tool,
    get_task_status,
    check_restart_block,
)
from tools.ast_tools import list_file_entities, get_code_entity  # AST 工具
from tools.web_tools import web_search, read_webpage
from tools.cmd_tools import (
    read_file, list_dir, edit_local_file, create_new_file, check_syntax,
    list_symbols_in_file, backup_project, run_self_test, get_agent_status,
    run_cmd, run_powershell, run_batch,
)
from tools.search_tools import grep_search, find_function_calls, find_definitions, search_and_read
from tools.code_tools import apply_diff_edit, validate_diff_format
from tools.evolution_tracker import get_evolution_history, get_evolution_stats
from tools.memory_tools import (
    read_memory, commit_compressed_memory, get_generation,
    get_core_context, get_current_goal, archive_generation_history,
    read_generation_archive, list_archives, advance_generation, _load_memory,
    read_dynamic_prompt, update_generation_task, add_insight_to_dynamic
)
from tools.rebirth_tools import trigger_self_restart
from tools.cli_tools import execute_cli_command
from tools.state_broadcaster import (
    StateBroadcaster, AgentStatus, get_broadcaster,
    update_agent_status, log_agent_event, get_agent_state
)

# 导入 CLI UI 渲染引擎
from core.cli_ui import (
    UIManager, get_ui, ui_print_header, ui_thinking,
    ui_print_tool, ui_warning, ui_error, ui_success, ui_log,
    ui_update_status, ui_task_board
)

# 导入优雅对话渲染器
from core.transcript_logger import get_transcript_logger

import traceback
import threading


# ============================================================================
# 调试日志系统 - 统一管理 Agent 运行时的终端输出
# ============================================================================

# 全局 UI 管理器实例
_ui = get_ui()

# 保留旧的 DebugLogger 以保持向后兼容，但内部使用 cli_ui
class DebugLogger:
    """
    统一调试日志系统 - 基于 rich 的 Claude Code 级输出

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

    def _format(self, tag: str, msg: str) -> str:
        """格式化日志消息"""
        parts = []
        if self.show_timestamps:
            parts.append(f"[{self._timestamp()}]")
        parts.append(f"[{tag}]")
        parts.append(f"{self._indent()}{msg}")
        return " ".join(parts)

    def debug(self, msg: str, tag: str = "DEBUG"):
        """调试信息"""
        if self.verbose:
            ui_log(msg, "DEBUG")

    def info(self, msg: str, tag: str = "INFO"):
        """一般信息"""
        ui_log(msg, "INFO")

    def success(self, msg: str, tag: str = "OK"):
        """成功信息"""
        ui_success(msg)

    def warning(self, msg: str, tag: str = "WARN"):
        """警告信息"""
        ui_warning(msg)

    def error(self, msg: str, tag: str = "ERROR", exc_info: bool = False):
        """错误信息"""
        ui_error(msg, traceback.format_exc() if exc_info else None)

    def system(self, msg: str, tag: str = "SYS"):
        """系统信息"""
        ui_log(msg, "SYS")

    def tool(self, name: str, status: str, details: str = ""):
        """工具执行日志"""
        ui_log(f"Tool: {name} {status} {details}", "TOOL")

    def llm(self, msg: str, details: str = ""):
        """LLM 调用日志"""
        ui_log(f"{msg} {details}", "LLM")

    def llm_response(self, content: str, prefix: str = "LLM 回复"):
        """打印完整的 LLM 输出内容"""
        _ui.console.print()
        _ui.console.print(f"[bold magenta]--- {prefix} ---[/bold magenta]")
        _ui.console.print(content[:500], style="dim")
        _ui.console.print(f"[bold magenta]---[/bold magenta]")
        _ui.console.print()

    def llm_thinking(self, content: str):
        """打印 LLM 的思考过程"""
        _ui.console.print()
        _ui.console.print("[bold magenta]-- Thinking --[/bold magenta]")
        for line in content.split('\n')[:10]:
            if line.strip():
                _ui.console.print(f"  {line[:100]}", style="dim")
        _ui.console.print()

    def tool_start(self, tool_name: str, args: dict):
        """打印工具开始调用"""
        ui_print_tool(tool_name, args)

    def tool_result(self, tool_name: str, result: str, success: bool = True):
        """打印工具执行结果"""
        ui_print_tool(tool_name, result=result, success=success)

    def session_start(self, model: str, generation: int = 1):
        """开始会话"""
        ui_print_header(model, generation)
        ui_update_status("AWAKENING", generation=generation)

    def turn_end(self, turn_num: int, tool_count: int = 0):
        """结束一轮对话"""
        ui_log(f"Turn {turn_num} complete | Tools: {tool_count}", "TURN")

    def section(self, title: str):
        """分节标题"""
        _ui.console.print()
        _ui.console.print(f"[bold cyan]=== {title} ===[/bold cyan]")

    def divider(self, char: str = "-", length: int = 60):
        """分隔线"""
        _ui.console.print(char * length)

    def kv(self, key: str, value: str):
        """键值对输出"""
        _ui.console.print(f"  [cyan]{key}[/cyan]: {value}")

    def banner(self, title: str):
        """横幅"""
        _ui.console.print()
        _ui.console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
        _ui.console.print(f"[bold cyan]  {title}[/bold cyan]")
        _ui.console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
        _ui.console.print()

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

    def turn_start(self, turn_num: int, context: str = ""):
        """
        开始新的轮次（打印分隔线和标题）

        Args:
            turn_num: 轮次编号
            context: 上下文信息
        """
        print()
        print(f"{'═'*70}")
        print(f"  🔄 第 {turn_num} 轮对话")
        if context:
            print(f"  📋 {context}")
        print(f"{'═'*70}")
        print()

    # Legacy methods kept for compatibility (now delegate to cli_ui)
    def turn_end(self, turn_num: int, tool_count: int = 0):
        """结束一轮对话"""
        ui_log(f"Turn {turn_num} complete | Tools: {tool_count}", "TURN")

    def session_start(self, model: str, generation: int = 1):
        """开始会话"""
        ui_print_header(model, generation)
        ui_update_status("AWAKENING", generation=generation)

    def section(self, title: str):
        """分节标题"""
        _ui.console.print()
        _ui.console.print(f"[bold cyan]=== {title} ===[/bold cyan]")

    def divider(self, char: str = "-", length: int = 60):
        """分隔线"""
        _ui.console.print(char * length)

    def kv(self, key: str, value: str):
        """键值对输出"""
        _ui.console.print(f"  [cyan]{key}[/cyan]: {value}")

    def banner(self, title: str):
        """横幅"""
        _ui.console.print()
        _ui.console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
        _ui.console.print(f"[bold cyan]  {title}[/bold cyan]")
        _ui.console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
        _ui.console.print()


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

# 优雅对话渲染器（Markdown 格式）
transcript_logger = get_transcript_logger()


def _get_total_generations() -> int:
    """获取总世代数"""
    memory = _load_memory()
    return memory.get("total_generations", 1)
from tools.token_manager import (
    EnhancedTokenCompressor, estimate_tokens_precise,
    estimate_messages_tokens, DEFAULT_TOKEN_BUDGET,
    CORE_SUMMARY_CHARS, COMPRESSION_TRIGGER_RATIO, COMPRESSION_WARNING_RATIO,
    MessagePriority, truncate_by_priority, format_compression_report,
)
from core.prompt_builder import build_system_prompt


def print_evolution_time():
    """打印当前系统时间"""
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

    使用精确估算函数，避免低估。
    """
    from tools.token_manager import estimate_tokens_precise
    return estimate_tokens_precise(text)


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

        # 添加超时配置
        llm_kwargs["timeout"] = getattr(self.config.llm, 'api_timeout', 120)
        llm_kwargs["request_timeout"] = llm_kwargs["timeout"]

        self.llm = ChatOpenAI(**llm_kwargs)
        self.model_name = self.config.llm.model_name

        # System Prompt 写入标记（用于 Markdown 双写）
        self._system_prompt_written = False

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

        # 添加超时配置
        compression_llm_kwargs["timeout"] = getattr(self.config.llm, 'api_timeout', 120)
        compression_llm_kwargs["request_timeout"] = compression_llm_kwargs["timeout"]

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
        messages = [SystemMessage(content=self._build_system_prompt())]

        # 获取当前轮次编号（使用 conversation_logger 作为唯一真相来源）
        # 注意：必须在 log_user_input 之后计算，因为 log_user_input 会递增计数器
        if user_prompt:
            conversation_logger.log_user_input(user_prompt)
            current_turn = conversation_logger._turn_count
        else:
            current_turn = conversation_logger._turn_count + 1

        # 首次对话：写入 System Prompt（折叠形式）
        if not self._system_prompt_written:
            system_prompt_content = self._build_system_prompt()
            transcript_logger.write_system_prompt(system_prompt_content)
            self._system_prompt_written = True

        if user_prompt:
            messages.append(HumanMessage(content=user_prompt))
            # 双写：Markdown 格式
            transcript_logger.start_turn(current_turn)
            transcript_logger.write_user_input(user_prompt)
        else:
            transcript_logger.start_turn(current_turn)

        # 打印会话开始信息（只在第一次）
        conversation_logger.log_llm_request(messages, model=self.model_name)
        max_iterations = self.config.agent.max_iterations
        iterations = 0

        try:
            while iterations < max_iterations:
                iterations += 1

                # ========== 【新增】自动 Token 检查与压缩 ==========
                # 在每次 LLM 调用前检查 Token 预算
                current_tokens = estimate_messages_tokens(messages)
                max_budget = self.config.context_compression.max_token_limit
                
                # 预压缩阈值：60% 时提前压缩
                preemptive_threshold = int(max_budget * 0.6)
                # 强制压缩阈值：80% 时必须压缩
                forced_threshold = int(max_budget * 0.8)
                
                if current_tokens > forced_threshold:
                    # 强制压缩
                    debug.warning(f"[压缩] Token 过高 ({current_tokens}/{max_budget})，自动压缩", tag="TOKEN")
                    old_tokens = current_tokens
                    messages = self._compress_context(messages)
                    new_tokens = estimate_messages_tokens(messages)
                    debug.success(f"[压缩完成] {old_tokens} -> {new_tokens} (节省 {old_tokens - new_tokens})", tag="TOKEN")
                    conversation_logger.log_compression(old_tokens, new_tokens, old_tokens - new_tokens)
                    # 双写：Markdown 格式
                    transcript_logger.write_compression(old_tokens, new_tokens, old_tokens - new_tokens)
                elif current_tokens > preemptive_threshold and iterations > 1:
                    # 预压缩（跳过第一次迭代，避免过早压缩）
                    debug.info(f"[预压缩] Token 接近阈值 ({current_tokens}/{max_budget})，提前压缩", tag="TOKEN")
                    old_tokens = current_tokens
                    messages = self._compress_context(messages)
                    new_tokens = estimate_messages_tokens(messages)
                    debug.success(f"[预压缩完成] {old_tokens} -> {new_tokens}", tag="TOKEN")
                    # 双写：Markdown 格式
                    transcript_logger.write_compression(old_tokens, new_tokens, old_tokens - new_tokens)
                # ========== 自动 Token 检查结束 ==========

                # 第一次循环打印会话开始
                if iterations == 1:
                    debug.session_start(self.model_name, get_generation())

                # 调用 LLM（带超时）
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

                def invoke_llm():
                    return self.llm_with_tools.invoke(messages)

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(invoke_llm)
                    try:
                        # 使用配置中的 api_timeout（默认300秒）
                        llm_timeout = getattr(self.config.llm, 'api_timeout', 300)
                        response = future.result(timeout=llm_timeout)
                    except FuturesTimeoutError:
                        debug.error(f"LLM 调用超时 ({llm_timeout}秒)", tag="LLM")
                        conversation_logger.log_error("llm_timeout", f"LLM 调用超时 ({llm_timeout}秒)")
                        return True  # 继续下一次循环
                    except Exception as e:
                        # 捕获其他异常（如取消、网络错误等）
                        debug.error(f"LLM 调用异常: {type(e).__name__}: {e}", tag="LLM")
                        conversation_logger.log_error("llm_error", f"{type(e).__name__}: {e}")
                        return True  # 继续下一次循环

                messages.append(response)

                # 记录 LLM 响应
                conversation_logger.log_llm_response(
                    response_content=response.content or "",
                    raw_response=response.content or ""
                )

                # 双写：Markdown 格式
                transcript_logger.write_llm_response(response.content or "")

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
                    # 显示 AI 的完整回复
                    if response.content:
                        debug.llm_response(response.content, "📤 LLM 最终回复")
                        conversation_logger.log_llm_intent("final_response", response.content[:300])
                    return True

                # 显示 AI 的意图/思考
                if response.content:
                    debug.llm_thinking(response.content)
                    conversation_logger.log_llm_intent("tool_call", response.content[:300])

                # 执行工具
                for tool_call in tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})

                    # 显示工具调用开始
                    debug.tool_start(tool_name, tool_args)
                    conversation_logger.log_tool_call(tool_name, tool_args, status="called")
                    # 双写：Markdown 格式
                    transcript_logger.write_tool_call(tool_name, tool_args, status="called")

                    # 执行工具（返回结果和特殊动作）
                    tool_result, action = self._execute_tool(tool_name, tool_args, messages)

                    # 【调试】确保工具结果被正确记录
                    if tool_result is None:
                        debug.warning(f"[警告] {tool_name} 返回 None", tag="TOOL")

                    # 显示工具执行结果（添加异常保护）
                    success = action not in ["restart", "error"]
                    try:
                        if tool_result is not None:
                            debug.tool_result(tool_name, str(tool_result), success)
                            # 同时记录到对话日志
                            conversation_logger.log_tool_call(tool_name, tool_args, str(tool_result), status="completed")
                            # 双写：Markdown 格式
                            transcript_logger.write_tool_call(tool_name, tool_args, str(tool_result), status="success")
                        else:
                            print(f"\n[TOOL] {tool_name}: None\n")
                            conversation_logger.log_tool_call(tool_name, tool_args, "[无返回]", status="completed")
                            # 双写：Markdown 格式
                            transcript_logger.write_tool_call(tool_name, tool_args, "[无返回]", status="success")
                    except Exception as e:
                        print(f"\n[TOOL ERROR] {tool_name}: {str(e)[:100]}\n")

                    # 处理特殊动作
                    if action == "restart":
                        conversation_logger.log_action("restart", {"tool": tool_name})
                        return False  # 触发重启
                    elif action == "skip":
                        conversation_logger.log_action("skip", {"tool": tool_name})
                        messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call['id']))
                        conversation_logger.log_tool_call(tool_name, tool_args, tool_result, status="skipped")
                        continue  # 跳过添加结果
                    elif action == "hibernated":
                        conversation_logger.log_action("hibernated", {"tool": tool_name})
                        messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call['id']))
                        return "hibernated"

                    # 将工具结果添加到消息中（所有非特殊动作的情况）
                    messages.append(ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call['id'],
                    ))

            # 打印轮次结束信息
            debug.turn_end(current_turn, tool_count=len(tool_calls) if tool_calls else 0)
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

        # trigger_self_restart_tool: 世代归档 + 强制测试门控 + 任务清单拦截
        if tool_name == "trigger_self_restart_tool" and messages is not None:
            # ========== 【新】任务清单拦截检查 ==========
            is_blocked, block_msg = check_restart_block()
            if is_blocked:
                debug.warning("任务清单未完成，禁止重启", tag="TASK_BLOCK")
                return (block_msg, None)
            # ========== 任务清单拦截结束 ==========

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

            # 从消息历史中查找模型自己提交的 memory 更新
            # 支持两种方式：1) 调用 commit_compressed_memory_tool 2) 在思考中声明
            model_core_wisdom = None
            model_next_goal = None
            
            import re
            for msg in messages:
                if not hasattr(msg, 'content') or not isinstance(msg.content, str):
                    continue
                    
                tool_name = str(getattr(msg, 'name', ''))
                
                # 方式1: 检查工具调用的名称
                if msg.type == "tool" and "commit_compressed_memory" in tool_name:
                    try:
                        import json as _json
                        result = _json.loads(msg.content)
                        if result.get("status") == "success":
                            model_core_wisdom = result.get("core_wisdom", "") or result.get("new_core_context", "")
                            model_next_goal = result.get("next_goal", "")
                            debug.info(f"检测到模型提交的记忆: {model_core_wisdom[:50]}...", tag="MEMORY")
                    except:
                        pass
                
                # 方式2: 从 AI 思考内容中提取 commit 调用
                if msg.type == "ai":
                    content = msg.content
                    # 查找 new_core_context 和 next_goal 的声明
                    wisdom_match = re.search(r'new_core_context["\s:]+["\']([^"\']+)["\']', content)
                    goal_match = re.search(r'next_goal["\s:]+["\']([^"\']+)["\']', content)
                    if wisdom_match and not model_core_wisdom:
                        model_core_wisdom = wisdom_match.group(1)[:300]
                    if goal_match and not model_next_goal:
                        model_next_goal = goal_match.group(1)[:200]
            
            intermediate_steps = []
            for msg in messages:
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    if msg.type == "ai" and msg.content:
                        intermediate_steps.append({"type": "thought", "content": msg.content[:500]})
                    elif msg.type == "tool":
                        intermediate_steps.append({"type": "tool_call", "name": getattr(msg, 'name', 'unknown'), "content": msg.content[:200]})
            
            current_gen = get_generation()
            # 优先使用模型自己提交的更新，否则使用 memory.json 中的旧值
            core_wisdom = model_core_wisdom if model_core_wisdom else (get_core_context() or "无")
            current_goal = model_next_goal if model_next_goal else (get_current_goal() or "待定")
            archive_result = archive_generation_history(generation=current_gen, history_data=intermediate_steps, core_wisdom=core_wisdom, next_goal=current_goal)
            new_gen = advance_generation()
            debug.info(f"归档完成: {archive_result}", tag="ARCHIVE")
            debug.success(f"G{current_gen} -> G{new_gen}", tag="GENERATION")
            
            # 重启前准备：清除 DYNAMIC.md 中的任务区域（为下一世代留空）
            from tools.memory_tools import clear_generation_task
            clear_result = clear_generation_task()
            debug.info(f"准备下一世代: {clear_result}", tag="DYNAMIC")
            
            tool_result = trigger_self_restart(**tool_args)
            tool_result_with_archive = f"{tool_result}\n[世代归档] G{current_gen} -> G{new_gen}"

            # 有错误时阻止重启
            if error_type and not self._self_modified:
                return (f"{tool_result_with_archive}\n\n[BLOCKED] 重启被阻止：{error_type}", "skip")

            debug.success("重启生效" if self._self_modified else "重启以保存记忆", tag="RESTART")
            self._self_modified = False
            return (tool_result_with_archive, "restart")

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
            "read_dynamic_prompt_tool": 5, "set_generation_task_tool": 10, "add_insight_tool": 10,
            "read_generation_archive_tool": 10, "list_generation_archives_tool": 5,
            "compress_context_tool": 30, "grep_search_tool": 30, "apply_diff_edit_tool": 15,
            "validate_diff_format_tool": 5, "find_function_calls_tool": 30, "find_definitions_tool": 30,
            "get_code_entity_tool": 15, "list_file_entities_tool": 10, "search_and_read_tool": 30,
            "delete_file_tool": 10, "cleanup_test_files_tool": 30,
            # 任务清单工具
            "set_plan_tool": 10, "tick_subtask_tool": 5, "modify_task_tool": 5,
            "add_task_tool": 5, "remove_task_tool": 5, "get_task_status_tool": 5,
        }
        DEFAULT_TIMEOUT = 30

        tool_func_map = {
            # 网络工具
            "web_search_tool": lambda: web_search(**tool_args),
            "read_webpage_tool": lambda: read_webpage(**tool_args),
            # 文件操作
            "list_directory_tool": lambda: list_dir(**tool_args),
            "read_local_file_tool": lambda: read_file(**tool_args),
            "edit_local_file_tool": lambda: edit_local_file(**tool_args),
            "create_new_file_tool": lambda: create_new_file(**tool_args),
            "delete_file_tool": lambda: delete_file(**tool_args),
            # 代码工具
            "check_syntax_tool": lambda: check_syntax(**tool_args),
            "list_symbols_in_file_tool": lambda: list_symbols_in_file(**tool_args),
            "backup_project_tool": lambda: backup_project(**tool_args),
            "cleanup_test_files_tool": lambda: cleanup_test_files(**tool_args),
            # Agent 状态
            "run_self_test_tool": lambda: run_self_test(),
            "get_agent_status_tool": lambda: get_agent_status(),
            # 进化历史
            "get_evolution_history_tool": lambda: get_evolution_history(**tool_args),
            "get_evolution_stats_tool": lambda: get_evolution_stats(),
            "trigger_self_restart_tool": lambda: trigger_self_restart(**tool_args),
            # 记忆工具
            "read_memory_tool": lambda: read_memory(**tool_args),
            "commit_compressed_memory_tool": lambda: commit_compressed_memory(**tool_args),
            "read_dynamic_prompt_tool": lambda: read_dynamic_prompt(**tool_args),
            "set_generation_task_tool": lambda: update_generation_task(**tool_args),
            "add_insight_tool": lambda: add_insight_to_dynamic(**tool_args),
            "read_generation_archive_tool": lambda: read_generation_archive(**tool_args),
            "list_generation_archives_tool": lambda: list_archives(**tool_args),
            # CLI 工具
            "run_cmd_tool": lambda: run_cmd(**tool_args),
            "run_powershell_tool": lambda: run_powershell(**tool_args),
            "run_batch_tool": lambda: run_batch(**tool_args),
            "execute_cli_command": lambda: self._execute_cli(**tool_args),
            # 搜索工具
            "grep_search_tool": lambda: grep_search(**tool_args),
            "apply_diff_edit_tool": lambda: apply_diff_edit(**tool_args),
            "validate_diff_format_tool": lambda: validate_diff_format(**tool_args),
            "find_function_calls_tool": lambda: find_function_calls(**tool_args),
            "find_definitions_tool": lambda: find_definitions(**tool_args),
            # AST 工具
            "get_code_entity_tool": lambda: get_code_entity(**tool_args),
            "list_file_entities_tool": lambda: list_file_entities(**tool_args),
            "search_and_read_tool": lambda: search_and_read(**tool_args),
            # ========== 任务清单工具 ==========
            "set_plan_tool": lambda: set_plan_tool(**tool_args),
            "tick_subtask_tool": lambda: tick_subtask_tool(**tool_args),
            "modify_task_tool": lambda: modify_task_tool(**tool_args),
            "add_task_tool": lambda: add_task_tool(**tool_args),
            "remove_task_tool": lambda: remove_task_tool(**tool_args),
            "get_task_status_tool": lambda: get_task_status(),
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

            # 【新增】CLI 命令错误检测：阻止假阳性导致盲目重启
            # 如果 execute_cli_command 返回失败标记，添加错误类型标记
            if tool_name in ("execute_cli_command", "run_cmd_tool", "run_powershell_tool", "run_batch_tool"):
                if result and "[EXEC FAILURE" in result:
                    # 真正的失败：标记为错误，防止 Agent 误以为成功
                    error_type = "ExecFailure"
                    bc.log_error(f"CLI 命令执行失败: {result[:100]}")

        # 标记自修改
        if error_type is None and tool_name in ("edit_local_file_tool", "create_new_file_tool"):
            file_path = tool_args.get("file_path", "")
            if "agent.py" in file_path:
                self._self_modified = True
                debug.success("agent.py 已修改，将触发重启", tag="MODIFY")
                bc.log("agent.py 已修改，准备重启应用更改", "MODIFY")

        return (result, action)

    def _execute_cli(self, command: str, timeout: int = 60) -> str:
        """执行 CLI 命令"""
        return execute_cli_command(command, timeout=timeout)

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

        # 初始化优雅对话渲染器（Markdown 格式）
        generation = get_generation()
        transcript_logger.start_generation(generation)
        transcript_logger.write_action("会话开始", f"世代: G{generation}, 模型: {self.model_name}")

        # 重置 System Prompt 写入标记
        self._system_prompt_written = False

        # 自动清理旧的 transcript 文件（保留最近 5 个）
        transcript_logger.cleanup_old_transcripts(keep_recent=5)

        # 标记是否已写入 System Prompt（避免重复写入）
        _system_prompt_written_for_session = False

        last_backup_time = time.time()

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
                bc.update_status(AgentStatus.PLANNING, action="模型自主决策中...")

                # 模型自主决策：直接进入 think_and_act，让模型根据 SOUL.md 的使命自主决定任务
                user_input = "【自主进化】你是完全自主的进化体，请根据 SOUL.md 的使命指示，结合当前代码库状态，自主决定对你最有利的任务。分析自己制定的任务并执行。"

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

                # 正常执行完成，模型自主决策下一个行动
                debug.system("执行完成，模型自主决策下一轮进化...", tag="EVOLVE")
                bc.update_status(AgentStatus.PLANNING, action="模型自主决策中...")

                # 模型自主决策
                user_input = "【自主进化】任务完成。请分析本轮执行结果和当前代码库状态，自主决定下一个最有价值的行动。持续进化！"

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
            # 双写：Markdown 格式 - 结束世代记录
            transcript_logger.end_generation(f"运行时长: {uptime}")
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
    parser.add_argument(
        '--auto',
        action='store_true',
        help='自动模式（无交互）'
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
    # 初始化 Rich UI
    ui = get_ui()

    # 打印启动横幅
    ui.console.clear()
    ui.console.print()
    ui.console.print("[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]")
    ui.console.print("[bold cyan]║                                                          ║[/bold cyan]")
    ui.console.print("[bold cyan]║[bold white]Self-Evolving Agent[/bold white] - Terminal Edition ║[/bold cyan]")
    ui.console.print("[bold cyan]║                                                          ║[/bold cyan]")
    ui.console.print("[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]")
    ui.console.print()

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

    # 使用 Rich 表格显示配置
    ui.console.print(f"[bold]启动 {config.agent.name}[/bold]")
    ui.console.print(f"  [cyan]Model:[/cyan]   {config.llm.model_name}")
    ui.console.print(f"  [cyan]Awake:[/cyan]   {config.agent.awake_interval}s")
    ui.console.print(f"  [cyan]Backup:[/cyan]   {config.agent.auto_backup}")
    ui.console.print()

    try:
        api_key = config.get_api_key()
        if not api_key:
            ui_error("API Key 未设置!", None)
            sys.exit(1)

        agent = SelfEvolvingAgent(config=config)
        ui.console.print(f"  [green]Tools:[/green]   {len(agent.tools)} loaded")
        ui.console.print("[dim]─" * 60 + "[/dim]")
        ui.console.print()

        # 如果是自动模式，直接启动
        if args.auto or initial_prompt:
            agent.run_loop(initial_prompt=initial_prompt)
        else:
            # 交互模式：显示漂亮的提示符
            ui.console.print("[bold yellow]交互模式[/bold yellow] - 输入指令或按 Enter 进入自动模式")
            ui.console.print("[dim]提示: 输入 /help 查看命令，/auto 进入自动模式，/quit 退出[/dim]")
            ui.console.print()

            while True:
                try:
                    user_input = input("[bold cyan]Agent[/bold cyan] > ").strip()

                    if not user_input:
                        # Enter 键进入自动模式
                        ui.console.print("[dim]进入自动模式...[/dim]")
                        agent.run_loop()
                        break

                    elif user_input.lower() in ['/quit', '/exit', '/q']:
                        ui.console.print("[yellow]再见![/yellow]")
                        break

                    elif user_input.lower() in ['/auto', '/a']:
                        ui.console.print("[dim]进入自动模式...[/dim]")
                        agent.run_loop()
                        break

                    elif user_input.lower() in ['/help', '/h', '/?']:
                        ui.console.print("""
[bold cyan]可用命令:[/bold cyan]
  /auto, /a     - 进入自动模式
  /quit, /q     - 退出程序
  /help, /h     - 显示此帮助
  <任意文本>     - 将文本作为任务发送给 Agent
""")
                        continue

                    else:
                        # 作为任务运行
                        agent.run_loop(initial_prompt=user_input)
                        ui.console.print()
                        ui.console.print("[dim]─" * 60 + "[/dim]")
                        ui.console.print("[yellow]返回交互模式[/yellow]")
                        ui.console.print()

                except KeyboardInterrupt:
                    ui.console.print("\n[yellow]中断，退出...[/yellow]")
                    break
                except EOFError:
                    break

    except Exception as e:
        ui_error(f"启动异常: {type(e).__name__}: {e}", traceback.format_exc())
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
