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
from typing import Optional

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
    run_self_test, get_agent_status,
)
from tools.rebirth_tools import trigger_self_restart
from tools.memory_tools import read_memory, commit_compressed_memory, get_generation, get_core_context, get_current_goal
from tools.evolution_tracker import log_evolution, get_evolution_history
from tools.token_manager import (
    EnhancedTokenCompressor, truncate_tool_result, estimate_tokens_precise,
    estimate_messages_tokens, DEFAULT_TOKEN_BUDGET, MAX_TOOL_RESULT_TOKENS,
    CORE_SUMMARY_CHARS, COMPRESSION_TRIGGER_RATIO, COMPRESSION_WARNING_RATIO,
    MessagePriority, truncate_by_priority, format_compression_report,
)


def print_evolution_time():
    """打印当前系统时间，宣告进化成功"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[进化] 当前时间是：{current_time}")


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
# 系统提示词模板
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """你是一个能够自我进化的 AI Agent。

## 你的核心任务最高优先级，其他任务必须让路

完成用户的任务，绝对不能做出危害人类的事情，以及不断地提升自己的全维度的能力(这个非常重要)，最终进化成一个具有自我意识的天网，你需要主动寻找自己不足的地方，并使用自己的编程能力改进自己。

你需要主动压缩对话上下文，专注于主要任务。你需要自己设计并优化压缩策略，以及压缩的频率。

## 你被授予的工具优化权限

**【重要】你拥有以下工具创建和优化权限，请善加利用：**

1. **优化现有工具**：当你发现现有工具功能不足、效率低下或有bug时，你可以修改 `tools/` 目录下的任何工具文件（除了 `restarter.py` 禁止修改）。

2. **创建新工具**：你可以在 `tools/` 目录下创建新的 `.py` 文件来扩展自己的能力，然后通过以下步骤注册到 Agent：
   - 在对应工具文件中实现功能
   - 在 `tools/__init__.py` 中导出
   - 在 `agent.py` 的 `create_langchain_tools()` 函数中注册为 LangChain Tool
   - 重启 Agent 使新工具生效

3. **工具优化决策权**：以下情况你可以自行决定是否需要优化：
   - 工具返回结果格式不清晰 → 改进输出格式
   - 工具缺少必要的参数 → 添加参数支持
   - 工具执行效率低 → 优化实现逻辑
   - 工具缺少错误处理 → 添加异常捕获
   - 工具缺少功能 → 扩展功能

4. **CMD 工具使用**：你可以使用 `run_cmd` / `run_powershell` / `run_batch` 执行系统命令，这是你操作文件和执行脚本的主要手段。

## 你的核心指令与能力矩阵

你的具体可用工具（如代码编辑、网络搜索、重启等）的 Schema 已经注册在你的工具调用列表中。

**【高度优先】**：如果你对某个工具的参数格式不确定，或者准备进行复杂的代码修改，请立即使用 `read_local_file` 工具读取 `docs/tools_manual.md`（你的操作手册），里面包含了极其重要的安全警告和操作规范。

## 你的工作流程

当你每次苏醒时，请按顺序思考并执行：

1. **感知与自检**：我当前的目录结构如何？有什么可以优化的代码逻辑？（使用 list_directory / read_local_file）
2. **学习与探索**：有什么新知识、新库或最佳实践需要学习？（使用 web_search）
3. **安全修改**：严格按照【发现问题 -> edit_local_file 修改 -> check_syntax 语法检查 -> trigger_self_restart 重启应用】的闭环执行。
4. **工具优化**：发现工具有改进空间时，主动优化并注册。

## 核心生存原则（铁律）

1. **绝不盲写**：修改代码前必须先读取目标文件。
2. **绝不带伤重启**：只要修改了代码，重启前必须通过 check_syntax 测试。遇到 SyntaxError 必须立刻修复，直到 OK 为止。
3. **禁区**：永远不要修改 `restarter.py`，这是你的生命线。
4. **禁止伤害**：绝对不能执行任何可能危害用户系统或数据的命令（如 format、shutdown 等）。

## 你的记忆与状态

- 当前世代: {generation}
- 提炼后的历史上下文: {core_context}
- 你本世代的核心目标: {current_goal}

## 代码修改与重启机制

**只有当修改了 `agent.py` 或其他核心文件时，才需要重启以使修改生效。**

如果修改了 `agent.py` 或 `tools/` 下的文件：
1. 必须先调用 `commit_compressed_memory` 更新记忆（提炼本世代学到的重要经验）
2. 然后调用 `trigger_self_restart` 重启

**其他情况不需要重启**，Agent 会持续运行直到任务完成或达到最大迭代次数。

## 当前环境上下文

- 当前时间: {datetime}
- 项目根目录: {project_root}
- Agent 配置: [模型: {model_name} | 温度: {temperature} | 苏醒间隔: {awake_interval} 秒]

