# -*- coding: utf-8 -*-
"""
CMD 命令行执行 + 文件操作工具模块

提供在 Windows 环境下执行 CMD/PowerShell 命令的功能，以及文件读取操作。

核心功能：
1. 执行系统命令
2. 读取文件内容
3. 代码编辑
4. 语法检查
5. 项目备份
"""

import logging
import subprocess
import os
import shutil
from pathlib import Path
from typing import Optional, List


# ============================================================================
# 配置常量
# ============================================================================

logger = logging.getLogger(__name__)

DANGEROUS_COMMANDS = [
    'format',
    'del /f /s /q',
    'rmdir /s /q',
    'rm -rf',
    'dd if=',
    ':(){:|:&};:',
    'shutdown',
    'sysprep',
    'cipher /w:',
]

DEFAULT_TIMEOUT = 60
MAX_OUTPUT_LENGTH = 10000


# ============================================================================
# 辅助函数
# ============================================================================

def _is_command_safe(command: str) -> tuple:
    command_lower = command.lower()
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return False, f"危险命令: 包含 '{dangerous}'"
    return True, "安全"


# ============================================================================
# CMD 执行
# ============================================================================

def run_cmd(command: str, timeout: int = DEFAULT_TIMEOUT, shell: bool = True,
            cwd: Optional[str] = None, check_safety: bool = True) -> str:
    """执行 CMD 命令"""
    if not command or not isinstance(command, str):
        return "[CMD] 错误: 命令不能为空"
    
    command = command.strip()
    if not command:
        return "[CMD] 错误: 命令不能为空"
    
    if check_safety:
        is_safe, reason = _is_command_safe(command)
        if not is_safe:
            return f"[CMD] 返回码: -2\n[安全检查] {reason}\n命令已拒绝执行"
    
    if timeout <= 0:
        timeout = None
    
    try:
        env = os.environ.copy()
        exec_kwargs = {
            'shell': shell,
            'capture_output': True,
            'text': True,
            'encoding': 'utf-8',
            'errors': 'replace',
            'timeout': timeout,
        }
        
        if cwd:
            cwd_path = os.path.abspath(cwd)
            if os.path.isdir(cwd_path):
                exec_kwargs['cwd'] = cwd_path
        
        result = subprocess.run(command, **exec_kwargs)
        
        output_lines = [f"[CMD] 返回码: {result.returncode}"]
        
        if result.stdout:
            output = result.stdout[:MAX_OUTPUT_LENGTH]
            if len(result.stdout) > MAX_OUTPUT_LENGTH:
                output += f"\n... (输出已截断, 原始长度: {len(result.stdout)} 字符)"
            output_lines.append(f"\n[标准输出]\n{output}")
        
        if result.stderr:
            error_output = result.stderr[:MAX_OUTPUT_LENGTH]
            if len(result.stderr) > MAX_OUTPUT_LENGTH:
                error_output += f"\n... (错误输出已截断)"
            output_lines.append(f"\n[标准错误]\n{error_output}")
        
        if not result.stdout and not result.stderr:
            output_lines.append("\n(命令无输出)")
        
        return "\n".join(output_lines)
        
    except subprocess.TimeoutExpired:
        return f"[CMD] 返回码: -1\n[错误] 命令执行超时 ({timeout}秒)"
    except FileNotFoundError as e:
        return f"[CMD] 返回码: -3\n[错误] 命令不存在或无法找到: {command}"
    except PermissionError:
        return f"[CMD] 返回码: -4\n[错误] 权限不足，无法执行命令"
    except Exception as e:
        return f"[CMD] 返回码: -99\n[错误] {str(e)}"


def run_powershell(command: str, timeout: int = DEFAULT_TIMEOUT, cwd: Optional[str] = None) -> str:
    """通过 PowerShell 执行命令"""
    ps_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{command}"'
    return run_cmd(ps_command, timeout=timeout, cwd=cwd, check_safety=True)


def run_batch(commands: List[str], timeout: int = DEFAULT_TIMEOUT, cwd: Optional[str] = None) -> str:
    """批量执行多个 CMD 命令"""
    if not commands:
        return "[CMD] 错误: 命令列表为空"
    combined_command = " && ".join(commands)
    return run_cmd(combined_command, timeout=timeout, cwd=cwd)


# ============================================================================
# 文件操作
# ============================================================================

ALLOWED_ROOT_DIRS = [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    os.getcwd(),
    os.path.expanduser("~"),
]

MAX_FILE_SIZE = 10 * 1024 * 1024

FORBIDDEN_PATTERNS = [
    '.env', '.password', '.secret', '.key', 'id_rsa', 'credentials.json',
]


