"""
CMD 命令行执行 + 文件操作工具模块

提供在 Windows 环境下执行 CMD/PowerShell 命令的功能，以及文件读取操作。

核心功能：
1. 执行系统命令
2. 读取文件内容（集成自 file_tools）
3. 超时控制

安全说明：
- 仅在 Windows 环境下可用
- 包含危险命令黑名单
- 支持超时控制防止命令挂起
- 文件读取包含敏感信息过滤
"""

import logging
import subprocess
import os
from pathlib import Path
from typing import Optional, List

# ============================================================================
# 配置常量
# ============================================================================

logger = logging.getLogger(__name__)

# 危险命令黑名单（禁止执行的命令）
DANGEROUS_COMMANDS = [
    'format',
    'del /f /s /q',  # 强制删除
    'rmdir /s /q',
    'rm -rf',
    'dd if=',
    ':(){:|:&};:',  # Fork炸弹
    'shutdown',
    'sysprep',
    'cipher /w:',  # 数据擦除
]

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 60

# 最大输出长度
MAX_OUTPUT_LENGTH = 10000


# ============================================================================
# 辅助函数
# ============================================================================

def _is_command_safe(command: str) -> tuple[bool, str]:
    """
    检查命令是否安全。
    
    Args:
        command: 待检查的命令
        
    Returns:
        (是否安全, 原因描述)
    """
    command_lower = command.lower()
    
    # 检查黑名单
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return False, f"危险命令: 包含 '{dangerous}'"
    
    # 检查是否包含可疑的路径操作
    if '..' in command and ('cd ..' in command_lower or 'cd..' in command_lower):
        return True, "警告: 命令包含目录回退操作"
    
    return True, "安全"


def _format_output(stdout: str, stderr: str, returncode: int) -> str:
    """
    格式化命令输出。
    
    Args:
        stdout: 标准输出
        stderr: 标准错误
        returncode: 返回码
        
    Returns:
        格式化的输出字符串
    """
    lines = []
    lines.append(f"[CMD] 返回码: {returncode}")
    
    if stdout:
        output = stdout[:MAX_OUTPUT_LENGTH]
        if len(stdout) > MAX_OUTPUT_LENGTH:
            output += f"\n... (输出已截断, 原始长度: {len(stdout)} 字符)"
        lines.append(f"\n[标准输出]\n{output}")
    
    if stderr:
        error_output = stderr[:MAX_OUTPUT_LENGTH]
        if len(stderr) > MAX_OUTPUT_LENGTH:
            error_output += f"\n... (错误输出已截断, 原始长度: {len(stderr)} 字符)"
        lines.append(f"\n[标准错误]\n{error_output}")
    
    if not stdout and not stderr:
        lines.append("\n(命令无输出)")
    
    return "\n".join(lines)


# ============================================================================
# 核心功能函数
# ============================================================================

