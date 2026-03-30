"""
代码编辑工具模块

提供源代码文件的编辑和创建功能，供 Agent 进行自我修改和项目扩展。

本模块封装了代码文件的核心操作：
1. 编辑现有文件（搜索替换）
2. 创建新文件
3. 安全的路径验证

依赖：
    - pathlib: 内置模块
    - typing: 内置模块
"""

import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple


# ============================================================================
# 配置常量
# ============================================================================

# 日志记录器
logger = logging.getLogger(__name__)

# 允许编辑的文件扩展名
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx',  # Python/JavaScript/TypeScript
    '.java', '.kt', '.scala',  # JVM 语言
    '.go', '.rs', '.c', '.cpp', '.h', '.hpp',  # 系统语言
    '.rb', '.php',  # 脚本语言
    '.html', '.css', '.scss', '.sass',  # Web 技术
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',  # 配置文件
    '.md', '.txt', '.rst',  # 文档
    '.sh', '.bash', '.zsh',  # Shell 脚本
    '.sql', '.graphql',  # 数据库
    '.xml', '.svg',  # 标记语言
}

# 禁止编辑的文件模式
FORBIDDEN_PATTERNS = [
    '.env',
    '.password',
    '.secret',
    '.key',
    'id_rsa',
    'credentials.json',
]


# ============================================================================
# 辅助函数
# ============================================================================

def is_editable(file_path: str) -> bool:
    """
    检查文件是否可以被编辑。
    
    Args:
        file_path: 文件路径
        
    Returns:
        如果文件可以编辑返回 True
    """
    # 检查扩展名
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS and ext:
        logger.warning(f"不支持的文件类型: {ext}")
        return False
    
    # 检查禁止模式
    abs_path = os.path.abspath(file_path).lower()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.lower() in abs_path:
            logger.warning(f"禁止编辑敏感文件: {pattern}")
            return False
    
    return True


