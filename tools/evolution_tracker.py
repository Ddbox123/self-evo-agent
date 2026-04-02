"""
进化追踪模块 - 记录 Agent 的自我修改历史

每次 Agent 修改代码后，记录：
- 修改的文件和位置
- 修改的原因
- 修改的结果（成功/失败）
- 代码差异（diff）

这有助于分析进化路径和回溯问题。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# ============================================================================
# 配置
# ============================================================================

def _get_workspace_path() -> Path:
    """获取工作区域路径"""
    project_root = Path(__file__).parent.parent.resolve()
    workspace = project_root / "workspace"
    workspace.mkdir(exist_ok=True)
    return workspace

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
EVOLUTION_LOG_FILE = _get_workspace_path() / "evolution_log.json"

# 最大记录条数（超过后自动清理）
MAX_LOG_ENTRIES = 100


# ============================================================================
# 数据结构
# ============================================================================

class EvolutionEntry:
    """进化记录条目"""

    def __init__(
        self,
        generation: int,
        file_modified: str,
        change_type: str,  # "add", "modify", "delete"
        reason: str,
        success: bool,
        details: str = "",
    ):
        self.timestamp = datetime.now().isoformat()
        self.generation = generation
        self.file_modified = file_modified
        self.change_type = change_type
        self.reason = reason
        self.success = success
        self.details = details

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "generation": self.generation,
            "file": self.file_modified,
            "type": self.change_type,
            "reason": self.reason,
            "success": self.success,
            "details": self.details,
        }


# ============================================================================
# 核心函数
# ============================================================================

def _load_log() -> List[Dict[str, Any]]:
    """加载进化日志"""
    if not EVOLUTION_LOG_FILE.exists():
        return []
    try:
        with open(EVOLUTION_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_log(entries: List[Dict[str, Any]]) -> bool:
    """保存进化日志"""
    try:
        # 超过最大条数时，保留最近的记录
        if len(entries) > MAX_LOG_ENTRIES:
            entries = entries[-MAX_LOG_ENTRIES:]

        with open(EVOLUTION_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def log_evolution(
    generation: int,
    file_modified: str,
    change_type: str,
    reason: str,
    success: bool,
    details: str = "",
) -> str:
    """
    记录一次自我修改。

    Args:
        generation: 当前世代
        file_modified: 被修改的文件
        change_type: 变更类型 ("add", "modify", "delete")
        reason: 修改原因
        success: 是否成功
        details: 详细信息

    Returns:
        操作结果
    """
    entry = EvolutionEntry(
        generation=generation,
        file_modified=file_modified,
        change_type=change_type,
        reason=reason,
        success=success,
        details=details,
    )

    entries = _load_log()
    entries.append(entry.to_dict())

    if _save_log(entries):
        status = "[OK]" if success else "[X]"
        return (
            f"{status} 进化记录已保存\n"
            f"  文件: {file_modified}\n"
            f"  世代: G{generation}\n"
            f"  原因: {reason}"
        )
    else:
        return "错误: 进化记录保存失败"


def get_evolution_history(limit: int = 10) -> str:
    """
    获取进化历史记录。

    Args:
        limit: 返回的最近记录条数

    Returns:
        格式化的历史记录
    """
    entries = _load_log()

    if not entries:
        return "暂无进化记录"

    # 返回最近的记录
    recent = entries[-limit:] if len(entries) > limit else entries

    lines = ["=" * 50, "进化历史记录", "=" * 50, ""]

    for i, entry in enumerate(reversed(recent), 1):
        status = "[OK]" if entry.get("success") else "[X]"
        lines.append(f"{i}. [{status}] G{entry['generation']} | {entry['file']}")
        lines.append(f"   时间: {entry['timestamp']}")
        lines.append(f"   原因: {entry['reason']}")
        if entry.get('details'):
            lines.append(f"   详情: {entry['details'][:100]}...")
        lines.append("")

    lines.append(f"共 {len(entries)} 条记录")
    return "\n".join(lines)


def get_evolution_stats() -> str:
    """
    获取进化统计信息。

    Returns:
        统计报告
    """
    entries = _load_log()

    if not entries:
        return "暂无进化数据"

    # 统计
    total = len(entries)
    successful = sum(1 for e in entries if e.get("success"))
    failed = total - successful

    # 按文件统计
    files: Dict[str, int] = {}
    for entry in entries:
        file = entry.get("file", "unknown")
        files[file] = files.get(file, 0) + 1

    # 按类型统计
    types: Dict[str, int] = {}
    for entry in entries:
        t = entry.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    # 生成报告
    lines = [
        "=" * 50,
        "进化统计报告",
        "=" * 50,
        "",
        f"总修改次数: {total}",
        f"成功: {successful} ({successful*100//total if total else 0}%)",
        f"失败: {failed}",
        "",
        "按文件统计:",
    ]

    for file, count in sorted(files.items(), key=lambda x: -x[1]):
        lines.append(f"  {file}: {count}次")

    lines.append("")
    lines.append("按类型统计:")
    for t, count in types.items():
        lines.append(f"  {t}: {count}次")

    return "\n".join(lines)


def get_last_modification() -> Optional[Dict[str, Any]]:
    """获取最后一次修改记录"""
    entries = _load_log()
    return entries[-1] if entries else None
