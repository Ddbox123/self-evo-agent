#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码库分析器测试

测试 core/codebase_analyzer.py 的功能
"""

import pytest
import sys
import os
import ast

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.codebase_analyzer import (
    CodebaseAnalyzer,
    FileEntity,
    ModuleInfo,
    CodeHotspot,
    CodebaseMap,
)


class TestCodebaseAnalyzer:
    """代码库分析器测试类"""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """创建分析器实例"""
        return CodebaseAnalyzer(project_root=str(tmp_path))

    @pytest.fixture
    def project_analyzer(self):
        """创建使用实际项目的分析器"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return CodebaseAnalyzer(project_root=project_root)

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, analyzer):
        """测试初始化"""
        assert analyzer is not None
        assert analyzer.project_root is not None

    def test_init_module_purposes(self, analyzer):
        """测试模块用途初始化"""
        assert len(analyzer._module_purposes) > 0
        assert "agent.py" in analyzer._module_purposes

    # =========================================================================
    # 文件类型识别测试
    # =========================================================================

    def test_get_file_type(self, analyzer, tmp_path):
        """测试文件类型识别"""
        assert analyzer._get_file_type(tmp_path / "test.py") == "python"
        assert analyzer._get_file_type(tmp_path / "test.md") == "markdown"
        assert analyzer._get_file_type(tmp_path / "test.json") == "json"
        assert analyzer._get_file_type(tmp_path / "test.yaml") == "config"
        assert analyzer._get_file_type(tmp_path / "test.txt") == "other"

    # =========================================================================
    # 复杂度计算测试
    # =========================================================================

    def test_calculate_complexity_simple(self, analyzer):
        """测试简单代码复杂度"""
        code = """
def foo():
    return 1
"""
        tree = ast.parse(code)
        complexity = analyzer._calculate_complexity(tree)
        assert complexity == 1

    def test_calculate_complexity_with_if(self, analyzer):
        """测试带 if 的复杂度"""
        code = """
def foo():
    if a:
        return 1
    else:
        return 2
"""
        tree = ast.parse(code)
        complexity = analyzer._calculate_complexity(tree)
        assert complexity >= 2

    def test_calculate_complexity_with_loops(self, analyzer):
        """测试带循环的复杂度"""
        code = """
def foo():
    for i in range(10):
        if i > 5:
            return i
    return 0
"""
        tree = ast.parse(code)
        complexity = analyzer._calculate_complexity(tree)
        assert complexity >= 2

    def test_calculate_complexity_with_exception(self, analyzer):
        """测试带异常处理的复杂度"""
        code = """
def foo():
    try:
        x = 1
    except:
        pass
"""
        tree = ast.parse(code)
        complexity = analyzer._calculate_complexity(tree)
        assert complexity >= 1

    def test_calculate_complexity_invalid(self, analyzer):
        """测试无效代码"""
        complexity = analyzer._calculate_complexity(None)
        assert complexity == 0

    # =========================================================================
    # 导入提取测试
    # =========================================================================

    def test_extract_imports(self, analyzer):
        """测试导入提取"""
        code = """
import os
import sys
from pathlib import Path
from typing import List, Dict
"""
        tree = ast.parse(code)
        imports = analyzer._extract_imports(tree)

        assert "os" in imports
        assert "sys" in imports
        assert "pathlib" in imports
        assert "typing" in imports

    def test_extract_imports_from(self, analyzer):
        """测试 from 导入"""
        code = """
from core.event_bus import EventBus, Event
from tools import Key_Tools
"""
        tree = ast.parse(code)
        imports = analyzer._extract_imports(tree)

        assert "core.event_bus" in imports
        assert "tools" in imports

    def test_extract_imports_empty(self, analyzer):
        """测试无导入"""
        code = """
def foo():
    return 1
"""
        tree = ast.parse(code)
        imports = analyzer._extract_imports(tree)
        assert len(imports) == 0

    # =========================================================================
    # 文件分析测试
    # =========================================================================

    def test_analyze_file_python(self, analyzer, tmp_path):
        """测试分析 Python 文件"""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def test_func():
    return True

class TestClass:
    def method(self):
        pass
""", encoding='utf-8')

        entity = analyzer._analyze_file(test_file)

        assert entity is not None
        assert entity.name == "test_module.py"
        assert entity.file_type == "python"
        assert entity.lines > 0
        assert entity.functions >= 1
        assert entity.classes >= 1

    def test_analyze_file_with_complexity(self, analyzer, tmp_path):
        """测试分析带复杂度的文件"""
        test_file = tmp_path / "complex.py"
        test_file.write_text("""
