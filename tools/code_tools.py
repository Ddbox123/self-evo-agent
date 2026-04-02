#!/usr/bin/env python3
"""
Diff Block 编辑器 - 实现 Cursor/Aider 风格的精准代码替换

支持 SEARCH/REPLACE 块格式的智能解析和替换：
<<<<<<< SEARCH
def old_code():
    pass
=======
def new_code():
    pass
>>>>>>> REPLACE

特性：
1. 健壮的块解析，支持多种空白符差异
2. 多块连续编辑（一个 diff_text 多个 SEARCH/REPLACE 对）
3. 精确匹配验证，防止误替换
4. 详细的错误报告
"""

import re
import os
from pathlib import Path
from typing import Tuple, Optional, List
import difflib


def _normalize_whitespace(text: str) -> str:
    """规范化空白符，用于比较"""
    lines = text.split('\n')
    normalized = []
    for line in lines:
        # 保留行的核心内容，但标准化尾部空白
        normalized.append(line.rstrip())
    # 移除末尾空行的影响
    while normalized and not normalized[-1]:
        normalized.pop()
    return '\n'.join(normalized)


def _find_match_position(content: str, search_block: str, allow_fuzzy: bool = False) -> Optional[Tuple[int, int]]:
    """
    在内容中查找匹配块的位置

    Args:
        content: 文件内容
        search_block: 要查找的块
        allow_fuzzy: 是否允许模糊匹配

    Returns:
        (起始位置, 结束位置) 或 None
    """
    search_normalized = _normalize_whitespace(search_block)

    # 精确匹配（规范化后）
    lines = content.split('\n')
    search_lines = search_normalized.split('\n')

    for i in range(len(lines) - len(search_lines) + 1):
        match = True
        for j, search_line in enumerate(search_lines):
            content_line = lines[i + j].rstrip()
            if content_line != search_line:
                match = False
                break
        if match:
            # 计算字符位置
            start_line = i
            end_line = i + len(search_lines)
            start_pos = sum(len(lines[k]) + 1 for k in range(start_line))
            end_pos = sum(len(lines[k]) + 1 for k in range(end_line))
            return (start_pos, end_pos)

    # 模糊匹配（允许 minor_diff）
    if allow_fuzzy:
        for i in range(len(lines) - len(search_lines) + 1):
            match_ratio = difflib.SequenceMatcher(
                None,
                '\n'.join(l.rstrip() for l in lines[i:i + len(search_lines)]),
                search_normalized
            ).ratio()
            if match_ratio > 0.85:
                start_line = i
                end_line = i + len(search_lines)
                start_pos = sum(len(lines[k]) + 1 for k in range(start_line))
                end_pos = sum(len(lines[k]) + 1 for k in range(end_line))
                return (start_pos, end_pos)

    return None


def _parse_diff_blocks(diff_text: str) -> List[Tuple[str, str]]:
    """
    解析 diff_text 中的所有 SEARCH/REPLACE 块

    Args:
        diff_text: 包含 SEARCH/REPLACE 块的文本

    Returns:
        [(search_block, replace_block), ...] 列表
    """
    blocks = []

    # 匹配 SEARCH/REPLACE 块的正则
    pattern = r'<<<<<<<\s*SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>>\s*REPLACE'

    matches = list(re.finditer(pattern, diff_text, re.DOTALL))

    if not matches:
        # 尝试简化格式（无 "SEARCH"/"REPLACE" 标签）
        simple_pattern = r'<<<<<<<\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>>'
        matches = list(re.finditer(simple_pattern, diff_text, re.DOTALL))

    for match in matches:
        search_block = match.group(1).strip()
        replace_block = match.group(2).strip()
        blocks.append((search_block, replace_block))

    return blocks


