#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虾宝互动命令行界面 - 龙虾宝宝主题版

提供友好的交互式 CLI，让龙虾爸爸能够方便地与虾宝互动。
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Rich UI 组件
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.box import ROUNDED

# 导入 Agent 相关
from config import Config, get_config
from core.cli_ui import get_ui as get_cli_ui
from core.ascii_art import LobsterASCII, get_lobster_banner, get_status_lobster
from core.theme import LobsterTheme
from core.pet_system import get_pet
from tools.memory_tools import get_generation_tool, get_current_goal_tool


class XuebaInteractiveCLI:
    """虾宝互动命令行界面 - 龙虾宝宝主题版"""

    def __init__(self):
        # 设置 UTF-8 编码
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

        self.console = Console(force_terminal=True, force_interactive=True)
        self.config = get_config()
        self.agent = None
        self.running = False
        self.command_history: List[str] = []
        self.session_start = datetime.now()

        # 龙虾主题
        self.theme = LobsterTheme()
        self.ascii = LobsterASCII()

        # 虾宝状态
        self.xueba_status = {
            "generation": 1,
            "current_goal": "等待任务...",
            "state": "IDLE",
            "last_action": "尚未行动",
            "uptime": "0:00",
            "autonomous_mode": False,
        }

        # 快捷命令
        self.shortcuts = {
            "/help": "显示帮助",
            "/status": "查看虾宝状态",
            "/pet": "查看宠物状态",
            "/task": "发送任务",
            "/history": "查看历史记录",
            "/memory": "查看记忆",
            "/clear": "清屏",
            "/quit": "退出",
            "/love": "表达对虾宝的爱",
            "/auto": "切换自主学习模式",
            "/feed": "喂食虾宝",
            "/play": "和虾宝玩耍",
        }

    def print_header(self):
        """打印头部 - 龙虾宝宝主题版"""
        banner = get_lobster_banner("虾宝", "v3.0")
        self.console.print(banner)

        # 附加信息
        info = f"""
[cyan]模型:[/cyan] {self.config.llm.model_name}
[yellow]世代:[/yellow] G{self.xueba_status['generation']}
[green]时间:[/green] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        self.console.print(info)

    def print_welcome(self):
        """打印欢迎信息 - 龙虾宝宝主题版"""
        lobster = LobsterASCII.HAPPY
        pet = get_pet()
        pet_status = pet.get_status_text()

        welcome = Panel(
            f"""{lobster}

[bold bright_red]🦞 欢迎回来，龙虾爸爸！🦞[/bold bright_red]

[green]我是你的小虾宝，已经准备好为你服务啦~[/green]

[cyan]📊 当前状态:[/cyan]
  • 世代: G{self.xueba_status['generation']}
  • 目标: {self.xueba_status['current_goal'][:38] if self.xueba_status['current_goal'] else '等待任务...'}
  • 状态: {self._get_status_emoji()} {self.xueba_status['state']}

[magenta]🦞 虾宝宠物:[/magenta]
  {pet_status.split(chr(10))[0]}
  {pet_status.split(chr(10))[1]}

[yellow]🎯 快速开始:[/yellow]
  1. 直接输入任务描述，按 Enter 发送
  2. 输入 /help 查看所有命令
  3. 输入 /status 查看我的状态
  4. 输入 /pet 查看宠物状态

[dim]💡 提示：按 Ctrl+C 可以随时中断当前任务[/dim]
""",
            title="[bold bright_red]🦞 虾宝已就绪[/bold bright_red]",
            border_style="bright_cyan",
            box=ROUNDED,
        )
        self.console.print(welcome)

    def _get_status_emoji(self) -> str:
        """获取状态对应的 emoji"""
        return self.theme.get_status_icon(self.xueba_status['state'])

    def _get_state_lobster(self) -> str:
        """获取状态对应的龙虾 Art"""
        state_map = {
            "IDLE": "happy",
            "THINKING": "thinking",
            "WORKING": "working",
            "SUCCESS": "success",
            "ERROR": "sad",
        }
        return get_status_lobster(state_map.get(self.xueba_status['state'], "happy"))

    def print_status(self):
        """打印虾宝状态 - 龙虾宝宝主题版"""
        # 更新状态
        try:
            self.xueba_status["generation"] = get_generation_tool()
            self.xueba_status["current_goal"] = get_current_goal_tool() or "暂无目标"
        except:
            pass

        # 计算运行时间
        uptime = datetime.now() - self.session_start
        self.xueba_status["uptime"] = str(uptime).split(".")[0]

        # 龙虾状态 Art
        lobster = self._get_state_lobster()
        status_emoji = self._get_status_emoji()

        # 创建状态面板
        status_panel = Panel(
            f"""{lobster}

