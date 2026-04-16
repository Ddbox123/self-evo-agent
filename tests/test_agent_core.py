#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 核心测试

测试 core/agent_core.py 的功能
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_core import (
    AgentCore,
    AgentConfig,
    AgentMetrics,
    TaskContext,
    LLMProvider,
    ToolRegistry,
    MemoryManager,
    get_agent_core,
    reset_agent_core,
)


class TestAgentConfig:
    """Agent 配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AgentConfig()
        assert config.name == "虾宝"
        assert config.workspace == "workspace"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7

    def test_custom_config(self):
        """测试自定义配置"""
        config = AgentConfig(
            name="TestAgent",
            model_name="gpt-3.5",
            temperature=0.5,
        )
        assert config.name == "TestAgent"
        assert config.model_name == "gpt-3.5"
        assert config.temperature == 0.5


class TestAgentMetrics:
    """Agent 指标测试"""

    def test_default_metrics(self):
        """测试默认指标"""
        metrics = AgentMetrics()
        assert metrics.tasks_completed == 0
        assert metrics.tasks_failed == 0
        assert metrics.total_tokens_used == 0
        assert metrics.llm_calls == 0
        assert metrics.tool_calls == 0


class TestTaskContext:
    """任务上下文测试"""

    def test_task_creation(self):
        """测试创建任务"""
        task = TaskContext(
            task_id="test_1",
            description="测试任务",
        )
        assert task.task_id == "test_1"
        assert task.description == "测试任务"
        assert task.status == "pending"
        assert task.result is None
        assert task.error is None

    def test_task_with_metadata(self):
        """测试带元数据的任务"""
        task = TaskContext(
            task_id="test_2",
            description="测试任务",
            metadata={"key": "value"},
        )
        assert task.metadata["key"] == "value"


class TestLLMProvider:
    """LLM 提供者测试"""

    def test_init(self, tmp_path):
        """测试初始化"""
        config = AgentConfig()
        provider = LLMProvider(config)
        assert provider.config == config
        assert provider.get_model_name() == "gpt-4"


class TestToolRegistry:
    """工具注册表测试"""

    def test_init(self):
        """测试初始化"""
        registry = ToolRegistry()
        assert len(registry.list_tools()) == 0

    def test_register(self):
        """测试注册工具"""
        registry = ToolRegistry()
        registry.register("test_tool", {"name": "test"})
        assert "test_tool" in registry.list_tools()
        assert registry.get("test_tool") is not None

    def test_unregister(self):
        """测试注销工具"""
        registry = ToolRegistry()
        registry.register("test_tool", {"name": "test"})
        registry.unregister("test_tool")
        assert "test_tool" not in registry.list_tools()

    def test_get_nonexistent(self):
        """测试获取不存在的工具"""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_get_by_category(self):
        """测试按类别获取"""
        registry = ToolRegistry()
        registry.register("shell_read", {"type": "shell"})
        registry.register("memory_read", {"type": "memory"})
        registry.register("shell_write", {"type": "shell"})

        shell_tools = registry.get_by_category("shell")
        assert len(shell_tools) >= 2


class TestMemoryManager:
    """记忆管理器测试"""

    def test_init(self):
        """测试初始化"""
        manager = MemoryManager()
        assert len(manager._memory) == 0
        assert len(manager._history) == 0

    def test_store_and_retrieve(self):
        """测试存储和检索"""
        manager = MemoryManager()
        manager.store("key1", "value1")
        assert manager.retrieve("key1") == "value1"

    def test_retrieve_default(self):
        """测试检索默认值"""
        manager = MemoryManager()
        assert manager.retrieve("nonexistent", "default") == "default"

    def test_forget(self):
        """测试遗忘"""
        manager = MemoryManager()
        manager.store("key1", "value1")
        manager.forget("key1")
        assert manager.retrieve("key1") is None

    def test_get_history(self):
        """测试获取历史"""
        manager = MemoryManager()
        manager.store("key1", "value1")
        manager.store("key2", "value2")
        history = manager.get_history()
        assert len(history) == 2


class TestAgentCore:
    """Agent 核心测试"""

    def test_init(self, tmp_path):
        """测试初始化"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)
        assert core.config == config
        assert core._metrics.tasks_completed == 0
        assert core._running is False

    def test_get_status(self, tmp_path):
        """测试获取状态"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)
        status = core.get_status()
        assert status["name"] == "虾宝"
        assert status["running"] is False
        assert "metrics" in status

    def test_pause_not_running(self, tmp_path):
        """测试暂停（未运行时）"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)
        # Agent 未运行时不返回 True
        result = core.pause()
        # pause 只在 _running=True 时返回 True
        assert result is False

    def test_reset_metrics(self, tmp_path):
        """测试重置指标"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)
        core._metrics.tasks_completed = 10
        core.reset_metrics()
        assert core._metrics.tasks_completed == 0

    def test_event_handlers(self, tmp_path):
        """测试事件处理器"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)

        events = []

        def handler(data):
            events.append(data)

        core.on("test_event", handler)
        core._emit_event("test_event", {"value": 123})
        assert len(events) == 1
        assert events[0]["value"] == 123

        core.off("test_event", handler)
        core._emit_event("test_event", {"value": 456})
        assert len(events) == 1

    def test_execute_task_exists(self, tmp_path):
        """测试任务执行方法存在"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core = AgentCore(config)

        # 检查方法存在
        assert hasattr(core, 'execute_task')
        assert callable(core.execute_task)


class TestSingleton:
    """单例测试"""

    def test_get_agent_core(self, tmp_path):
        """测试获取单例"""
        reset_agent_core()
        config = AgentConfig(workspace=str(tmp_path / "workspace"))
        core1 = get_agent_core(config)
        core2 = get_agent_core()
        assert core1 is core2