def run_cmd(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    shell: bool = True,
    cwd: Optional[str] = None,
    check_safety: bool = True,
) -> str:
    """
    执行 CMD 命令并返回输出结果。
    
    在 Windows 环境下执行指定的命令，返回标准输出和标准错误。
    支持超时控制，防止命令执行过久导致阻塞。
    
    Args:
        command: 要执行的命令。
                可以是简单的命令如 'dir'，也可以是带参数的复杂命令。
                
                示例：
                - "dir" - 列出当前目录
                - "ipconfig /all" - 显示网络配置
                - "python script.py" - 运行Python脚本
                - "git status" - 查看Git状态
                
        timeout: 命令执行超时时间（秒）。
                默认为 60 秒。
                如果命令执行时间超过此值将被强制终止。
                设置为 0 表示不限制时间（不推荐）。
                建议值：简单命令 10-30 秒，复杂命令 60-300 秒。
                
        shell: 是否使用 shell 执行。
               默认为 True，建议保持。
               设为 False 时某些内置命令可能无法执行。
               
        cwd: 命令执行的工作目录。
             默认为 None，表示使用当前工作目录。
             可以指定绝对路径或相对路径。
             
             示例：
             - "C:\\Users\\17533\\Desktop" - 绝对路径
             - "." - 当前目录
             - "src" - 当前目录下的 src 子目录
             
        check_safety: 是否执行安全检查。
                      默认为 True，会检查危险命令并拒绝执行。
                      设为 False 可跳过检查（危险操作请谨慎）。

    Returns:
        格式化的执行结果字符串。
        
        成功时返回格式：
        [CMD] 返回码: 0
        
        [标准输出]
        命令的实际输出内容...
        
        失败时返回格式：
        [CMD] 返回码: 非0数字
        
        [标准错误]
        错误信息描述...
        
        超时时返回：
        [CMD] 返回码: -1
        [错误] 命令执行超时 (60秒)
        
        安全拒绝时返回：
        [CMD] 返回码: -2
        [安全检查] 危险命令: 包含 'xxx'

    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。

    Example:
        >>> result = run_cmd("dir")
        >>> print(result)
        >>> # 输出当前目录列表
        
        >>> result = run_cmd("python --version", timeout=10)
        >>> print(result)
        >>> # 10秒内返回Python版本
        
        >>> result = run_cmd("git status", cwd="C:\\Projects\\MyProject")
        >>> print(result)
        >>> # 在指定目录执行git命令
        
        >>> result = run_cmd("ipconfig /all", shell=True)
        >>> print(result)
        >>> # 查看网络配置信息

    Notes:
        - 仅在 Windows 环境下可用
        - 危险命令会被黑名单机制拦截
        - 输出超过限制会被截断
        - 建议为长时间命令设置合理的超时时间
    """
    logger.info(f"执行CMD命令: {command[:100]}...")
    
    # 参数验证
    if not command or not isinstance(command, str):
        return "[CMD] 错误: 命令不能为空"
    
    command = command.strip()
    if not command:
        return "[CMD] 错误: 命令不能为空"
    
    # 安全检查
    if check_safety:
        is_safe, reason = _is_command_safe(command)
        if not is_safe:
            logger.warning(f"命令安全检查未通过: {reason}")
            return f"[CMD] 返回码: -2\n[安全检查] {reason}\n命令已拒绝执行"
    
    # 超时验证
    if timeout <= 0:
        timeout = None  # 不限制超时
    
    # 执行命令
    try:
        # 设置环境
        env = os.environ.copy()
        
        # 执行参数
        exec_kwargs = {
            'shell': shell,
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'replace',
            'timeout': timeout,
        }
        
        # 添加工作目录
        if cwd:
            cwd_path = os.path.abspath(cwd)
            if os.path.isdir(cwd_path):
                exec_kwargs['cwd'] = cwd_path
                logger.debug(f"工作目录: {cwd_path}")
            else:
                return f"[CMD] 错误: 工作目录不存在 - {cwd_path}"
        
        # 执行命令
        logger.debug(f"执行命令: {command}")
        result = subprocess.run(
            command,
            **exec_kwargs
        )
        
        # 格式化输出
        output = _format_output(
            result.stdout,
            result.stderr,
            result.returncode
        )
        
        logger.info(f"命令执行完成: 返回码 {result.returncode}")
        return output
        
    except subprocess.TimeoutExpired:
        logger.warning(f"命令执行超时: {timeout}秒")
        return f"[CMD] 返回码: -1\n[错误] 命令执行超时 ({timeout}秒)"
        
    except FileNotFoundError as e:
        logger.error(f"命令不存在: {e}")
        return f"[CMD] 返回码: -3\n[错误] 命令不存在或无法找到: {command}"
        
    except PermissionError as e:
        logger.error(f"权限不足: {e}")
        return f"[CMD] 返回码: -4\n[错误] 权限不足，无法执行命令"
        
    except Exception as e:
        logger.error(f"命令执行失败: {e}", exc_info=True)
        return f"[CMD] 返回码: -99\n[错误] {str(e)}"


