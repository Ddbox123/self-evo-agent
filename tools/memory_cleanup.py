#!/usr/bin/env python3
"""
瞬时记忆管理器 - 阅后即焚机制

在 Agent 完成"探索期"进入"执行期"时，自动清理中间步骤，
只保留关键的修改结论，大幅减少 Token 消耗。

核心逻辑：
1. 标记"探索期"和"执行期"的消息
2. 在关键操作成功后，自动压缩/清理历史
3. 保留必要的上下文，丢弃无价值的探测日志
"""

from typing import List, Dict, Any, Optional
from enum import Enum


class MessageType(Enum):
    """消息类型枚举"""
    EXPLORATION = "exploration"  # 探索期消息（list_dir, read_file, grep_search 等）
    EXECUTION = "execution"      # 执行期消息（edit_local_file, create_new_file 等）
    RESULT = "result"           # 结果/结论消息
    SYSTEM = "system"           # 系统消息


# 探索期工具（会被标记为"可清理"）
EXPLORATION_TOOLS = {
    'list_directory_tool',
    'read_local_file_tool',
    'grep_search_tool',
    'search_and_read_tool',
    'list_symbols_in_file_tool',
    'get_code_entity_tool',
    'find_function_calls_tool',
    'find_definitions_tool',
    'check_syntax_tool',  # 单独检查语法也属于探索
}

# 执行期工具（操作成功后，前面的探索消息可被清理）
EXECUTION_TOOLS = {
    'edit_local_file_tool',
    'apply_diff_edit_tool',
    'create_new_file_tool',
    'run_cmd_tool',
    'run_powershell_tool',
    'run_batch_tool',
}

# 关键结果关键词（保留包含这些关键词的消息）
KEY_RESULT_PATTERNS = [
    '成功', '完成', '✓', '已修改', '已创建', '语法正确',
    '修改了', '更新了', '新增', '删除', '移动', '重命名'
]


class EphemeralMemoryManager:
    """
    瞬时记忆管理器

    在 Agent 的"探索期"（list_dir, read_file, grep_search 等）完成后，
    自动清理中间步骤，只保留关键结论。
    """

    def __init__(self):
        self._exploration_buffer: List[Dict[str, Any]] = []
        self._last_execution_result: Optional[Dict[str, Any]] = None
        self._compression_enabled = True

    def mark_exploration(self, tool_name: str, args: Dict, result: str) -> None:
        """
        标记一条探索消息

        Args:
            tool_name: 工具名称
            args: 工具参数
            result: 执行结果
        """
        if tool_name in EXPLORATION_TOOLS:
            self._exploration_buffer.append({
                'type': MessageType.EXPLORATION,
                'tool': tool_name,
                'args': args,
                'result': result,
            })

    def mark_execution(self, tool_name: str, args: Dict, result: str, success: bool) -> None:
        """
        标记一条执行消息，并触发记忆清理

        Args:
            tool_name: 工具名称
            args: 工具参数
            result: 执行结果
            success: 是否成功

        Returns:
            需要清理的消息数量
        """
        self._last_execution_result = {
            'type': MessageType.EXECUTION,
            'tool': tool_name,
            'args': args,
            'result': result,
            'success': success,
        }

        # 如果执行成功，清空探索缓冲区
        if success and tool_name in EXECUTION_TOOLS:
            cleared_count = len(self._exploration_buffer)
            self._exploration_buffer.clear()
            return cleared_count

        return 0

    def should_compress(self, message: Dict[str, Any]) -> bool:
        """
        判断消息是否应该被压缩/清理

        Args:
            message: 消息字典

        Returns:
            True 如果应该清理
        """
        if not self._compression_enabled:
            return False

        tool_name = message.get('tool', '')

        # 探索工具的消息通常可以清理
        if tool_name in EXPLORATION_TOOLS:
            return True

        # 检查结果是否包含关键信息
        result = message.get('result', '')
        if result:
            for pattern in KEY_RESULT_PATTERNS:
                if pattern in result:
                    return False

        return False

    def get_exploration_summary(self) -> str:
        """
        获取探索摘要（在清理前）

        Returns:
            探索操作的摘要描述
        """
        if not self._exploration_buffer:
            return ""

        summaries = []
        seen_files = set()

        for item in self._exploration_buffer:
            tool = item['tool']
            args = item['args']

            if tool == 'list_directory_tool':
                summaries.append(f"查看了目录: {args.get('path', '.')}")
            elif tool == 'read_local_file_tool':
                fpath = args.get('file_path', '')
                if fpath not in seen_files:
                    summaries.append(f"读取了文件: {fpath}")
                    seen_files.add(fpath)
            elif tool == 'grep_search_tool':
                summaries.append(f"搜索了: {args.get('regex_pattern', '')}")
            elif tool == 'get_code_entity_tool':
                fpath = args.get('file_path', '')
                entity = args.get('entity_name', '')
                summaries.append(f"提取了 {fpath} 中的 {entity}")

        return " | ".join(summaries) if summaries else ""

    def clear_buffer(self) -> None:
        """清空探索缓冲区"""
        self._exploration_buffer.clear()

    def enable_compression(self) -> None:
        """启用压缩"""
        self._compression_enabled = True

    def disable_compression(self) -> None:
        """禁用压缩"""
        self._compression_enabled = False


