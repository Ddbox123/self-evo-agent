"""
安全工具模块

提供代码质量检查和项目管理功能，确保 Agent 的自我修改安全可靠。

本模块包含：
1. 语法检查 - 验证代码语法正确性
2. 项目备份 - 防止错误修改导致系统不可用

依赖：
    - py_compile: 内置模块 (Python)
    - ast: 内置模块 (Python)
    - shutil: 内置模块
    - datetime: 内置模块
"""

import ast
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# 配置常量
# ============================================================================

# 日志记录器
logger = logging.getLogger(__name__)

# 备份目录
DEFAULT_BACKUP_DIR = "backups"

# 最大备份保留数量
MAX_BACKUP_COUNT = 50

# 要检查语法的文件扩展名
CHECKABLE_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'jsx',
    '.tsx': 'tsx',
}

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


# ============================================================================
# 辅助函数
# ============================================================================

def ensure_backup_dir() -> Path:
    """
    确保备份目录存在。
    
    Returns:
        备份目录的 Path 对象
    """
    backup_dir = PROJECT_ROOT / DEFAULT_BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_project_files(include_patterns: Optional[List[str]] = None,
                      exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """
    获取项目中的所有源代码文件。
    
    Args:
        include_patterns: 包含的文件模式列表
        exclude_patterns: 排除的文件模式列表
        
    Returns:
        文件路径列表
    """
    if include_patterns is None:
        include_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
    
    if exclude_patterns is None:
        exclude_patterns = [
            '__pycache__', '.git', '.venv', 'venv',
            'node_modules', '.pytest_cache', '.mypy_cache',
            '*.pyc', '*.pyo', 'dist', 'build', '.eggs'
        ]
    
    files = []
    
    for pattern in include_patterns:
        for path in PROJECT_ROOT.rglob(pattern):
            # 检查是否应该排除
            should_exclude = False
            for exclude in exclude_patterns:
                if exclude.startswith('*'):
                    if path.suffix == exclude[1:]:
                        should_exclude = True
                        break
                elif exclude in str(path):
                    should_exclude = True
                    break
            
            if not should_exclude and path.is_file():
                files.append(path)
    
    return sorted(files)


def clean_old_backups(backup_dir: Path, max_count: int = MAX_BACKUP_COUNT) -> int:
    """
    清理多余的旧备份。
    
    Args:
        backup_dir: 备份目录
        max_count: 保留的最大备份数量
        
    Returns:
        删除的备份数量
    """
    try:
        # 获取所有备份文件，按修改时间排序
        backups = sorted(
            backup_dir.glob('backup_*.zip'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 删除多余的备份
        deleted = 0
        for backup in backups[max_count:]:
            try:
                backup.unlink()
                deleted += 1
                logger.debug(f"已删除旧备份: {backup.name}")
            except Exception as e:
                logger.warning(f"删除备份失败: {backup.name}, {e}")
        
        return deleted
        
    except Exception as e:
        logger.error(f"清理备份失败: {e}")
        return 0


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    格式化时间戳。
    
    Args:
        dt: datetime 对象，默认为当前时间
        
    Returns:
        格式化的时间戳字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y%m%d_%H%M%S')


# ============================================================================
# 核心功能函数
# ============================================================================

def check_syntax(file_path: str, language: Optional[str] = None) -> str:
    """
    检查文件的语法正确性。
    
    此函数对指定的代码文件进行语法检查，返回详细的检查报告。
    主要用于 Agent 修改代码后验证修改的正确性，防止引入语法错误。
    
    Args:
        file_path: 要检查的文件路径。
                  支持相对路径和绝对路径。
                  
                  示例：
                  - "agent.py" - 当前目录
                  - "./tools/web_tools.py" - 相对路径
                  - "/path/to/project/main.py" - 绝对路径
                  - "*.py" 或 "tools/*.py" - 模式匹配（检查多个文件）
                  
        language: 代码语言。
                 默认为 None，表示根据文件扩展名自动检测。
                 支持的值：
                 - "python" 或 "py"
                 - "javascript" 或 "js"
                 - "typescript" 或 "ts"
                 
                 注意：目前主要支持 Python 语法检查，
                 其他语言返回相应提示。
    
    Returns:
        格式化的检查报告字符串。
        
        Python 语法检查成功时：
        ```
        ✓ 语法检查通过
        文件: /path/to/file.py
        行数: 150
        预估复杂度: 中等
        
        分析摘要:
        - 导入语句: 12
        - 函数定义: 8
        - 类定义: 2
        - 顶级语句: 5
        ```
        
        检查成功但有问题时：
        ```
        ⚠ 语法检查完成，发现问题
        文件: /path/to/file.py
        错误数: 2
        
        问题详情:
        1. 第 25 行: unexpected EOF while parsing
           提示: 可能缺少闭合括号
           
        2. 第 30 行: invalid syntax
           提示: 'return' 语句不能在函数外部使用
        ```
        
        无法检查时：
        ```
        ⚠ 无法执行语法检查
        文件: /path/to/file.py
        原因: 不支持此文件类型的语法检查 (.js)
        
        提示: JavaScript/TypeScript 文件可以使用以下工具检查：
        - ESLint
        - TypeScript 编译器 (tsc --noEmit)
        ```
        
        失败时：
        - "错误: 文件不存在"
        - "错误: 无法读取文件"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = check_syntax("agent.py")
        >>> print(result)
        >>> # 输出检查结果
        
        >>> # 检查多个文件
        >>> for f in ["a.py", "b.py", "c.py"]:
        ...     print(check_syntax(f))
        
        >>> # 指定语言
        >>> result = check_syntax("script.py", language="python")
    
    Notes:
        - Python 文件使用内置的 ast 模块进行深度分析
        - 不仅仅是语法检查，还会分析代码结构
        - 返回代码统计信息（函数数、类数等）
        - 对于不支持的语言，提供替代工具建议
    """
    logger.info(f"检查语法: {file_path}")
    
    # 参数验证
    if not file_path:
        return "错误: 文件路径不能为空"
    
    file_path = file_path.strip()
    
    # 路径解析
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        abs_path = path.resolve()
    except Exception as e:
        return f"错误: 无效的路径 - {e}"
    
    # 处理通配符
    if '*' in str(abs_path):
        results = []
        for matched in PROJECT_ROOT.glob(str(abs_path)):
            if matched.is_file():
                result = check_syntax(str(matched), language)
                results.append(result)
        
        if not results:
            return f"错误: 没有匹配的文件: {file_path}"
        
        return "\n\n" + "=" * 50 + "\n\n".join(results)
    
    # 检查文件存在
    if not abs_path.exists():
        return f"错误: 文件不存在 - {abs_path}"
    
    if not abs_path.is_file():
        return f"错误: 路径不是文件 - {abs_path}"
    
    # 检测语言
    ext = abs_path.suffix.lower()
    
    if language is None:
        language = CHECKABLE_EXTENSIONS.get(ext, None)
    
    # Python 语法检查
    if language in ('python', 'py') or ext == '.py':
        return _check_python_syntax(abs_path)
    
    # 不支持的语言
    lang_name = {
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JSX',
        '.tsx': 'TSX',
    }.get(ext, ext)
    
    suggestions = {
        '.js': 'ESLint、TypeScript 编译器 (tsc)',
        '.ts': 'TypeScript 编译器 (tsc --noEmit)',
        '.jsx': 'ESLint',
        '.tsx': 'ESLint',
    }
    
    return f"""⚠ 无法执行语法检查
文件: {abs_path}
原因: 不支持此文件类型的语法检查 ({lang_name})

提示: {suggestions.get(ext, '请使用相应的 linter 或编译器')}"""


def _check_python_syntax(file_path: Path) -> str:
    """
    Python 专用的语法检查。
    
    Args:
        file_path: Python 文件路径
        
    Returns:
        检查结果字符串
    """
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        
        # 解析 AST
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            # 语法错误
            error_type = e.__class__.__name__
            error_msg = str(e).replace('\n', ' ') if str(e) else error_type
            
            # 生成提示
            hints = _generate_syntax_hint(e)
            
            return f"""⚠ 语法检查完成，发现问题
文件: {file_path}
错误数: 1

问题详情:
  第 {e.lineno} 行: {error_msg}
  {hints}"""
        
        # 代码分析
        analysis = _analyze_python_code(tree)
        
        # 复杂度评估
        complexity = _estimate_complexity(tree)
        
        # 成功结果
        return f"""✓ 语法检查通过
文件: {file_path}
行数: {source.count('\n') + 1}
预估复杂度: {complexity}

分析摘要:
- 导入语句: {analysis['imports']}
- 函数定义: {analysis['functions']}
- 类定义: {analysis['classes']}
- 顶级语句: {analysis['top_level']}"""
        
    except PermissionError:
        return f"错误: 无法读取文件（权限不足）- {file_path}"
    except Exception as e:
        return f"错误: 检查失败 - {str(e)}"


def _generate_syntax_hint(error: SyntaxError) -> str:
    """
    根据语法错误生成修复提示。
    
    Args:
        error: SyntaxError 对象
        
    Returns:
        提示字符串
    """
    msg = str(error).lower()
    
    hints = {
        'eof': '提示: 可能缺少闭合括号、方括号或引号',
        'unexpected': '提示: 检查语句是否在正确的作用域内',
        'invalid syntax': '提示: 可能是缩进错误或使用了非法字符',
        'paren': '提示: 括号未正确闭合',
        'bracket': '提示: 方括号未正确闭合',
        'brace': '提示: 花括号未正确闭合',
        'unterminated': '提示: 字符串引号未正确闭合',
        'indent': '提示: 检查缩进是否一致（建议使用 4 空格）',
    }
    
    for key, hint in hints.items():
        if key in msg:
            return hint
    
    return '提示: 请检查相关行的语法'


def _analyze_python_code(tree: ast.AST) -> Dict[str, int]:
    """
    分析 Python 代码结构。
    
    Args:
        tree: AST 树
        
    Returns:
        包含统计信息的字典
    """
    analysis = {
        'imports': 0,
        'functions': 0,
        'classes': 0,
        'top_level': 0,
    }
    
    class CodeVisitor(ast.NodeVisitor):
        def visit_Import(self, node):
            analysis['imports'] += 1
            self.generic_visit(node)
        
        def visit_ImportFrom(self, node):
            analysis['imports'] += 1
            self.generic_visit(node)
        
        def visit_FunctionDef(self, node):
            if isinstance(node.parent, ast.Module) if hasattr(ast, 'parent') else True:
                analysis['functions'] += 1
            self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            analysis['classes'] += 1
            self.generic_visit(node)
    
    visitor = CodeVisitor()
    visitor.visit(tree)
    
    # 统计顶级语句
    analysis['top_level'] = len([n for n in tree.body 
                                 if not isinstance(n, (ast.Import, ast.ImportFrom,
                                                       ast.FunctionDef, ast.ClassDef))])
    
    return analysis


def _estimate_complexity(tree: ast.AST) -> str:
    """
    估算代码复杂度。
    
    Args:
        tree: AST 树
        
    Returns:
        复杂度等级描述
    """
    # 统计各种节点
    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self):
            self.functions = 0
            self.conditionals = 0
            self.loops = 0
            self.comprehensions = 0
        
        def visit_FunctionDef(self, node):
            self.functions += 1
            self.generic_visit(node)
        
        def visit_If(self, node):
            self.conditionals += 1
            self.generic_visit(node)
        
        def visit_For(self, node):
            self.loops += 1
            self.generic_visit(node)
        
        def visit_While(self, node):
            self.loops += 1
            self.generic_visit(node)
        
        def visit_ListComp(self, node):
            self.comprehensions += 1
            self.generic_visit(node)
        
        def visit_DictComp(self, node):
            self.comprehensions += 1
            self.generic_visit(node)
        
        def visit_SetComp(self, node):
            self.comprehensions += 1
            self.generic_visit(node)
    
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    
    # 计算简单复杂度分数
    score = (visitor.functions * 2 + 
             visitor.conditionals * 1.5 + 
             visitor.loops * 2 +
             visitor.comprehensions * 1.5)
    
    if score < 10:
        return "简单"
    elif score < 30:
        return "中等"
    elif score < 60:
        return "复杂"
    else:
        return "非常复杂"


def backup_project(version_note: str = "") -> str:
    """
    创建项目备份。
    
    此函数将整个项目打包成压缩文件，便于在重大修改前保存快照。
    支持时间戳命名和版本注释，便于管理和恢复。
    
    Args:
        version_note: 版本注释/说明。
                     用于描述此次备份的用途或版本信息。
                     
                     示例：
                     - "重大重构前"
                     - "添加新功能 v1.2"
                     - "修复关键 bug"
                     - "daily backup"
                     - "" (空注释也允许)
    
    Returns:
        操作结果的描述字符串。
        
        成功时返回：
        ```
        ✓ 备份创建成功
        文件: backups/backup_20240115_103000_v1.zip
        大小: 2.5 MB
        
        版本说明: 重大重构前
        包含文件: 25 个文件, 3 个目录
        
        提示: 如需恢复，请解压备份文件到项目目录
        ```
        
        失败时返回错误描述：
        - "错误: 备份目录创建失败"
        - "错误: 没有找到要备份的文件"
        - "错误: 备份创建失败 - 磁盘空间不足"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = backup_project("添加 web_tools 模块")
        >>> print(result)
        >>> # 输出备份结果
        
        >>> # 定期自动备份
        >>> result = backup_project(f"每日备份 {datetime.now().date()}")
        >>> print(result)
    
    Notes:
        - 备份文件保存在项目根目录的 backups/ 文件夹
        - 文件名格式: backup_YYYYMMDD_HHMMSS.zip
        - 包含版本注释作为元数据
        - 自动清理超过限制的旧备份（保留最近 50 个）
        - 排除缓存、临时文件和构建产物
    """
    logger.info("创建项目备份")
    
    # 生成时间戳
    timestamp = format_timestamp()
    
    # 清理版本注释（用于文件名）
    safe_note = re.sub(r'[^\w\-]', '_', version_note)[:30] if version_note else ""
    if safe_note:
        backup_filename = f"backup_{timestamp}_{safe_note}.zip"
    else:
        backup_filename = f"backup_{timestamp}.zip"
    
    # 确保备份目录存在
    try:
        backup_dir = ensure_backup_dir()
    except Exception as e:
        return f"错误: 备份目录创建失败 - {str(e)}"
    
    backup_path = backup_dir / backup_filename
    
    # 获取要备份的文件
    files_to_backup = get_project_files()
    
    if not files_to_backup:
        return "错误: 没有找到要备份的文件"
    
    try:
        # 创建 ZIP 压缩包
        file_count = 0
        
        with zipfile.ZipFile(backup_path, 'w', 
                            compression=zipfile.ZIP_DEFLATED,
                            compresslevel=6) as zf:
            # 添加说明文件
            metadata = f"""项目备份元数据
==================

备份时间: {datetime.now().isoformat()}
版本说明: {version_note or '(无)'}
包含文件: {len(files_to_backup)}
"""
            zf.writestr('METADATA.txt', metadata)
            file_count += 1
            
            # 添加项目文件
            for file_path in files_to_backup:
                try:
                    arcname = file_path.relative_to(PROJECT_ROOT)
                    zf.write(file_path, arcname)
                    file_count += 1
                except Exception as e:
                    logger.warning(f"跳过文件: {file_path}, {e}")
        
        # 计算备份大小
        backup_size = backup_path.stat().st_size
        
        # 清理旧备份
        deleted = clean_old_backups(backup_dir)
        
        # 构建结果
        result_lines = [
            "✓ 备份创建成功",
            f"文件: {backup_path}",
            f"大小: {_format_size(backup_size)}",
            "",
            f"版本说明: {version_note or '(无)'}",
            f"包含文件: {file_count} 个项目",
        ]
        
        if deleted > 0:
            result_lines.append(f"自动清理: 删除了 {deleted} 个旧备份")
        
        result_lines.extend([
            "",
            "提示: 如需恢复，请解压备份文件到项目目录",
            f"命令: unzip -o {backup_filename}",
        ])
        
        logger.info(f"备份创建成功: {backup_path}")
        return '\n'.join(result_lines)
        
    except PermissionError:
        return f"错误: 备份创建失败 - 权限不足，请检查 {backup_dir} 目录权限"
    except Exception as e:
        logger.error(f"备份创建失败: {e}", exc_info=True)
        return f"错误: 备份创建失败 - {str(e)}"


def _format_size(size_bytes: int) -> str:
    """
    格式化文件大小。
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# 导入 re 模块（在 backup_project 中使用）
import re