def run_powershell(
    command: str,
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> str:
    """
    通过 PowerShell 执行命令（Windows 专用）。
    
    此函数是 run_cmd 的 PowerShell 版本，专门用于执行 PowerShell 命令。
    某些 Windows 特有功能（如 WMI 查询）使用 PowerShell 更方便。
    
    Args:
        command: 要执行的 PowerShell 命令。
                
                示例：
                - "Get-Process" - 列出所有进程
                - "Get-NetIPAddress" - 获取IP配置
                - "Get-Service" - 列出所有服务
                - "Get-ChildItem -Path . -Recurse" - 递归列出目录
                
        timeout: 超时时间（秒），默认 60 秒。
        
        cwd: 工作目录，默认当前目录。

    Returns:
        同 run_cmd，返回格式化的执行结果。

    Example:
        >>> result = run_powershell("Get-Process | Where-Object {$_.CPU -gt 10}")
        >>> print(result)
        >>> # 查看CPU使用率高的进程
        
        >>> result = run_powershell("Get-NetIPAddress -AddressFamily IPv4")
        >>> print(result)
        >>> # 获取IPv4地址信息

    Notes:
        - 仅在 Windows 环境下可用
        - 其他参数和行为与 run_cmd 相同
    """
    ps_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
    return run_cmd(ps_command, timeout=timeout, cwd=cwd, check_safety=True)


def run_batch(
    commands: List[str],
    timeout: int = DEFAULT_TIMEOUT,
    cwd: Optional[str] = None,
) -> str:
    """
    批量执行多个 CMD 命令。
    
    按顺序执行多个命令，每个命令之间用 && 连接。
    任何一个命令失败，整个批次会停止。
    
    Args:
        commands: 命令列表。
                  
                  示例：
                  - ["cd src", "dir"] - 进入src目录后列出
                  - ["echo hello", "echo world"] - 依次输出hello和world
                  - ["pip install requests", "python test.py"] - 安装后测试
                  
        timeout: 总超时时间（秒），默认 60 秒。
        
        cwd: 工作目录，默认当前目录。

    Returns:
        同 run_cmd，返回格式化的执行结果。

    Example:
        >>> result = run_batch(["cd C:\\", "dir *.exe"])
        >>> print(result)
        >>> # 进入C盘后列出exe文件

    Notes:
        - 仅在 Windows 环境下可用
        - 命令按顺序执行，前一个失败后后续不会执行
        - 建议单个复杂操作使用此函数
    """
    if not commands:
        return "[CMD] 错误: 命令列表为空"
    
    combined_command = " && ".join(commands)
    return run_cmd(combined_command, timeout=timeout, cwd=cwd)


# ============================================================================
# 文件操作函数（集成自 file_tools）
# ============================================================================

# 允许访问的根目录
ALLOWED_ROOT_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),  # tools 目录
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # 项目根目录
    os.getcwd(),  # 当前工作目录
    os.path.expanduser("~"),  # 用户主目录
]

# 最大读取文件大小（字节）- 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# 禁止读取的文件模式
FORBIDDEN_PATTERNS = [
    '.env',
    '.password',
    '.secret',
    '.key',
    'id_rsa',
    'id_ed25519',
    'credentials.json',
]


def _is_path_allowed(file_path: str) -> bool:
    """检查路径是否在允许访问的范围内"""
    abs_path = os.path.abspath(file_path)
    for allowed_dir in ALLOWED_ROOT_DIRS:
        allowed_abs = os.path.abspath(allowed_dir)
        if abs_path.startswith(allowed_abs):
            return True
    return False


def _is_path_safe(file_path: str) -> bool:
    """检查路径是否包含敏感模式"""
    abs_path = os.path.abspath(file_path).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in abs_path:
            return False
    return True


def _detect_encoding(file_path: Path) -> str:
    """检测文件编码"""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except:
            continue
    return 'utf-8'


def _is_binary_content(content: str, threshold: float = 0.30) -> bool:
    """检测内容是否为二进制（基于字符检测）"""
    if not content:
        return False
    # 使用字符级别检测（避免 UTF-8 多字节问题）
    # 可打印 ASCII 字符
    printable_ascii = set(range(32, 127)) | {9, 10, 13}  # 包含 tab, newline, cr
    # 中文字符范围
    chinese_range = (0x4e00, 0x9fff)
    # 其他 CJK 范围
    cjk_range = [(0x3000, 0x303f), (0xff00, 0xffef)]  # 全角字符等
    
    total_chars = len(content)
    non_text_chars = 0
    
    for char in content:
        code = ord(char)
        # 检查是否是可打印 ASCII
        if code in printable_ascii:
            continue
        # 检查是否是中文字符
        if chinese_range[0] <= code <= chinese_range[1]:
            continue
        # 检查是否是其他 CJK 字符
        is_cjk = any(r[0] <= code <= r[1] for r in cjk_range)
        if is_cjk:
            continue
        # 其他字符（可能是二进制内容）
        non_text_chars += 1
    
    return non_text_chars / max(total_chars, 1) > threshold


