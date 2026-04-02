# -*- coding: utf-8 -*-
"""
Observer Dashboard - 一键启动脚本

同时启动：
1. Agent 守护进程
2. Dashboard Web 监控面板

使用方法:
    python start_all.py              # 启动全部
    python start_all.py --agent-only # 仅启动 Agent
    python start_all.py --web-only  # 仅启动 Dashboard
    python start_all.py --port 8888 # 指定 Dashboard 端口
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


class MultiProcessLauncher:
    """多进程启动器"""

    def __init__(self):
        self.processes = {}
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
║            Self-Evolving Agent + Observer Dashboard               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)

    def print_status(self, process_name, status, extra=""):
        """打印状态"""
        symbols = {
            "STARTING": "🟡",
            "RUNNING": "🟢",
            "STOPPED": "🔴",
            "ERROR": "❌",
        }
        sym = symbols.get(status, "⚪")
        print(f"  {sym} {process_name}: {status} {extra}")

    def start_dashboard(self, port: int = 8000) -> subprocess.Popen:
        """启动 Dashboard 服务"""
        print("\n[Dashboard] 正在启动 Web 监控面板...")

        dashboard_script = PROJECT_ROOT / "dashboard" / "server.py"
        if not dashboard_script.exists():
            print(f"[错误] Dashboard 脚本不存在: {dashboard_script}")
            return None

        # 检查依赖
        try:
            import fastapi
            import uvicorn
        except ImportError:
            print("[安装依赖] 正在安装 FastAPI 和 Uvicorn...")
            subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], check=True)

        env = os.environ.copy()
        process = subprocess.Popen(
            [sys.executable, str(dashboard_script), "--port", str(port)],
            cwd=str(PROJECT_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # 等待启动
        for i in range(10):
            time.sleep(1)
            if process.poll() is not None:
                print(f"[错误] Dashboard 进程启动失败")
                return None

            # 检查端口是否可用
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()

            if result == 0:
                print(f"[Dashboard] 启动成功! 访问地址: http://localhost:{port}")
                print(f"[Dashboard] 状态 WebSocket: ws://localhost:{port}/ws/state")
                print(f"[Dashboard] 日志 WebSocket: ws://localhost:{port}/ws/logs")
                return process

        print(f"[错误] Dashboard 启动超时")
        return None

    def start_agent(self) -> subprocess.Popen:
        """启动 Agent 进程"""
        print("\n[Agent] 正在启动自我进化 Agent...")

        agent_script = PROJECT_ROOT / "agent.py"
        if not agent_script.exists():
            print(f"[错误] Agent 脚本不存在: {agent_script}")
            return None

        env = os.environ.copy()
        process = subprocess.Popen(
            [sys.executable, str(agent_script)],
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

    def stream_output(self, process: subprocess.Popen, name: str, color: str = ""):
        """流式输出进程日志"""
        reset = "\033[0m"
        colors = {
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "cyan": "\033[96m",
            "purple": "\033[95m",
        }
        color_code = colors.get(color, "")

        try:
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                if line:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"{color_code}[{timestamp}][{name}]{reset} {line.rstrip()}")
        except Exception as e:
            print(f"[错误] 读取 {name} 输出失败: {e}")

    def stop_all(self):
        """停止所有进程"""
        print("\n\n[系统] 正在停止所有进程...")

        self.running = False

        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"[系统] 停止 {name} (PID: {process.pid})...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"[系统] {name} 已停止")

        print("\n[系统] 全部进程已停止。再见!")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Observer Dashboard - 一键启动自我进化 Agent 和监控面板",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_all.py              启动全部服务
  python start_all.py --agent-only 仅启动 Agent
  python start_all.py --web-only   仅启动 Dashboard
  python start_all.py --port 8888  使用自定义端口

快捷键:
  Ctrl+C  优雅退出所有进程
        """,
    )

    parser.add_argument(
        "--agent-only",
        action="store_true",
        help="仅启动 Agent（不启动 Dashboard）",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="仅启动 Dashboard（不启动 Agent）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Dashboard 端口号 (默认: 8080)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="不自动打开浏览器",
    )

    args = parser.parse_args()

    # 创建启动器
    launcher = MultiProcessLauncher()

    # 打印横幅
    launcher.print_banner()

    # 信号处理
    def signal_handler(sig, frame):
        launcher.stop_all()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动 Dashboard
    dashboard_process = None
    if not args.agent_only:
        dashboard_process = launcher.start_dashboard(args.port)
        if dashboard_process:
            launcher.processes["Dashboard"] = dashboard_process
            launcher.print_status("Dashboard", "RUNNING", f"(端口 {args.port})")
        else:
            launcher.print_status("Dashboard", "ERROR")
            sys.exit(1)
    else:
        launcher.print_status("Dashboard", "STOPPED", "(跳过)")

    # 启动 Agent
    agent_process = None
    if not args.web_only:
        agent_process = launcher.start_agent()
        if agent_process:
            launcher.processes["Agent"] = agent_process
            launcher.print_status("Agent", "RUNNING", f"(PID: {agent_process.pid})")
        else:
            launcher.print_status("Agent", "ERROR")
            sys.exit(1)
    else:
        launcher.print_status("Agent", "STOPPED", "(跳过)")

    # 启动日志输出线程
    import threading

    def output_dashboard():
        launcher.stream_output(dashboard_process, "DASH", "cyan")

    def output_agent():
        launcher.stream_output(agent_process, "AGENT", "green")

    if dashboard_process:
        t_dashboard = threading.Thread(target=output_dashboard, daemon=True)
        t_dashboard.start()

    if agent_process:
        t_agent = threading.Thread(target=output_agent, daemon=True)
        t_agent.start()

    # 自动打开浏览器
    if dashboard_process and not args.no_browser:
        import webbrowser
        time.sleep(2)
        url = f"http://localhost:{args.port}"
        print(f"\n[浏览器] 正在打开 {url}...")
        webbrowser.open(url)

    # 打印启动信息
    print("\n" + "=" * 60)
    print("  所有服务已启动!")
    print("=" * 60)

    if not args.agent_only and not args.web_only:
        print(f"""
  监控面板: http://localhost:{args.port}
  Agent 进程: PID {agent_process.pid}

  按 Ctrl+C 优雅退出
        """)
    elif args.agent_only:
        print(f"""
  Agent 进程: PID {agent_process.pid}

  按 Ctrl+C 优雅退出
        """)
    else:
        print(f"""
  监控面板: http://localhost:{args.port}

  按 Ctrl+C 优雅退出
        """)

    # 等待进程结束
    try:
        while True:
            time.sleep(1)

            # 检查进程状态
            for name, process in list(launcher.processes.items()):
                if process and process.poll() is not None:
                    exit_code = process.poll()
                    if exit_code == 0:
                        launcher.print_status(name, "STOPPED", "(正常退出)")
                    else:
                        launcher.print_status(name, "STOPPED", f"(退出码: {exit_code})")
                    del launcher.processes[name]

                    # 如果 Dashboard 退出，自动关闭 Agent 并退出
                    if name == "Dashboard" and not args.agent_only:
                        print("\n[系统] Dashboard 已关闭，正在停止 Agent...")
                        # 停止 Agent
                        if "Agent" in launcher.processes:
                            agent_proc = launcher.processes["Agent"]
                            if agent_proc and agent_proc.poll() is None:
                                try:
                                    agent_proc.terminate()
                                    agent_proc.wait(timeout=5)
                                except:
                                    agent_proc.kill()
                                launcher.print_status("Agent", "STOPPED", "(已关闭)")
                        print("\n[系统] 所有服务已停止。再见!")
                        sys.exit(0)

            # 所有进程都退出了
            if not launcher.processes:
                print("\n[系统] 所有进程已退出")
                break

    except KeyboardInterrupt:
        launcher.stop_all()


if __name__ == "__main__":
    main()
