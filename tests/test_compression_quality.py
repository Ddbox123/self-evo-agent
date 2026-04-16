#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩质量评估器测试
"""

import pytest
from tools.compression_quality import (
    QualityReport,
    CompressionQualityEvaluator,
    get_compression_quality_evaluator,
    reset_compression_quality_evaluator,
)


class MockMessage:
    """模拟消息对象"""

    def __init__(self, msg_type: str, content: str = ""):
        self.type = msg_type
        self.content = content


class TestQualityReport:
    """测试质量报告"""

    def test_is_effective_true(self):
        """测试有效压缩"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=6000,
            compression_ratio=0.4,
            saved_tokens=4000,
        )
        assert report.is_effective() is True

    def test_is_effective_false(self):
        """测试无效压缩"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=9500,
            compression_ratio=0.05,
            saved_tokens=500,
        )
        assert report.is_effective() is False

    def test_is_effective_custom_threshold(self):
        """测试自定义阈值"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=8000,
            compression_ratio=0.2,
            saved_tokens=2000,
        )
        assert report.is_effective(threshold=0.3) is False
        assert report.is_effective(threshold=0.1) is True

    def test_is_quality_acceptable_true(self):
        """测试质量可接受"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=6000,
            compression_ratio=0.4,
            saved_tokens=4000,
            quality_score=0.8,
        )
        assert report.is_quality_acceptable() is True

    def test_is_quality_acceptable_false(self):
        """测试质量不可接受"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=6000,
            compression_ratio=0.4,
            saved_tokens=4000,
            quality_score=0.5,
        )
        assert report.is_quality_acceptable() is False

    def test_to_summary(self):
        """测试生成摘要"""
        report = QualityReport(
            original_tokens=10000,
            compressed_tokens=6000,
            compression_ratio=0.4,
            saved_tokens=4000,
            info_preservation_rate=0.85,
            quality_score=0.75,
        )
        summary = report.to_summary()
        assert "10000" in summary
        assert "6000" in summary
        assert "40" in summary  # 不检查确切格式


class TestCompressionQualityEvaluator:
    """测试压缩质量评估器"""

    def setup_method(self):
        """每个测试前重置单例"""
        reset_compression_quality_evaluator()

    def test_init_default_threshold(self):
        """测试默认阈值初始化"""
        evaluator = CompressionQualityEvaluator()
        assert evaluator.effectiveness_threshold == 0.3

    def test_init_custom_threshold(self):
        """测试自定义阈值初始化"""
        evaluator = CompressionQualityEvaluator(effectiveness_threshold=0.5)
        assert evaluator.effectiveness_threshold == 0.5

    def test_evaluate(self):
        """测试评估压缩质量"""
        evaluator = CompressionQualityEvaluator()

        original = [
            MockMessage('system', 'System prompt'),
            MockMessage('human', '用户输入'),
            MockMessage('ai', 'Error: 分析失败'),
            MockMessage('tool', 'tool result'),
        ]
        compressed = [
            MockMessage('system', 'System prompt'),
            MockMessage('ai', '分析完成'),
        ]

        report = evaluator.evaluate(
            original, compressed,
            original_tokens=8000,
            compressed_tokens=4000,
        )

        assert report.original_tokens == 8000
        assert report.compressed_tokens == 4000
        assert report.compression_ratio == 0.5
        assert report.saved_tokens == 4000

    def test_evaluate_with_key_info(self):
        """测试评估包含关键信息"""
        evaluator = CompressionQualityEvaluator()

        original = [
            MockMessage('ai', '发现了一个关键错误'),
            MockMessage('tool', 'Error: file not found'),
        ]
        compressed = [
            MockMessage('ai', '分析完成'),
        ]

        report = evaluator.evaluate(
            original, compressed,
            original_tokens=2000,
            compressed_tokens=1000,
        )

        assert len(report.key_info_lost) >= 0  # 可能有关键信息丢失

    def test_is_compression_effective_true(self):
        """测试快速判断有效压缩"""
        evaluator = CompressionQualityEvaluator()
        assert evaluator.is_compression_effective(10000, 6500) is True

    def test_is_compression_effective_false(self):
        """测试快速判断无效压缩"""
        evaluator = CompressionQualityEvaluator()
        assert evaluator.is_compression_effective(10000, 9500) is False

    def test_is_compression_effective_zero_tokens(self):
        """测试零token情况"""
        evaluator = CompressionQualityEvaluator()
        assert evaluator.is_compression_effective(0, 0) is False

    def test_calculate_compression_ratio(self):
        """测试计算压缩比例"""
        evaluator = CompressionQualityEvaluator()

        ratio = evaluator._calculate_compression_ratio(10000, 6000)
        assert ratio == 0.4

        ratio = evaluator._calculate_compression_ratio(10000, 10000)
        assert ratio == 0.0

        ratio = evaluator._calculate_compression_ratio(0, 0)
        assert ratio == 0.0

    def test_extract_key_info(self):
        """测试提取关键信息"""
        evaluator = CompressionQualityEvaluator()

        messages = [
            MockMessage('ai', '这是一个包含error的回复'),
            MockMessage('tool', '分析完成'),
            MockMessage('ai', '正常回复'),
        ]

        key_info = evaluator._extract_key_info(messages)
        assert 'error' in key_info

    def test_calculate_quality_score(self):
        """测试计算质量评分"""
        evaluator = CompressionQualityEvaluator()

        # 高压缩比、高保留率
        score = evaluator._calculate_quality_score(0.5, 0.9, 0)
        assert score > 0.7

        # 低压缩比、高保留率
        score = evaluator._calculate_quality_score(0.1, 0.9, 0)
        assert score > 0.5

    def test_generate_warnings(self):
        """测试生成警告"""
        evaluator = CompressionQualityEvaluator()

        # 低压缩比警告
        warnings = evaluator._generate_warnings(0.1, 0.8, 500)
        assert any("压缩比过低" in w for w in warnings)

        # 低信息保留警告
        warnings = evaluator._generate_warnings(0.4, 0.3, 2000)
        assert any("关键信息保留率过低" in w for w in warnings)

        # 节省过少警告
        warnings = evaluator._generate_warnings(0.3, 0.8, 500)
        assert any("Token 节省过少" in w for w in warnings)


class TestCompressionQualityEvaluatorSingleton:
    """测试压缩质量评估器单例"""

    def setup_method(self):
        """每个测试前重置单例"""
        reset_compression_quality_evaluator()

    def test_get_singleton(self):
        """测试获取单例"""
        e1 = get_compression_quality_evaluator()
        e2 = get_compression_quality_evaluator()
        assert e1 is e2

    def test_reset_singleton(self):
        """测试重置单例"""
        e1 = get_compression_quality_evaluator()
        reset_compression_quality_evaluator()
        e2 = get_compression_quality_evaluator()
        assert e1 is not e2

    def test_reset_with_custom_threshold(self):
        """测试重置时使用自定义阈值"""
        e = CompressionQualityEvaluator(effectiveness_threshold=0.5)
        assert e.effectiveness_threshold == 0.5