def foo():
    if a:
        if b:
            if c:
                return 1
    return 0
""", encoding='utf-8')

        entity = analyzer._analyze_file(test_file)
        assert entity.complexity >= 2

    # =========================================================================
    # 热点识别测试
    # =========================================================================

    def test_identify_hotspots(self, analyzer, tmp_path):
        """测试热点识别"""
        # 创建测试文件
        for i in range(3):
            f = tmp_path / f"test_{i}.py"
            f.write_text(f"""
def foo():
    for i in range(100):
        if i > 50:
            while True:
                break
        elif i < 20:
            pass
""")

        analyzer._file_entities = {}
        for f in tmp_path.glob("*.py"):
            try:
                entity = analyzer._analyze_file(f)
                analyzer._file_entities[str(f)] = entity
            except Exception:
                pass

        analyzer._identify_hotspots()

        assert len(analyzer._hotspots) > 0

    # =========================================================================
    # 健康度评估测试
    # =========================================================================

    def test_get_code_health(self, analyzer, tmp_path):
        """测试代码健康度评估"""
        test_file = tmp_path / "healthy.py"
        test_file.write_text("""
def simple_func():
    return True
""", encoding='utf-8')

        entity = analyzer._analyze_file(test_file)
        analyzer._file_entities[str(test_file)] = entity

        health = analyzer.get_code_health(str(test_file))

        assert "health_score" in health
        assert "issues" in health
        assert "metrics" in health
        assert 0.0 <= health["health_score"] <= 1.0

    def test_get_code_health_nonexistent(self, analyzer):
        """测试不存在文件的健康度"""
        health = analyzer.get_code_health("/nonexistent/file.py")
        assert "error" in health

    # =========================================================================
    # 模块分析测试
    # =========================================================================

    def test_infer_module_purpose(self, analyzer):
        """测试推断模块用途"""
        entities = [FileEntity(path="test.py", name="test.py", file_type="python",
                              lines=100, complexity=5, functions=5, classes=1)]

        # test 不含 tools，返回"功能模块"
        purpose = analyzer._infer_module_purpose("mod", entities)
        assert purpose == "功能模块", f"Expected '功能模块' for 'mod', got {purpose}"

        purpose = analyzer._infer_module_purpose("my_core", entities)
        assert purpose == "核心功能模块", f"Expected '核心功能模块' for 'my_core', got {purpose}"

        purpose = analyzer._infer_module_purpose("my_tools", entities)
        assert purpose == "工具模块", f"Expected '工具模块' for 'my_tools', got {purpose}"

        purpose = analyzer._infer_module_purpose("my_tests", entities)
        assert purpose == "测试模块", f"Expected '测试模块' for 'my_tests', got {purpose}"

    # =========================================================================
    # 依赖图测试
    # =========================================================================

    def test_build_import_graph(self, analyzer, tmp_path):
        """测试构建导入图"""
        # 创建测试文件
        test_file = tmp_path / "main.py"
        test_file.write_text("""
from tools.shell_tools import read_file
from core.event_bus import EventBus
import os
""", encoding='utf-8')

        entity = analyzer._analyze_file(test_file)
        analyzer._file_entities[str(test_file)] = entity
        analyzer._build_import_graph()

        # 验证导入图有内容
        assert len(analyzer._import_graph) > 0

    # =========================================================================
    # 扫描测试
    # =========================================================================

    def test_scan_project(self, analyzer, tmp_path):
        """测试项目扫描"""
        # 创建测试文件
        (tmp_path / "test1.py").write_text("def foo(): pass")
        (tmp_path / "test2.py").write_text("def bar(): pass")

        result = analyzer.scan_project()

        assert "total_files" in result
        assert "files" in result
        assert result["total_files"] >= 2

    def test_scan_project_with_patterns(self, analyzer, tmp_path):
        """测试带模式的扫描"""
        # 创建测试文件
        (tmp_path / "test.py").write_text("def foo(): pass")
        (tmp_path / "test.md").write_text("# Test")

        # 只扫描 Python 文件
        result = analyzer.scan_project(include_patterns=["*.py"])

        assert result["total_files"] == 1

    def test_scan_project_exclude_patterns(self, analyzer, tmp_path):
        """测试排除模式"""
        # 创建测试文件
        (tmp_path / "test.py").write_text("def foo(): pass")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "test.pyc").write_text("")

        result = analyzer.scan_project()

        # __pycache__ 应该被排除
        file_paths = [f["path"] for f in result["files"]]
        assert not any("__pycache__" in p for p in file_paths)

    # =========================================================================
    # 代码库地图测试
    # =========================================================================

    def test_generate_codebase_map(self, analyzer, tmp_path):
        """测试生成代码库地图"""
        # 创建测试文件
        (tmp_path / "main.py").write_text("""