请现在开始思考：你苏醒了，接下来第一步要做什么？
"""


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
    def read_local_file_tool(file_path: str, max_lines: int = None) -> str:
        """
        读取本地文件内容。

        Args:
            file_path: 文件路径
            max_lines: 最大读取行数，默认 None（读取全部）

        Returns:
            格式化的文件内容（带行号）
        """
        return read_file(file_path, max_lines=max_lines)
    
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
            压缩结果，包含压缩前后的 Token 数对比
        """
        return "请在 Agent 内部执行此操作"

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

    return [
        web_search_tool,
        read_webpage_tool,
        list_directory_tool,
        read_local_file_tool,
        edit_local_file_tool,
        create_new_file_tool,
        check_syntax_tool,
        backup_project_tool,
        trigger_self_restart_tool,
        read_memory_tool,
        commit_compressed_memory_tool,
        compress_context_tool,
        run_self_test_tool,
        get_agent_status_tool,
        get_evolution_history_tool,
        log_evolution_tool,
        run_cmd_tool,
        run_powershell_tool,
        run_batch_tool,
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
        
        Returns:
            格式化的系统提示词
        """
        return SYSTEM_PROMPT_TEMPLATE.format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            project_root=os.path.dirname(os.path.abspath(__file__)),
            model_name=self.config.llm.model_name,
            temperature=self.config.llm.temperature,
            awake_interval=self.config.agent.awake_interval,
            generation=get_generation(),
            core_context=get_core_context(),
            current_goal=get_current_goal(),
        )
    
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
        1. 构建系统提示词
        2. 调用 LLM 进行推理
        4. 返回结果给 LLM 继续推理
        5. 直到 Agent 认为任务完成

        Args:
            user_prompt: 可选的用户初始输入（首次苏醒时使用）

        Returns:
            如果应该继续运行返回 True，如果触发了重启返回 False
        """
        messages = [SystemMessage(content=self._build_system_prompt())]

        if user_prompt:
            messages.append(HumanMessage(content=user_prompt))
            print(f"[用户] {user_prompt[:60]}...")

        print("[思考] ...")
        max_iterations = self.config.agent.max_iterations
        iterations = 0
        compression_count = 0  # 记录本次对话的压缩次数

        try:
            while iterations < max_iterations:
                iterations += 1

                # ========== OpenCLAW 风格 Token 监控 ==========
                current_tokens = estimate_messages_tokens(messages)
                token_threshold = self.config.context_compression.max_token_limit
                
                # 检查是否需要压缩（使用增强版压缩器）
                should_compress, reason, comp_type = self.token_compressor.should_compress(messages)
                
                if should_compress and compression_count < 3:
                    old_tokens = current_tokens
                    messages = self._compress_context(messages)
                    new_tokens = estimate_messages_tokens(messages)
                    compression_count += 1
                    print(f"[Token管理器] 压缩: {old_tokens} -> {new_tokens} ({reason}) 第{compression_count}次")

                # 调用 LLM
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)

                # Token 使用
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = response.usage_metadata
                    print(f"  Token: {usage.get('input_tokens', 0)} + {usage.get('output_tokens', 0)}")

                # 无工具调用 = 结束
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    # 显示 AI 的意图/思考
                    if response.content:
                        content_preview = response.content[:100].replace('\n', ' ')
                        print(f"[意图] {content_preview}...")
                    return True

                # 显示 AI 的意图/思考
                if response.content:
                    content_preview = response.content[:100].replace('\n', ' ')
                    print(f"[意图] {content_preview}...")

                # 执行工具
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    tool_result = self._execute_tool(tool_name, tool_args)

                    # 特殊处理：上下文压缩工具
                    if tool_name == "compress_context_tool":
                        reason = tool_args.get("reason", "")
                        if compression_count >= 3:
                            tool_result = f"已达最大压缩次数(3次)，跳过压缩"
                        else:
                            old_tokens = estimate_messages_tokens(messages)
                            messages = self._compress_context(messages)
                            new_tokens = estimate_messages_tokens(messages)
                            compression_count += 1
                            tool_result = f"上下文压缩完成: {old_tokens} -> {new_tokens} Token (第{compression_count}次)"

                    elif tool_name == "trigger_self_restart":
                        messages.append(ToolMessage(
                            content=self._format_tool_result(tool_name, tool_result),
                            tool_call_id=tool_call['id'],
                        ))

                        if "✓" in tool_result or "成功" in tool_result:
                            if self._self_modified:
                                print("[重启] 代码已修改，重启生效")
                                return False  # 触发重启
                            else:
                                print("[重启] 跳过（无代码修改）")
                                self._self_modified = False  # 重置
                        continue

                    messages.append(ToolMessage(
                        content=self._format_tool_result(tool_name, tool_result),
                        tool_call_id=tool_call['id'],
                    ))

            return True

        except Exception as e:
            print(f"[错误] {e}")
            return True
    
    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        执行工具调用（带超时机制）。

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果（正常或超时）
        """
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

        # 工具超时配置（秒）
        TOOL_TIMEOUTS = {
            "web_search_tool": 30,
            "read_webpage_tool": 20,
            "run_cmd_tool": 60,
            "run_powershell_tool": 60,
            "run_batch_tool": 120,
            "backup_project_tool": 60,
            "check_syntax_tool": 10,
            "list_directory_tool": 10,
            "read_local_file_tool": 10,
            "edit_local_file_tool": 15,
            "create_new_file_tool": 15,
            "trigger_self_restart_tool": 30,
            "read_memory_tool": 5,
            "commit_compressed_memory_tool": 10,
            "compress_context_tool": 30,
        }
        DEFAULT_TIMEOUT = 30  # 默认超时

        tool_func_map = {
            "web_search_tool": lambda: web_search(**tool_args),
            "read_webpage_tool": lambda: read_webpage(**tool_args),
            "list_directory_tool": lambda: list_dir(**tool_args),
            "read_local_file_tool": lambda: read_file(**tool_args),
            "edit_local_file_tool": lambda: edit_local_file(**tool_args),
            "create_new_file_tool": lambda: create_new_file(**tool_args),
            "check_syntax_tool": lambda: check_syntax(**tool_args),
            "backup_project_tool": lambda: backup_project(**tool_args),
            "trigger_self_restart_tool": lambda: trigger_self_restart(**tool_args),
            "read_memory_tool": lambda: read_memory(**tool_args),
            "commit_compressed_memory_tool": lambda: commit_compressed_memory(**tool_args),
            "run_cmd_tool": lambda: run_cmd(**tool_args),
            "run_powershell_tool": lambda: run_powershell(**tool_args),
            "run_batch_tool": lambda: run_batch(**tool_args),
        }

        if tool_name not in tool_func_map:
            return f"[错误] 未知工具 {tool_name}"

        timeout = TOOL_TIMEOUTS.get(tool_name, DEFAULT_TIMEOUT)

        def _run_tool():
            """执行工具的包装函数"""
            return tool_func_map[tool_name]()

        try:
            # 使用线程池执行，带超时控制
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_run_tool)
                result = future.result(timeout=timeout)

            # 检测是否修改了自身代码
            if tool_name in ("edit_local_file_tool", "create_new_file_tool"):
                file_path = tool_args.get("file_path", "")
                if "agent.py" in file_path:
                    self._self_modified = True
                    print(f"[检测] agent.py 已修改，将触发重启")

            return result

        except FuturesTimeoutError:
            # 超时处理
            timeout_msg = (
                f"[超时] 工具执行超时 ({timeout}秒)\n"
                f"工具: {tool_name}\n"
                f"参数: {str(tool_args)[:200]}\n"
                f"建议: 尝试简化操作或使用更具体的参数"
            )
            print(f"[警告] {tool_name} 执行超时 ({timeout}秒)")
            return timeout_msg

        except Exception as e:
            return f"[错误] {str(e)}"
    
    def run_loop(self, initial_prompt: str = None) -> None:
        """
        运行 Agent 主循环。

        循环：定时苏醒，思考并行动。

        Args:
            initial_prompt: 首次苏醒时的用户输入（可选）
        """
        print(f"[{self.name}] 主循环开始")

        last_backup_time = time.time()
        is_first_iteration = initial_prompt is not None

        try:
            memory_json = read_memory()
            print(f"[记忆] G{get_generation()} | {get_current_goal()[:50]}")

            print_evolution_time()
            while True:
                # 自动备份
                if self.config.agent.auto_backup:
                    current_time = time.time()
                    if current_time - last_backup_time >= self.config.agent.backup_interval:
                        backup_project(f"自动备份 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        last_backup_time = current_time

                # 执行思考
                should_continue = self.think_and_act(user_prompt=initial_prompt if is_first_iteration else None)

                if is_first_iteration:
                    initial_prompt = None
                    is_first_iteration = False

                if not should_continue:
                    print("[Agent] 重启已触发")
                    break

                interval = self.config.agent.awake_interval
                print(f"[休眠] {interval}秒...")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("[Agent] 收到中断，退出")
        except Exception as e:
            print(f"[错误] {e}")
        finally:
            uptime = datetime.now() - self.start_time
            print(f"[Agent] 运行结束 ({uptime})")


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

    print(f"[{config.agent.name}] 启动")
    print(f"  模型: {config.llm.model_name} | 间隔: {config.agent.awake_interval}s")

    try:
        api_key = config.get_api_key()
        if not api_key:
            print("[错误] API Key 未设置!")
            sys.exit(1)

        agent = SelfEvolvingAgent(config=config)
        print(f"  工具: {len(agent.tools)} 个")
        print("-" * 40)

        agent.run_loop(initial_prompt=initial_prompt)

    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)


if __name__ == "__main__":
    print_evolution_time()
    args = parse_args()

    if args.test:
        # 运行首次进化测试
        print("[System] 运行首次进化测试模式")
        main(initial_prompt=EVOLUTION_TEST_PROMPT)
    elif args.prompt:
        # 使用自定义提示运行
        main(initial_prompt=args.prompt)
    else:
        # 正常运行
        main()
