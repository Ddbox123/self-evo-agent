#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键停止 Agent 脚本

用于停止所有正在运行的 agent.py 进程
"""

import subprocess
import sys
import os


def find_and_kill_agent():
    """查找并停止所有 agent.py 进程"""
    killed = []
    my_pid = os.getpid()

    # 使用 tasklist 查找 python 进程
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split(',')
                if len(parts) >= 2:
                    pid = parts[1].strip('"')

                    # 跳过自己
                    if pid == str(my_pid):
                        continue

                    # 获取进程命令行
                    cmd_result = subprocess.run(
                        ["powershell", "-Command",
                         f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    cmdline = cmd_result.stdout.strip()
                    # 只处理 agent.py，排除 stop_agent.py 自身
                    if 'agent.py' in cmdline and 'stop_agent.py' not in cmdline:
                        print(f"  -> Found Agent process PID={pid}")
                        print(f"     Cmd: {cmdline[:80]}...")
                        # 强制终止
                        kill_result = subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True,
                            text=True
                        )
                        if kill_result.returncode == 0:
                            print(f"     Stopped successfully")
                            killed.append(pid)
                        else:
                            print(f"     Stop failed: {kill_result.stderr}")

    except Exception as e:
        print(f"Error: {e}")

    return killed


def main():
    print("=" * 60)
    print("Agent Stop Script")
    print("=" * 60)

    print("\n[1] Searching for Agent processes...")
    killed = find_and_kill_agent()

    print("\n[2] Result:")
    if killed:
        print(f"  Stopped {len(killed)} process(es): {killed}")
    else:
        print("  No Agent processes found or already stopped")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
