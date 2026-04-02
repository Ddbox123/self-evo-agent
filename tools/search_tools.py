#!/usr/bin/env python3
"""
全局搜索工具 - 模拟 IDE 的全局正则检索

提供类似 Cursor/Aider 的全局代码搜索能力，支持：
1. 正则表达式全文搜索
2. 文件类型过滤
3. 大文件智能处理
4. 匹配上下文展示
"""

import re
import os
from pathlib import Path
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# 搜索配置
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_MATCHES_PER_FILE = 100
MAX_CONTEXT_LINES = 3  # 匹配行前后显示的上下文行数
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg', 'node_modules',
    '.venv', 'venv', 'env', '.env', '.idea', '.vscode',
    'dist', 'build', '.tox', '.pytest_cache', '.mypy_cache',
    'site-packages', 'egg-info', '.eggs'
}
SKIP_EXTENSIONS = {'.exe', '.dll', '.so', '.dylib', '.pyc', '.pyo', '.pyd'}
INCLUDE_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json', '.yaml', '.yml', '.toml', '.txt', '.html', '.css', '.xml', '.sh', '.bat', '.ps1'}


def _normalize_path(file_path: str) -> Path:
    """规范化文件路径"""
    return Path(file_path).resolve()


def _should_skip_path(path: Path) -> bool:
    """检查是否应该跳过该路径"""
    parts = path.parts
    for skip_dir in SKIP_DIRS:
        if skip_dir in parts:
            return True
    return False


def _should_process_file(file_path: Path) -> bool:
    """检查是否应该处理该文件"""
    if not file_path.is_file():
        return False
    if file_path.suffix.lower() in SKIP_EXTENSIONS:
        return False
    try:
        size = file_path.stat().st_size
        if size > MAX_FILE_SIZE:
            return False
    except OSError:
        return False
    return True


