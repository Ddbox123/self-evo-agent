"""
文件和目录操作工具模块

提供本地文件系统的基本操作功能，供 Agent 进行项目管理和文件探索。

本模块封装了常用的文件和目录操作：
1. 列出目录内容
2. 读取文件内容
3. 安全的路径验证

依赖：
    - os: 内置模块
    - pathlib: 内置模块 (Python 3.4+)
"""

import logging
import os
from pathlib import Path
from typing import List, Optional


# ============================================================================
# 配置常量
# ============================================================================

# 日志记录器
logger = logging.getLogger(__name__)

# 允许访问的根目录（限制 Agent 的文件系统访问范围）
ALLOWED_ROOT_DIRS = [
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # 项目根目录
    os.getcwd(),  # 当前工作目录
    os.path.expanduser("~"),  # 用户主目录
]

# 最大读取文件大小（字节）- 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# 禁止访问的文件模式
FORBIDDEN_PATTERNS = [
    '.env',
    '.password',
    '.secret',
    '.key',
    'id_rsa',
    'id_ed25519',
    'credentials.json',
]


# ============================================================================
# 辅助函数
# ============================================================================

def is_path_allowed(file_path: str) -> bool:
    """
    检查路径是否在允许访问的范围内。
    
    Args:
        file_path: 要检查的文件路径
        
    Returns:
        如果路径在允许范围内返回 True，否则返回 False
    """
    abs_path = os.path.abspath(file_path)
    
    for allowed_dir in ALLOWED_ROOT_DIRS:
        allowed_abs = os.path.abspath(allowed_dir)
        if abs_path.startswith(allowed_abs):
            return True
    
    return False


def is_path_safe(file_path: str) -> bool:
    """
    检查路径是否包含危险模式。
    
    Args:
        file_path: 要检查的文件路径
        
    Returns:
        如果路径安全返回 True，否则返回 False
    """
    abs_path = os.path.abspath(file_path).lower()
    
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in abs_path:
            logger.warning(f"访问被拒绝 - 检测到敏感模式: {pattern}")
            return False
    
    return True


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读的字符串。
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的大小字符串，如 "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_permissions(mode: int) -> str:
    """
    格式化文件权限为 rwx 字符串。
    
    Args:
        mode: 文件模式
        
    Returns:
        权限字符串，如 "rwxr-xr-x"
    """
    perms = []
    
    # 所有者权限
    perms.append('r' if mode & 0o400 else '-')
    perms.append('w' if mode & 0o200 else '-')
    perms.append('x' if mode & 0o100 else '-')
    
    # 组权限
    perms.append('r' if mode & 0o040 else '-')
    perms.append('w' if mode & 0o020 else '-')
    perms.append('x' if mode & 0o010 else '-')
    
    # 其他用户权限
    perms.append('r' if mode & 0o004 else '-')
    perms.append('w' if mode & 0o002 else '-')
    perms.append('x' if mode & 0o001 else '-')
    
    return ''.join(perms)


# ============================================================================
# 核心功能函数
# ============================================================================