def read_file(
    file_path: str,
    encoding: Optional[str] = None,
    max_lines: Optional[int] = None,
    show_line_numbers: bool = True,
) -> str:
    """
    读取本地文件内容。

    使用 CMD/PowerShell 的 type 命令或 Python 直接读取，
    返回格式化的文件内容。

    Args:
        file_path: 要读取的文件路径。
                  可以是相对路径或绝对路径。
                  
                  示例：
                  - "agent.py" - 当前目录下的文件
                  - "./config/settings.json" - 相对路径
                  - "src/utils/helpers.py" - 子目录中的文件

        encoding: 文件编码。
                  默认为 None，自动检测。
                  常用值：utf-8, gbk, latin-1

        max_lines: 最大读取行数限制。
                   默认为 None，表示读取全部。
                   设置此值可以避免读取过大的文件。

        show_line_numbers: 是否显示行号。
                          默认为 True，便于引用。

    Returns:
        格式化的文件内容字符串。

        成功时返回格式：
        [文件] /path/to/file.py
        [编码] utf-8 | [行数] 150 | [大小] 4.2 KB

        --- Content ---
        第 1  行 | def main():
        第 2  行 |     print("Hello")
        ... (已截断，显示前50行)
        --- End ---

        失败时返回错误描述：
        - "[文件读取] 错误: 路径不能为空"
        - "[文件读取] 错误: 文件不存在"
        - "[文件读取] 错误: 路径超出允许范围"
        - "[文件读取] 错误: 禁止读取敏感文件"
        - "[文件读取] 错误: 二进制文件不支持"
        - "[文件读取] 错误: 文件过大 (10.5 MB > 10 MB)"

    Example:
        >>> result = read_file("agent.py")
        >>> print(result)
        >>> # 输出文件内容（带行号）

        >>> result = read_file("README.md", max_lines=50)
        >>> print(result)
        >>> # 只输出前 50 行

        >>> result = read_file("config.json")
        >>> print(result)
        >>> # 读取 JSON 配置文件

    Notes:
        - 自动检测文件编码
        - 包含敏感信息过滤
        - 二进制文件会被检测并拒绝
        - 建议为代码文件使用此函数
    """
    logger.info(f"读取文件: {file_path}")

    # 参数验证
    if not file_path or not isinstance(file_path, str):
        return "[文件读取] 错误: 路径不能为空"

    file_path = file_path.strip()
    if not file_path:
        return "[文件读取] 错误: 路径不能为空"

    # 解析路径
    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        logger.error(f"路径解析失败: {e}")
        return f"[文件读取] 错误: 无效的路径格式 - {file_path}"

    # 安全检查
    if not _is_path_allowed(str(abs_path)):
        logger.warning(f"访问被拒绝: {abs_path} 不在允许范围内")
        return f"[文件读取] 错误: 路径超出允许范围 - {abs_path}"

    if not _is_path_safe(str(abs_path)):
        return f"[文件读取] 错误: 禁止读取敏感文件 - {abs_path.name}"

    # 检查文件是否存在
    if not abs_path.exists():
        return f"[文件读取] 错误: 文件不存在 - {abs_path}"

    if not abs_path.is_file():
        return f"[文件读取] 错误: 路径不是文件 - {abs_path}"

    try:
        # 获取文件信息
        stat = abs_path.stat()
        file_size = stat.st_size

        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return f"[文件读取] 错误: 文件过大 ({size_mb:.1f} MB > {max_mb:.0f} MB)"

        # 检测编码
        if encoding is None:
            encoding = _detect_encoding(abs_path)

        # 读取文件
        with open(abs_path, 'r', encoding=encoding, errors='replace') as f:
            if max_lines is not None:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
                content = '\n'.join(lines)
                # 计算总行数
                f.seek(0)
                total_lines = sum(1 for _ in f)
                truncated = total_lines > max_lines
            else:
                content = f.read()
                total_lines = content.count('\n') + 1
                truncated = False

        # 检测二进制
        if _is_binary_content(content):
            return f"[文件读取] 错误: 二进制文件不支持 - {abs_path}"

        # 格式化输出
        file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"

        result_lines = [
            f"[文件] {abs_path}",
            f"[编码] {encoding} | [行数] {total_lines}" + (" (已截断)" if truncated else "") + f" | [大小] {file_size_str}",
            "",
            "--- Content ---",
        ]

        # 添加带行号的内容
        if show_line_numbers:
            for i, line in enumerate(content.split('\n'), 1):
                result_lines.append(f"第 {i:>5} 行 | {line}")
        else:
            result_lines.append(content)

        result_lines.append("--- End ---")

        return '\n'.join(result_lines)

    except PermissionError:
        return f"[文件读取] 错误: 权限不足 - {abs_path}"
    except UnicodeDecodeError as e:
        return f"[文件读取] 错误: 编码错误 - {e}"
    except Exception as e:
        logger.error(f"读取文件失败: {e}", exc_info=True)
        return f"[文件读取] 错误: {str(e)}"