def grep_search(
    regex_pattern: str,
    include_ext: str = ".py",
    search_dir: str = ".",
    case_sensitive: bool = True,
    max_results: int = 500
) -> str:
    """
    全局正则表达式搜索

    Args:
        regex_pattern: 正则表达式模式
        include_ext: 要搜索的文件扩展名（如 ".py", ".js", "*" 表示所有）
        search_dir: 搜索的根目录
        case_sensitive: 是否区分大小写
        max_results: 最大返回结果数

    Returns:
        格式化的搜索结果，包含文件路径、行号、匹配行内容
    """
    if not regex_pattern:
        return "[搜索] 错误: 正则表达式不能为空"

    search_dir_path = _normalize_path(search_dir)
    if not search_dir_path.exists():
        return f"[搜索] 错误: 目录不存在 - {search_dir_path}"

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.compile(regex_pattern, flags)
    except re.error as e:
        return f"[搜索] 错误: 无效的正则表达式 - {e}"

    # 确定要搜索的扩展名
    if include_ext == "*":
        extensions = INCLUDE_EXTENSIONS
    elif include_ext.startswith("."):
        extensions = {include_ext.lower()}
    else:
        extensions = {f".{include_ext.lstrip('.')}"}

    results: List[Tuple[str, int, str, List[str]]] = []  # (文件路径, 行号, 匹配行, 上下文)

    try:
        for root, dirs, files in os.walk(search_dir_path):
            # 过滤目录
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            root_path = Path(root)

            for filename in files:
                file_path = root_path / filename

                if not _should_process_file(file_path):
                    continue

                # 检查扩展名
                if extensions and file_path.suffix.lower() not in extensions:
                    continue

                # 跳过包含 skip 路径的文件
                if _should_skip_path(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                match_count = 0
                for line_num, line in enumerate(lines, 1):
                    if pattern.search(line):
                        # 收集上下文
                        context_start = max(0, line_num - 1 - MAX_CONTEXT_LINES)
                        context_end = min(len(lines), line_num + MAX_CONTEXT_LINES)
                        context = [lines[i].rstrip() for i in range(context_start, context_end)]

                        results.append((
                            str(file_path),
                            line_num,
                            line.rstrip(),
                            context
                        ))
                        match_count += 1

                        if match_count >= MAX_MATCHES_PER_FILE:
                            break

                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break

            if len(results) >= max_results:
                break

    except Exception as e:
        return f"[搜索] 错误: 遍历目录时出错 - {e}"

    # 格式化输出
    if not results:
        return f"[搜索] 未找到匹配项\n正则: {regex_pattern}\n目录: {search_dir_path}\n类型: {include_ext}"

    output_lines = [
        f"[搜索] 正则: {regex_pattern}",
        f"[搜索] 目录: {search_dir_path}",
        f"[搜索] 类型: {include_ext}",
        f"[搜索] 找到 {len(results)} 个匹配\n",
        "=" * 80,
    ]

    current_file = None
    for file_path, line_num, match_line, context in results:
        if file_path != current_file:
            current_file = file_path
            output_lines.append(f"\n📁 {file_path}")
            output_lines.append("-" * 80)

        # 上下文行
        for ctx_line in context:
            if ctx_line == match_line:
                output_lines.append(f"  → 第 {line_num} 行 | {ctx_line}")
            else:
                output_lines.append(f"    第 {context.index(ctx_line) + (line_num - MAX_CONTEXT_LINES)} 行 | {ctx_line}")

    output_lines.append("\n" + "=" * 80)
    output_lines.append(f"[搜索完成] 共 {len(results)} 个匹配")

    return '\n'.join(output_lines)


def find_function_calls(
    function_name: str,
    search_dir: str = ".",
    include_ext: str = ".py"
) -> str:
    """
    查找特定函数的所有调用位置

    Args:
        function_name: 函数名
        search_dir: 搜索目录
        include_ext: 文件类型

    Returns:
        所有调用位置的列表
    """
    pattern = rf'\b{re.escape(function_name)}\s*\('
    return grep_search(pattern, include_ext, search_dir)


def find_definitions(
    symbol_name: str,
    search_dir: str = ".",
    include_ext: str = ".py"
) -> str:
    """
    查找符号（函数、类、变量）的定义位置

    Args:
        symbol_name: 符号名
        search_dir: 搜索目录
        include_ext: 文件类型

    Returns:
        所有定义位置的列表
    """
    # 匹配 def func_name 或 class ClassName 或 var_name =
    patterns = [
        rf'\bdef\s+{re.escape(symbol_name)}\s*\(',
        rf'\bclass\s+{re.escape(symbol_name)}\s*[\(:]',
        rf'\b{re.escape(symbol_name)}\s*=\s*(?!=)',
    ]
    combined_pattern = '|'.join(patterns)
    return grep_search(combined_pattern, include_ext, search_dir)


def search_imports(
    module_or_name: str,
    search_dir: str = ".",
    include_ext: str = ".py"
) -> str:
    """
    查找特定的 import 语句

    Args:
        module_or_name: 模块名或导入的名称
        search_dir: 搜索目录
        include_ext: 文件类型

    Returns:
        所有 import 该模块/名称的位置
    """
    patterns = [
        rf'^import\s+.*{re.escape(module_or_name)}',
        rf'^from\s+.*{re.escape(module_or_name)}\s+import',
    ]
    combined_pattern = '|'.join(patterns)
    return grep_search(combined_pattern, include_ext, search_dir)


def search_and_read(
    query: str,
    context_lines: int = 5,
    include_ext: str = ".py",
    search_dir: str = ".",
    max_matches: int = 50
) -> str:
    """
    搜索并读取 - 一步到位的代码检索

    在项目中全局搜索 query，对于每个匹配项，自动携带上下文行返回代码。
    将原来需要 2-3 轮 LLM 交互的操作（grep -> read -> 读取更多上下文）压缩为 1 轮。

    Args:
        query: 搜索关键词（支持正则表达式）
        context_lines: 每个匹配项返回的上下文行数（前后各 context_lines 行）
        include_ext: 文件类型过滤
        search_dir: 搜索目录
        max_matches: 最大匹配数（超过则截断）

    Returns:
        格式化的搜索结果，每个匹配包含完整的上下文代码块
    """
    if not query:
        return "[搜索读取] 错误: 查询不能为空"

    search_dir_path = _normalize_path(search_dir)
    if not search_dir_path.exists():
        return f"[搜索读取] 错误: 目录不存在 - {search_dir_path}"

    # 编译正则
    try:
        pattern = re.compile(query)
    except re.error as e:
        return f"[搜索读取] 错误: 无效的正则表达式 - {e}"

    # 确定扩展名
    if include_ext == "*":
        extensions = INCLUDE_EXTENSIONS
    elif include_ext.startswith("."):
        extensions = {include_ext.lower()}
    else:
        extensions = {f".{include_ext.lstrip('.')}"}

    # 收集所有匹配
    all_matches = []

    try:
        for root, dirs, files in os.walk(search_dir_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            root_path = Path(root)

            for filename in files:
                file_path = root_path / filename

                if not _should_process_file(file_path):
                    continue
                if file_path.suffix.lower() not in extensions:
                    continue
                if _should_skip_path(file_path):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                file_matches = []
                for line_num, line in enumerate(lines, 1):
                    if pattern.search(line):
                        # 计算上下文范围
                        start_ctx = max(0, line_num - 1 - context_lines)
                        end_ctx = min(len(lines), line_num + context_lines)

                        # 提取上下文代码块
                        context_block = []
                        for i in range(start_ctx, end_ctx):
                            is_match_line = (i == line_num - 1)
                            marker = ">>>" if is_match_line else "   "
                            context_block.append((i + 1, marker, lines[i].rstrip()))

                        file_matches.append({
                            'line': line_num,
                            'context': context_block,
                            'match_line': line.rstrip(),
                        })

                if file_matches:
                    all_matches.append({
                        'file': str(file_path),
                        'matches': file_matches,
                    })

                if len(all_matches) >= max_matches:
                    break

            if len(all_matches) >= max_matches:
                break

    except Exception as e:
        return f"[搜索读取] 错误: 遍历目录时出错 - {e}"

    if not all_matches:
        return (
            f"[搜索读取] 未找到匹配项\n"
            f"查询: {query}\n"
            f"目录: {search_dir_path}\n"
            f"类型: {include_ext}"
        )

    # 格式化输出
    total_matches = sum(len(f['matches']) for f in all_matches)

    output = [
        f"[搜索读取] 查询: {query}",
        f"[搜索读取] 目录: {search_dir_path}",
        f"[搜索读取] 类型: {include_ext}",
        f"[搜索读取] 找到 {total_matches} 处匹配，分布在 {len(all_matches)} 个文件中\n",
        "=" * 80,
    ]

    for file_idx, file_data in enumerate(all_matches, 1):
        output.append(f"\n{'=' * 40}")
        output.append(f"📁 {file_data['file']}")
        output.append(f"{'=' * 40}")

        for match_idx, match in enumerate(file_data['matches'], 1):
            output.append(f"\n--- 匹配 {match_idx} (第 {match['line']} 行) ---")

            # 收集代码块
            code_lines = []
            for line_num, marker, content in match['context']:
                code_lines.append(f"{marker} {line_num:4d} | {content}")

            output.append("```python")
            output.extend(code_lines)
            output.append("```")

    output.append("\n" + "=" * 80)
    output.append(f"[搜索读取完成] 共 {total_matches} 处匹配")

    return '\n'.join(output)


# 导出给 agent 使用的工具函数
def create_grep_search_tool():
    """创建可序列化的搜索工具函数"""
    return grep_search