def list_directory(path: str, show_hidden: bool = False, recursive: bool = False) -> str:
    """
    列出指定目录的内容。
    
    此函数返回目录的详细列表，包括文件大小、修改时间和权限信息。
    旨在帮助 Agent 了解项目结构和进行文件探索。
    
    Args:
        path: 要列出的目录路径。
              可以是相对路径或绝对路径。
              
              示例：
              - "." 或 "" - 当前目录
              - "./src" - 当前目录下的 src 子目录
              - "/home/user/project" - 绝对路径
              - ".." - 上级目录
              
        show_hidden: 是否显示隐藏文件（以 . 开头的文件）。
                    默认为 False，设置为 True 可查看隐藏文件。
                    
        recursive: 是否递归列出子目录。
                  默认为 False，只列出当前目录。
                  设置为 True 会递归遍历所有子目录。
    
    Returns:
        格式化的目录列表字符串。
        
        成功时返回格式：
        目录: /path/to/directory
        总计: 15 个项目 (3 个目录, 12 个文件)
        
        [目录]
        drwxr-xr-x  src/          2024-01-15 10:30  (子目录)
        drwxr-xr-x  tests/        2024-01-15 10:30  (子目录)
        
        [文件]
        -rw-r--r--  main.py        2024-01-15 10:30  2.5 KB
        -rw-r--r--  README.md      2024-01-15 10:30  4.2 KB
        
        失败时返回错误描述字符串：
        - "错误: 路径不存在"
        - "错误: 路径不是目录"
        - "错误: 访问被拒绝（权限不足）"
        - "错误: 路径超出允许范围"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = list_directory("./src")
        >>> print(result)
        >>> # 输出目录列表
        
        >>> result = list_directory(".", recursive=True)
        >>> print(result)
        >>> # 输出递归目录树
    
    Notes:
        - 结果按类型（目录优先）和名称排序
        - 包含详细的文件元信息便于分析
        - 限制在允许的目录范围内
    """
    logger.info(f"列出目录: {path}")
    
    # 参数验证
    if not path or not isinstance(path, str):
        return "错误: 目录路径不能为空"
    
    path = path.strip()
    
    # 解析路径
    try:
        if path in (".", ""):
            target_path = Path.cwd()
        else:
            target_path = Path(path)
        
        # 转换为绝对路径
        abs_path = target_path.resolve()
        
    except Exception as e:
        logger.error(f"路径解析失败: {e}")
        return f"错误: 无效的路径格式 - {path}"
    
    # 安全检查
    if not is_path_allowed(str(abs_path)):
        logger.warning(f"访问被拒绝: {abs_path} 不在允许范围内")
        return f"错误: 路径超出允许范围 - {abs_path}"
    
    # 检查路径是否存在
    if not abs_path.exists():
        logger.error(f"路径不存在: {abs_path}")
        return f"错误: 路径不存在 - {abs_path}"
    
    # 检查是否为目录
    if not abs_path.is_dir():
        logger.error(f"不是目录: {abs_path}")
        return f"错误: 路径不是目录 - {abs_path}"
    
    try:
        # 构建结果字符串
        result_lines = []
        result_lines.append(f"目录: {abs_path}")
        
        items: List[Path] = list(abs_path.iterdir())
        
        # 分离目录和文件
        dirs = []
        files = []
        
        for item in items:
            # 跳过隐藏文件
            if not show_hidden and item.name.startswith('.'):
                continue
            
            if item.is_dir():
                dirs.append(item)
            else:
                files.append(item)
        
        # 统计信息
        total_items = len(dirs) + len(files)
        result_lines.append(f"总计: {total_items} 个项目 ({len(dirs)} 个目录, {len(files)} 个文件)\n")
        
        # 列出目录
        if dirs:
            result_lines.append("[目录]")
            for d in sorted(dirs):
                try:
                    stat = d.stat()
                    perms = format_permissions(stat.st_mode)
                    mtime = os.path.getmtime(d)
                    import datetime
                    dt = datetime.datetime.fromtimestamp(mtime)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                    result_lines.append(f"  {perms}  {d.name}/        {time_str}")
                except Exception:
                    result_lines.append(f"  drwxr-xr-x  {d.name}/")
        
        # 列出文件
        if files:
            result_lines.append("\n[文件]")
            for f in sorted(files):
                try:
                    stat = f.stat()
                    perms = format_permissions(stat.st_mode)
                    size = stat.st_size
                    size_str = format_file_size(size)
                    mtime = os.path.getmtime(f)
                    import datetime
                    dt = datetime.datetime.fromtimestamp(mtime)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                    result_lines.append(f"  {perms}  {f.name:<20} {time_str}  {size_str:>10}")
                except Exception:
                    result_lines.append(f"  -rw-r--r--  {f.name}")
        
        # 递归模式
        if recursive and dirs:
            result_lines.append("\n" + "=" * 60)
            result_lines.append("[递归子目录内容]")
            
            for d in sorted(dirs):
                sub_result = list_directory(str(d), show_hidden, recursive)
                result_lines.append(f"\n{sub_result}")
        
        result = "\n".join(result_lines)
        logger.debug(f"目录列表完成: {abs_path}, 项目数: {total_items}")
        return result
        
    except PermissionError:
        logger.error(f"权限不足: {abs_path}")
        return f"错误: 访问被拒绝（权限不足）- {abs_path}"
    except Exception as e:
        logger.error(f"列出目录失败: {e}", exc_info=True)
        return f"错误: {str(e)}"


