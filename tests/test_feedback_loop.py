#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反馈循环测试

测试 core/feedback_loop.py 的功能
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.feedback_loop import (
    FeedbackLoop,
    Feedback,
    FeedbackType,
    FeedbackSource,
    FeedbackResult,
    get_feedback_loop,
    reset_feedback_loop,
)


class TestFeedbackType:
    """反馈类型测试"""

    def test_all_types(self):
        """测试所有反馈类型"""
        assert FeedbackType.SUCCESS.value == "success"
        assert FeedbackType.FAILURE.value == "failure"
        assert FeedbackType.WARNING.value == "warning"
        assert FeedbackType.INFO.value == "info"
        assert FeedbackType.IMPROVEMENT.value == "improvement"


class TestFeedbackSource:
    """反馈来源测试"""

    def test_all_sources(self):
        """测试所有反馈来源"""
        assert FeedbackSource.USER.value == "user"
        assert FeedbackSource.SYSTEM.value == "system"
        assert FeedbackSource.SELF.value == "self"
        assert FeedbackSource.EXTERNAL.value == "external"


class TestFeedback:
    """反馈测试"""

    def test_feedback_creation(self):
        """测试创建反馈"""
        feedback = Feedback(
            feedback_id="test_1",
            feedback_type=FeedbackType.SUCCESS,
            source=FeedbackSource.USER,
            content="Test feedback",
        )
        assert feedback.feedback_id == "test_1"
        assert feedback.feedback_type == FeedbackType.SUCCESS
        assert feedback.confidence == 1.0


class TestFeedbackResult:
    """反馈结果测试"""

    def test_result_creation(self):
        """测试创建反馈结果"""
        result = FeedbackResult(accepted=True, action_taken="retry")
        assert result.accepted is True
        assert result.action_taken == "retry"


class TestFeedbackLoop:
    """反馈循环测试"""

    def test_init(self, tmp_path):
        """测试初始化"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))
        assert loop is not None
        assert len(loop._feedbacks) == 0

    def test_collect_feedback(self, tmp_path):
        """测试收集反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        feedback = loop.collect_feedback(
            feedback_type=FeedbackType.SUCCESS,
            content="Test success",
            source=FeedbackSource.USER,
        )

        assert feedback is not None
        assert feedback.feedback_type == FeedbackType.SUCCESS
        assert len(loop._feedbacks) == 1

    def test_collect_from_result(self, tmp_path):
        """测试从结果收集反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        feedback = loop.collect_from_result(
            action_id="action_1",
            action_type="test",
            success=True,
        )

        assert feedback.feedback_type == FeedbackType.SUCCESS
        assert feedback.action_id == "action_1"

    def test_collect_failure_feedback(self, tmp_path):
        """测试收集失败反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(
            feedback_type=FeedbackType.FAILURE,
            content="Test failure",
            source=FeedbackSource.SELF,
        )

        assert len(loop._feedbacks) == 1
        assert loop._feedbacks[0].feedback_type == FeedbackType.FAILURE

    def test_register_handler(self, tmp_path):
        """测试注册处理器"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        def handler(fb):
            return FeedbackResult(accepted=True)

        loop.register_handler(FeedbackType.SUCCESS, handler)
        assert len(loop._handlers[FeedbackType.SUCCESS]) == 1

    def test_aggregate_feedback(self, tmp_path):
        """测试聚合反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.FAILURE, "test2", FeedbackSource.SELF)

        aggregation = loop.aggregate_feedback()
        assert aggregation["total"] == 2
        assert "by_type" in aggregation
        assert "by_source" in aggregation

    def test_get_improvements(self, tmp_path):
        """测试获取改进建议"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        # 添加失败反馈
        loop.collect_feedback(
            FeedbackType.FAILURE,
            "Timeout error occurred",
            FeedbackSource.SELF,
        )

        improvements = loop.get_improvements()
        # 应该有一些改进建议
        assert isinstance(improvements, list)

    def test_apply_improvement(self, tmp_path):
        """测试应用改进"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        improvement = {
            "type": "timeout_handling",
            "description": "增加超时处理",
            "confidence": 0.9,
        }

        result = loop.apply_improvement(improvement)
        assert result is True

    def test_get_feedbacks(self, tmp_path):
        """测试获取反馈列表"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.FAILURE, "test2", FeedbackSource.SELF)

        feedbacks = loop.get_feedbacks()
        assert len(feedbacks) == 2

    def test_get_feedbacks_by_type(self, tmp_path):
        """测试按类型获取反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.FAILURE, "test2", FeedbackSource.SELF)

        successes = loop.get_feedbacks(feedback_type=FeedbackType.SUCCESS)
        assert len(successes) == 1
        assert successes[0].feedback_type == FeedbackType.SUCCESS

    def test_get_feedbacks_by_source(self, tmp_path):
        """测试按来源获取反馈"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.SUCCESS, "test2", FeedbackSource.SELF)

        user_feedbacks = loop.get_feedbacks(source=FeedbackSource.USER)
        assert len(user_feedbacks) == 1

    def test_get_statistics(self, tmp_path):
        """测试获取统计"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.FAILURE, "test2", FeedbackSource.SELF)

        stats = loop.get_statistics()
        assert "total_feedbacks" in stats
        assert stats["total_feedbacks"] == 2

    def test_analyze_trends(self, tmp_path):
        """测试分析趋势"""
        reset_feedback_loop()
        loop = FeedbackLoop(project_root=str(tmp_path))

        loop.collect_feedback(FeedbackType.SUCCESS, "test1", FeedbackSource.USER)
        loop.collect_feedback(FeedbackType.FAILURE, "test2", FeedbackSource.SELF)

        trends = loop.analyze_trends(days=7)
        assert "total_feedbacks" in trends
        assert "success_rate" in trends


class TestSingleton:
    """单例测试"""

    def test_get_feedback_loop(self, tmp_path):
        """测试获取单例"""
        reset_feedback_loop()
        loop1 = get_feedback_loop(str(tmp_path))
        loop2 = get_feedback_loop()
        assert loop1 is loop2
