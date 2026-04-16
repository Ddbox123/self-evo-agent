#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
压缩策略管理器测试
"""

import pytest
from tools.compression_strategy import (
    CompressionLevel,
    CompressionConfig,
    CompressionThresholds,
    CompressionStrategy,
    get_compression_strategy,
    reset_compression_strategy,
)


class TestCompressionLevel:
    """测试压缩级别枚举"""

    def test_compression_levels_exist(self):
        """测试所有压缩级别都存在"""
        assert CompressionLevel.LIGHT is not None
        assert CompressionLevel.STANDARD is not None
        assert CompressionLevel.DEEP is not None
        assert CompressionLevel.EMERGENCY is not None

    def test_compression_level_values(self):
        """测试压缩级别值"""
        assert CompressionLevel.LIGHT.value == "light"
        assert CompressionLevel.STANDARD.value == "standard"
        assert CompressionLevel.DEEP.value == "deep"
        assert CompressionLevel.EMERGENCY.value == "emergency"


class TestCompressionStrategy:
    """测试压缩策略管理器"""

    def setup_method(self):
        """每个测试前重置单例"""
        reset_compression_strategy()

    def test_init_default_thresholds(self):
        """测试默认阈值初始化"""
        strategy = CompressionStrategy()
        assert strategy.thresholds.light_threshold == 0.6
        assert strategy.thresholds.standard_threshold == 0.8
        assert strategy.thresholds.deep_threshold == 0.9
        assert strategy.thresholds.emergency_threshold == 0.95

    def test_init_custom_thresholds(self):
        """测试自定义阈值初始化"""
        custom = CompressionThresholds(
            light_threshold=0.5,
            standard_threshold=0.7,
            deep_threshold=0.85,
            emergency_threshold=0.9,
        )
        strategy = CompressionStrategy(custom)
        assert strategy.thresholds.light_threshold == 0.5
        assert strategy.thresholds.standard_threshold == 0.7

    def test_get_config_light(self):
        """测试获取轻度压缩配置"""
        strategy = CompressionStrategy()
        config = strategy.get_config(CompressionLevel.LIGHT)
        assert config.level == CompressionLevel.LIGHT
        assert config.summary_max_chars == 500
        assert config.keep_ai_messages == 5

    def test_get_config_standard(self):
        """测试获取标准压缩配置"""
        strategy = CompressionStrategy()
        config = strategy.get_config(CompressionLevel.STANDARD)
        assert config.level == CompressionLevel.STANDARD
        assert config.summary_max_chars == 1000
        assert config.keep_ai_messages == 3

    def test_get_config_deep(self):
        """测试获取深度压缩配置"""
        strategy = CompressionStrategy()
        config = strategy.get_config(CompressionLevel.DEEP)
        assert config.level == CompressionLevel.DEEP
        assert config.summary_max_chars == 2000
        assert config.keep_ai_messages == 2

    def test_get_config_emergency(self):
        """测试获取紧急压缩配置"""
        strategy = CompressionStrategy()
        config = strategy.get_config(CompressionLevel.EMERGENCY)
        assert config.level == CompressionLevel.EMERGENCY
        assert config.summary_max_chars == 3000
        assert config.keep_ai_messages == 1

    def test_calculate_compression_ratio_light(self):
        """测试轻度压缩比例"""
        strategy = CompressionStrategy()
        ratio = strategy.calculate_compression_ratio(CompressionLevel.LIGHT)
        assert ratio == 0.8  # 保留80%

    def test_calculate_compression_ratio_standard(self):
        """测试标准压缩比例"""
        strategy = CompressionStrategy()
        ratio = strategy.calculate_compression_ratio(CompressionLevel.STANDARD)
        assert ratio == 0.5  # 保留50%

    def test_calculate_compression_ratio_deep(self):
        """测试深度压缩比例"""
        strategy = CompressionStrategy()
        ratio = strategy.calculate_compression_ratio(CompressionLevel.DEEP)
        assert ratio == 0.3  # 保留30%

    def test_calculate_compression_ratio_emergency(self):
        """测试紧急压缩比例"""
        strategy = CompressionStrategy()
        ratio = strategy.calculate_compression_ratio(CompressionLevel.EMERGENCY)
        assert ratio == 0.15  # 保留15%

    def test_determine_level_normal(self):
        """测试正常状态"""
        strategy = CompressionStrategy()
        level = strategy.determine_level(8000, 16000)
        assert level == CompressionLevel.LIGHT

    def test_determine_level_light(self):
        """测试轻度压缩阈值"""
        strategy = CompressionStrategy()
        level = strategy.determine_level(10000, 16000)
        assert level == CompressionLevel.LIGHT

    def test_determine_level_standard(self):
        """测试标准压缩阈值"""
        strategy = CompressionStrategy()
        level = strategy.determine_level(13000, 16000)
        assert level == CompressionLevel.STANDARD

    def test_determine_level_deep(self):
        """测试深度压缩阈值"""
        strategy = CompressionStrategy()
        level = strategy.determine_level(14500, 16000)
        assert level == CompressionLevel.DEEP

    def test_determine_level_emergency(self):
        """测试紧急压缩阈值"""
        strategy = CompressionStrategy()
        level = strategy.determine_level(15500, 16000)
        assert level == CompressionLevel.EMERGENCY

    def test_determine_level_with_compression_count(self):
        """测试考虑压缩次数"""
        strategy = CompressionStrategy()
        # 第一次深度压缩
        level1 = strategy.determine_level(14500, 16000, compression_count=0)
        assert level1 == CompressionLevel.DEEP
        # 第二次应该使用保守策略
        level2 = strategy.determine_level(14500, 16000, compression_count=2)
        assert level2 == CompressionLevel.STANDARD

    def test_set_summary_chars(self):
        """测试设置摘要字数"""
        strategy = CompressionStrategy()
        strategy.set_summary_chars(CompressionLevel.LIGHT, 800)
        config = strategy.get_config(CompressionLevel.LIGHT)
        assert config.summary_max_chars == 800

    def test_set_keep_ai_messages(self):
        """测试设置保留AI消息数"""
        strategy = CompressionStrategy()
        strategy.set_keep_ai_messages(CompressionLevel.STANDARD, 5)
        config = strategy.get_config(CompressionLevel.STANDARD)
        assert config.keep_ai_messages == 5

    def test_should_preserve_system_message(self):
        """测试系统消息总是保留"""
        strategy = CompressionStrategy()

        class MockMessage:
            type = 'system'
            content = 'System prompt'

        msg = MockMessage()
        for level in [CompressionLevel.LIGHT, CompressionLevel.STANDARD,
                       CompressionLevel.DEEP, CompressionLevel.EMERGENCY]:
            assert strategy.should_preserve_message(msg, level) is True

    def test_should_preserve_tool_calls_in_deep(self):
        """测试深度压缩保留工具调用"""
        strategy = CompressionStrategy()

        class MockMessage:
            type = 'ai'
            tool_calls = [{'name': 'test_tool'}]

        msg = MockMessage()
        assert strategy.should_preserve_message(msg, CompressionLevel.DEEP) is True


class TestCompressionStrategySingleton:
    """测试压缩策略单例"""

    def setup_method(self):
        """每个测试前重置单例"""
        reset_compression_strategy()

    def test_get_singleton(self):
        """测试获取单例"""
        s1 = get_compression_strategy()
        s2 = get_compression_strategy()
        assert s1 is s2

    def test_reset_singleton(self):
        """测试重置单例"""
        s1 = get_compression_strategy()
        reset_compression_strategy()
        s2 = get_compression_strategy()
        assert s1 is not s2

    def test_reset_with_custom_thresholds(self):
        """测试重置时使用自定义阈值"""
        custom = CompressionThresholds(light_threshold=0.7)
        s = CompressionStrategy(custom)
        assert s.thresholds.light_threshold == 0.7