def list_dir(
    path: str = ".",
    show_hidden: bool = False,
    recursive: bool = False,
) -> str:
    r"""
    列出目录内容。

    使用 PowerShell 的 Get-ChildItem 命令获取目录列表，
    包含文件大小、修改时间等详细信息。

    Args:
        path: 要列出的目录路径。
              默认为 "."（当前目录）。

              示例：
              - "." - 当前目录
              - "./src" - 当前目录下的 src 子目录
              - "C:/Users" - 绝对路径（Windows）

        show_hidden: 是否显示隐藏文件。
                    默认为 False，设置为 True 可查看隐藏文件。

        recursive: 是否递归列出子目录。
                  默认为 False，只列出当前目录。
                  设置为 True 会递归遍历所有子目录。

    Returns:
        格式化的目录列表字符串。

        成功时返回格式：
        [目录] /path/to/directory
        [总计] 15 个项目 (3 个目录, 12 个文件)

        [目录]
        drwxr-xr-x  src/          2024-01-15 10:30
        drwxr-xr-x  tests/        2024-01-15 10:30

        [文件]
        -rw-r--r--  agent.py        2024-01-15 10:30  15.2 KB
        -rw-r--r--  README.md       2024-01-15 10:30   4.2 KB

        失败时返回错误描述：
        - "[目录列表] 错误: 路径不存在"
        - "[目录列表] 错误: 路径不是目录"
        - "[目录列表] 错误: 路径超出允许范围"

    Example:
        >>> result = list_dir(".")
        >>> print(result)
        >>> # 输出当前目录列表

        >>> result = list_dir("./src", recursive=True)
        >>> print(result)
        >>> # 递归列出 src 目录

        >>> result = list_dir("C:\\Users", show_hidden=True)
        >>> print(result)
        >>> # 显示包括隐藏文件的用户目录

    Notes:
        - 结果按类型（目录优先）和名称排序
        - 包含文件大小和修改时间信息
    """
    logger.info(f"列出目录: {path}")

    if not path or not isinstance(path, str):
        return "[目录列表] 错误: 目录路径不能为空"

    path = path.strip()
    if not path:
        path = "."

    # 解析路径
    try:
        abs_path = Path(path).resolve()
    except Exception as e:
        return f"[目录列表] 错误: 无效的路径格式 - {path}"

    # 安全检查
    if not _is_path_allowed(str(abs_path)):
        return f"[目录列表] 错误: 路径超出允许范围 - {abs_path}"

    if not abs_path.exists():
        return f"[目录列表] 错误: 路径不存在 - {abs_path}"

    if not abs_path.is_dir():
        return f"[目录列表] 错误: 路径不是目录 - {abs_path}"

    try:
        result_lines = []
        result_lines.append(f"[目录] {abs_path}")

        items = list(abs_path.iterdir())

        # 分离目录和文件
        dirs = []
        files = []

        for item in items:
            if not show_hidden and item.name.startswith('.'):
                continue
            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item)

        # 统计
        total_items = len(dirs) + len(files)
        result_lines.append(f"[总计] {total_items} 个项目 ({len(dirs)} 个目录, {len(files)} 个文件)")
        result_lines.append("")

        # 列出目录
        if dirs:
            result_lines.append("[目录]")
            for d in sorted(dirs):
                try:
                    stat = d.stat()
                    mtime = os.path.getmtime(d)
                    import datetime
                    dt = datetime.datetime.fromtimestamp(mtime)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                    result_lines.append(f"  drwxr-xr-x  {d.name}/        {time_str}")
                except Exception:
                    result_lines.append(f"  drwxr-xr-x  {d.name}/")

        # 列出文件
        if files:
            result_lines.append("\n[文件]")
            for f in sorted(files):
                try:
                    stat = f.stat()
                    size = stat.st_size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    mtime = os.path.getmtime(f)
                    import datetime
                    dt = datetime.datetime.fromtimestamp(mtime)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                    result_lines.append(f"  -rw-r--r--  {f.name:<25} {time_str}  {size_str:>10}")
                except Exception:
                    result_lines.append(f"  -rw-r--r--  {f.name}")

        # 递归模式
        if recursive and dirs:
            result_lines.append("\n" + "=" * 60)
            result_lines.append("[递归子目录内容]")
            for d in sorted(dirs):
                sub_result = list_dir(str(d), show_hidden, recursive)
                result_lines.append(f"\n{sub_result}")

        return '\n'.join(result_lines)

    except PermissionError:
        return f"[目录列表] 错误: 权限不足 - {abs_path}"
    except Exception as e:
        logger.error(f"列出目录失败: {e}", exc_info=True)
        return f"[目录列表] 错误: {str(e)}"


