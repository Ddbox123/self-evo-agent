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
    - traceback: 内置模块
"""

import ast
import logging
import os
import shutil
import sys
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============================================================================
# 配置常量
# ============================================================================

# 日志记录器
logger = logging.getLogger(__name__)

# 备份目录
DEFAULT_BACKUP_DIR = "backups"

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


def format_size(size_bytes: int) -> str:
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


# ============================================================================
# 核心功能函数
# ============================================================================

def check_syntax(file_path: str) -> str:
    """
    检查 Python 文件的语法正确性。
    
    使用 Python 内置的 ast 模块解析目标文件，执行以下检查：
    1. 读取文件内容
    2. 使用 ast.parse() 解析源码
    3. 如果捕获到 SyntaxError，生成详细的错误追踪信息
    4. 如果成功，返回 'Syntax OK'
    
    Args:
        file_path: 要检查的 Python 文件路径。
                  支持相对路径和绝对路径。
                  
                  示例：
                  - "agent.py" - 当前目录
                  - "./tools/web_tools.py" - 相对路径
                  - "/path/to/project/main.py" - 绝对路径
    
    Returns:
        检查结果字符串。
        
        语法正确时：
        >>> check_syntax("agent.py")
        'Syntax OK'
        
        语法错误时返回详细追踪信息：
        >>> check_syntax("broken.py")
        '''
        Traceback (most recent call last):
          File "broken.py", line 10
            print("hello
                       ^
        SyntaxError: invalid syntax
        
        错误位置:
          - 文件: broken.py
          - 行号: 10
          - 列号: 14
          - 错误类型: SyntaxError
          - 错误信息: invalid syntax
        
        可能的原因:
          - 字符串未正确闭合（缺少引号）
          - 括号/方括号/花括号未配对
          - 缩进不一致
          - 关键字拼写错误
        '''
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = check_syntax("tools/code_tools.py")
        >>> print(result)
        Syntax OK
        
        >>> result = check_syntax("broken_file.py")
        >>> print(result)
        Traceback (most recent call last):
          ...
    
    Notes:
        - 仅支持 Python 文件（.py 后缀）
        - 使用 Python 标准库的 ast 模块进行解析
        - 错误信息包含完整的 traceback，便于 Agent 理解错误位置
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
    
    # 检查文件存在
    if not abs_path.exists():
        return f"错误: 文件不存在 - {abs_path}"
    
    if not abs_path.is_file():
        return f"错误: 路径不是文件 - {abs_path}"
    
    # 检查是否为 Python 文件
    if abs_path.suffix.lower() != '.py':
        return f"错误: 仅支持 .py 文件 - {abs_path}"
    
    try:
        # 读取文件内容
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        
        # 使用 ast.parse() 检查语法
        # 如果语法正确，ast.parse() 会返回一个 ast.Module 对象
        # 如果有语法错误，会抛出 SyntaxError 异常
        ast.parse(source, filename=str(abs_path))
        
        # 语法检查通过
        logger.info(f"语法检查通过: {abs_path}")
        return "Syntax OK"
        
    except SyntaxError as e:
        # 捕获语法错误，生成详细的 traceback 信息
        logger.warning(f"语法错误: {abs_path}, {e}")
        
        # 使用 traceback 模块生成详细的错误追踪
        tb_lines = traceback.format_exception(
            type(e).__name__,
            e,
            e.__traceback__,
            limit=10  # 限制追溯深度
        )
        traceback_str = ''.join(tb_lines)
        
        # 构建详细的错误报告
        error_report = []
        error_report.append("=" * 60)
        error_report.append("语法错误详情")
        error_report.append("=" * 60)
        error_report.append("")
        error_report.append("Traceback (most recent call last):")
        error_report.append(traceback_str)
        error_report.append("")
        error_report.append("=" * 60)
        error_report.append("错误位置:")
        error_report.append(f"  - 文件: {abs_path}")
        error_report.append(f"  - 行号: {e.lineno}")
        if hasattr(e, 'offset') and e.offset:
            error_report.append(f"  - 列号: {e.offset}")
        error_report.append(f"  - 错误类型: {type(e).__name__}")
        error_report.append(f"  - 错误信息: {e.msg if hasattr(e, 'msg') else str(e)}")
        error_report.append("")
        error_report.append("=" * 60)
        error_report.append("可能的修复建议:")
        
        # 根据错误类型提供具体的修复建议
        error_msg = str(e).lower()
        
        if 'eof' in error_msg:
            error_report.append("  - 检查是否缺少闭合符号: ) ] } \" '")
            error_report.append("  - 多行字符串可能未正确结束")
        elif 'unterminated' in error_msg or 'eol' in error_msg:
            error_report.append("  - 字符串引号未正确闭合")
            error_report.append("  - 检查是否在字符串中间换行")
        elif 'invalid syntax' in error_msg:
            error_report.append("  - 检查是否有非法字符或拼写错误")
            error_report.append("  - 确保关键字拼写正确（如 def, return, import 等）")
        elif 'unexpected' in error_msg:
            error_report.append("  - 检查语句是否在正确的作用域内")
            error_report.append("  - 确保缩进正确")
        elif 'indent' in error_msg:
            error_report.append("  - 检查缩进是否一致（建议使用 4 空格）")
            error_report.append("  - 确保没有混用空格和 Tab")
            error_report.append("  - 类和函数的定义需要正确的缩进层级")
        elif 'paren' in error_msg or 'bracket' in error_msg or 'brace' in error_msg:
            error_report.append("  - 检查括号/方括号/花括号是否配对")
            error_report.append("  - 确保每个开符号都有对应的闭符号")
        elif 'named' in error_msg and 'must' in error_msg:
            error_report.append("  - 关键字参数赋值错误")
            error_report.append("  - 检查是否使用了保留关键字作为变量名")
        else:
            error_report.append("  - 请仔细检查错误行的语法")
            error_report.append("  - 对照 Python 语法规范进行修正")
        
        error_report.append("=" * 60)
        
        return '\n'.join(error_report)
        
    except UnicodeDecodeError:
        return f"错误: 文件编码问题，请确保文件是 UTF-8 编码 - {abs_path}"
        
    except PermissionError:
        return f"错误: 权限不足，无法读取文件 - {abs_path}"
        
    except Exception as e:
        logger.error(f"检查失败: {e}", exc_info=True)
        return f"错误: 检查失败 - {str(e)}"