def read_local_file(file_path: str, encoding: Optional[str] = None,
                   max_lines: Optional[int] = None) -> str:
    """
    读取本地文件的内容。
    
    此函数安全地读取文本文件内容，并返回格式化的结果。
    支持指定编码和行数限制，适用于查看代码、配置文件等。
    
    Args:
        file_path: 要读取的文件路径。
                  可以是相对路径或绝对路径。
                  
                  示例：
                  - "agent.py" - 当前目录下的文件
                  - "./config/settings.json" - 相对路径
                  - "/home/user/project/README.md" - 绝对路径
                  - "src/utils/helpers.py" - 子目录中的文件
                  
        encoding: 文件编码。
                 默认自动检测，常用值包括：
                 - "utf-8" - UTF-8 编码（推荐）
                 - "gbk" - GBK 编码（中文 Windows）
                 - "latin-1" - 拉丁编码
                 如果文件包含乱码，可以尝试指定编码。
                 
        max_lines: 最大读取行数限制。
                   默认为 None，表示读取全部内容。
                   设置此值可以避免读取过大的文件。
                   例如：max_lines=100 只读取前 100 行。
    
    Returns:
        格式化的文件内容字符串。
        
        成功时返回格式：
        文件: /path/to/file.py
        编码: utf-8
        行数: 150
        大小: 4.2 KB
        
        --- Content ---
        第 1  行 | def main():
        第 2  行 |     print("Hello")
        第 3  行 |     return 0
        ...
        --- End ---
        
        失败时返回错误描述字符串：
        - "错误: 文件不存在"
        - "错误: 文件是目录"
        - "错误: 文件过大 ({size})，最大允许 {max_size}"
        - "错误: 二进制文件不支持"
        - "错误: 编码不支持"
        - "错误: 访问被拒绝（权限不足）"
        - "错误: 路径超出允许范围"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = read_local_file("agent.py")
        >>> print(result)
        >>> # 输出文件内容
        
        >>> result = read_local_file("README.md", max_lines=50)
        >>> print(result)
        >>> # 只输出前 50 行
        
        >>> result = read_local_file("config.json", encoding="utf-8")
        >>> print(result)
        >>> # 使用 UTF-8 编码读取
    
    Notes:
        - 自动添加行号便于引用
        - 保留文件元信息（编码、行数、大小）
        - 自动检测文件编码
        - 禁止读取敏感文件
        - 二进制文件会被检测并拒绝
    """
    logger.info(f"读取文件: {file_path}")
    
    # 参数验证
    if not file_path or not isinstance(file_path, str):
        return "错误: 文件路径不能为空"
    
    file_path = file_path.strip()
    
    # 解析路径
    try:
        target_path = Path(file_path)
        abs_path = target_path.resolve()
    except Exception as e:
        logger.error(f"路径解析失败: {e}")
        return f"错误: 无效的路径格式 - {file_path}"
    
    # 安全检查
    if not is_path_allowed(str(abs_path)):
        logger.warning(f"访问被拒绝: {abs_path} 不在允许范围内")
        return f"错误: 路径超出允许范围 - {abs_path}"
    
    if not is_path_safe(str(abs_path)):
        return f"错误: 禁止读取敏感文件 - {abs_path}"
    
    # 检查文件是否存在
    if not abs_path.exists():
        logger.error(f"文件不存在: {abs_path}")
        return f"错误: 文件不存在 - {abs_path}"
    
    # 检查是否为文件（不是目录）
    if not abs_path.is_file():
        logger.error(f"不是文件: {abs_path}")
        return f"错误: 路径不是文件 - {abs_path}"
    
    try:
        # 获取文件信息
        stat = abs_path.stat()
        file_size = stat.st_size
        
        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            size_str = format_file_size(file_size)
            max_str = format_file_size(MAX_FILE_SIZE)
            logger.warning(f"文件过大: {size_str} > {max_str}")
            return f"错误: 文件过大 ({size_str})，最大允许 {max_str}"
        
        # 检测编码
        if encoding is None:
            encoding = detect_encoding(abs_path)
        
        # 读取文件内容
        with open(abs_path, 'r', encoding=encoding, errors='replace') as f:
            if max_lines is not None:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                content = ''.join(lines)
                total_lines = sum(1 for _ in open(abs_path, 'r', encoding=encoding, errors='replace'))
                truncated = total_lines > max_lines
            else:
                content = f.read()
                total_lines = content.count('\n') + 1
                truncated = False
        
        # 检测是否为二进制文件（包含大量不可打印字符）
        if is_binary_content(content):
            return f"错误: 二进制文件不支持直接读取 - {abs_path}"
        
        # 格式化输出
        file_size_str = format_file_size(file_size)
        
        result_lines = [
            f"文件: {abs_path}",
            f"编码: {encoding}",
            f"行数: {total_lines}" + (" (已截断)" if truncated else ""),
            f"大小: {file_size_str}",
            "",
            "--- Content ---",
        ]
        
        # 添加带行号的内容
        for i, line in enumerate(content.split('\n'), 1):
            line_num = f"{i:>6} | "
            result_lines.append(line_num + line.rstrip())
        
        result_lines.append("--- End ---")
        
        result = "\n".join(result_lines)
        logger.debug(f"文件读取成功: {abs_path}, {total_lines} 行")
        return result
        
    except PermissionError:
        logger.error(f"权限不足: {abs_path}")
        return f"错误: 访问被拒绝（权限不足）- {abs_path}"
    except UnicodeDecodeError as e:
        logger.error(f"编码错误: {e}")
        # 尝试其他常见编码
        for alt_encoding in ['utf-8', 'gbk', 'latin-1', 'cp1252']:
            try:
                with open(abs_path, 'r', encoding=alt_encoding) as f:
                    f.read()
                return f"错误: 文件编码不是 {encoding}，可能是 {alt_encoding}"
            except:
                continue
        return f"错误: 无法识别文件编码"
    except Exception as e:
        logger.error(f"读取文件失败: {e}", exc_info=True)
        return f"错误: {str(e)}"