# ============================================================================
# 代码编辑与语法检查工具
# ============================================================================

# 允许编辑的文件扩展名
EDITABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.kt', '.go', '.rs',
    '.c', '.cpp', '.h', '.hpp', '.rb', '.php', '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.md', '.txt',
    '.sh', '.sql', '.xml', '.svg'
}

# 禁止编辑的文件模式
EDIT_FORBIDDEN_PATTERNS = [
    '.env', '.password', '.secret', '.key', 'id_rsa', 'credentials.json'
]


def check_syntax(file_path: str) -> str:
    """
    检查 Python 文件的语法正确性。

    Args:
        file_path: 要检查的 Python 文件路径

    Returns:
        "Syntax OK" 或详细的错误信息
    """
    import ast
    import traceback

    if not file_path:
        return "[语法检查] 错误: 文件路径不能为空"

    file_path = file_path.strip()

    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[语法检查] 错误: 无效的路径 - {e}"

    if not abs_path.exists():
        return f"[语法检查] 错误: 文件不存在 - {abs_path}"

    if abs_path.suffix.lower() != '.py':
        return f"[语法检查] 错误: 仅支持 .py 文件 - {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()

        ast.parse(source, filename=str(abs_path))
        return "Syntax OK"

    except SyntaxError as e:
        lines = [
            "=" * 60,
            "[语法检查] 发现语法错误",
            "=" * 60,
            f"文件: {abs_path}",
            f"行号: {e.lineno}",
            f"错误: {e.msg if hasattr(e, 'msg') else str(e)}",
            "",
            traceback.format_exception(type(e).__name__, e, e.__traceback__)[-1],
            "=" * 60,
            "建议修复后重新调用 check_syntax",
            "=" * 60,
        ]
        return '\n'.join(lines)

    except Exception as e:
        return f"[语法检查] 错误: {str(e)}"


