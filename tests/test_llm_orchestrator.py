#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Orchestrator 测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_create_config(self):
        """测试创建配置"""
        from core.llm_orchestrator import LLMConfig
        config = LLMConfig(
            model_name="gpt-4",
            temperature=0.5,
        )
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.5

    def test_config_defaults(self):
        """测试默认配置"""
        from core.llm_orchestrator import LLMConfig
        config = LLMConfig()
        assert config.model_name == "gpt-4o"
        assert config.temperature == 0.7
        assert config.api_timeout == 600


class TestLLMResponse:
    """测试 LLM 响应"""

    def test_create_response(self):
        """测试创建响应"""
        from core.llm_orchestrator import LLMResponse
        response = LLMResponse(
            content="Hello",
            raw_response=None,
        )
        assert response.content == "Hello"
        assert response.duration == 0.0


class TestLLMCallOptions:
    """测试 LLM 调用选项"""

    def test_create_options(self):
        """测试创建选项"""
        from core.llm_orchestrator import LLMCallOptions
        options = LLMCallOptions(
            temperature=0.5,
        )
        assert options.temperature == 0.5


class TestLLMOrchestrator:
    """测试 LLM Orchestrator"""

    def test_init_empty(self):
        """测试初始化"""
        from core.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        assert orchestrator.config is not None
        assert orchestrator._llm is None

    def test_init_with_config(self):
        """测试使用配置初始化"""
        from core.llm_orchestrator import LLMOrchestrator, LLMConfig
        config = LLMConfig(model_name="gpt-4")
        orchestrator = LLMOrchestrator(config)
        assert orchestrator.config.model_name == "gpt-4"

    def test_get_statistics(self):
        """测试获取统计"""
        from core.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        stats = orchestrator.get_statistics()
        assert "total_calls" in stats
        assert stats["total_calls"] == 0
        assert "errors" in stats
        assert stats["errors"] == 0

    def test_get_call_history_empty(self):
        """测试获取空的历史"""
        from core.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        history = orchestrator.get_call_history()
        assert len(history) == 0

    def test_clear_history(self):
        """测试清除历史"""
        from core.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        orchestrator.clear_history()
        assert len(orchestrator._call_history) == 0

    def test_reset_stats(self):
        """测试重置统计"""
        from core.llm_orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator()
        orchestrator._stats["total_calls"] = 10
        orchestrator.reset_stats()
        assert orchestrator._stats["total_calls"] == 0

    def test_get_compression_llm(self):
        """测试获取压缩 LLM"""
        from core.llm_orchestrator import LLMOrchestrator
        with patch('core.llm_orchestrator.ChatOpenAI'):
            orchestrator = LLMOrchestrator()
            orchestrator.initialize()
            assert orchestrator._compression_llm is not None


class TestLLMOrchestratorIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        from core.llm_orchestrator import LLMOrchestrator, LLMConfig
        config = LLMConfig(model_name="gpt-4", temperature=0.5)
        orchestrator = LLMOrchestrator(config)

        # 获取统计
        stats = orchestrator.get_statistics()
        assert stats["total_calls"] == 0
        assert stats["errors"] == 0

        # 清除历史
        orchestrator.clear_history()
        assert len(orchestrator.get_call_history()) == 0

        # 重置统计
        orchestrator.reset_stats()
        stats = orchestrator.get_statistics()
        assert stats["total_calls"] == 0