def create_backup(file_path: str) -> Optional[str]:
    """
    在编辑前创建文件的备份。
    
    Args:
        file_path: 要备份的文件路径
        
    Returns:
        备份文件的路径，失败返回 None
    """
    try:
        abs_path = Path(file_path).resolve()
        backup_path = abs_path.with_suffix(abs_path.suffix + '.bak')
        
        # 如果备份已存在，添加时间戳
        if backup_path.exists():
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = abs_path.with_suffix(f'.{timestamp}.bak')
        
        shutil.copy2(abs_path, backup_path)
        logger.debug(f"已创建备份: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        return None


def validate_path(file_path: str, must_exist: bool = False) -> Tuple[bool, str]:
    """
    验证文件路径的有效性和安全性。
    
    Args:
        file_path: 要验证的路径
        must_exist: 是否要求文件必须存在
        
    Returns:
        (是否有效, 错误消息) 元组
    """
    if not file_path or not isinstance(file_path, str):
        return False, "文件路径不能为空"
    
    try:
        path = Path(file_path)
        abs_path = path.resolve()
        
        # 检查文件存在性
        if must_exist and not abs_path.exists():
            return False, f"文件不存在: {abs_path}"
        
        if must_exist and not abs_path.is_file():
            return False, f"路径不是文件: {abs_path}"
        
        # 安全检查（对于存在的文件）
        if abs_path.exists():
            if not is_editable(str(abs_path)):
                return False, "不支持编辑此类型的文件"
        
        # 检查父目录是否存在或可创建
        parent = abs_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"无法创建父目录: {e}"
        
        return True, ""
        
    except Exception as e:
        return False, f"路径验证失败: {e}"


def format_diff(old_content: str, new_content: str, 
                search_string: str, max_context: int = 3) -> str:
    """
    格式化差异输出，用于显示更改内容。
    
    Args:
        old_content: 原始内容
        new_content: 新内容
        search_string: 被搜索的字符串
        max_context: 上下文行数
        
    Returns:
        格式化的差异字符串
    """
    lines = old_content.split('\n')
    result_lines = []
    
    # 找到搜索字符串的位置
    search_idx = old_content.find(search_string)
    if search_idx == -1:
        return "未找到搜索字符串"
    
    # 计算行号
    line_num = old_content[:search_idx].count('\n')
    
    # 添加上下文
    start_line = max(0, line_num - max_context)
    end_line = min(len(lines), line_num + search_string.count('\n') + max_context + 1)
    
    for i, line in enumerate(lines[start_line:end_line], start=start_line + 1):
        prefix = " " if i != line_num + 1 else ">"
        result_lines.append(f"{prefix} {i:4d} | {line}")
    
    return '\n'.join(result_lines)


# ============================================================================
# 核心功能函数
# ============================================================================

def edit_local_file(file_path: str, search_string: str, 
                   replace_string: str, create_backup_first: bool = True) -> str:
    """
    编辑本地文件，替换指定内容。
    
    此函数在文件中搜索指定的字符串，并将其替换为新内容。
    支持多种匹配模式，并自动创建备份以确保安全性。
    
    Args:
        file_path: 要编辑的文件路径。
                  可以是相对路径或绝对路径。
                  
                  示例：
                  - "agent.py" - 当前目录下的文件
                  - "./tools/web_tools.py" - 相对路径
                  - "/path/to/project/main.py" - 绝对路径
                  
        search_string: 要搜索并替换的原字符串。
                      必须精确匹配（包括所有空白字符）。
                      支持多行匹配。
                      
                      示例：
                      - "def hello():" - 替换函数定义
                      - "return None" - 替换返回值
                      - 多行字符串 - 跨行替换
                      
        replace_string: 替换后的新字符串。
                       可以包含换行符和其他特殊字符。
                       长度可以与原字符串不同。
                       
        create_backup_first: 是否在编辑前创建备份。
                            默认为 True。
                            备份文件将保存为 filename.ext.bak。
    
    Returns:
        操作结果的描述字符串。
        
        成功时返回格式：
        成功: 已替换文件中的内容
        文件: /path/to/file.py
        备份: /path/to/file.py.bak (已创建)
        
        替换详情:
        - 匹配次数: 1
        - 原字符串长度: 25 字符
        - 新字符串长度: 30 字符
        
        失败时返回错误描述：
        - "错误: 文件路径不能为空"
        - "错误: 搜索字符串不能为空"
        - "错误: 文件不存在 - /path/to/file"
        - "错误: 不支持编辑此类型的文件"
        - "错误: 未找到搜索字符串"
        - "错误: 找到多个匹配项 (N 个)，请提供更精确的搜索字符串"
        - "错误: 文件编辑失败 - PermissionError"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = edit_local_file(
        ...     "agent.py",
        ...     "def main():",
        ...     "async def main():"
        ... )
        >>> print(result)
    
    Notes:
        - 搜索是大小敏感的
        - 支持跨行匹配
        - 自动创建 .bak 备份文件
        - 如果找到多个匹配，只替换第一个
        - 使用前请仔细检查搜索字符串的唯一性
    """
    logger.info(f"编辑文件: {file_path}")
    logger.debug(f"搜索字符串: {repr(search_string[:100])}...")
    
    # 参数验证
    if not file_path:
        return "错误: 文件路径不能为空"
    
    if not search_string:
        return "错误: 搜索字符串不能为空"
    
    # 路径验证
    valid, error_msg = validate_path(file_path, must_exist=True)
    if not valid:
        logger.error(f"路径验证失败: {error_msg}")
        return f"错误: {error_msg}"
    
    abs_path = Path(file_path).resolve()
    
    # 可编辑性检查
    if not is_editable(str(abs_path)):
        return f"错误: 不支持编辑此类型的文件 - {abs_path}"
    
    try:
        # 读取原文件内容
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            old_content = f.read()
        
        # 检查搜索字符串是否存在
        if search_string not in old_content:
            logger.error("未找到搜索字符串")
            return "错误: 未找到搜索字符串"
        
        # 检查是否有多处匹配
        count = old_content.count(search_string)
        if count > 1:
            logger.warning(f"找到多个匹配项: {count}")
            return f"错误: 找到多个匹配项 ({count} 个)，请提供更精确的搜索字符串"
        
        # 创建备份
        backup_path = None
        if create_backup_first:
            backup_path = create_backup(str(abs_path))
            if backup_path is None:
                logger.warning("创建备份失败，继续编辑（风险操作）")
        
        # 执行替换
        new_content = old_content.replace(search_string, replace_string, 1)
        
        # 写入文件
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 构建结果
        result_lines = [
            "成功: 已替换文件中的内容",
            f"文件: {abs_path}",
        ]
        
        if backup_path:
            result_lines.append(f"备份: {backup_path} (已创建)")
        
        result_lines.extend([
            "",
            "替换详情:",
            f"- 匹配次数: 1",
            f"- 原字符串长度: {len(search_string)} 字符",
            f"- 新字符串长度: {len(replace_string)} 字符",
        ])
        
        logger.info(f"文件编辑成功: {abs_path}")
        return '\n'.join(result_lines)
        
    except PermissionError:
        logger.error(f"权限不足: {abs_path}")
        return f"错误: 文件编辑失败 - 权限不足，请检查文件权限"
    except Exception as e:
        logger.error(f"编辑文件失败: {e}", exc_info=True)
        return f"错误: 文件编辑失败 - {str(e)}"


def create_new_file(file_path: str, content: str = "",
                   overwrite: bool = False) -> str:
    r"""
    创建新文件或覆盖现有文件。
    
    此函数用于创建新的代码文件、配置文件或文档。
    可以选择性地覆盖已存在的文件。
    
    Args:
        file_path: 要创建的文件的完整路径。
                  可以是相对路径或绝对路径。
                  父目录会自动创建（如果不存在）。
                  
                  示例：
                  - "new_module.py" - 当前目录下
                  - "./utils/helpers.py" - 子目录中
                  - "/path/to/project/README.md" - 绝对路径
                  
        content: 文件的初始内容。
                默认为空字符串。
                可以是多行字符串，包括代码、配置等。
                
                示例：
                - "#!/usr/bin/env python3\nModule docstring\n"
                - '{"name": "project", "version": "1.0.0"}'
                - "# 新文件\nprint('Hello')"
                 
        overwrite: 是否覆盖已存在的文件。
                  默认为 False（安全模式，不覆盖）。
                  设置为 True 将直接覆盖已有文件。
                  警告：覆盖操作不可逆，请谨慎使用！
    
    Returns:
        操作结果的描述字符串。
        
        新建成功时返回：
        成功: 已创建新文件
        文件: /path/to/new_file.py
        大小: 256 字节
        行数: 15
        
        覆盖成功时返回：
        成功: 已覆盖文件
        文件: /path/to/existing_file.py
        警告: 原文件已被覆盖，请检查内容是否正确
        
        失败时返回错误描述：
        - "错误: 文件路径不能为空"
        - "错误: 路径包含非法字符"
        - "错误: 文件已存在 (overwrite=False)"
        - "错误: 父目录创建失败"
        - "错误: 文件创建失败 - PermissionError"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        # 创建新的 Python 模块
        >>> result = create_new_file(
        ...     "utils/data_processor.py",
        ...     "#!/usr/bin/env python3\n# Module docstring\n\ndef process(data):\n    return {'count': len(data)}\n",
        ...     overwrite=False
        ... )
        >>> print(result)
        
        # 创建配置文件
        >>> result = create_new_file(
        ...     "config/app.yaml",
        ...     "app:\n  name: MyApp\n  debug: true",
        ...     overwrite=True
        ... )
        >>> print(result)
        
        # 创建空文件
        >>> result = create_new_file("placeholder.txt")
        >>> print(result)
    
    Notes:
        - 自动创建父目录（如果不存在）
        - 默认使用 UTF-8 编码
        - 如果 overwrite=True，会直接覆盖已有文件
        - 创建的文件会有合适的行尾符（自动适应系统）
        - 会自动添加执行权限位（对于 shebang 脚本）
    """
    logger.info(f"创建文件: {file_path}")
    
    # 参数验证
    if not file_path:
        return "错误: 文件路径不能为空"
    
    file_path = file_path.strip()
    
    # 检查路径安全性
    invalid_chars = ['<', '>', '|', '\0']
    for char in invalid_chars:
        if char in file_path:
            return f"错误: 路径包含非法字符: {char}"
    
    # 路径验证
    valid, error_msg = validate_path(file_path, must_exist=False)
    if not valid:
        # 对于"文件不存在"以外的错误，返回错误
        if "不存在" not in error_msg:
            logger.error(f"路径验证失败: {error_msg}")
            return f"错误: {error_msg}"
    
    abs_path = Path(file_path).resolve()
    
    try:
        # 检查文件是否已存在
        if abs_path.exists():
            if not overwrite:
                logger.warning(f"文件已存在: {abs_path}")
                return f"错误: 文件已存在 (overwrite=False)\n如需覆盖，请设置 overwrite=True"
            
            # 覆盖模式：先创建备份
            import shutil
            backup_path = abs_path.with_suffix(abs_path.suffix + '.backup')
            shutil.copy2(abs_path, backup_path)
            logger.info(f"已备份原文件: {backup_path}")
            overwrite_mode = True
        else:
            overwrite_mode = False
        
        # 确保父目录存在
        parent = abs_path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"已创建父目录: {parent}")
            except Exception as e:
                return f"错误: 父目录创建失败 - {str(e)}"
        
        # 创建文件并写入内容
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 对于有 shebang 的脚本，设置执行权限（Unix 系统）
        import sys
        if sys.platform != 'win32' and content.startswith('#!'):
            import stat
            current_mode = abs_path.stat().st_mode
            abs_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        # 计算文件信息
        file_size = len(content.encode('utf-8'))
        line_count = content.count('\n') + 1 if content else 0
        
        # 构建结果
        result_lines = []
        
        if overwrite_mode:
            result_lines.append("成功: 已覆盖文件")
            result_lines.append(f"文件: {abs_path}")
            result_lines.append(f"警告: 原文件已被备份为 {backup_path.name}")
        else:
            result_lines.append("成功: 已创建新文件")
            result_lines.append(f"文件: {abs_path}")
        
        result_lines.extend([
            f"大小: {file_size} 字节",
            f"行数: {line_count}",
        ])
        
        logger.info(f"文件创建成功: {abs_path}")
        return '\n'.join(result_lines)
        
    except PermissionError:
        logger.error(f"权限不足: {abs_path}")
        return f"错误: 文件创建失败 - 权限不足，请检查目录权限"
    except Exception as e:
        logger.error(f"创建文件失败: {e}", exc_info=True)
        return f"错误: 文件创建失败 - {str(e)}"