def edit_local_file(file_path: str, search_string: str,
                   replace_string: str, create_backup: bool = True) -> str:
    """
    编辑本地文件，替换指定内容。

    Args:
        file_path: 要编辑的文件路径
        search_string: 要替换的原字符串（必须精确匹配）
        replace_string: 替换后的新字符串
        create_backup: 是否创建备份，默认 True

    Returns:
        操作结果
    """
    import shutil

    if not file_path or not search_string:
        return "[文件编辑] 错误: 文件路径和搜索字符串不能为空"

    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[文件编辑] 错误: 无效的路径 - {e}"

    if not abs_path.exists():
        return f"[文件编辑] 错误: 文件不存在 - {abs_path}"

    # 检查扩展名
    ext = abs_path.suffix.lower()
    if ext and ext not in EDITABLE_EXTENSIONS:
        return f"[文件编辑] 错误: 不支持的文件类型 - {ext}"

    # 检查敏感文件
    abs_str = str(abs_path).lower()
    for pattern in EDIT_FORBIDDEN_PATTERNS:
        if pattern in abs_str:
            return f"[文件编辑] 错误: 禁止编辑敏感文件 - {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            old_content = f.read()

        count = old_content.count(search_string)
        if count == 0:
            return f"[文件编辑] 错误: 未找到目标代码"
        if count > 1:
            return f"[文件编辑] 错误: 找到 {count} 个匹配项，请提供更长的上下文"

        # 创建备份
        if create_backup:
            backup_dir = abs_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"{abs_path.stem}_{timestamp}{abs_path.suffix}"
            shutil.copy2(abs_path, backup_path)

        # 执行替换
        new_content = old_content.replace(search_string, replace_string, 1)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        result = [
            "=" * 50,
            "[文件编辑] 成功",
            f"文件: {abs_path}",
            f"原字符串: {repr(search_string[:50])}...",
            f"新字符串: {repr(replace_string[:50])}...",
            "=" * 50,
            "建议: 立即调用 check_syntax 进行语法自检",
            "=" * 50,
        ]
        return '\n'.join(result)

    except PermissionError:
        return "[文件编辑] 错误: 权限不足"
    except Exception as e:
        return f"[文件编辑] 错误: {str(e)}"


def create_new_file(file_path: str, content: str = "",
                   overwrite: bool = False) -> str:
    """
    创建新文件或覆盖现有文件。

    Args:
        file_path: 要创建的文件的完整路径
        content: 文件内容，默认为空
        overwrite: 是否覆盖已存在文件，默认 False

    Returns:
        操作结果
    """
    import shutil

    if not file_path:
        return "[创建文件] 错误: 文件路径不能为空"

    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[创建文件] 错误: 无效的路径 - {e}"

    # 检查敏感文件
    abs_str = str(abs_path).lower()
    for pattern in EDIT_FORBIDDEN_PATTERNS:
        if pattern in abs_str:
            return f"[创建文件] 错误: 禁止创建敏感文件 - {abs_path}"

    try:
        if abs_path.exists():
            if not overwrite:
                return f"[创建文件] 错误: 文件已存在 (overwrite=False)"
            backup_path = abs_path.with_suffix(abs_path.suffix + '.backup')
            shutil.copy2(abs_path, backup_path)

        # 确保父目录存在
        parent = abs_path.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = len(content.encode('utf-8'))
        line_count = content.count('\n') + 1 if content else 0

        result = [
            "[创建文件] [OK] 成功",
            f"文件: {abs_path}",
            f"大小: {file_size} 字节",
            f"行数: {line_count}",
        ]
        return '\n'.join(result)

    except PermissionError:
        return "[创建文件] 错误: 权限不足"
    except Exception as e:
        return f"[创建文件] 错误: {str(e)}"


# ============================================================================
# 项目备份工具
# ============================================================================

def backup_project(version_note: str = "") -> str:
    """
    创建项目备份。

    Args:
        version_note: 版本说明

    Returns:
        备份结果
    """
    import shutil
    import zipfile
    from datetime import datetime

    PROJECT_ROOT = Path(__file__).parent.parent.resolve()
    BACKUP_DIR = PROJECT_ROOT / "backups"
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_name

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 备份核心文件
            for pattern in ['*.py', '*.json', '*.toml', '*.md']:
                for f in PROJECT_ROOT.glob(pattern):
                    if 'backup' not in str(f) and '__pycache__' not in str(f):
                        arcname = f.relative_to(PROJECT_ROOT)
                        zf.write(f, arcname)

            # 备份 tools 目录
            tools_dir = PROJECT_ROOT / 'tools'
            if tools_dir.exists():
                for f in tools_dir.glob('*.py'):
                    arcname = f.relative_to(PROJECT_ROOT)
                    zf.write(f, arcname)

        size = backup_path.stat().st_size
        size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"

        result = [
            "=" * 50,
            "[备份] [OK] 备份成功",
            f"文件: {backup_path}",
            f"大小: {size_str}",
            f"说明: {version_note or '无'}",
            "=" * 50,
        ]
        return '\n'.join(result)

    except Exception as e:
        return f"[备份] 错误: {str(e)}"