# 全局实例
_memory_manager = EphemeralMemoryManager()


def get_memory_manager() -> EphemeralMemoryManager:
    """获取全局记忆管理器实例"""
    return _memory_manager


def compress_message_history(messages: List[Dict[str, Any]], max_history: int = 20) -> List[Dict[str, Any]]:
    """
    压缩消息历史

    在成功执行修改操作后，调用此函数压缩历史消息，
    保留最近的 max_history 条消息，并确保包含关键的执行结果。

    Args:
        messages: 原始消息列表
        max_history: 保留的最大消息数

    Returns:
        压缩后的消息列表
    """
    if len(messages) <= max_history:
        return messages

    # 保留最近的 max_history 条
    compressed = messages[-max_history:]

    return compressed


def filter_exploration_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    过滤探索消息，只保留关键信息

    将多次读取同一文件的操作合并为一条摘要。

    Args:
        messages: 原始消息列表

    Returns:
        过滤后的消息列表
    """
    if not messages:
        return messages

    result = []
    current_file_reads: Dict[str, Dict] = {}  # file_path -> 合并的信息

    for msg in messages:
        tool = msg.get('tool', '')
        args = msg.get('args', {})

        if tool == 'read_local_file_tool':
            fpath = args.get('file_path', '')
            if fpath in current_file_reads:
                # 已读取过此文件，更新行范围
                existing = current_file_reads[fpath]
                new_offset = args.get('offset', 0)
                new_max = args.get('max_lines', float('inf'))
                # 合并为更宽的范围
                existing['args']['offset'] = min(existing['args'].get('offset', 0), new_offset)
                if new_max != float('inf'):
                    existing['args']['max_lines'] = max(existing['args'].get('max_lines', 0), new_max)
            else:
                current_file_reads[fpath] = msg.copy()
        else:
            # 非读取操作，flush 合并的读取
            if current_file_reads:
                for fp, read_msg in current_file_reads.items():
                    result.append(read_msg)
                current_file_reads.clear()
            result.append(msg)

    # Flush 剩余的读取
    if current_file_reads:
        for fp, read_msg in current_file_reads.items():
            result.append(read_msg)

    return result


def create_memory_cleanup_tool():
    """
    创建记忆清理工具

    返回一个函数，可在成功修改后调用以清理历史
    """
    def cleanup_after_success(
        messages: List[Dict[str, Any]],
        keep_last_n: int = 15
    ) -> str:
        """
        在成功操作后清理历史消息

        Args:
            messages: 消息历史
            keep_last_n: 保留最近 N 条消息

        Returns:
            清理摘要
        """
        original_count = len(messages)

        # 过滤重复的探索操作
        filtered = filter_exploration_messages(messages)

        # 截取最近的消息
        compressed = filtered[-keep_last_n:] if len(filtered) > keep_last_n else filtered

        cleaned_count = original_count - len(compressed)

        return (
            f"[记忆清理] 原始消息: {original_count} 条\n"
            f"[记忆清理] 清理后: {len(compressed)} 条\n"
            f"[记忆清理] 减少: {cleaned_count} 条 ({cleaned_count*100//max(original_count,1)}%)"
        )

    return cleanup_after_success


# 导出便捷函数
cleanup_after_success = create_memory_cleanup_tool()
