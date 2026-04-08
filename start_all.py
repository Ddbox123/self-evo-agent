# -*- coding: utf-8 -*-
"""
Agent Launcher - 一键启动自我进化 Agent

使用方法:
    python start_all.py              # 启动 Agent
    python start_all.py --auto       # 自动模式（无交互）
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


class AgentLauncher:
    """Agent 启动器"""

    def __init__(self):
        self.process = None
        self.running = True

    def print_banner(self):
        """打印启动横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗        ║
║     ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║        ║
║     ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║        ║
║     ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║        ║
║     ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║        ║
║     ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝        ║
║                                                                  ║
║              Self-Evolving Agent - Terminal Edition                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def start_agent(self, auto_mode: bool = False) -> subprocess.Popen:
        """启动 Agent 进程"""
        print("\n[Agent] 正在启动自我进化 Agent...")

        agent_script = PROJECT_ROOT / "agent.py"
        if not agent_script.exists():
            print(f"[错误] Agent 脚本不存在: {agent_script}")
            return None

        env = os.environ.copy()

        # 传递自动模式参数
        args = [sys.executable, str(agent_script)]
        if auto_mode:
            args.append("--auto")

        process = subprocess.Popen(
            args,
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # 等待启动
        for i in range(5):
            time.sleep(1)
            if process.poll() is not None:
                print(f"[错误] Agent 进程启动失败")
                return None

        print(f"[Agent] 启动成功! (PID: {process.pid})")
        return process

    def stream_output(self, process: subprocess.Popen):
        """流式输出 Agent 日志"""
        try:
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}][AGENT] {line.rstrip()}")
        except Exception as e:
            print(f"[错误] 读取 Agent 输出失败: {e}")

    def stop_agent(self):
        """停止 Agent"""
        print("\n\n[系统] 正在停止 Agent...")

        self.running = False

        if self.process and self.process.poll() is None:
            print(f"[系统] 停止 Agent (PID: {self.process.pid})...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            print(f"[系统] Agent 已停止")

        print("\n[系统] 再见!")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Self-Evolving Agent - Terminal Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_all.py       启动 Agent（交互模式）
  python start_all.py --auto 启动 Agent（自动模式）

快捷键:
  Ctrl+C  优雅退出
        """,
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="自动模式（无交互）",
    )

    args = parser.parse_args()

    # 创建启动器
    launcher = AgentLauncher()

    # 打印横幅
    launcher.print_banner()

    # 信号处理
    def signal_handler(sig, frame):
        launcher.stop_agent()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动 Agent
    launcher.process = launcher.start_agent(auto_mode=args.auto)
    if not launcher.process:
        sys.exit(1)

    # 启动日志输出线程
    import threading
    t_agent = threading.Thread(target=launcher.stream_output, args=(launcher.process,), daemon=True)
    t_agent.start()

    # 打印启动信息
    print("\n" + "=" * 60)
    print("  Self-Evolving Agent 已启动!")
    print("=" * 60)
    print(f"""
  Agent 进程: PID {launcher.process.pid}

  按 Ctrl+C 优雅退出
    """)

    # 等待进程结束
    try:
        while True:
            time.sleep(1)

            # 检查进程状态
            if launcher.process and launcher.process.poll() is not None:
                exit_code = launcher.process.poll()
                if exit_code == 0:
                    print("\n[系统] Agent 正常退出")
                else:
                    print(f"\n[系统] Agent 已退出 (退出码: {exit_code})")
                break

    except KeyboardInterrupt:
        launcher.stop_agent()


if __name__ == "__main__":
    main()