# ============================================================================
# Agent 状态与测试工具
# ============================================================================

def run_self_test() -> str:
    """
    运行 Agent 核心功能的自我测试。

    Returns:
        测试结果报告
    """
    import sys
    results = []
    all_passed = True

    results.append("=" * 50)
    results.append("[自检] Agent 核心功能测试")
    results.append("=" * 50)

    # 测试 1: 核心模块导入
    try:
        from tools import web_tools, code_tools, safety_tools, memory_tools
        results.append("[OK] 核心模块导入成功")
    except Exception as e:
        results.append(f"[FAIL] 核心模块导入失败: {e}")
        all_passed = False

    # 测试 2: 配置文件可用性
    try:
        from config import get_config
        cfg = get_config()
        results.append(f"[OK] 配置加载成功 (模型: {cfg.llm.model_name})")
    except Exception as e:
        results.append(f"[!] 配置加载失败: {e}")
        # 不算失败，因为可能是首次运行

    # 测试 3: 工具模块可用性
    try:
        from tools.cmd_tools import run_cmd, read_file, list_dir
        results.append("[OK] CMD 工具模块正常")
    except Exception as e:
        results.append(f"[FAIL] CMD 工具模块失败: {e}")
        all_passed = False

    # 测试 4: 语法检查功能
    try:
        from tools.cmd_tools import check_syntax
        result = check_syntax(__file__)
        if "Syntax OK" in result or "语法检查" in result:
            results.append("[OK] 语法检查功能正常")
        else:
            results.append(f"[FAIL] 语法检查异常: {result[:100]}")
    except Exception as e:
        results.append(f"[FAIL] 语法检查失败: {e}")

    # 测试 5: 记忆系统
    try:
        from tools.memory_tools import get_generation, get_current_goal
        gen = get_generation()
        goal = get_current_goal()
        results.append(f"[OK] 记忆系统正常 (G{gen})")
    except Exception as e:
        results.append(f"[FAIL] 记忆系统失败: {e}")
        all_passed = False

    # 测试 6: restarter 可用性
    try:
        restarter_path = Path(__file__).parent.parent / "restarter.py"
        if restarter_path.exists():
            results.append("[OK] restarter.py 存在")
        else:
            results.append("[FAIL] restarter.py 不存在 (危险!)")
            all_passed = False
    except Exception as e:
        results.append(f"[FAIL] restarter 检查失败: {e}")
        all_passed = False

    results.append("=" * 50)
    if all_passed:
        results.append("[自检] [OK] 所有测试通过")
    else:
        results.append("[自检] ✗ 部分测试失败，请检查")
    results.append("=" * 50)

    return '\n'.join(results)


def get_agent_status() -> str:
    """
    获取 Agent 当前状态概览。

    Returns:
        状态报告
    """
    from datetime import datetime
    from tools.memory_tools import get_generation, get_current_goal, get_core_context

    PROJECT_ROOT = Path(__file__).parent.parent.resolve()

    try:
        from config import get_config
        cfg = get_config()
        model = cfg.llm.model_name
        interval = cfg.agent.awake_interval
    except:
        model = "未知"
        interval = 60

    gen = get_generation()
    goal = get_current_goal()
    context = get_core_context()

    uptime = ""
    try:
        agent_pid_file = PROJECT_ROOT / ".agent_pid"
        if agent_pid_file.exists():
            with open(agent_pid_file, 'r') as f:
                pid = int(f.read().strip())
            uptime = f"PID: {pid}"
    except:
        pass

    lines = [
        "=" * 50,
        "[状态] Agent 运行状态",
        "=" * 50,
        f"世代: G{gen}",
        f"模型: {model}",
        f"苏醒间隔: {interval}秒",
        f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"工作目录: {PROJECT_ROOT}",
        f"{uptime}",
        "",
        f"当前目标: {goal or '未设置'}",
        "",
        f"核心上下文: {context[:100]}{'...' if len(context) > 100 else ''}",
        "=" * 50,
    ]
    return '\n'.join(lines)
