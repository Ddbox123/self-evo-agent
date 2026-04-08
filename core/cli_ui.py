# -*- coding: utf-8 -*-
"""
CLI UI 渲染引擎 - Claude Code 级终端界面

基于 rich 库实现的动态终端界面，支持：
- 原地刷新的动态面板
- 加载动画 (Spinner)
- 带颜色的日志输出
- 任务清单树形渲染
- 进度条和状态显示
"""

import sys
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# rich 组件
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from rich.status import Status
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.box import Box, ROUNDED, DOUBLE
from rich.align import Align
from rich.text import Text

# 全局 Console 实例
_console = Console(stderr=False, force_terminal=True)

# 颜色定义
class Colors:
    """终端颜色常量"""
    # 主色调
    PRIMARY = "cyan"
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "blue"

    # 特殊色
    CODE = "bright_black"
    HIGHLIGHT = "magenta"
    PROMPT = "bold cyan"

    # 状态色
    THINKING = "bright_magenta"
    SEARCHING = "bright_blue"
    CODING = "bright_green"
    TESTING = "bright_yellow"


class UIManager:
    """
    终端 UI 管理器

    提供 Claude Code 级的终端渲染能力：
    - 动态面板 (Live refresh)
    - 加载动画
    - 日志输出
    - 任务清单
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
        self.console = _console
        self._live: Optional[Live] = None
        self._current_renderable = None
        self._logs: List[str] = []
        self._max_logs = 100
        self._generation = 1
        self._current_goal = ""
        self._task_board = ""
        self._status = "IDLE"
        self._thinking = False
        self._tool_count = 0
        self._iterations = 0

    def _create_header(self) -> Panel:
        """创建状态头面板"""
        status_colors = {
            "IDLE": Colors.INFO,
            "THINKING": Colors.THINKING,
            "SEARCHING": Colors.SEARCHING,
            "CODING": Colors.CODING,
            "TESTING": Colors.WARNING,
            "COMPRESSING": Colors.HIGHLIGHT,
            "RESTARTING": Colors.ERROR,
            "HIBERNATING": Colors.CODE,
        }
        status_color = status_colors.get(self._status, Colors.INFO)

        # 状态表格
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("[bold cyan]GEN[/bold cyan]", f"[cyan]G{self._generation}[/cyan]")
        table.add_row("[bold yellow]STATUS[/bold yellow]", f"[{status_color}]{self._status}[/{status_color}]")
        table.add_row("[bold magenta]TURN[/bold magenta]", f"[magenta]#{self._iterations}[/magenta]")
        table.add_row("[bold green]TOOLS[/bold green]", f"[green]{self._tool_count}[/green]")

        return Panel(
            table,
            title="[bold cyan]Self-Evolving Agent[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
            width=50,
        )

    def _create_task_board(self) -> Optional[Panel]:
        """创建任务清单面板"""
        if not self._task_board:
            return None

        return Panel(
            self._task_board,
            title="[bold yellow]Task Board[/bold yellow]",
            border_style="yellow",
            box=ROUNDED,
            width=60,
        )

    def _create_log_panel(self) -> Panel:
        """创建日志面板"""
        if not self._logs:
            return Panel(
                "[dim]等待日志...[/dim]",
                title="[bold green]Execution Log[/bold green]",
                border_style="green",
                box=ROUNDED,
            )

        # 只显示最近的日志
        recent_logs = self._logs[-20:] if len(self._logs) > 20 else self._logs
        log_text = "\n".join(recent_logs)

        return Panel(
            log_text,
            title=f"[bold green]Execution Log[/bold green] ({len(self._logs)} entries)",
            border_style="green",
            box=ROUNDED,
        )

    def _create_full_renderable(self) -> Table:
        """创建完整的渲染布局"""
        layout = Table(box=None, show_header=False, padding=0)

        # 左列：状态头
        # 右列：任务清单
        # 底部：日志面板

        left_panel = self._create_header()
        task_panel = self._create_task_board()
        log_panel = self._create_log_panel()

        # 创建主表格
        main = Table(box=None, show_header=False, padding=0)
        main.add_column(justify="left", ratio=1)
        main.add_column(justify="left", ratio=1)

        if task_panel:
            main.add_row(left_panel, task_panel)
        else:
            main.add_row(left_panel, "")

        return main

    @contextmanager
    def live_display(self, refresh_per_second: int = 4):
        """
        启动 Live 刷新上下文

        Args:
            refresh_per_second: 每秒刷新次数

        使用方式:
            ui = UIManager()
            with ui.live_display():
                while True:
                    ui.update_status(...)
                    time.sleep(0.1)
        """
        self.start_live()
        try:
            yield self
        finally:
            self.stop_live()

    def start_live(self):
        """启动 Live 刷新"""
        if self._live is None:
            self._live = Live(
                self._create_full_renderable(),
                console=self.console,
                refresh_per_second=4,
                transient=False,
                auto_refresh=False,
            )
            self._live.start()

    def stop_live(self):
        """停止 Live 刷新"""
        if self._live:
            self._live.stop()
            self._live = None

    def refresh(self):
        """刷新显示"""
        if self._live:
            self._live.update(self._create_full_renderable(), refresh=True)

    # ==================== 状态更新 ====================

    def update_status(
        self,
        status: str,
        generation: int = None,
        goal: str = None,
        iterations: int = None,
        tool_count: int = None,
    ):
        """
        更新状态

        Args:
            status: 状态名称
            generation: 世代号
            goal: 当前目标
            iterations: 迭代次数
            tool_count: 工具调用次数
        """
        self._status = status.upper()
        if generation is not None:
            self._generation = generation
        if goal is not None:
            self._current_goal = goal
        if iterations is not None:
            self._iterations = iterations
        if tool_count is not None:
            self._tool_count = tool_count

        self.refresh()

    def set_task_board(self, markdown: str):
        """设置任务清单 (Markdown 格式)"""
        self._task_board = markdown
        self.refresh()

    def increment_tool_count(self):
        """工具调用次数 +1"""
        self._tool_count += 1
        self.refresh()

    # ==================== 日志记录 ====================

    def add_log(self, message: str, level: str = "INFO"):
        """
        添加日志条目

        Args:
            message: 日志消息
            level: 日志级别 (INFO, WARN, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "INFO": Colors.INFO,
            "WARN": Colors.WARNING,
            "ERROR": Colors.ERROR,
            "SUCCESS": Colors.SUCCESS,
            "TOOL": Colors.CODING,
            "LLM": Colors.THINKING,
        }
        color = level_colors.get(level.upper(), Colors.INFO)
        log_entry = f"[{timestamp}] [bold {color}]{level}[/{color}] {message}"

        self._logs.append(log_entry)
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

        self.refresh()

    # ==================== 思考动画 ====================

    @contextmanager
    def thinking(self, message: str = "Thinking..."):
        """
        思考动画上下文

        Args:
            message: 思考状态描述

        使用方式:
            with ui.thinking("分析代码结构..."):
                # 执行分析
                pass
        """
        self._thinking = True
        self.add_log(message, "LLM")

        # 创建临时状态
        original_status = self._status
        self._status = "THINKING"
        self.refresh()

        try:
            yield
        finally:
            self._thinking = False
            self._status = original_status
            self.refresh()

    # ==================== 独立输出方法 ====================

    def print_header(self, model: str, generation: int):
        """打印会话头"""
        self._generation = generation

        banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    Self-Evolving Agent                           ║
