# -*- coding: utf-8 -*-
"""
LangChain 工具包装模块

将项目工具统一包装为 LangChain Tool 格式。
"""

import os
import sys
from typing import List, Optional

# 添加项目根目录到 Python 路径（如果尚未添加）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langchain_core.tools import BaseTool

# 导入所有项目工具
from tools.web_tools import web_search, read_webpage
from tools.cmd_tools import (
    read_file,
    edit_local_file,
    create_new_file,
    list_symbols_in_file,
    backup_project,
    delete_file,
    cleanup_test_files,
)
from tools.rebirth_tools import trigger_self_restart
from tools.memory_tools import (
    read_memory,
    commit_compressed_memory,
    get_generation,
    read_generation_archive,
    list_archives,
    read_dynamic_prompt,
    update_generation_task,
    add_insight_to_dynamic,
    record_codebase_insight,
    get_global_codebase_map,
)
from tools.evolution_tracker import log_evolution, get_evolution_history
from tools.search_tools import (
    grep_search,
    find_function_calls,
    find_definitions,
    search_imports,
    search_and_read,
)
from tools.code_tools import apply_diff_edit, validate_diff_format
from tools.cli_tools import execute_cli_command


def create_langchain_tools() -> List[BaseTool]:
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
    def read_local_file_tool(file_path: str, max_lines: Optional[int] = None, offset: int = 0) -> str:
        """
        读取本地文件内容。

        ⚠️ 【Token 保护拦截规则】
        - 如果 .py 文件超过 200 行，将被拦截！
        - 请改用 `list_file_entities` 查看大纲，再用 `get_code_entity` 提取目标函数

        Args:
            file_path: 文件路径
            max_lines: 最大读取行数，默认 None（读取全部）
            offset: 从第几行开始读取（0-based），用于跳过大段代码，默认 0

        Returns:
            格式化的文件内容（带行号）
        """
        # 【拦截规则】大文件保护
        import os
        if file_path.endswith('.py'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                if (max_lines is None or max_lines > 200) and line_count > 200:
                    return (
                        f"[🚫 拦截] 文件过大 ({line_count} 行)！\n"
                        f"禁止大水漫灌式读取 .py 文件！\n\n"
                        f"✅ 正确做法：\n"
                        f"1. 先用 list_file_entities('{file_path}') 查看大纲\n"
                        f"2. 再用 get_code_entity('{file_path}', '目标函数名') 精准提取\n\n"
                        f"如果你需要读取特定部分，可以用 max_lines 参数限制行数（如 max_lines=100）。"
                    )
            except Exception:
                pass

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
    def read_dynamic_prompt_tool() -> str:
        """
        读取当前动态提示词的内容。

        动态提示词区域包含：
        - 当前世代的任务（整个世代有效）
        - 积累的洞察（跨世代保留）

        Returns:
            动态提示词的当前内容
        """
        return read_dynamic_prompt()

    @tool
    def set_generation_task_tool(task: str) -> str:
        """
        【世代开始时必调】设置当前世代的任务。

        每个世代开始时，模型应首先分析当前状态，然后调用此工具
        将自己制定的任务写入系统提示词。该任务在整个世代有效，
        直到下个世代重新生成新任务。

        Args:
            task: 当前世代的任务描述（Markdown 格式）
                例如：
                ```
                1. 探索 tools/ 目录，分析现有工具的实现
                2. 识别可以改进的代码模式
                3. 实现至少一个代码改进
                4. 确保语法正确，重启验证
                ```

        Returns:
            更新结果
        """
        return update_generation_task(task)

    @tool
    def add_insight_tool(insight: str) -> str:
        """
        【随时可调】将洞察追加到积累区域。

        模型在进化过程中发现的洞见、原则、最佳实践等，
        可以通过此工具追加到动态提示词。这些内容会跨世代保留，
        成为模型持续进化的知识基础。

        Args:
            insight: 洞察内容（建议简洁，一两句话）
                例如：
                - "修改多人协作代码时，应先备份"
                - "避免在循环中调用 API"
                - "重要修改后必须重启验证"

        Returns:
            更新结果
        """
        return add_insight_to_dynamic(insight)

    @tool
    def record_codebase_insight_tool(module_path: str, insight: str) -> str:
        """
        【刻印认知】将代码库分析结论持久化到数据库。

        当你重构了某个模块，或者首次探索了一个前代未知的模块后，
        必须立即调用此工具更新认知地图，造福你的下一代！

        ⚠️ 重要：每次修改代码后，都要调用此工具记录你的发现！

        Args:
            module_path: 模块路径，如 'tools/ast_tools.py' 或 'agent.py'
            insight: 该模块的核心作用、已知问题或最佳调用方式
                     例如："包含强大的 AST 透视能力，绝对不要用普通工具读大文件"

        Returns:
            操作结果
        """
        return record_codebase_insight(module_path, insight)

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
        要替换的旧代码（只需包含核心行，无需精确匹配缩进）
        =======
        新代码
        >>>>>>> REPLACE

        【重要】SEARCH 块会自动规范化：
        - 行首空格会被忽略（允许宽松匹配）
        - 行尾空白会被忽略
        - 空行会被跳过
        
        可包含多个块一次性修改多处！

        Args:
            file_path: 要编辑的文件路径
            diff_text: SEARCH/REPLACE 块文本

        Returns:
            操作结果描述
        """
        return apply_diff_edit(file_path=file_path, diff_text=diff_text, allow_fuzzy=True)

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
    def list_file_entities_tool(file_path: str, entity_type: str = "all") -> str:
        """
        【AST 透视】列出 Python 文件的所有类和函数骨架。

        ⚠️ 【铁律】当你初次遇到任何未知的 .py 文件时，**第一步必须是**
        调用此工具获取结构大纲，禁止直接读取全文件！

        使用 Python AST 解析，极速获取：
        - 所有类和函数名称
        - 行号位置
        - 文档字符串预览
        - 装饰器信息

        Args:
            file_path: Python 文件路径
            entity_type: 过滤类型 ('class', 'function', 'all')

        Returns:
            格式化的实体列表，包含名称、类型、位置
        """
        try:
            from tools.ast_tools import list_file_entities
            return list_file_entities(file_path, entity_type)
        except Exception as e:
            return f"[AST 工具错误] 导入失败: {type(e).__name__}: {e}"

    @tool
    def get_code_entity_tool(file_path: str, entity_name: str) -> str:
        """
        【AST 精准抽血】直接提取特定类或函数的完整代码。

        在 list_file_entities 获取大纲后，使用此工具精准提取目标代码。

        适用场景：
        - 知道函数/类名，一键提取完整代码
        - 查看特定方法的实现
        - 避免读取整个大文件

        Args:
            file_path: Python 文件路径
            entity_name: 类名或函数名（如 "SelfEvolvingAgent"、"wake_up"）

        Returns:
            实体的完整代码及行号范围
        """
        try:
            from tools.ast_tools import get_code_entity
            return get_code_entity(file_path, entity_name)
        except Exception as e:
            return f"[AST 工具错误] 导入失败: {type(e).__name__}: {e}"

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
    def execute_cli_command(command: str, timeout: int = 60) -> str:
        """
        【万能 CLI 工具】执行任意 Shell 命令的终极工具。

        基于 CodeAct 范式，这是你的核心能力。你可以用它执行任何命令：
        - ls -la, tree, dir        # 列出目录
        - cat, type, head, tail   # 查看文件
        - grep, find, where        # 搜索文件/内容
        - python -m py_compile     # 语法检查
        - pytest, unittest         # 运行测试
        - pip list, pip install    # 包管理
        - git status, git diff     # Git 操作
        - 任何你想到的 Shell 命令

        Args:
            command: 要执行的 Shell 命令
            timeout: 超时时间（秒），默认 60 秒

        Returns:
            合并后的命令输出（stdout + stderr）
        """
        return execute_cli_command(command, timeout=timeout)

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
        # 网络工具
        web_search_tool,
        read_webpage_tool,
        # 文件操作
        read_local_file_tool,
        edit_local_file_tool,
        create_new_file_tool,
        list_symbols_in_file_tool,
        backup_project_tool,
        # 记忆系统
        read_memory_tool,
        commit_compressed_memory_tool,
        read_dynamic_prompt_tool,
        set_generation_task_tool,
        add_insight_tool,
        record_codebase_insight_tool,
        read_generation_archive_tool,
        list_generation_archives_tool,
        # 生命周期
        trigger_self_restart_tool,
        enter_hibernation_tool,
        get_evolution_history_tool,
        log_evolution_tool,
        # 万能 CLI（CodeAct 范式）
        execute_cli_command,
        # Cursor/Aider 范式工具
        grep_search_tool,
        apply_diff_edit_tool,
        validate_diff_format_tool,
        find_function_calls_tool,
        find_definitions_tool,
        # AST 工具
        get_code_entity_tool,
        list_file_entities_tool,
        search_and_read_tool,
        # 文件清理
        delete_file_tool,
        cleanup_test_files_tool,
    ]