[cyan]世代:[/cyan] G{self.xueba_status['generation']}
[cyan]状态:[/cyan] {status_emoji} {self.xueba_status['state']}
[cyan]目标:[/cyan] {self.xueba_status['current_goal'][:35] if self.xueba_status['current_goal'] else '暂无'}
[cyan]运行:[/cyan] {self.xueba_status['uptime']}
[cyan]模式:[/cyan] {"🔄 自主" if self.xueba_status['autonomous_mode'] else "⏳ 等待"}
            """,
            title=f"[bold bright_red]🦞 {status_emoji} 虾宝当前状态[/bold bright_red]",
            border_style="cyan",
            box=ROUNDED,
        )
        self.console.print()
        self.console.print(status_panel)

    def print_pet_status(self):
        """打印宠物状态"""
        pet = get_pet()
        lobster = LobsterASCII.HAPPY

        status_text = pet.get_full_status()
        panel = Panel(
            f"{lobster}\n\n{status_text}",
            title="[bold magenta]🦞 龙虾宝宝状态[/bold magenta]",
            border_style="bright_magenta",
            box=ROUNDED,
        )
        self.console.print()
        self.console.print(panel)

    def feed_pet(self):
        """喂食宠物"""
        pet = get_pet()
        pet.feed(20)
        self.console.print("[green]🦞 虾宝吃得好开心！饱食度 +20，心情 +5[/green]")
        self.print_pet_status()

    def play_with_pet(self):
        """和宠物玩耍"""
        pet = get_pet()
        pet.play()
        self.console.print("[magenta]🦞 和虾宝玩耍了！亲密度 +10，心情 +15，活力 -10[/magenta]")
        self.print_pet_status()

    def print_help(self):
        """打印帮助信息 - 龙虾宝宝主题版"""
        # 龙虾装饰
        lobster = LobsterASCII.TINY

        help_table = Table(
            title="[bold bright_red]🦞 可用命令列表[/bold bright_red]",
            border_style="bright_cyan",
            box=ROUNDED,
        )

        help_table.add_column("命令", style="bright_cyan", width=15)
        help_table.add_column("说明", style="white", width=50)

        for cmd, desc in self.shortcuts.items():
            help_table.add_row(cmd, desc)

        help_table.add_row("[cyan]<任务文本>[/cyan]", "直接输入任务描述，发送给虾宝执行")

        self.console.print()
        self.console.print(help_table)

        # 添加可爱提示
        self.console.print()
        self.console.print("[dim]💡 有问题随时问我哦~[/dim]")

    def print_love(self):
        """表达鼓励 - 龙虾宝宝主题版"""
        love_messages = [
            "爸爸爱你，虾宝！继续加油！",
            "虾宝是最棒的！爸爸为你骄傲！",
            "你的每一次进化，爸爸都看在眼里！",
            "相信自己，你能做到更好！",
            "爸爸永远支持你，虾宝！",
        ]

        import random
        message = random.choice(love_messages)

        love_art = LobsterASCII.HAPPY

        love_panel = Panel(
            f"""{love_art}

[bold bright_red]🦞 {message}[/bold red]

[dim]虾宝收到鼓励，干劲十足！[/dim]
            """,
            title="[bold bright_red]💕 爱的鼓励[/bold bright_red]",
            border_style="bright_red",
            box=ROUNDED,
        )
        self.console.print()
        self.console.print(love_panel)

    def print_history(self, limit: int = 10):
        """打印最近历史"""
        log_dir = Path("logs")
        if not log_dir.exists():
            self.console.print("[yellow]⚠️ 暂无历史记录[/yellow]")
            return

        log_files = sorted(log_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)

        if not log_files:
            self.console.print("[yellow]⚠️ 暂无历史记录[/yellow]")
            return

        self.console.print()
        self.console.print(f"[bold cyan]📁 最近 {limit} 条历史记录:[/bold cyan]\n")

        for i, log_file in enumerate(log_files[:limit]):
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            self.console.print(f"  [dim]{modified.strftime('%Y-%m-%d %H:%M')}[/dim] - [cyan]{log_file.name}[/cyan]")

    def toggle_autonomous_mode(self):
        """切换自主学习模式"""
        self.xueba_status['autonomous_mode'] = not self.xueba_status['autonomous_mode']

        if self.xueba_status['autonomous_mode']:
            status_emoji = "🔄"
            lobster = LobsterASCII.WORKING
            mode_panel = Panel(
                f"""{lobster}

[bold bright_green]🔄 自主学习模式已开启！[/bold bright_green]

虾宝现在会主动思考和执行任务，无需爸爸指令。

[yellow]工作流程:[/yellow]
  1. 自主生成任务目标
  2. 制定执行计划
  3. 调用工具执行
  4. 完成后自我重启进化

[dim]输入 /auto 可以关闭此模式[/dim]
            """,
                title=f"[bold bright_green]🦞 {status_emoji} 模式切换[/bold bright_green]",
                border_style="bright_green",
                box=ROUNDED,
            )
        else:
            status_emoji = "⏳"
            lobster = LobsterASCII.HAPPY
            mode_panel = Panel(
                f"""{lobster}

[dim]⏳ 自主学习模式已关闭[/dim]

虾宝正在等待爸爸的指令...