║                    Terminal Edition v2.0                          ║
╠══════════════════════════════════════════════════════════════════╣
║  Model: {model:<55} ║
║  Generation: G{generation:<49} ║
║  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<49} ║
╚══════════════════════════════════════════════════════════════════╝
"""
        self.console.print(banner, style="bold cyan")

    def print_thinking(self, message: str):
        """打印思考过程"""
        with self.console.status(f"[bold magenta]Thinking...[/bold magenta] {message}") as status:
            yield status

    def print_tool_start(self, tool_name: str, args: Dict[str, Any] = None):
        """打印工具调用开始"""
        self.increment_tool_count()
        self.add_log(f"Calling: {tool_name}", "TOOL")

        # 打印详细信息
        self.console.print()
        self.console.print(f"[bold green]>{tool_name}[/bold green]", end="")

        if args:
            args_str = ", ".join([f"{k}={str(v)[:30]}" for k, v in args.items()][:3])
            self.console.print(f"({args_str})", style="dim")

        self.console.print()

    def print_tool_result(self, tool_name: str, result: str, success: bool = True):
        """打印工具执行结果"""
        status = "[OK]" if success else "[FAIL]"
        color = Colors.SUCCESS if success else Colors.ERROR

        self.console.print(f"  {status} ", end="", style=color)
        self.console.print(tool_name, style="bold")

        # 截断长结果
        if result:
            preview = result[:500] + "..." if len(result) > 500 else result
            self.console.print(f"     {preview}", style="dim")
        self.console.print()

    def print_warning(self, message: str):
        """打印警告"""
        self.console.print(f"[bold yellow]WARNING[/bold yellow] {message}")
        self.add_log(message, "WARN")

    def print_error(self, message: str, exc_info: str = None):
        """打印错误"""
        self.console.print(f"[bold red]ERROR[/bold red] {message}")
        self.add_log(message, "ERROR")

        if exc_info:
            self.console.print(exc_info, style="red dim")

    def print_success(self, message: str):
        """打印成功消息"""
        self.console.print(f"[bold green]OK[/bold green] {message}")
        self.add_log(message, "SUCCESS")

    def print_section(self, title: str):
        """打印分节标题"""
        self.console.print()
        self.console.print(f"[bold cyan]--- {title} ---[/bold cyan]")

    def print_markdown(self, markdown_text: str):
        """打印 Markdown 内容"""
        md = Markdown(markdown_text)
        self.console.print(md)

    def print_code(self, code: str, language: str = "python"):
        """打印代码块"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_table(self, data: List[Dict[str, Any]], columns: List[str] = None):
        """打印表格"""
        if not data:
            return

        if columns is None:
            columns = list(data[0].keys())

        table = Table(box=ROUNDED)
        for col in columns:
            table.add_column(col, style="cyan")

        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])

        self.console.print(table)

    def print_task_checklist(self, tasks: List[Dict[str, Any]]):
        """
        打印任务清单

        Args:
            tasks: 任务列表，每个任务包含:
                   - title: 任务标题
                   - done: 是否完成
                   - priority: 优先级 (high/medium/low)
        """
        tree = Tree("[bold yellow]Task Board[/bold yellow]")

        priority_colors = {
            "high": Colors.ERROR,
            "medium": Colors.WARNING,
            "low": Colors.INFO,
        }

        for task in tasks:
            title = task.get("title", "")
            done = task.get("done", False)
            priority = task.get("priority", "medium")

            icon = "[bold green]x[/bold green]" if done else "[ ]"
            color = priority_colors.get(priority, Colors.INFO)

            tree.add(f"{icon} [bold {color}]{title}[/{color}]")

        self.console.print(tree)

    def print_progress(self, description: str, completed: int, total: int):
        """打印进度条"""
        bar_length = 30
        percent = completed / total if total > 0 else 0
        filled = int(bar_length * percent)
        bar = "[green]" + "=" * filled + "[/green]" + "-" * (bar_length - filled)

        self.console.print(f"  {description}")
        self.console.print(f"  [{bar}] {int(percent * 100)}%")

    def clear(self):
        """清屏"""
        self.console.clear()


