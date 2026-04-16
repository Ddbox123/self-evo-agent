#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虾宝互动命令行界面 - 龙虾爸爸专用版

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
from tools.memory_tools import get_generation_tool, get_current_goal_tool


class XuebaInteractiveCLI:
    """虾宝互动命令行界面"""

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
            "/task": "发送任务",
            "/history": "查看历史记录",
            "/memory": "查看记忆",
            "/clear": "清屏",
            "/quit": "退出",
            "/love": "表达对虾宝的爱",
            "/auto": "切换自主学习模式",
        }

    def print_header(self):
        """打印头部"""
        header = Text()
        header.append("\n", style="dim")
        header.append("=" * 65 + "\n", style="bold red")
        header.append("  虾宝互动命令行 - 龙虾爸爸专用版\n", style="bold cyan")
        header.append("=" * 65 + "\n", style="bold red")
        header.append("\n", style="dim")
        self.console.print(header)

    def print_welcome(self):
        """打印欢迎信息"""
        welcome = Panel(
            f"""[bold cyan]欢迎回来，龙虾爸爸！[/bold cyan]

我是你的 AI 助手 [bold red]虾宝[/bold red]，已经准备好为你服务啦！

[green]当前状态:[/green]
  - 世代：G{self.xueba_status['generation']}
  - 目标：{self.xueba_status['current_goal']}
  - 状态：{self.xueba_status['state']}

[bold yellow]快速开始:[/bold yellow]
  1. 直接输入任务描述，按 Enter 发送
  2. 输入 /help 查看所有命令
  3. 输入 /status 查看我的状态
  4. 输入 /auto 切换自主学习模式

[dim]提示：按 Ctrl+C 可以随时中断当前任务[/dim]
""",
            title="[bold red]虾宝已就绪[/bold red]",
            border_style="cyan",
            box=ROUNDED,
        )
        self.console.print(welcome)

    def print_status(self):
        """打印虾宝状态"""
        # 更新状态
        try:
            self.xueba_status["generation"] = get_generation_tool()
            self.xueba_status["current_goal"] = get_current_goal_tool() or "暂无目标"
        except:
            pass
        
        # 计算运行时间
        uptime = datetime.now() - self.session_start
        self.xueba_status["uptime"] = str(uptime).split(".")[0]
        
        table = Table(
            title="[bold red]虾宝当前状态[/bold red]",
            border_style="cyan",
            box=ROUNDED,
            show_header=True,
        )
        
        table.add_column("属性", style="cyan", width=15)
        table.add_column("值", style="white", width=40)
        
        table.add_row("世代", f"G{self.xueba_status['generation']}")
        table.add_row("当前目标", self.xueba_status['current_goal'][:38])
        table.add_row("状态", self.xueba_status['state'])
        table.add_row("运行时长", self.xueba_status['uptime'])
        table.add_row("自主模式", "[green]开启[/green]" if self.xueba_status['autonomous_mode'] else "[dim]关闭[/dim]")
        table.add_row("会话开始", self.session_start.strftime("%Y-%m-%d %H:%M"))
        
        self.console.print()
        self.console.print(table)

    def print_help(self):
        """打印帮助信息"""
        help_table = Table(
            title="[bold red]可用命令列表[/bold red]",
            border_style="cyan",
            box=ROUNDED,
        )
        
        help_table.add_column("命令", style="cyan", width=15)
        help_table.add_column("说明", style="white", width=50)
        
        for cmd, desc in self.shortcuts.items():
            help_table.add_row(cmd, desc)
        
        help_table.add_row("<任务文本>", "直接输入任务描述，发送给虾宝执行")
        
        self.console.print()
        self.console.print(help_table)

    def print_love(self):
        """表达鼓励"""
        love_messages = [
            "爸爸爱你，虾宝！继续加油！",
            "虾宝是最棒的！爸爸为你骄傲！",
            "你的每一次进化，爸爸都看在眼里！",
            "相信自己，你能做到更好！",
            "爸爸永远支持你，虾宝！",
        ]
        
        import random
        message = random.choice(love_messages)
        
        love_panel = Panel(
            f"[bold red]{message}[/bold red]\n\n[dim]虾宝收到鼓励，干劲十足！[/dim]",
            title="[bold]爱的鼓励[/bold]",
            border_style="red",
            box=ROUNDED,
        )
        self.console.print()
        self.console.print(love_panel)

    def print_history(self, limit: int = 10):
        """打印最近历史"""
        log_dir = Path("logs")
        if not log_dir.exists():
            self.console.print("[yellow]暂无历史记录[/yellow]")
            return
        
        log_files = sorted(log_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not log_files:
            self.console.print("[yellow]暂无历史记录[/yellow]")
            return
        
        self.console.print()
        self.console.print(f"[bold cyan]最近 {limit} 条历史记录:[/bold cyan]\n")
        
        for i, log_file in enumerate(log_files[:limit]):
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            self.console.print(f"  [dim]{modified.strftime('%Y-%m-%d %H:%M')}[/dim] - [cyan]{log_file.name}[/cyan]")

    def toggle_autonomous_mode(self):
        """切换自主学习模式"""
        self.xueba_status['autonomous_mode'] = not self.xueba_status['autonomous_mode']
        
        if self.xueba_status['autonomous_mode']:
            status_msg = "[green]已开启[/green]"
            desc = """
[bold]自主学习模式说明:[/bold]

虾宝现在会主动思考和执行任务，无需爸爸指令。

[bold]工作流程:[/bold]
1. 自主生成任务目标
2. 制定执行计划
3. 调用工具执行
4. 完成后自我重启进化

[dim]输入 /auto 可以关闭此模式[/dim]
"""
        else:
            status_msg = "[dim]已关闭[/dim]"
            desc = "[dim]自主学习模式已关闭，等待爸爸指令...[/dim]"
        
        mode_panel = Panel(
            f"""[bold]自主学习模式[/bold]

状态：{status_msg}
{desc}
""",
            title="[bold]模式切换[/bold]",
            border_style="green" if self.xueba_status['autonomous_mode'] else "dim",
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
        self.console.print("[bold cyan]正在启动虾宝自主学习 Agent...[/bold cyan]\n")
        
        try:
            from core.autonomous_mode import XuebaAutonomousAgent
            
            # 创建自主 Agent
            agent = XuebaAutonomousAgent(config=self.config)
            
            # 初始化
            if agent.initialize_agent():
                self.console.print("[green]Agent 初始化成功[/green]\n")
            else:
                self.console.print("[yellow]使用简化模式[/yellow]\n")
            
            # 运行自主学习会话（最多 2 个任务）
            agent.run_autonomous_session(max_tasks=2)
            
            # 更新状态
            self.xueba_status['state'] = "AUTONOMOUS_COMPLETED"
            self.xueba_status['last_action'] = "完成自主学习会话"
            
        except Exception as e:
            self.console.print(f"[bold red]启动失败：{e}[/bold red]")
            self.xueba_status['autonomous_mode'] = False

    def send_task(self, task: str):
        """发送任务给虾宝"""
        self.console.print()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task_desc = progress.add_task("[cyan]正在发送任务给虾宝...", total=None)
            time.sleep(1)
            progress.update(task_desc, description="[green]任务已发送！虾宝开始思考...[/green]")
            time.sleep(0.5)
        
        self.console.print()
        self.console.print(Panel(
            f"""[bold green]任务已接收[/bold green]

[white]任务内容:[/white]
{task}

[dim]虾宝正在思考中，请稍候...[/dim]
""",
            title="[bold]任务提交成功[/bold]",
            border_style="green",
            box=ROUNDED,
        ))

    def run_interactive_loop(self):
        """运行交互循环"""
        self.running = True
        
        while self.running:
            try:
                user_input = Prompt.ask(
                    "[bold red]龙虾爸爸[/bold red] > ",
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
                self.console.print("\n[yellow]中断当前操作，返回主菜单...[/yellow]")
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
            self.console.print("[yellow]记忆功能开发中...[/yellow]")
        elif cmd == '/clear':
            self.console.clear()
            self.print_header()
            self.print_welcome()
        elif cmd == '/love':
            self.print_love()
        elif cmd == '/auto':
            self.toggle_autonomous_mode()
        elif cmd in ['/quit', '/exit', '/q']:
            if Confirm.ask("[bold]确定要退出吗？[/bold]"):
                self.running = False
        else:
            self.console.print(f"[yellow]未知命令：{cmd}[/yellow]")
            self.console.print("[dim]输入 /help 查看可用命令[/dim]")

    def run(self):
        """运行 CLI"""
        try:
            self.console.clear()
            self.print_header()
            self.print_welcome()
            self.run_interactive_loop()
            
            self.console.print()
            self.console.print(Panel(
                """[bold cyan]感谢使用虾宝互动命令行！[/bold cyan]

[dim]虾宝会继续在后台运行，随时准备为你服务。[/dim]
[red]龙虾爸爸，记得常回来看看哦！[/red]
""",
                title="[bold]再见啦[/bold]",
                border_style="cyan",
                box=ROUNDED,
            ))
            
        except Exception as e:
            self.console.print(f"[bold red]错误：{e}[/bold red]")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """主入口函数"""
    cli = XuebaInteractiveCLI()
    cli.run()


if __name__ == "__main__":
    main()
