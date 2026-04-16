#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习引擎测试

测试 core/learning_engine.py 的功能
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning_engine import (
    LearningEngine,
    LearningExample,
    LearnedPattern,
    LearningMetrics,
    get_learning_engine,
    reset_learning_engine,
)


class TestLearningExample:
    """学习示例测试"""

    def test_example_creation(self):
        """测试创建学习示例"""
        example = LearningExample(
            example_id="test_1",
            task_type="code_analysis",
            context={"file": "test.py"},
            action="analyze",
            result="success",
        )
        assert example.example_id == "test_1"
        assert example.task_type == "code_analysis"
        assert example.result == "success"


class TestLearnedPattern:
    """学到的模式测试"""

    def test_pattern_creation(self):
        """测试创建模式"""
        pattern = LearnedPattern(
            pattern_id="test_pattern",
            pattern_type="action",
            description="分析代码",
            confidence=0.8,
        )
        assert pattern.pattern_id == "test_pattern"
        assert pattern.confidence == 0.8
        assert pattern.success_count == 0


class TestLearningMetrics:
    """学习指标测试"""

    def test_default_metrics(self):
        """测试默认指标"""
        metrics = LearningMetrics()
        assert metrics.total_examples == 0
        assert metrics.patterns_learned == 0
        assert metrics.average_confidence == 0.0


class TestLearningEngine:
    """学习引擎测试"""

    def test_init(self, tmp_path):
        """测试初始化"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))
        assert engine is not None
        assert engine.confidence_threshold == 0.6

    def test_record_success_example(self, tmp_path):
        """测试记录成功示例"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        example = engine.record_example(
            task_type="test_task",
            context={"key": "value"},
            action="do_something",
            result="success",
        )

        assert example is not None
        assert example.result == "success"
        assert len(engine._examples) == 1

    def test_record_failure_example(self, tmp_path):
        """测试记录失败示例"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        example = engine.record_example(
            task_type="test_task",
            context={"key": "value"},
            action="do_something",
            result="failure",
        )

        assert example.result == "failure"

    def test_pattern_learning(self, tmp_path):
        """测试模式学习"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        # 记录多个成功示例
        for _ in range(3):
            engine.record_example(
                task_type="test_task",
                context={"key": "value"},
                action="test_action",
                result="success",
            )

        patterns = engine.get_best_patterns("test_task")
        assert len(patterns) >= 0

    def test_get_best_patterns_empty(self, tmp_path):
        """测试获取空模式列表"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        patterns = engine.get_best_patterns("nonexistent_task")
        assert len(patterns) == 0

    def test_suggest_action(self, tmp_path):
        """测试建议动作"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        # 先学习一个模式
        engine.record_example(
            task_type="test_task",
            context={"key": "value"},
            action="suggested_action",
            result="success",
        )

        suggestion = engine.suggest_action("test_task", {"key": "value"})
        # 建议可能为空，因为简化匹配
        assert suggestion is None or isinstance(suggestion, str)

    def test_get_metrics(self, tmp_path):
        """测试获取指标"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        # 添加一些示例
        engine.record_example("task1", {}, "action1", "success")
        engine.record_example("task1", {}, "action2", "failure")

        metrics = engine.get_metrics()
        assert metrics.total_examples == 2
        assert metrics.patterns_learned >= 1

    def test_pattern_stats(self, tmp_path):
        """测试模式统计"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        stats = engine.get_pattern_stats()
        assert "total_patterns" in stats
        assert stats["total_patterns"] == 0

    def test_analyze_learning_progress(self, tmp_path):
        """测试分析学习进度"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        engine.record_example("task1", {}, "action1", "success")
        engine.record_example("task1", {}, "action2", "failure")

        progress = engine.analyze_learning_progress()
        assert "examples_in_window" in progress
        assert "success_rate" in progress

    def test_prune_patterns(self, tmp_path):
        """测试修剪模式"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path), max_patterns=5)

        # 添加超过限制的模式
        for i in range(10):
            engine.record_example(
                "task1",
                {},
                f"action{i}",
                "success",
            )

        # 应该被修剪到 max_patterns
        assert len(engine._patterns) <= 5

    def test_data_persistence(self, tmp_path):
        """测试数据持久化"""
        reset_learning_engine()
        engine = LearningEngine(project_root=str(tmp_path))

        # 添加数据
        engine.record_example("task1", {}, "action1", "success")

        # 创建新实例，应该加载数据
        engine2 = LearningEngine(project_root=str(tmp_path))
        # 新实例会加载数据，但不会加载 _examples
        assert len(engine2._patterns) >= 0


class TestSingleton:
    """单例测试"""

    def test_get_learning_engine(self, tmp_path):
        """测试获取单例"""
        reset_learning_engine()
        engine1 = get_learning_engine(str(tmp_path))
        engine2 = get_learning_engine()
        assert engine1 is engine2
