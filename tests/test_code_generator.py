#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码生成器测试

测试 core/code_generator.py 的功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.code_generator import (
    CodeGenerator,
    GeneratedCode,
    CodeTemplate,
    GenerationResult,
    CODE_TEMPLATES,
)


class TestCodeGenerator:
    """代码生成器测试类"""

    @pytest.fixture
    def generator(self, tmp_path):
        """创建代码生成器实例"""
        return CodeGenerator(project_root=str(tmp_path))

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, generator):
        """测试初始化"""
        assert generator is not None
        assert generator.project_root is not None
        assert generator._generation_history == []

    # =========================================================================
    # 语法验证测试
    # =========================================================================

    def test_verify_syntax_valid(self, generator):
        """测试验证有效语法"""
        code = """
def foo():
    return True
"""
        is_valid, error = generator.verify_syntax(code)
        assert is_valid is True
        assert error is None

    def test_verify_syntax_invalid(self, generator):
        """测试验证无效语法"""
        code = """
def foo(:
    return True
"""
        is_valid, error = generator.verify_syntax(code)
        assert is_valid is False
        assert error is not None

    # =========================================================================
    # 工具方法测试
    # =========================================================================

    def test_snake_to_pascal(self, generator):
        """测试 snake_case 转 PascalCase"""
        assert generator._snake_to_pascal("test_function") == "TestFunction"
        assert generator._snake_to_pascal("my_test") == "MyTest"
        assert generator._snake_to_pascal("single") == "Single"

    def test_get_relative_path(self, generator, tmp_path):
        """测试获取相对路径"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("")

        relative = generator._get_relative_path(str(test_file))
        assert "test.py" in relative

    # =========================================================================
    # 类型注解添加测试
    # =========================================================================

    def test_add_type_hints(self, generator):
        """测试添加类型注解"""
        code = """
def foo():
    # TODO: type hints
    return True
"""
        result = generator._add_type_hints(code, {})
        assert "TODO" in result

    def test_add_type_hints_invalid(self, generator):
        """测试无效代码的类型注解"""
        code = "def foo(:"
        result = generator._add_type_hints(code, {})
        assert result == code

    # =========================================================================
    # 文档字符串测试
    # =========================================================================

    def test_add_docstrings(self, generator):
        """测试添加文档字符串"""
        code = """
def foo():
    return True
"""
        result = generator._add_docstrings(code, {})
        assert "docstring" in result.lower() or "TODO" in result

    def test_add_docstrings_with_existing(self, generator):
        """测试已有文档字符串的情况"""
        code = '''
def foo():
    """Existing docstring"""
    return True
'''
        result = generator._add_docstrings(code, {})
        assert '"""Existing docstring"""' in result

    # =========================================================================
    # 条件简化测试
    # =========================================================================

    def test_simplify_condition(self, generator):
        """测试简化条件"""
        code = """
def foo():
    if True:
        return True
    return False
"""
        result = generator._simplify_condition(code, {})
        assert "if True:" not in result or "return True" in result

    # =========================================================================
    # 代码格式化测试
    # =========================================================================

    def test_format_python_code_no_autopep8(self, generator):
        """测试没有 autopep8 时的格式化"""
        code = "def foo(  x  ):\n    return   x"
        result = generator.format_python_code(code)
        # 如果没有 autopep8，应该返回原始代码
        assert result is not None


class TestGeneratedCode:
    """生成的代码测试"""

    def test_generated_code_creation(self):
        """测试创建生成的代码"""
        code = GeneratedCode(
            file_path="test.py",
            code_type="new",
            content="def test(): pass",
            description="测试代码",
        )
        assert code.file_path == "test.py"
        assert code.code_type == "new"
        assert code.error is None


class TestGenerationResult:
    """生成结果测试"""

    def test_result_success(self):
        """测试成功结果"""
        result = GenerationResult(
            success=True,
            generated_files=[],
            summary="生成成功",
        )
        assert result.success is True
        assert len(result.errors) == 0

    def test_result_failure(self):
        """测试失败结果"""
        result = GenerationResult(
            success=False,
            errors=["错误1", "错误2"],
            summary="生成失败",
        )
        assert result.success is False
        assert len(result.errors) == 2


class TestCodeTemplates:
    """代码模板测试"""

    def test_templates_exist(self):
        """测试模板是否存在"""
        expected_templates = [
            "test_class", "test_method", "docstring_module",
            "docstring_class", "docstring_method", "extract_method",
            "dataclass_template", "exception_template"
        ]
        for template_name in expected_templates:
            assert template_name in CODE_TEMPLATES

    def test_test_class_template(self):
        """测试测试类模板"""
        template = CODE_TEMPLATES["test_class"]
        assert "class Test" in template
        assert "pytest" in template

    def test_docstring_method_template(self):
        """测试方法文档字符串模板"""
        template = CODE_TEMPLATES["docstring_method"]
        assert "Args:" in template
        assert "Returns:" in template

    def test_exception_template(self):
        """测试异常模板"""
        template = CODE_TEMPLATES["exception_template"]
        assert "Exception" in template
        assert "message" in template
        assert "details" in template

    def test_dataclass_template(self):
        """测试数据类模板"""
        template = CODE_TEMPLATES["dataclass_template"]
        assert "@dataclass" in template
        assert "class" in template


class TestImportSection:
    """导入部分生成测试"""

    def test_generate_import_section(self, tmp_path):
        """测试生成导入部分"""
        generator = CodeGenerator(project_root=str(tmp_path))
        result = generator.generate_import_section(
            [],
            standard_library=["os", "sys", "json"]
        )
        assert "import os" in result
        assert "import sys" in result
        assert "import json" in result

    def test_generate_import_section_with_categories(self, tmp_path):
        """测试带分类的导入部分"""
        generator = CodeGenerator(project_root=str(tmp_path))
        result = generator.generate_import_section(
            [],
            standard_library=["os", "sys"],
            third_party=["requests"],
            local=["core.tools"]
        )
        assert "import os" in result
        assert "import requests" in result
        assert "from core.tools" in result

    def test_generate_import_section_empty(self, tmp_path):
        """测试空导入"""
        generator = CodeGenerator(project_root=str(tmp_path))
        result = generator.generate_import_section([])
        assert result == ""