def apply_diff_edit(file_path: str, diff_text: str, allow_fuzzy: bool = False) -> str:
    """
    应用 Diff Block 编辑

    支持以下格式：
    <<<<<<< SEARCH
    old code line 1
    old code line 2
    =======
    new code line 1
    new code line 2
    >>>>>>> REPLACE

    可包含多个块连续替换。

    Args:
        file_path: 要编辑的文件路径
        diff_text: SEARCH/REPLACE 块文本
        allow_fuzzy: 是否允许模糊匹配（当精确匹配失败时）

    Returns:
        操作结果描述
    """
    # 验证文件存在
    path = Path(file_path)
    if not path.exists():
        return f"[编辑] 错误: 文件不存在 - {file_path}"

    if not path.is_file():
        return f"[编辑] 错误: 路径不是文件 - {file_path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"[编辑] 错误: 无法读取文件 - {e}"

    # 解析 diff 块
    blocks = _parse_diff_blocks(diff_text)

    if not blocks:
        return (
            f"[编辑] 错误: 无法解析 diff_text\n"
            f"请确保使用正确的格式:\n"
            f"<<<<<<< SEARCH\n"
            f"要替换的旧代码\n"
            f"=======\n"
            f"新代码\n"
            f">>>>>>> REPLACE"
        )

    new_content = content
    changes_made = []

    for idx, (search_block, replace_block) in enumerate(blocks):
        # 规范化搜索块（用于显示）
        search_display = search_block.strip()

        # 尝试精确匹配
        match_pos = _find_match_position(new_content, search_block, allow_fuzzy=False)

        if match_pos is None and allow_fuzzy:
            match_pos = _find_match_position(new_content, search_block, allow_fuzzy=True)

        if match_pos is None:
            # 找不到匹配
            # 尝试显示相似的代码段
            similar = _find_similar_snippet(new_content, search_block)
            return (
                f"[编辑] 错误: 在文件中找不到匹配的代码块\n\n"
                f"[搜索块内容 - 前200字符]:\n{search_display[:200]}...\n\n"
                f"{similar}"
            )

        start_pos, end_pos = match_pos

        # 执行替换
        new_content = new_content[:start_pos] + replace_block + new_content[end_pos:]
        changes_made.append(f"块 {idx + 1}: 替换成功")

    # 写入文件
    try:
        # 保留原始文件的换行符风格
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(new_content)
    except Exception as e:
        return f"[编辑] 错误: 无法写入文件 - {e}"

    # 返回成功信息
    result = [f"[编辑] 成功修改 {file_path}"]
    result.append(f"共处理 {len(blocks)} 个块:")
    for change in changes_made:
        result.append(f"  ✓ {change}")

    return '\n'.join(result)


def _find_similar_snippet(content: str, search_block: str, context_lines: int = 3) -> str:
    """找到并返回最相似的代码片段用于提示用户"""
    search_lines = [l.strip() for l in search_block.split('\n') if l.strip()]
    if not search_lines:
        return ""

    content_lines = content.split('\n')
    best_match = None
    best_ratio = 0

    for i in range(len(content_lines)):
        snippet = '\n'.join(content_lines[i:i + len(search_lines)])
        ratio = difflib.SequenceMatcher(None, snippet, search_block).ratio()
        if ratio > best_ratio and ratio > 0.3:
            best_ratio = ratio
            best_match = content_lines[i:i + len(search_lines) + context_lines]

    if best_match:
        lines_preview = '\n'.join(f"  第{i+1}行: {l[:80]}" for i, l in enumerate(best_match[:5]))
        return f"[提示] 文件中相似的代码:\n{lines_preview}"

    return ""


def validate_diff_format(diff_text: str) -> Tuple[bool, str]:
    """
    验证 diff_text 格式是否正确

    Args:
        diff_text: 要验证的 diff 文本

    Returns:
        (是否有效, 错误信息)
    """
    blocks = _parse_diff_blocks(diff_text)

    if not blocks:
        return False, "未找到有效的 SEARCH/REPLACE 块。请使用以下格式:\n<<<<<<< SEARCH\n...old code...\n=======\n...new code...\n>>>>>>> REPLACE"

    return True, f"格式正确，包含 {len(blocks)} 个块"


def preview_diff(file_path: str, diff_text: str) -> str:
    """
    预览 diff 效果（不实际修改文件）

    Args:
        file_path: 文件路径
        diff_text: diff 块

    Returns:
        预览结果
    """
    path = Path(file_path)
    if not path.exists():
        return f"[预览] 错误: 文件不存在 - {file_path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"[预览] 错误: 无法读取文件 - {e}"

    blocks = _parse_diff_blocks(diff_text)
    if not blocks:
        return "[预览] 错误: 无法解析 diff 块"

    lines = content.split('\n')
    result = ["[预览] Diff 效果:\n"]

    for idx, (search_block, replace_block) in enumerate(blocks):
        result.append(f"--- 块 {idx + 1} ---")

        # 找到匹配位置
        match_pos = _find_match_position(content, search_block)
        if match_pos:
            start_line = content[:match_pos[0]].count('\n') + 1
            result.append(f"将替换第 {start_line} 行附近的代码:")
            result.append("  [-] " + "\n  [-] ".join(search_block.split('\n')[:5]))
            result.append("  [+] " + "\n  [+] ".join(replace_block.split('\n')[:5]))
        else:
            result.append("  ⚠ 未找到匹配位置")

        result.append("")

    return '\n'.join(result)


# 创建工具实例
grep_search = None  # 将在 __init__ 中导入
apply_diff = apply_diff_edit
