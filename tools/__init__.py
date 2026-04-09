# -*- coding: utf-8 -*-
"""
工具模块初始化文件

统一工具入口，所有工具通过 tool_list.py 统一管理。
旧版 __init__.py 导出仅供参考，新代码应从 tool_list 导入。
"""

# ============================================================================
# 推荐导入方式 (新代码使用)
# ============================================================================
# from tools.tool_list import (
#     TOOL_MAP,  # 工具名 -> 函数 映射
#     build_tool_map_with_suffix,  # 构建 agent.py 使用的带 _tool 后缀映射
#     TOOL_TIMEOUT_MAP,  # 超时配置
#     RETRYABLE_TOOLS,  # 可重试工具集合
#     # 具体工具函数
#     web_search, read_file, edit_local_file, ...
# )

# ============================================================================
# 兼容旧代码的导出 (保留但标注)
# ============================================================================

# 以下导出仅为兼容旧代码，新工具请在 tool_list.py 中添加


# ============================================================================
# Shell 工具 (整合自 cli_tools.py 和 cmd_tools.py)
# ============================================================================
from tools.shell_tools import (
    # 文件操作
    read_file as read_file,
    list_directory as list_dir,
    edit_file as edit_local_file,
    create_file as create_new_file,
    check_python_syntax as check_syntax,
    extract_symbols as list_symbols_in_file,
    backup_project as backup_project,
    cleanup_test_files as cleanup_test_files,
    # 命令执行
    execute_shell_command as run_cmd,
    execute_shell_command as execute_cli_command,
    run_powershell as run_powershell,
    run_batch as run_batch,
    # Agent 状态
    self_test as run_self_test,
    get_agent_status as get_agent_status,
)

# 重生工具
from tools.rebirth_tools import (
    trigger_self_restart_tool as trigger_self_restart,
    enter_hibernation_tool as enter_hibernation,
)

# 记忆与进化工具
from tools.memory_tools import (
    read_memory_tool as read_memory,
    commit_compressed_memory_tool as commit_compressed_memory,
    get_generation_tool as get_generation,
    get_current_goal,
    get_core_context,
    read_generation_archive_tool as read_generation_archive,
    list_archives_tool as list_archives,
    read_dynamic_prompt_tool as read_dynamic_prompt,
    update_generation_task_tool as update_generation_task,
    add_insight_to_dynamic_tool as add_insight_to_dynamic,
    record_codebase_insight_tool as record_codebase_insight,
    get_global_codebase_map_tool as get_global_codebase_map,
)

# 全局搜索工具 (Cursor/Aider 范式)
from tools.search_tools import (
    grep_search_tool as grep_search,
    find_function_calls_tool as find_function_calls,
    find_definitions_tool as find_definitions,
    search_imports_tool as search_imports,
    search_and_read_tool as search_and_read,
)

# ============================================================================
# 代码分析工具 (整合自 code_tools.py 和 ast_tools.py)
# ============================================================================
from tools.code_analysis_tools import (
    # AST 工具
    get_code_entity,
    list_file_entities,
    get_file_entities,
    # Diff 工具
    apply_diff_edit,
    apply_diff_edit as apply_diff,
    validate_diff_format,
    preview_diff,
)

# 任务清单工具
from tools.task_tools import (
    set_plan_tool,
    tick_subtask_tool,
    modify_task_tool,
    add_task_tool,
    remove_task_tool,
    get_task_status,
    check_restart_block,
)

# 高级压缩工具
from tools.token_manager import (
    EnhancedTokenCompressor,
    truncate_tool_result,
    estimate_tokens_precise,
    estimate_messages_tokens,
    MessagePriority,
    format_compression_report,
)

# 统一工具映射 (可选依赖)
try:
    from tools.tool_list import (
        TOOL_MAP,
        build_tool_map_with_suffix,
        TOOL_TIMEOUT_MAP,
        RETRYABLE_TOOLS,
    )
except ImportError:
    TOOL_MAP = {}
    build_tool_map_with_suffix = None
    TOOL_TIMEOUT_MAP = {}
    RETRYABLE_TOOLS = set()

__all__ = [
    # 工具映射
    "TOOL_MAP",
    "build_tool_map_with_suffix",
    "TOOL_TIMEOUT_MAP",
    "RETRYABLE_TOOLS",
    # Shell 工具
    "read_file",
    "list_dir",
    "edit_local_file",
    "create_new_file",
    "check_syntax",
    "list_symbols_in_file",
    "backup_project",
    "cleanup_test_files",
    "run_cmd",
    "run_powershell",
    "run_batch",
    "execute_cli_command",
    "run_self_test",
    "get_agent_status",
    # 记忆工具
    "read_memory",
    "commit_compressed_memory",
    "get_generation",
    "get_current_goal",
    "get_core_context",
    "read_generation_archive",
    "list_archives",
    "read_dynamic_prompt",
    "update_generation_task",
    "add_insight_to_dynamic",
    "record_codebase_insight",
    "get_global_codebase_map",
    # 搜索工具
    "grep_search",
    "find_function_calls",
    "find_definitions",
    "search_imports",
    "search_and_read",
    # 代码分析工具
    "apply_diff_edit",
    "apply_diff",
    "validate_diff_format",
    "preview_diff",
    "get_code_entity",
    "list_file_entities",
    "get_file_entities",
    # 任务工具
    "set_plan_tool",
    "tick_subtask_tool",
    "modify_task_tool",
    "add_task_tool",
    "remove_task_tool",
    "get_task_status",
    "check_restart_block",
    # 重生工具
    "trigger_self_restart",
    "enter_hibernation",
    # Token 管理工具
    "EnhancedTokenCompressor",
    "truncate_tool_result",
    "estimate_tokens_precise",
    "estimate_messages_tokens",
    "MessagePriority",
    "format_compression_report",
]
