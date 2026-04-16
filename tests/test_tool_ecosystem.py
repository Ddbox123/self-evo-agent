#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.4 单元测试 - 工具生态系统模块

测试模块：
- core/tool_ecosystem.py
"""

import pytest
import sys
import os
from pathlib import Path

# Fix path
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)

from core.tool_ecosystem import (
    DynamicLoader, CompositeToolManager, PluginManager, ToolEcosystem,
    ToolDefinition, CompositeToolSpec, ToolStep, PluginInfo, ExecutionRecord,
    ToolType,
    get_tool_ecosystem, reset_tool_ecosystem,
)


class TestToolDefinition:
    def test_create_definition(self):
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool",
            tool_type=ToolType.BASIC,
            category="testing",
        )
        assert tool.name == "test_tool"
        assert tool.tool_type == ToolType.BASIC


class TestCompositeToolSpec:
    def test_create_spec(self):
        steps = [
            ToolStep(tool_name="read_file", parameters={"path": "/test.py"}),
            ToolStep(tool_name="analyze", parameters={"content": "$read_file"}),
        ]
        spec = CompositeToolSpec(
            name="test_composite",
            description="Test composite",
            steps=steps,
        )
        assert spec.name == "test_composite"
        assert len(spec.steps) == 2

    def test_tool_step_defaults(self):
        step = ToolStep(tool_name="test_tool")
        assert step.retry_on_failure is False
        assert step.max_retries == 3


class TestPluginInfo:
    def test_create_plugin_info(self):
        plugin = PluginInfo(
            plugin_id="test_plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test",
            entry_point="main",
        )
        assert plugin.plugin_id == "test_plugin"
        assert plugin.enabled is True


class TestExecutionRecord:
    def test_create_record(self):
        record = ExecutionRecord(
            tool_name="test_tool",
            success=True,
            duration_seconds=1.5,
            output={"result": "ok"},
        )
        assert record.success is True
        assert record.duration_seconds == 1.5


class TestDynamicLoader:
    def test_init(self):
        loader = DynamicLoader(".")
        assert loader.project_root is not None

    def test_register_tool(self):
        loader = DynamicLoader(".")
        tool = ToolDefinition(
            name="registered_tool",
            description="Registered tool",
            tool_type=ToolType.DYNAMIC,
        )
        loader.register_tool(tool)
        retrieved = loader.get_tool("registered_tool")
        assert retrieved is not None
        assert retrieved.name == "registered_tool"

    def test_unregister_tool(self):
        loader = DynamicLoader(".")
        tool = ToolDefinition(
            name="to_unregister",
            description="Tool to unregister",
            tool_type=ToolType.DYNAMIC,
        )
        loader.register_tool(tool)
        assert loader.unregister_tool("to_unregister") is True
        assert loader.get_tool("to_unregister") is None

    def test_list_tools(self):
        loader = DynamicLoader(".")
        for i in range(5):
            tool = ToolDefinition(
                name="tool_" + str(i),
                description="Tool " + str(i),
                tool_type=ToolType.BASIC,
                category="test_category" if i % 2 == 0 else "other",
            )
            loader.register_tool(tool)

        all_tools = loader.list_tools()
        assert len(all_tools) == 5

        basic_tools = loader.list_tools(tool_type=ToolType.BASIC)
        assert len(basic_tools) == 5

        test_tools = loader.list_tools(category="test_category")
        assert len(test_tools) == 3

    def test_discover_tools(self):
        loader = DynamicLoader(".")
        count = loader.discover_tools()
        assert count >= 0


class TestCompositeToolManager:
    def test_init(self):
        manager = CompositeToolManager()
        assert manager._composite_tools is not None

    def test_register_composite(self):
        manager = CompositeToolManager()
        spec = CompositeToolSpec(
            name="my_composite",
            description="My composite",
            steps=[],
        )
        manager.register_composite(spec)
        retrieved = manager.get_composite("my_composite")
        assert retrieved is not None
        assert retrieved.name == "my_composite"

    def test_list_composites(self):
        manager = CompositeToolManager()
        for i in range(3):
            spec = CompositeToolSpec(
                name="composite_" + str(i),
                description="Composite " + str(i),
                steps=[],
            )
            manager.register_composite(spec)

        composites = manager.list_composites()
        assert len(composites) == 3


class TestPluginManager:
    def test_init(self):
        manager = PluginManager()
        assert manager.plugin_dir is not None

    def test_discover_plugins_no_dir(self):
        manager = PluginManager("/tmp/nonexistent_plugins_12345")
        plugins = manager.discover_plugins()
        assert isinstance(plugins, list)

    def test_load_plugin_not_found(self):
        manager = PluginManager()
        assert manager.load_plugin("nonexistent_plugin_xyz") is False

    def test_unload_plugin_not_loaded(self):
        manager = PluginManager()
        assert manager.unload_plugin("nonexistent_plugin_xyz") is False

    def test_list_plugins_empty(self):
        manager = PluginManager()
        plugins = manager.list_plugins()
        assert len(plugins) == 0

    def test_get_plugin_not_found(self):
        manager = PluginManager()
        plugin = manager.get_plugin("nonexistent")
        assert plugin is None


class TestToolEcosystem:
    def test_init(self):
        ecosystem = ToolEcosystem(".")
        assert ecosystem.dynamic_loader is not None
        assert ecosystem.composite_manager is not None
        assert ecosystem.plugin_manager is not None

    def test_initialize(self):
        ecosystem = ToolEcosystem(".")
        stats = ecosystem.initialize()
        assert "tools_discovered" in stats
        assert "composites_registered" in stats
        assert "plugins_discovered" in stats

    def test_get_statistics(self):
        ecosystem = ToolEcosystem(".")
        stats = ecosystem.get_statistics()
        assert "total_tools" in stats
        assert "composite_tools" in stats
        assert "plugins" in stats


class TestToolEcosystemIntegration:
    def test_singleton_behavior(self):
        ecosystem1 = get_tool_ecosystem(".")
        ecosystem2 = get_tool_ecosystem(".")
        assert ecosystem1 is ecosystem2
        reset_tool_ecosystem()
        ecosystem3 = get_tool_ecosystem(".")
        assert ecosystem3 is not ecosystem1

    def test_full_initialization(self):
        reset_tool_ecosystem()
        ecosystem = get_tool_ecosystem(".")
        stats = ecosystem.initialize()
        assert stats["tools_discovered"] >= 0
        assert stats["composites_registered"] >= 1

    def test_register_and_execute(self):
        ecosystem = ToolEcosystem(".")
        tool = ToolDefinition(
            name="custom_tool",
            description="Custom tool",
            tool_type=ToolType.BASIC,
        )
        ecosystem.dynamic_loader.register_tool(tool)
        retrieved = ecosystem.dynamic_loader.get_tool("custom_tool")
        assert retrieved is not None


@pytest.fixture(autouse=True)
def cleanup():
    yield
    reset_tool_ecosystem()