def backup_project(version_note: str = "") -> str:
    """
    创建项目备份。
    
    使用 shutil 模块将以下内容打包成 zip 文件：
    1. tools/ 目录（包含所有工具模块）
    2. agent.py（主入口文件）
    
    备份文件将保存到 backups/ 目录，使用时间戳命名。
    
    Args:
        version_note: 版本注释/说明。
                     用于描述此次备份的用途。
                     
                     示例：
                     - "添加新功能"
                     - "修复 bug"
                     - "重大重构"
                     - "" (空注释也允许)
    
    Returns:
        操作结果的描述字符串。
        
        成功时返回：
        >>> backup_project("测试备份")
        '''
        备份创建成功
        文件: backups/backup_20240115_103000.zip
        大小: 15.3 KB
        包含: agent.py, tools/
        版本说明: 测试备份
        
        提示: 如需恢复，请解压备份文件到项目目录
        '''
        
        失败时返回错误描述：
        - "错误: 备份目录创建失败"
        - "错误: 源文件不存在"
        - "错误: 备份创建失败"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = backup_project("添加 web_tools 模块")
        >>> print(result)
        
        >>> # 快速备份
        >>> result = backup_project()
        >>> print(result)
    
    Notes:
        - 备份文件保存在项目根目录的 backups/ 文件夹
        - 文件名格式: backup_YYYYMMDD_HHMMSS.zip
        - 包含版本注释作为元数据
        - 使用 shutil 模块进行文件复制和打包
    """
    logger.info("创建项目备份")
    
    # 生成时间戳
    timestamp = format_timestamp()
    backup_filename = f"backup_{timestamp}.zip"
    
    # 确保备份目录存在
    try:
        backup_dir = ensure_backup_dir()
        logger.info(f"备份目录: {backup_dir}")
    except Exception as e:
        return f"错误: 备份目录创建失败 - {str(e)}"
    
    backup_path = backup_dir / backup_filename
    
    # 定义要备份的内容
    # 1. agent.py
    # 2. tools/ 目录
    agent_file = PROJECT_ROOT / "agent.py"
    tools_dir = PROJECT_ROOT / "tools"
    
    # 检查源文件是否存在
    if not agent_file.exists():
        return f"错误: agent.py 不存在 - {agent_file}"
    
    if not tools_dir.exists():
        return f"错误: tools/ 目录不存在 - {tools_dir}"
    
    if not tools_dir.is_dir():
        return f"错误: tools/ 不是目录 - {tools_dir}"
    
    try:
        # 使用 shutil 打包
        # 首先创建临时目录，将要备份的文件复制进去
        import tempfile
        import re
        
        # 创建临时工作目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 复制 agent.py 到临时目录
            agent_dest = temp_path / "agent.py"
            shutil.copy2(agent_file, agent_dest)
            logger.debug(f"已复制: {agent_file} -> {agent_dest}")
            
            # 递归复制 tools/ 目录到临时目录
            tools_dest = temp_path / "tools"
            shutil.copytree(tools_dir, tools_dest)
            logger.debug(f"已复制: {tools_dir} -> {tools_dest}")
            
            # 创建 ZIP 文件
            # 使用 shutil.make_archive 创建 zip
            # 注意：make_archive 会自动添加 .zip 后缀
            archive_base = temp_path / f"backup_{timestamp}"
            
            # 手动创建 zip 文件以获得更好的控制
            with zipfile.ZipFile(backup_path, 'w', 
                                compression=zipfile.ZIP_DEFLATED,
                                compresslevel=9) as zf:
                # 添加元数据文件
                metadata = f"""Self-Evolving Agent Backup
=========================

Backup Time: {datetime.now().isoformat()}
Timestamp: {timestamp}
Version Note: {version_note or '(none)'}

Contents:
- agent.py
- tools/ (all modules)
"""
                zf.writestr('METADATA.txt', metadata)
                
                # 添加 agent.py
                zf.write(agent_dest, arcname='agent.py')
                
                # 递归添加 tools/ 目录中的所有文件
                file_count = 1  # 包含 METADATA.txt
                for root, dirs, files in os.walk(tools_dest):
                    for file in files:
                        # 跳过 __pycache__ 和 .pyc 文件
                        if '__pycache__' in root or file.endswith('.pyc'):
                            continue
                        
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(tools_dest)
                        zf.write(file_path, arcname=f'tools/{arcname}')
                        file_count += 1
                        logger.debug(f"已添加: {file_path}")
                
                # 也需要添加 agent.py 的计数
                file_count += 1  # agent.py
        
        # 计算备份大小
        backup_size = backup_path.stat().st_size
        
        # 构建结果
        result_lines = [
            "备份创建成功",
            "-" * 40,
            f"文件: {backup_path}",
            f"大小: {format_size(backup_size)}",
            "-" * 40,
            "包含:",
            "  - agent.py",
            "  - tools/",
            f"版本说明: {version_note or '(无)'}",
            "-" * 40,
            "",
            "提示: 如需恢复，请解压备份文件到项目目录",
            f"命令: unzip -o {backup_filename}",
        ]
        
        logger.info(f"备份创建成功: {backup_path}")
        return '\n'.join(result_lines)
        
    except PermissionError:
        return f"错误: 权限不足，请检查目录权限 - {backup_dir}"
    except Exception as e:
        logger.error(f"备份创建失败: {e}", exc_info=True)
        return f"错误: 备份创建失败 - {str(e)}"


