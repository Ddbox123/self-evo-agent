#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Registry 测试
"""

import pytest
from datetime import datetime


class TestToolMetadata:
    """测试工具元数据"""

    def test_create_metadata(self):
        """测试创建元数据"""
        from core.tool_registry import ToolMetadata
        metadata = ToolMetadata(
            name="test_tool",
            description="A test tool",
        )
        assert metadata.name == "test_tool"
        assert metadata.description == "A test tool"
        assert metadata.usage_count == 0

    def test_metadata_defaults(self):
        """测试默认元数据"""
        from core.tool_registry import ToolMetadata
        metadata = ToolMetadata(name="test")
        assert metadata.category.value == "custom"


class TestToolRegistration:
    """测试工具注册"""

    def test_create_registration(self):
        """测试创建注册"""
        from core.tool_registry import ToolMetadata, ToolRegistration
        metadata = ToolMetadata(name="test")
        registration = ToolRegistration(
            name="test",
            func=lambda: None,
            metadata=metadata,
        )
        assert registration.name == "test"
        assert registration.enabled is True


class TestToolCategory:
    """测试工具类别"""

    def test_categories(self):
        """测试所有类别"""
        from core.tool_registry import ToolCategory
        categories = list(ToolCategory)
        assert len(categories) > 0
        assert ToolCategory.SHELL in categories
        assert ToolCategory.MEMORY in categories


class TestToolRegistry:
    """测试工具注册表"""

    def test_init(self):
        """测试初始化"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        assert isinstance(registry._tools, dict)

    def test_register(self):
        """测试注册工具"""
        from core.tool_registry import ToolRegistry, ToolMetadata
        registry = ToolRegistry()

        def test_func():
            return "test"

        result = registry.register(
            name="test_tool",
            func=test_func,
            metadata=ToolMetadata(name="test_tool", description="Test"),
        )
        assert result is True
        assert registry.is_registered("test_tool")

    def test_unregister(self):
        """测试注销工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register("test_tool", lambda: None)

        result = registry.unregister("test_tool")
        assert result is True
        assert not registry.is_registered("test_tool")

    def test_unregister_nonexistent(self):
        """测试注销不存在的工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result = registry.unregister("nonexistent")
        assert result is False

    def test_get_tool(self):
        """测试获取工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register("test_tool", lambda: None)

        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"

    def test_get_nonexistent_tool(self):
        """测试获取不存在的工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_list_tools(self):
        """测试列出工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register("tool1", lambda: None)
        registry.register("tool2", lambda: None)

        tools = registry.list_tools()
        assert "tool1" in tools
        assert "tool2" in tools

    def test_search(self):
        """测试搜索工具"""
        from core.tool_registry import ToolRegistry, ToolMetadata
        registry = ToolRegistry()
        registry.register(
            "web_search",
            lambda: None,
            metadata=ToolMetadata(name="web_search", description="Search the web"),
        )
        registry.register(
            "file_reader",
            lambda: None,
            metadata=ToolMetadata(name="file_reader", description="Read files"),
        )

        results = registry.search("search")
        assert "web_search" in results

    def test_enable_disable(self):
        """测试启用禁用工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register("test_tool", lambda: None)

        registry.disable("test_tool")
        assert registry.get_tool("test_tool").enabled is False

        registry.enable("test_tool")
        assert registry.get_tool("test_tool").enabled is True

    def test_get_statistics(self):
        """测试获取统计"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        registry.register("test_tool", lambda: None)

        stats = registry.get_statistics()
        assert "total_tools" in stats
        assert stats["total_tools"] >= 1

    def test_get_tool_info(self):
        """测试获取工具信息"""
        from core.tool_registry import ToolRegistry, ToolMetadata
        registry = ToolRegistry()
        registry.register(
            "test_tool",
            lambda: None,
            metadata=ToolMetadata(name="test_tool", description="Test tool"),
        )

        info = registry.get_tool_info("test_tool")
        assert info is not None
        assert info["name"] == "test_tool"
        assert info["description"] == "Test tool"

    def test_get_tool_info_nonexistent(self):
        """测试获取不存在工具的信息"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        info = registry.get_tool_info("nonexistent")
        assert info is None


class TestToolRegistryExecute:
    """测试工具执行"""

    def test_execute_success(self):
        """测试成功执行"""
        from core.tool_registry import ToolRegistry, ToolMetadata
        registry = ToolRegistry()

        def test_func(a, b):
            return a + b

        registry.register(
            "add",
            test_func,
            metadata=ToolMetadata(name="add", description="Add two numbers"),
        )

        result, action = registry.execute("add", {"a": 1, "b": 2})
        assert result == 3

    def test_execute_nonexistent(self):
        """测试执行不存在的工具"""
        from core.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result, action = registry.execute("nonexistent", {})
        assert "未注册" in result

    def test_execute_disabled(self):
        """测试执行禁用的工具"""
        from core.tool_registry import ToolRegistry, ToolMetadata
        registry = ToolRegistry()
        registry.register(
            "disabled_tool",
            lambda: "test",
            metadata=ToolMetadata(name="disabled_tool", description=""),
        )
        registry.disable("disabled_tool")

        result, action = registry.execute("disabled_tool", {})
        assert "已禁用" in result


class TestToolRegistryIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        from core.tool_registry import ToolRegistry, ToolMetadata, ToolCategory

        registry = ToolRegistry()

        # 注册工具
        registry.register(
            "calculator",
            lambda a, b: a + b,
            metadata=ToolMetadata(
                name="calculator",
                description="A calculator",
                category=ToolCategory.SHELL,
            ),
        )

        # 检查注册
        assert registry.is_registered("calculator")

        # 获取信息
        info = registry.get_tool_info("calculator")
        assert info["name"] == "calculator"
        assert info["category"] == "shell"

        # 执行
        result, _ = registry.execute("calculator", {"a": 5, "b": 3})
        assert result == 8

        # 获取统计
        stats = registry.get_statistics()
        assert stats["total_tools"] >= 1

        # 搜索
        results = registry.search("calc")
        assert "calculator" in results

        # 禁用
        registry.disable("calculator")
        result, _ = registry.execute("calculator", {"a": 1, "b": 2})
        assert "已禁用" in result

        # 启用
        registry.enable("calculator")
        result, _ = registry.execute("calculator", {"a": 1, "b": 2})
        assert result == 3

        # 注销
        registry.unregister("calculator")
        assert not registry.is_registered("calculator")