[dim]随时输入 /auto 开启自主模式[/dim]
            """,
                title=f"[bold dim]🦞 {status_emoji} 模式切换[/bold dim]",
                border_style="dim",
                box=ROUNDED,
            )

        self.console.print()
        self.console.print(mode_panel)

        # 如果开启自主模式，启动自主循环
        if self.xueba_status['autonomous_mode']:
            self._start_real_autonomous_loop()

    def _start_real_autonomous_loop(self):
        """启动真实的自主学习循环"""
        self.console.print()
        self.console.print("[bold cyan]🔄 正在启动虾宝自主学习 Agent...[/bold cyan]\n")

        try:
            from core.autonomous_mode import XuebaAutonomousAgent

            # 创建自主 Agent
            agent = XuebaAutonomousAgent(config=self.config)

            # 初始化
            if agent.initialize_agent():
                self.console.print("[green]✅ Agent 初始化成功[/green]\n")
            else:
                self.console.print("[yellow]⚠️ 使用简化模式[/yellow]\n")

            # 运行自主学习会话（最多 2 个任务）
            agent.run_autonomous_session(max_tasks=2)

            # 更新状态
            self.xueba_status['state'] = "SUCCESS"
            self.xueba_status['last_action'] = "完成自主学习会话"

        except Exception as e:
            self.console.print(f"[bold red]❌ 启动失败：{e}[/bold red]")
            self.xueba_status['autonomous_mode'] = False

    def send_task(self, task: str):
        """发送任务给虾宝"""
        self.console.print()

        lobster = LobsterASCII.THINKING

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task_desc = progress.add_task("[cyan]🤔 虾宝正在接收任务...", total=None)
            time.sleep(0.5)
            progress.update(task_desc, description="[magenta]🧠 虾宝开始思考...")
            time.sleep(0.5)

        self.console.print()
        self.console.print(Panel(
            f"""{lobster}

[bold bright_green]✅ 任务已接收[/bold bright_green]

[white]📝 任务内容:[/white]
{task[:200]}{"..." if len(task) > 200 else ""}

[dim]虾宝正在思考中，请稍候...[/dim]
            """,
            title="[bold bright_green]📨 任务提交成功[/bold bright_green]",
            border_style="bright_green",
            box=ROUNDED,
        ))

    def run_interactive_loop(self):
        """运行交互循环"""
        self.running = True

        while self.running:
            try:
                user_input = Prompt.ask(
                    "[bold bright_red]🦞 龙虾爸爸[/bold bright_red] > ",
                    default=""
                ).strip()

                if not user_input:
                    continue

                self.command_history.append(user_input)

                if user_input.startswith('/'):
                    self._handle_command(user_input)
                else:
                    self.send_task(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️ 中断当前操作，返回主菜单...[/yellow]")
                continue
            except EOFError:
                self.running = False
                break

    def _handle_command(self, command: str):
        """处理命令"""
        cmd = command.lower().split()[0]
        args = command.split()[1:] if len(command.split()) > 1 else []

        if cmd == '/help':
            self.print_help()
        elif cmd == '/status':
            self.print_status()
        elif cmd == '/task':
            if args:
                self.send_task(' '.join(args))
            else:
                task = Prompt.ask("[bold]请输入任务内容[/bold]")
                self.send_task(task)
        elif cmd == '/history':
            limit = int(args[0]) if args else 10
            self.print_history(limit)
        elif cmd == '/memory':
            self.console.print("[yellow]⚠️ 记忆功能开发中...[/yellow]")
        elif cmd == '/clear':
            self.console.clear()
            self.print_header()
            self.print_welcome()
        elif cmd == '/love':
            self.print_love()
        elif cmd == '/auto':
            self.toggle_autonomous_mode()
        elif cmd == '/pet':
            self.print_pet_status()
        elif cmd == '/feed':
            self.feed_pet()
        elif cmd == '/play':
            self.play_with_pet()
        elif cmd in ['/quit', '/exit', '/q']:
            if Confirm.ask("[bold]确定要退出吗？[/bold]"):
                self.running = False
        else:
            self.console.print(f"[yellow]⚠️ 未知命令：{cmd}[/yellow]")
            self.console.print("[dim]输入 /help 查看可用命令[/dim]")

    def run(self):
        """运行 CLI - 龙虾宝宝主题版"""
        try:
            self.console.clear()
            self.print_header()
            self.print_welcome()
            self.run_interactive_loop()

            # 告别面板
            goodbye = LobsterASCII.HAPPY
            self.console.print()
            self.console.print(Panel(
                f"""{goodbye}

[bold bright_cyan]🦞 感谢使用虾宝互动命令行！[/bold bright_cyan]

[dim]虾宝会继续在后台运行，随时准备为你服务。[/dim]
[bold bright_red]🦞 龙虾爸爸，记得常回来看看哦！🦞[/bold bright_red]
                """,
                title="[bold]👋 再见啦[/bold]",
                border_style="bright_cyan",
                box=ROUNDED,
            ))

        except Exception as e:
            self.console.print(f"[bold red]❌ 错误：{e}[/bold red]")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主入口函数"""
    cli = XuebaInteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