# ============================================================================
# 自我测试模块 - 验证 Agent 核心功能
# ============================================================================

def run_self_test() -> str:
    """
    运行 Agent 核心功能的自我测试。

    测试内容：
    1. 核心模块导入
    2. 配置文件可用性
    3. 工具模块可用性
    4. restarter.py 可用性
    5. 记忆系统可用性

    Returns:
        测试结果报告
    """
    results = []
    all_passed = True

    def test(name: str, condition: bool, detail: str = "") -> None:
        nonlocal all_passed
        status = "PASS" if condition else "X FAIL"
        if not condition:
            all_passed = False
        results.append(f"  [{status}] {name}")
        if detail and not condition:
            results.append(f"         {detail}")

    results.append("=" * 50)
    results.append("Agent 自我测试报告")
    results.append("=" * 50)
    results.append("")

    # 测试 1: 核心模块导入
    results.append("[1] 核心模块导入测试")
    try:
        import agent
        test("agent.py 可导入", True)
    except Exception as e:
        test("agent.py 可导入", False, str(e))

    try:
        import config
        test("config.py 可导入", True)
    except Exception as e:
        test("config.py 可导入", False, str(e))

    # 测试 2: 工具模块导入
    results.append("")
    results.append("[2] 工具模块导入测试")
    try:
        from tools import web_search, read_local_file, edit_local_file
        test("工具模块 可导入", True)
    except Exception as e:
        test("工具模块 可导入", False, str(e))

    # 测试 3: 配置文件检查
    results.append("")
    results.append("[3] 配置文件测试")
    config_path = PROJECT_ROOT / "config.toml"
    test("config.toml 存在", config_path.exists())
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            has_api_key = "api_key" in content
            test("config.toml 包含 api_key", has_api_key)
        except Exception as e:
            test("config.toml 可读", False, str(e))

    # 测试 4: restarter.py 检查
    results.append("")
    results.append("[4] 重启系统测试")
    restarter_path = PROJECT_ROOT / "restarter.py"
    test("restarter.py 存在", restarter_path.exists())
    if restarter_path.exists():
        try:
            import ast
            with open(restarter_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            test("restarter.py 语法正确", True)
        except SyntaxError as e:
            test("restarter.py 语法正确", False, f"行 {e.lineno}: {e.msg}")
        except Exception as e:
            test("restarter.py 可读", False, str(e))

    # 测试 5: 记忆系统测试
    results.append("")
    results.append("[5] 记忆系统测试")
    memory_path = PROJECT_ROOT / "memory.json"
    test("memory.json 可写/可读", memory_path.exists())
    if memory_path.exists():
        try:
            import json
            with open(memory_path, 'r', encoding='utf-8') as f:
                memory = json.load(f)
            has_generation = "generation" in memory
            test("memory.json 格式正确", has_generation)
        except Exception as e:
            test("memory.json 可读", False, str(e))

    # 测试 6: 语法自检能力
    results.append("")
    results.append("[6] 语法自检测试")
    try:
        from tools.safety_tools import check_syntax
        result = check_syntax(str(PROJECT_ROOT / "agent.py"))
        is_ok = "Syntax OK" in result
        test("agent.py 语法检查", is_ok)
    except Exception as e:
        test("语法检查工具", False, str(e))

    # 总结
    results.append("")
    results.append("=" * 50)
    if all_passed:
        results.append("所有测试通过！Agent 状态正常。")
    else:
        results.append("X 部分测试失败，请检查上述问题。")
    results.append("=" * 50)

    return "\n".join(results)


def get_agent_status() -> str:
    """
    获取 Agent 当前状态概览。

    Returns:
        状态报告
    """
    from tools.memory_tools import get_generation, get_current_goal, get_core_context
    from tools.evolution_tracker import get_evolution_stats

    lines = [
        "=" * 50,
        "Agent 状态概览",
        "=" * 50,
        "",
        f"世代: G{get_generation()}",
        f"当前目标: {get_current_goal() or '(未设置)'}",
        "",
        "核心上下文:",
        get_core_context() or '(无)',
        "",
        "进化统计:",
        get_evolution_stats(),
    ]

    return "\n".join(lines)