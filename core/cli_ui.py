# -*- coding: utf-8 -*-
"""
CLI UI 渲染引擎 - 龙虾宝宝主题版

基于 rich 库实现的动态终端界面，支持：
- 龙虾宝宝可爱主题
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

# 龙虾主题
from core.ascii_art import LobsterASCII, get_lobster_banner, get_status_lobster
from core.theme import LobsterTheme, get_theme, get_style
from core.pet_system import get_pet

# 全局 Console 实例
_console = Console(stderr=False, force_terminal=True)


class UIManager:
    """
    终端 UI 管理器 - 龙虾宝宝主题版

    提供可爱的终端渲染能力：
    - 龙虾宝宝 ASCII Art
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

        # 龙虾主题
        self.theme = get_theme()
        self.style = get_style()
        self.ascii = LobsterASCII()

        # 龙虾宝宝宠物
        self.pet = get_pet()

    def _create_header(self) -> Panel:
        """创建状态头面板 - 龙虾宝宝主题"""
        status_color = self.theme.get_status_color(self._status)
        status_icon = self.theme.get_status_icon(self._status)

        # 龙虾 ASCII Art
        lobster_art = get_status_lobster(self._status.lower())

        # 状态表格
        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()

        table.add_row(f"[bold {self.theme.LOBSTER_CYAN}]GEN[/bold {self.theme.LOBSTER_CYAN}]", f"[{self.theme.LOBSTER_CYAN}]G{self._generation}[/{self.theme.LOBSTER_CYAN}]")
        table.add_row(f"[bold {self.theme.LOBSTER_ORANGE}]STATUS[/bold {self.theme.LOBSTER_ORANGE}]", f"[{status_color}]{status_icon} {self._status}[/{status_color}]")
        table.add_row(f"[bold {self.theme.LOBSTER_PINK}]TURN[/bold {self.theme.LOBSTER_PINK}]", f"[{self.theme.LOBSTER_PINK}]#{self._iterations}[/{self.theme.LOBSTER_PINK}]")
        table.add_row(f"[bold {self.theme.LOBSTER_GREEN}]TOOLS[/bold {self.theme.LOBSTER_GREEN}]", f"[{self.theme.LOBSTER_GREEN}]{self._tool_count}[/{self.theme.LOBSTER_GREEN}]")

        # 组合内容和龙虾 Art
        content = f"[cyan]{lobster_art}[/cyan]\n{table}"

        return Panel(
            content,
            title=self.style.status_title,
            border_style=self.theme.LOBSTER_CYAN,
            box=ROUNDED,
            width=55,
        )

    def _create_task_board(self) -> Optional[Panel]:
        """创建任务清单面板"""
        if not self._task_board:
            return None

        return Panel(
            self._task_board,
            title=f"[bold {self.theme.LOBSTER_ORANGE}]📋 任务清单[/bold {self.theme.LOBSTER_ORANGE}]",
            border_style=self.theme.LOBSTER_ORANGE,
            box=ROUNDED,
            width=60,
        )

    def _create_log_panel(self) -> Panel:
        """创建日志面板 - 龙虾主题"""
        if not self._logs:
            return Panel(
                f"[dim]{get_status_lobster('happy')} 等待日志...[/dim]",
                title=f"[bold {self.theme.LOBSTER_GREEN}]📝 执行日志[/bold {self.theme.LOBSTER_GREEN}]",
                border_style=self.theme.LOBSTER_GREEN,
                box=ROUNDED,
            )

        # 只显示最近的日志
        recent_logs = self._logs[-20:] if len(self._logs) > 20 else self._logs
        log_text = "\n".join(recent_logs)

        return Panel(
            log_text,
            title=f"[bold {self.theme.LOBSTER_GREEN}]📝 执行日志[/bold {self.theme.LOBSTER_GREEN}] ({len(self._logs)} entries)",
            border_style=self.theme.LOBSTER_GREEN,
            box=ROUNDED,
        )

    def _create_full_renderable(self) -> Table:
        """创建完整的渲染布局"""
        layout = Table(box=None, show_header=False, padding=0)

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

    # ==================== 日志记录 - 龙虾主题 ====================

    def add_log(self, message: str, level: str = "INFO"):
        """
        添加日志条目 - 龙虾宝宝主题版
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = self.theme.get_log_icon(level.upper())
        color = self.theme.get_log_color(level.upper())

        log_entry = f"[dim]{timestamp}[/dim] {icon} [{color}]{level}[/{color}] {message}"

        self._logs.append(log_entry)
        if len(self._logs) > self._max_logs:
            self._logs.pop(0)

        self.refresh()

    # ==================== 思考动画 ====================

    @contextmanager
    def thinking(self, message: str = "Thinking..."):
        """
        思考动画上下文
        """
        self._thinking = True
        self.add_log(message, "LLM")

        original_status = self._status
        self._status = "THINKING"
        self.refresh()

        try:
            yield
        finally:
            self._thinking = False
            self._status = original_status
            self.refresh()

    # ==================== 独立输出方法 - 龙虾主题 ====================

    def print_header(self, model: str, generation: int):
        """打印会话头 - 龙虾宝宝版"""
        self._generation = generation

        banner = get_lobster_banner("虾宝", "v3.0")

        header = f"""
{banner}