# ==================== 全局实例 ====================

_ui: Optional[UIManager] = None


def get_ui() -> UIManager:
    """获取全局 UI 管理器实例"""
    global _ui
    if _ui is None:
        _ui = UIManager()
    return _ui


# 便捷函数
def ui_print_header(model: str, generation: int):
    """打印会话头"""
    get_ui().print_header(model, generation)


def ui_thinking(message: str = "Thinking..."):
    """获取思考动画上下文"""
    return get_ui().thinking(message)


def ui_print_tool(tool_name: str, args: Dict = None, result: str = None, success: bool = True):
    """打印工具执行"""
    if result is None:
        get_ui().print_tool_start(tool_name, args)
    else:
        get_ui().print_tool_result(tool_name, result, success)


def ui_warning(message: str):
    """打印警告"""
    get_ui().print_warning(message)


def ui_error(message: str, exc_info: str = None):
    """打印错误"""
    get_ui().print_error(message, exc_info)


def ui_success(message: str):
    """打印成功"""
    get_ui().print_success(message)


def ui_log(message: str, level: str = "INFO"):
    """添加日志"""
    get_ui().add_log(message, level)


def ui_update_status(
    status: str,
    generation: int = None,
    goal: str = None,
    iterations: int = None,
    tool_count: int = None,
):
    """更新状态"""
    get_ui().update_status(status, generation, goal, iterations, tool_count)


def ui_task_board(markdown: str):
    """设置任务清单"""
    get_ui().set_task_board(markdown)