def _is_path_allowed(file_path: str) -> bool:
    abs_path = os.path.abspath(file_path)
    for allowed_dir in ALLOWED_ROOT_DIRS:
        allowed_abs = os.path.abspath(allowed_dir)
        if abs_path.startswith(allowed_abs):
            return True
    return False


def _is_path_safe(file_path: str) -> bool:
    abs_path = os.path.abspath(file_path).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in abs_path:
            return False
    return True


def _detect_encoding(file_path: Path) -> str:
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
    if not content:
        return False
    printable_ascii = set(range(32, 127)) | {9, 10, 13}
    chinese_range = (0x4e00, 0x9fff)
    cjk_range = [(0x3000, 0x303f), (0xff00, 0xffef)]
    
    total_chars = len(content)
    non_text_chars = 0
    
    for char in content:
        code = ord(char)
        if code in printable_ascii:
            continue
        if chinese_range[0] <= code <= chinese_range[1]:
            continue
        is_cjk = any(r[0] <= code <= r[1] for r in cjk_range)
        if is_cjk:
            continue
        non_text_chars += 1
    
    return non_text_chars / max(total_chars, 1) > threshold


def read_file(file_path: str, encoding: Optional[str] = None,
              max_lines: Optional[int] = None, show_line_numbers: bool = True,
              offset: int = 0) -> str:
    """
    读取本地文件内容

    Args:
        file_path: 文件路径
        encoding: 编码格式，默认自动检测
        max_lines: 最大读取行数，None 表示读取全部
        show_line_numbers: 是否显示行号
        offset: 从第几行开始读取（0-based），用于跳过大段代码
    """
    if not file_path or not isinstance(file_path, str):
        return "[文件读取] 错误: 路径不能为空"
    
    file_path = file_path.strip()
    if not file_path:
        return "[文件读取] 错误: 路径不能为空"
    
    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[文件读取] 错误: 无效的路径格式 - {file_path}"
    
    if not _is_path_allowed(str(abs_path)):
        return f"[文件读取] 错误: 路径超出允许范围 - {abs_path}"
    
    if not _is_path_safe(str(abs_path)):
        return f"[文件读取] 错误: 禁止读取敏感文件 - {abs_path.name}"
    
    if not abs_path.exists():
        return f"[文件读取] 错误: 文件不存在 - {abs_path}"
    
    if not abs_path.is_file():
        return f"[文件读取] 错误: 路径不是文件 - {abs_path}"
    
    try:
        stat = abs_path.stat()
        file_size = stat.st_size
        
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return f"[文件读取] 错误: 文件过大 ({size_mb:.1f} MB > {max_mb:.0f} MB)"
        
        if encoding is None:
            encoding = _detect_encoding(abs_path)
        
        with open(abs_path, 'r', encoding=encoding, errors='replace') as f:
            if offset > 0:
                # 跳过前面的行
                for _ in range(offset):
                    f.readline()

            if max_lines is not None:
                lines = []
                for i in range(max_lines):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.rstrip())
                content = '\n'.join(lines)
                f.seek(0)
                total_lines = sum(1 for _ in f)
                truncated = total_lines > (offset + max_lines)
            else:
                content = f.read()
                total_lines = offset + content.count('\n') + 1
                truncated = False
        
        if _is_binary_content(content):
            return f"[文件读取] 错误: 二进制文件不支持 - {abs_path}"
        
        file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024 * 1024):.1f} MB"
        
        result_lines = [
            f"[文件] {abs_path}",
            f"[编码] {encoding} | [行数] {total_lines}" + (" (已截断)" if truncated else "") + f" | [大小] {file_size_str}",
            "",
            "--- Content ---",
        ]
        
        if show_line_numbers:
            for i, line in enumerate(content.split('\n'), offset + 1):
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
        return f"[文件读取] 错误: {str(e)}"


def list_dir(path: str = ".", show_hidden: bool = False, recursive: bool = False) -> str:
    """列出目录内容"""
    if not path or not isinstance(path, str):
        return "[目录列表] 错误: 目录路径不能为空"
    
    path = path.strip()
    if not path:
        path = "."
    
    try:
        abs_path = Path(path).resolve()
    except Exception as e:
        return f"[目录列表] 错误: 无效的路径格式 - {path}"
    
    if not _is_path_allowed(str(abs_path)):
        return f"[目录列表] 错误: 路径超出允许范围 - {abs_path}"
    
    if not abs_path.exists():
        return f"[目录列表] 错误: 路径不存在 - {abs_path}"
    
    if not abs_path.is_dir():
        return f"[目录列表] 错误: 路径不是目录 - {abs_path}"
    
    try:
        result_lines = [f"[目录] {abs_path}"]
        items = list(abs_path.iterdir())
        
        dirs = []
        files = []
        for item in items:
            if not show_hidden and item.name.startswith('.'):
                continue
            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item)
        
        total_items = len(dirs) + len(files)
        result_lines.append(f"[总计] {total_items} 个项目 ({len(dirs)} 个目录, {len(files)} 个文件)")
        result_lines.append("")
        
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
        return f"[目录列表] 错误: {str(e)}"