import os
def main():
    pass
""")

        codebase_map = analyzer.generate_codebase_map()

        assert isinstance(codebase_map, CodebaseMap)
        assert codebase_map.project_name is not None
        assert isinstance(codebase_map.generated_at, str)
        assert codebase_map.total_files >= 1
        assert codebase_map.total_lines > 0

    def test_generate_codebase_map_full(self, project_analyzer):
        """测试完整代码库地图生成"""
        codebase_map = project_analyzer.generate_codebase_map()

        assert codebase_map.total_files > 0
        assert codebase_map.total_lines > 0
        assert isinstance(codebase_map.modules, list)
        assert isinstance(codebase_map.metrics, dict)

    # =========================================================================
    # Markdown 输出测试
    # =========================================================================

    def test_format_as_markdown(self, analyzer, tmp_path):
        """测试 Markdown 格式化"""
        (tmp_path / "test.py").write_text("def foo(): pass")
        codebase_map = analyzer.generate_codebase_map()

        markdown = analyzer.format_as_markdown(codebase_map)

        assert "# 代码库认知地图" in markdown
        assert "项目概览" in markdown
        assert "模块结构" in markdown

    def test_format_as_markdown_without_map(self, analyzer):
        """测试无地图的 Markdown 格式化"""
        markdown = analyzer.format_as_markdown()

        assert "# 代码库认知地图" in markdown

    # =========================================================================
    # 工具方法测试
    # =========================================================================

    def test_entity_to_dict(self, analyzer):
        """测试实体转字典"""
        entity = FileEntity(
            path="test.py",
            name="test.py",
            file_type="python",
            lines=100,
            complexity=5,
            functions=5,
            classes=1,
            imports=["os", "sys"],
        )

        data = analyzer._entity_to_dict(entity)

        assert data["path"] == "test.py"
        assert data["name"] == "test.py"
        assert data["file_type"] == "python"
        assert data["lines"] == 100

    def test_hotspot_to_dict(self, analyzer):
        """测试热点转字典"""
        hotspot = CodeHotspot(
            file_path="test.py",
            reason="高复杂度",
            metrics={"complexity": 20},
            suggestions=["拆分函数"],
        )

        data = analyzer._hotspot_to_dict(hotspot)

        assert data["file"] == "test.py"
        assert data["reason"] == "高复杂度"
        assert "拆分函数" in data["suggestions"]

    # =========================================================================
    # 依赖查询测试
    # =========================================================================

    def test_get_module_dependencies(self, analyzer):
        """测试获取模块依赖"""
        analyzer._import_graph = {
            "main.py": {"tools", "core"},
            "tools": set(),
        }

        deps = analyzer.get_module_dependencies("main.py")
        assert "tools" in deps or "core" in deps

    def test_get_module_dependencies_none(self, analyzer):
        """测试无依赖"""
        deps = analyzer.get_module_dependencies("nonexistent.py")
        assert deps == []


class TestCodebaseMapStructure:
    """代码库地图结构测试"""

    def test_file_entity_structure(self):
        """测试文件实体结构"""
        entity = FileEntity(
            path="test.py",
            name="test.py",
            file_type="python",
            lines=100,
            complexity=5,
            functions=5,
            classes=1,
        )

        assert entity.path == "test.py"
        assert entity.lines == 100
        assert entity.complexity == 5

    def test_module_info_structure(self):
        """测试模块信息结构"""
        module = ModuleInfo(
            name="tools",
            path="tools",
            purpose="工具模块",
            dependencies=["core"],
            dependents=["agent.py"],
            complexity=10,
            health_score=0.8,
        )

        assert module.name == "tools"
        assert module.purpose == "工具模块"
        assert "core" in module.dependencies

    def test_code_hotspot_structure(self):
        """测试代码热点结构"""
        hotspot = CodeHotspot(
            file_path="agent.py",
            reason="文件过大",
            metrics={"lines": 800},
            suggestions=["拆分模块"],
        )

        assert hotspot.file_path == "agent.py"
        assert hotspot.reason == "文件过大"
        assert hotspot.metrics["lines"] == 800