[cyan]模型:[/cyan] {model}
[yellow]世代:[/yellow] G{generation}
[green]时间:[/green] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.console.print(header)

    def print_thinking(self, message: str):
        """打印思考过程"""
        with self.console.status(f"[bold magenta]🤔 思考中...[/bold magenta] {message}") as status:
            yield status

    def print_tool_start(self, tool_name: str, args: Dict[str, Any] = None):
        """打印工具调用开始 - 龙虾主题"""
        self.increment_tool_count()
        tool_icon = self.theme.get_tool_icon(tool_name)

        self.console.print()
        self.console.print(f"[bold magenta]🔧 {tool_icon} {tool_name}[/bold magenta]", end="")

        if args:
            args_str = ", ".join([f"{k}={str(v)[:30]}" for k, v in args.items()][:3])
            self.console.print(f"({args_str})", style="dim")

        self.console.print()

    def print_tool_result(self, tool_name: str, result: str, success: bool = True):
        """打印工具执行结果 - 龙虾主题"""
        status_icon = "✅" if success else "❌"
        color = self.theme.LOBSTER_GREEN if success else self.theme.LOBSTER_RED

        self.console.print(f"  {status_icon} ", end="", style=color)
        self.console.print(tool_name, style="bold")

        if result:
            preview = result[:500] + "..." if len(result) > 500 else result
            self.console.print(f"     {preview}", style="dim")
        self.console.print()

    def print_warning(self, message: str):
        """打印警告 - 龙虾主题"""
        self.console.print(f"[bold yellow]⚠️ 警告[/bold yellow] {message}")
        self.add_log(message, "WARN")

    def print_error(self, message: str, exc_info: str = None):
        """打印错误 - 龙虾主题"""
        self.console.print(f"[bold red]❌ 错误[/bold red] {message}")
        self.add_log(message, "ERROR")

        if exc_info:
            self.console.print(exc_info, style="red dim")

    def print_success(self, message: str):
        """打印成功消息 - 龙虾主题"""
        self.console.print(f"[bold green]✅ 成功[/bold green] {message}")
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
        打印任务清单 - 龙虾主题
        """
        tree = Tree(f"[bold yellow]📋 任务清单[/bold yellow]")

        for task in tasks:
            title = task.get("title", "")
            done = task.get("done", False)
            priority = task.get("priority", "medium")

            icon = "[bold green]✓[/bold green]" if done else "[ ]"
            priority_color = self.theme.LOBSTER_RED if priority == "high" else (self.theme.LOBSTER_ORANGE if priority == "medium" else "cyan")

            tree.add(f"{icon} [bold {priority_color}]{title}[/{priority_color}]")

        self.console.print(tree)

    def print_progress(self, description: str, completed: int, total: int):
        """打印进度条"""
        bar_length = 30
        percent = completed / total if total > 0 else 0
        filled = int(bar_length * percent)
        bar = f"[{self.theme.LOBSTER_GREEN}]" + "=" * filled + "[/]" + "-" * (bar_length - filled)

        self.console.print(f"  {description}")
        self.console.print(f"  [{bar}] {int(percent * 100)}%")

    def print_lobster_status(self, status: str = "happy", message: str = ""):
        """
        打印龙虾宝宝状态面板

        Args:
            status: 状态 (happy, thinking, working, sleeping, sad)
            message: 状态消息
        """
        lobster_art = get_status_lobster(status)
        status_icon = self.theme.get_status_icon(status.upper())

        content = f"[cyan]{lobster_art}[/cyan]\n"
        content += f"[bold cyan]状态:[/bold cyan] {status_icon} {status.upper()}\n"
        if message:
            content += f"[cyan]消息:[/cyan] {message}"

        panel = Panel(
            content,
            title=self.style.status_title,
            border_style=self.theme.LOBSTER_CYAN,
            box=ROUNDED,
        )
        self.console.print(panel)

    def print_pet_status(self):
        """打印龙虾宝宝宠物状态"""
        pet_text = self.pet.get_full_status()
        panel = Panel(
            pet_text,
            title="[bold magenta]🦞 龙虾宝宝[/bold magenta]",
            border_style="bright_magenta",
            box=ROUNDED,
        )
        self.console.print(panel)

    def print_welcome_panel(self):
        """打印欢迎面板 - 龙虾宝宝版"""
        lobster = LobsterASCII.HAPPY

        welcome = Panel(
            f"""{lobster}

[bold bright_red]🦞 欢迎回来，龙虾爸爸！🦞[/bold bright_red]

[green]我是你的小虾宝，已经准备好为你服务啦~[/green]

[cyan]📊 当前状态:[/cyan]
  • 世代: G{self._generation}
  • 目标: {self._current_goal[:30] if self._current_goal else '等待任务...'}
  • 状态: {self.theme.get_status_icon(self._status)} {self._status}

[yellow]🎯 快速开始:[/yellow]
  1. 直接输入任务，虾宝会帮你完成
  2. 输入 /help 查看所有命令
  3. 输入 /status 查看我的状态

[dim]💡 提示: 按 Ctrl+C 可以随时中断[/dim]
            """,
            title="[bold bright_red]🦞 虾宝已就绪[/bold bright_red]",
            border_style="bright_cyan",
            box=ROUNDED,
        )
        self.console.print(welcome)

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


def ui_lobster_status(status: str = "happy", message: str = ""):
    """打印龙虾状态"""
    get_ui().print_lobster_status(status, message)


def ui_welcome():
    """打印欢迎面板"""
    get_ui().print_welcome_panel()


def ui_print_welcome():
    """打印欢迎面板（别名）"""
    get_ui().print_welcome_panel()
