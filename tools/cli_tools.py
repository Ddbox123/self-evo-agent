#!/usr/bin/env python3
"""
终极 CLI 引擎 - 万能命令执行工具

本模块提供统一的 CLI 执行能力，替代所有细碎的 OS 命令包装工具。
基于 CodeAct 范式，Agent 可通过此工具执行任意 Shell 命令。

## 核心能力

1. **万物皆可执行**: ls, cat, grep, python, pytest, pip, git 等
2. **智能输出合并**: 同时捕获 stdout 和 stderr，统一返回
3. **超时保护**: 防止死循环命令导致主进程假死
4. **安全护栏**: 拦截危险命令

## 使用场景

```python
# 列出目录
execute_cli_command("ls -la")

# 查看文件
execute_cli_command("cat README.md")

# 语法检查
execute_cli_command("python -m py_compile agent.py")

# 运行测试
execute_cli_command("pytest tests/ -v")

# 搜索代码
# 搜索代码
# Python 一行脚本
execute_cli_command('python -c "import sys; print(sys.version)"')
```

## 安全限制

- 所有命令在项目根目录执行
- 危险命令被拦截并返回安全提示
"""

import subprocess
import os
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 危险命令前缀黑名单
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    ":(){ :|:& };:",  # Fork bomb
    "dd if=/dev/zero of=/dev/sda",  # 磁盘擦除
    "> /dev/sda",  # 直接写磁盘
]


def _is_dangerous(command: str) -> tuple[bool, str]:
    """检查命令是否危险"""
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True, f"危险命令拦截: {pattern}"
    return False, ""


def execute_cli_command(
    command: str,
    timeout: int = 60,
    cwd: Optional[str] = None
) -> str:
    """
    执行 CLI 命令的万能工具

    Args:
        command: 要执行的 Shell 命令
        timeout: 超时时间（秒），默认 60 秒。防止死循环命令。
        cwd: 工作目录，默认为项目根目录

    Returns:
        str: 合并后的命令输出（stdout + stderr）

    警告:
        - 不要执行交互式命令（如 vim, less）
        - 长时间任务请设置合适的 timeout
        - Windows 系统命令可能与 Linux 不同

    示例:
        >>> result = execute_cli_command("ls -la")
        >>> print(result)

        >>> result = execute_cli_command("pytest tests/", timeout=120)
        >>> print(result)
    """
    # 安全检查
    is_dangerous, msg = _is_dangerous(command)
    if is_dangerous:
        return f"[安全拦截] {msg}\n该命令被系统安全策略阻止。"

    # 设置工作目录
    if cwd is None:
        cwd = str(PROJECT_ROOT)

    # 确保工作目录存在
    if not os.path.exists(cwd):
        return f"[错误] 工作目录不存在: {cwd}"

    try:
        # 执行命令，同时捕获 stdout 和 stderr
        # Windows 使用系统默认编码，但遇到无法解码的字节时替换
        import locale
        system_encoding = locale.getpreferredencoding(False) or 'utf-8'

        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding=system_encoding,
            errors='replace',  # 替换无法解码的字符
            timeout=timeout
        )

        # 合并 stdout 和 stderr
        output_parts = []

        if result.stdout:
            output_parts.append(result.stdout.strip())

        if result.stderr:
            # stderr 通常是错误信息，用不同格式标记
            output_parts.append(f"[STDERR]\n{result.stderr.strip()}")

        if not output_parts:
            output_parts.append("[命令执行完成，无输出]")

        output = "\n\n".join(output_parts)

        # 【修复】如果命令返回非零状态码，必须明确标记为失败
        if result.returncode != 0:
            # 检查是否包含 error/exception 等关键词
            has_error_keywords = any(kw in output.lower() for kw in
                ["error", "exception", "failed", "fail", "traceback", "syntaxerror", "indentationerror"])
            if has_error_keywords:
                # 真正的错误：返回明确失败标记
                return f"[EXEC FAILURE | Exit Code: {result.returncode}]\n{output}"
            else:
                # 非零退出码但可能是警告（如 git pull 无更新）
                return f"[WARNING | Exit Code: {result.returncode}]\n{output}"

        return output

    except subprocess.TimeoutExpired:
        return f"[超时] 命令执行超过 {timeout} 秒被强制终止。\n请检查命令是否陷入死循环。"

    except FileNotFoundError:
        return f"[错误] 命令未找到: {command}\n请检查命令是否正确，或使用完整路径。"

    except PermissionError:
        return f"[权限错误] 无法执行命令: {command}\n可能需要管理员权限。"

    except Exception as e:
        return f"[执行错误] {type(e).__name__}: {str(e)}"


def quick_ping(host: str = "8.8.8.8", count: int = 1) -> str:
    """
    快速网络连通性检测

    Args:
        host: 目标主机，默认 8.8.8.8 (Google DNS)
        count: ping 次数，默认 1

    Returns:
        str: 连通性结果
    """
    import platform
    system = platform.system().lower()

    if system == "windows":
        cmd = f"ping -n {count} {host}"
    else:
        cmd = f"ping -c {count} {host}"

    return execute_cli_command(cmd, timeout=10)


def check_python_syntax(file_path: str) -> str:
    """
    Python 语法检查（便捷封装）

    Args:
        file_path: Python 文件路径

    Returns:
        str: 检查结果
    """
    return execute_cli_command(
        f"python -m py_compile {file_path}",
        timeout=30
    )


def run_pytest(test_path: str = "tests/", verbose: bool = True) -> str:
    """
    运行 pytest 测试（便捷封装）

    Args:
        test_path: 测试路径
        verbose: 是否详细输出

    Returns:
        str: 测试结果
    """
    v_flag = "-v" if verbose else ""
    return execute_cli_command(
        f"pytest {test_path} {v_flag}",
        timeout=120
    )


# 工具注册函数
def create_cli_tools():
    """创建 CLI 工具集"""
    return {
        'execute_cli_command': execute_cli_command,
        'quick_ping': quick_ping,
        'check_python_syntax': check_python_syntax,
        'run_pytest': run_pytest,
    }
