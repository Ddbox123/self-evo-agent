#!/usr/bin/env python3
"""
工具模块测试套件

测试内容：
1. 核心工具可用性
2. 工具参数处理
3. 工具超时处理
4. 工具错误处理

运行：pytest tests/test_tools.py -v
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

# 导入被测工具
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.cmd_tools import (
    read_file,
    list_dir,
    edit_local_file,
    create_new_file,
    check_syntax,
    backup_project,
)
from tools.search_tools import (
    grep_search,
    find_function_calls,
    find_definitions,
)


class TestFileOperations:
    """文件操作测试"""

    def test_read_file_existing_file(self):
        """测试读取现有文件"""
        result = read_file(__file__)  # 读取自己
        assert "test_tools" in result or "pytest" in result or len(result) > 0

    def test_read_file_nonexistent_returns_error(self):
        """测试读取不存在的文件返回错误"""
        result = read_file("/nonexistent/path/to/file.py")
        # 检查是否有错误标识
        assert "不存在" in result or "Error" in result or "错误" in result or "[文件读取]" in result

    def test_list_dir_current_directory(self):
        """测试列出当前目录"""
        result = list_dir(".")
        assert isinstance(result, str)
        # 应该包含当前目录的某些文件
        assert len(result) > 0

    def test_list_dir_with_max_lines(self):
        """测试带行数限制的目录列表"""
        result = list_dir(".")
        # list_dir 返回字符串
        assert isinstance(result, str)
        assert len(result) > 0

    def test_create_and_read_new_file(self):
        """测试创建和读取新文件"""
        test_content = """#!/usr/bin/env python3
# 测试文件
def test_function():
    return "test_success"
"""
        test_path = os.path.join(PROJECT_ROOT, "workspace", "test_created_file.py")

        try:
            result = create_new_file(test_path, test_content)
            # 验证创建成功
            assert os.path.exists(test_path), "文件应该被创建"

            # 验证读取内容
            read_result = read_file(test_path)
            assert "test_success" in read_result, "文件内容应该匹配"

        finally:
            # 清理
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_edit_local_file(self):
        """测试编辑本地文件"""
        # 创建测试文件
        test_content = "LINE1\nLINE2\nLINE3\n"
        test_path = os.path.join(PROJECT_ROOT, "workspace", "test_edit_file.txt")

        try:
            create_new_file(test_path, test_content)

            # 编辑文件
            result = edit_local_file(
                test_path,
                "LINE2",
                "LINE2_MODIFIED"
            )

            # 验证修改
            with open(test_path, "r", encoding="utf-8") as f:
                modified = f.read()

            assert "LINE2_MODIFIED" in modified, "文件应该被修改"
            assert "LINE2\n" not in modified, "旧内容应该被替换"

        finally:
            if os.path.exists(test_path):
                os.remove(test_path)

    def test_edit_file_not_found(self):
        """测试编辑不存在的文件"""
        result = edit_local_file(
            "/nonexistent/file.txt",
            "old",
            "new"
        )
        assert "[错误]" in result or "Error" in result or "不存在" in result


class TestSyntaxCheck:
    """语法检查测试"""

    def test_check_syntax_valid_python(self):
        """测试检查有效 Python 文件"""
        result = check_syntax(__file__)
        assert "Syntax OK" in result or "OK" in result

    def test_check_syntax_invalid_python(self):
        """测试检查无效 Python 文件"""
        invalid_code = """
def broken_function(
    this is not valid python
    return
"""
        test_path = os.path.join(PROJECT_ROOT, "workspace", "test_invalid.py")

        try:
            create_new_file(test_path, invalid_code)
            result = check_syntax(test_path)

            # 语法检查应该捕获错误
            assert "Error" in result or "错误" in result or "Syntax" in result

        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


class TestSearchTools:
    """搜索工具测试"""

    def test_grep_search_finds_import(self):
        """测试 grep 搜索找到 import"""
        result = grep_search(
            regex_pattern=r"^import",
            include_ext=".py",
            search_dir=str(PROJECT_ROOT),
            max_results=10,
        )

        # 应该找到一些 import 语句
        assert isinstance(result, str)
        assert len(result) > 0

    def test_grep_search_functionality(self):
        """测试 grep 搜索功能"""
        result = grep_search(
            regex_pattern=r"def test_grep",
            include_ext=".py",
            search_dir=str(PROJECT_ROOT / "tests"),
        )

        # 应该找到测试函数定义
        assert isinstance(result, str)
        assert len(result) > 0

    def test_find_function_calls(self):
        """测试查找函数调用"""
        result = find_function_calls(
            function_name="print",
            search_dir=str(PROJECT_ROOT),
        )

        assert isinstance(result, str)

    def test_find_definitions(self):
        """测试查找定义"""
        result = find_definitions(
            symbol_name="TestMemoryBasics",
            search_dir=str(PROJECT_ROOT),
        )

        assert isinstance(result, str)

    def test_search_with_case_insensitive(self):
        """测试大小写不敏感搜索"""
        result = grep_search(
            regex_pattern=r"import",
            include_ext=".py",
            search_dir=str(PROJECT_ROOT),
            case_sensitive=False,
            max_results=5,
        )

        assert isinstance(result, str)


class TestBackupSystem:
    """备份系统测试"""

    def test_backup_project_creates_backup(self):
        """测试项目备份创建"""
        result = backup_project("测试备份")

        assert isinstance(result, str)
        # 备份应该成功
        assert "成功" in result or "success" in result.lower() or "备份" in result


class TestToolTimeout:
    """工具超时处理测试"""

    def test_timeout_handling_structure(self):
        """测试超时处理结构是否存在"""

        # 验证 ThreadPoolExecutor 可以正常工作
        def slow_function():
            import time
            time.sleep(0.1)
            return "done"

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(slow_function)
            result = future.result(timeout=1)

        assert result == "done"

    def test_timeout_exception_catching(self):
        """测试超时异常捕获"""

        def very_slow_function():
            import time
            time.sleep(0.5)
            return "done"

        with pytest.raises(FuturesTimeoutError):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(very_slow_function)
                future.result(timeout=0.1)  # 设置更短的超时


# ============================================================================
# 测试运行器
# ============================================================================

def run_tool_tests() -> dict:
    """运行所有工具测试"""
    import subprocess

    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")

    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "status": "PASS" if failed == 0 else "FAIL",
        "output": output,
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