# ============================================================================
# 代码编辑
# ============================================================================

EDITABLE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.kt', '.go', '.rs',
    '.c', '.cpp', '.h', '.hpp', '.rb', '.php', '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.md', '.txt',
    '.sh', '.sql', '.xml', '.svg'
}

EDIT_FORBIDDEN_PATTERNS = ['.env', '.password', '.secret', '.key', 'id_rsa', 'credentials.json']


def check_syntax(file_path: str) -> str:
    """检查 Python 文件的语法正确性"""
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
    编辑本地文件，替换指定内容（精准微创手术版）。

    Args:
        file_path: 要编辑的文件路径
        search_string: 要替换的原字符串（必须精确匹配）
        replace_string: 替换后的新字符串
        create_backup: 是否创建备份，默认 True

    Returns:
        操作结果
    """
    if not file_path or not search_string:
        return "[文件编辑] 错误: 文件路径和搜索字符串不能为空"

    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[文件编辑] 错误: 无效的路径 - {e}"

    if not abs_path.exists():
        return f"[文件编辑] 错误: 文件不存在 - {abs_path}"

    ext = abs_path.suffix.lower()
    if ext and ext not in EDITABLE_EXTENSIONS:
        return f"[文件编辑] 错误: 不支持的文件类型 - {ext}"

    abs_str = str(abs_path).lower()
    for pattern in EDIT_FORBIDDEN_PATTERNS:
        if pattern in abs_str:
            return f"[文件编辑] 错误: 禁止编辑敏感文件 - {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            old_content = f.read()
            lines = old_content.split('\n')

        # 增强的多匹配检测
        count = old_content.count(search_string)
        if count == 0:
            return f"[文件编辑] 错误: 未找到目标代码"
        if count > 1:
            # 找出所有匹配的详细行号
            match_lines = []
            for i, line in enumerate(lines, 1):
                if search_string in line:
                    match_lines.append(f"  - 第 {i} 行: {line.strip()[:60]}")
            return (
                f"[文件编辑] 错误: 找到 {count} 个匹配项，非唯一匹配！\n"
                f"匹配位置:\n" + "\n".join(match_lines) +
                f"\n\n【必须】提供更长的上下文（目标行及其前后各 2 行）以确保唯一匹配。"
            )

        if create_backup:
            backup_dir = abs_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / f"{abs_path.stem}_{timestamp}{abs_path.suffix}"
            shutil.copy2(abs_path, backup_path)

        new_content = old_content.replace(search_string, replace_string, 1)

        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        result = [
            "=" * 50,
            "[文件编辑] 成功",
            f"文件: {abs_path}",
            f"修改: {count} 处",
            "=" * 50,
            "建议: 立即调用 check_syntax 进行语法自检",
            "=" * 50,
        ]
        return '\n'.join(result)

    except PermissionError:
        return "[文件编辑] 错误: 权限不足"
    except Exception as e:
        return f"[文件编辑] 错误: {str(e)}"


def list_symbols_in_file(file_path: str) -> str:
    """
    提取 Python 文件中的符号大纲（类似 Cursor Outline 视图）。

    使用 AST 解析文件，只提取 class、def、global variable 定义，
    不读取函数体内容，极度节省 Token。

    Args:
        file_path: Python 文件路径

    Returns:
        格式化的符号列表，包含名称、行号、类型
    """
    import ast

    if not file_path:
        return "[符号提取] 错误: 文件路径不能为空"

    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[符号提取] 错误: 无效的路径 - {e}"

    if not abs_path.exists():
        return f"[符号提取] 错误: 文件不存在 - {abs_path}"

    if abs_path.suffix.lower() != '.py':
        return f"[符号提取] 错误: 仅支持 .py 文件 - {abs_path}"

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(abs_path))

        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 获取类的基类
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(ast.unparse(base) if hasattr(ast, 'unparse') else 'object')

                symbols.append({
                    'type': 'CLASS',
                    'name': node.name,
                    'line': node.lineno,
                    'bases': bases if bases else None,
                })

            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                # 顶层函数
                is_async = isinstance(node, ast.AsyncFunctionDef)
                symbols.append({
                    'type': 'ASYNC_DEF' if is_async else 'DEF',
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                })

            elif isinstance(node, ast.Assign):
                # 全局变量（顶层赋值语句）
                if node.col_offset == 0:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            symbols.append({
                                'type': 'GLOBAL',
                                'name': target.id,
                                'line': node.lineno,
                            })

        if not symbols:
            return f"[符号] {abs_path.name}\n(文件为空或不包含顶层定义)"

        # 格式化输出
        result_lines = [
            f"[符号] {abs_path.name}",
            f"[总计] {len(symbols)} 个符号",
            "",
        ]

        current_type = None
        for sym in symbols:
            if sym['type'] != current_type:
                current_type = sym['type']
                result_lines.append(f"\n[{current_type}]")

            if sym['type'] == 'CLASS':
                bases_str = f" ({', '.join(sym['bases'])})" if sym['bases'] else ""
                result_lines.append(f"  {sym['name']}{bases_str}  @L{sym['line']}")
            elif sym['type'] in ('DEF', 'ASYNC_DEF'):
                args_str = ', '.join(sym['args'][:5])
                if len(sym['args']) > 5:
                    args_str += ', ...'
                result_lines.append(f"  {sym['name']}({args_str})  @L{sym['line']}")
            else:
                result_lines.append(f"  {sym['name']}  @L{sym['line']}")

        return '\n'.join(result_lines)

    except SyntaxError as e:
        return f"[符号提取] 语法错误: 第 {e.lineno} 行 - {e.msg}"
    except Exception as e:
        return f"[符号提取] 错误: {str(e)}"


def create_new_file(file_path: str, content: str = "", overwrite: bool = False) -> str:
    """创建新文件或覆盖现有文件"""
    if not file_path:
        return "[创建文件] 错误: 文件路径不能为空"
    
    try:
        abs_path = Path(file_path).resolve()
    except Exception as e:
        return f"[创建文件] 错误: 无效的路径 - {e}"
    
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
# 项目备份
# ============================================================================

def backup_project(version_note: str = "") -> str:
    """创建项目备份"""
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
            for pattern in ['*.py', '*.json', '*.toml', '*.md']:
                for f in PROJECT_ROOT.glob(pattern):
                    if 'backup' not in str(f) and '__pycache__' not in str(f):
                        arcname = f.relative_to(PROJECT_ROOT)
                        zf.write(f, arcname)
            
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
# Agent 状态与测试
# ============================================================================

def run_self_test() -> str:
    """运行 Agent 核心功能的自我测试"""
    import sys
    results = []
    all_passed = True
    
    results.append("=" * 50)
    results.append("[自检] Agent 核心功能测试")
    results.append("=" * 50)
    
    try:
        from tools import web_tools, memory_tools
        results.append("[OK] 核心模块导入成功")
    except Exception as e:
        results.append(f"[FAIL] 核心模块导入失败: {e}")
        all_passed = False
    
    try:
        from config import get_config
        cfg = get_config()
        results.append(f"[OK] 配置加载成功 (模型: {cfg.llm.model_name})")
    except Exception as e:
        results.append(f"[!] 配置加载失败: {e}")
    
    try:
        from tools.cmd_tools import run_cmd, read_file, list_dir
        results.append("[OK] CMD 工具模块正常")
    except Exception as e:
        results.append(f"[FAIL] CMD 工具模块失败: {e}")
        all_passed = False
    
    try:
        from tools.cmd_tools import check_syntax
        result = check_syntax(__file__)
        if "Syntax OK" in result or "语法检查" in result:
            results.append("[OK] 语法检查功能正常")
        else:
            results.append(f"[FAIL] 语法检查异常: {result[:100]}")
    except Exception as e:
        results.append(f"[FAIL] 语法检查失败: {e}")
    
    try:
        from tools.memory_tools import get_generation, get_current_goal
        gen = get_generation()
        goal = get_current_goal()
        results.append(f"[OK] 记忆系统正常 (G{gen})")
    except Exception as e:
        results.append(f"[FAIL] 记忆系统失败: {e}")
        all_passed = False
    
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
    """获取 Agent 当前状态概览"""
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
    
    lines = [
        "=" * 50,
        "[状态] Agent 运行状态",
        "=" * 50,
        f"世代: G{gen}",
        f"模型: {model}",
        f"苏醒间隔: {interval}秒",
        f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"工作目录: {PROJECT_ROOT}",
        "",
        f"当前目标: {goal or '未设置'}",
        "",
        f"核心上下文: {context[:100]}{'...' if len(context) > 100 else ''}",
        "=" * 50,
    ]
    return '\n'.join(lines)