def detect_encoding(file_path: Path) -> str:
    """
    检测文件编码。
    
    Args:
        file_path: 文件路径
        
    Returns:
        检测到的编码名称
    """
    # 常见编码列表
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1', 'cp1252']
    
    # 先尝试 UTF-8
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return 'utf-8'
    except UnicodeDecodeError:
        pass
    
    # 尝试检测 BOM
    with open(file_path, 'rb') as f:
        raw = f.read(4)
    
    if raw.startswith(b'\xff\xfe\x00\x00'):
        return 'utf-32-le'
    elif raw.startswith(b'\x00\x00\xfe\xff'):
        return 'utf-32-be'
    elif raw.startswith(b'\xff\xfe'):
        return 'utf-16-le'
    elif raw.startswith(b'\xfe\xff'):
        return 'utf-16-be'
    elif raw.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    
    # 尝试其他编码
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(1000)  # 只读取前 1000 字符检测
            return enc
        except:
            continue
    
    # 默认返回 utf-8
    return 'utf-8'


def is_binary_content(content: str, threshold: float = 0.30) -> bool:
    """
    检测内容是否为二进制。
    
    Args:
        content: 文件内容
        threshold: 二进制字符比例阈值
        
    Returns:
        如果可能是二进制返回 True
    """
    if not content:
        return False
    
    # 统计可打印字符和空白字符
    text_chars = set(bytes(range(32, 127)) + bytes([9, 10, 13]))  # tab, newline, cr
    
    non_text = sum(1 for byte in content.encode('utf-8', errors='ignore') 
                   if byte not in text_chars)
    
    return non_text / max(len(content), 1) > threshold
