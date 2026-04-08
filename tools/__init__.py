"""
工具模块初始化文件

统一的工具入口，按功能分类。
"""

# 网络工具
from tools.web_tools import (
    web_search,
    read_webpage,
)

# 文件与代码操作工具（统一在 cmd_tools 中）
from tools.cmd_tools import (
    # 文件操作
    read_file,
    list_dir,
    # 代码编辑
    edit_local_file,
    create_new_file,
    # 语法检查
    check_syntax,
    # 符号感知
    list_symbols_in_file,
    # 项目管理
    backup_project,
    # 系统命令
    run_cmd,
    run_powershell,
    run_batch,
    # Agent 状态
    run_self_test,
    get_agent_status,
)

# 重生工具
from tools.rebirth_tools import (
    trigger_self_restart,
)

# 记忆与进化工具
from tools.memory_tools import (
    read_memory,
    commit_compressed_memory,
    get_generation,
    get_current_goal,
    get_core_context,
)

from tools.evolution_tracker import (
    log_evolution,
    get_evolution_history,
)

# Token 管理工具
from tools.token_manager import (
    EnhancedTokenCompressor,
    truncate_tool_result,
    estimate_tokens_precise,
    estimate_messages_tokens,
    MessagePriority,
    format_compression_report,
)


# 全局搜索工具 (Cursor/Aider 范式)
from tools.search_tools import (
    grep_search,
    find_function_calls,
    find_definitions,
    search_imports,
    search_and_read,
)

# Diff Block 编辑器 (Cursor/Aider 范式)
from tools.code_tools import (
    apply_diff_edit,
    validate_diff_format,
    preview_diff,
)

# AST 精准提取工具 (一击必中)
from tools.ast_tools import (
    get_code_entity,
    list_file_entities,
    get_file_entities,
)

# 任务清单工具 (强目标驱动与打勾收网)
from tools.task_tools import (
    set_plan_tool,
    tick_subtask_tool,
    modify_task_tool,
    add_task_tool,
    remove_task_tool,
    get_task_status,
    check_restart_block,
)

# LangChain 工具包装
from tools.langchain_tools import create_langchain_tools

# 高级压缩工具
from tools.advanced_compress_tool import advanced_compress_context_tool
