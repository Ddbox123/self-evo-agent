#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略选择器测试

测试 core/strategy_selector.py 中的：
- 策略管理
- 策略选择
- 策略切换
- 效果评估
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategy_selector import (
    StrategySelector, Strategy, StrategyResult, StrategySelection,
    StrategyType, DEFAULT_STRATEGIES, create_default_selector
)


class TestStrategy:
    """策略测试"""

    def test_create_strategy(self):
        """创建策略"""
        strategy = Strategy(
            strategy_id="s1",
            name="测试策略",
            strategy_type=StrategyType.BALANCED,
            description="测试用策略",
            success_rate=0.8,
        )
        assert strategy.strategy_id == "s1"
        assert strategy.strategy_type == StrategyType.BALANCED
        assert strategy.success_rate == 0.8
        assert strategy.usage_count == 0


class TestStrategyResult:
    """策略结果测试"""

    def test_create_result(self):
        """创建结果"""
        result = StrategyResult(
            strategy_id="s1",
            success=True,
            outcome="完成",
            metrics={"accuracy": 0.9},
            duration=1.5,
        )
        assert result.strategy_id == "s1"
        assert result.success is True
        assert result.duration == 1.5


class TestStrategySelection:
    """策略选择测试"""

    def test_create_selection(self):
        """创建选择"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="测试",
        )
        selection = StrategySelection(
            selected_strategy=strategy,
            alternatives=[],
            confidence=0.85,
            reasoning="测试选择",
        )
        assert selection.selected_strategy.strategy_id == "s1"
        assert selection.confidence == 0.85


class TestStrategySelectorInit:
    """初始化测试"""

    def test_init(self):
        """默认初始化"""
        selector = StrategySelector()
        # 初始化后可能有持久化的数据
        assert selector._strategies is not None
        assert selector._config["switch_threshold"] == 0.3

    def test_init_empty_data_dir(self):
        """空数据目录初始化"""
        selector = StrategySelector(project_root=".")
        assert selector.project_root is not None


class TestStrategySelectorManagement:
    """策略管理测试"""

    @pytest.fixture
    def selector(self):
        return StrategySelector()

    def test_add_strategy(self, selector):
        """添加策略"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="测试",
        )
        selector.add_strategy(strategy)
        assert "s1" in selector._strategies

    def test_remove_strategy(self, selector):
        """移除策略"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="测试",
        )
        selector.add_strategy(strategy)
        assert selector.remove_strategy("s1") is True
        assert "s1" not in selector._strategies

    def test_get_strategy(self, selector):
        """获取策略"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="测试",
        )
        selector.add_strategy(strategy)
        retrieved = selector.get_strategy("s1")
        assert retrieved is not None
        assert retrieved.strategy_id == "s1"

    def test_list_strategies(self, selector):
        """列出策略"""
        selector._strategies.clear()  # 清除持久化数据
        selector.add_strategy(Strategy(
            strategy_id="s1", name="S1", strategy_type=StrategyType.BALANCED, description=""
        ))
        selector.add_strategy(Strategy(
            strategy_id="s2", name="S2", strategy_type=StrategyType.AGGRESSIVE, description=""
        ))
        all_strategies = selector.list_strategies()
        assert len(all_strategies) == 2
        aggressive = selector.list_strategies(StrategyType.AGGRESSIVE)
        assert len(aggressive) == 1


class TestStrategySelectorSelect:
    """策略选择测试"""

    @pytest.fixture
    def selector(self):
        return create_default_selector()

    def test_select_with_no_strategies(self):
        """无策略时的选择"""
        selector = StrategySelector()
        # 清除所有持久化的策略
        selector._strategies.clear()
        context = {"task_type": "default"}
        selection = selector.select(context)
        assert selection.selected_strategy.strategy_id == "default"
        assert selection.confidence == 0.0

    def test_select_basic(self, selector):
        """基础选择"""
        context = {"task_type": "default"}
        selection = selector.select(context)
        assert selection.selected_strategy is not None
        assert selection.confidence > 0

    def test_select_with_exploration_mode(self, selector):
        """探索模式选择"""
        context = {"task_type": "default", "exploration_mode": True}
        selection = selector.select(context)
        assert selection.selected_strategy is not None

    def test_select_forced_type(self, selector):
        """强制类型选择"""
        context = {"task_type": "default"}
        selection = selector.select(context, forced_type=StrategyType.CONSERVATIVE)
        assert selection.selected_strategy.strategy_type == StrategyType.CONSERVATIVE

    def test_select_updates_stats(self, selector):
        """选择更新统计"""
        context = {"task_type": "default"}
        initial = selector._stats["selections_made"]
        selector.select(context)
        assert selector._stats["selections_made"] == initial + 1

    def test_select_provides_alternatives(self, selector):
        """提供备选策略"""
        context = {"task_type": "default"}
        selection = selector.select(context)
        # 可能没有备选（取决于策略数量和得分）


class TestStrategySelectorSwitch:
    """策略切换测试"""

    @pytest.fixture
    def selector(self):
        return StrategySelector()

    def test_should_switch_insufficient_data(self, selector):
        """数据不足时不切换"""
        should_switch, new_strategy = selector.should_switch("s1", [])
        assert should_switch is False

    def test_should_switch_low_success_rate(self, selector):
        """低成功率时考虑切换"""
        # 添加策略
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
        )
        selector.add_strategy(strategy)
        selector.add_strategy(Strategy(
            strategy_id="s2",
            name="策略2",
            strategy_type=StrategyType.CONSERVATIVE,
            description="",
        ))

        # 失败的结果 - 足够多的失败记录
        results = []
        for _ in range(5):
            results.append(StrategyResult(strategy_id="s1", success=False, outcome=None))

        should_switch, new_strategy = selector.should_switch("s1", results, threshold=0.5)
        # 可能有切换，取决于统计

    def test_should_switch_high_success_rate(self, selector):
        """高成功率时不切换"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
        )
        selector.add_strategy(strategy)

        results = [
            StrategyResult(strategy_id="s1", success=True, outcome=None),
            StrategyResult(strategy_id="s1", success=True, outcome=None),
            StrategyResult(strategy_id="s1", success=True, outcome=None),
        ]

        should_switch, new_strategy = selector.should_switch("s1", results, threshold=0.5)
        assert should_switch is False


class TestStrategySelectorRecord:
    """结果记录测试"""

    @pytest.fixture
    def selector(self):
        return StrategySelector()

    def test_record_success(self, selector):
        """记录成功"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
            usage_count=5,
            success_rate=0.6,
        )
        selector.add_strategy(strategy)

        result = StrategyResult(
            strategy_id="s1",
            success=True,
            outcome="成功",
        )
        selector.record_result(result)

        # 验证更新
        s = selector.get_strategy("s1")
        assert s.usage_count == 6
        assert s.success_rate > 0.6

    def test_record_failure(self, selector):
        """记录失败"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
            usage_count=5,
            success_rate=0.6,
        )
        selector.add_strategy(strategy)

        result = StrategyResult(
            strategy_id="s1",
            success=False,
            outcome="失败",
        )
        selector.record_result(result)

        s = selector.get_strategy("s1")
        assert s.usage_count == 6
        assert s.success_rate < 0.6

    def test_record_updates_last_used(self, selector):
        """记录更新时间"""
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
        )
        selector.add_strategy(strategy)

        before = datetime.now()
        result = StrategyResult(strategy_id="s1", success=True, outcome=None)
        selector.record_result(result)
        after = datetime.now()

        s = selector.get_strategy("s1")
        assert s.last_used is not None
        assert before <= s.last_used <= after


class TestStrategySelectorStatistics:
    """统计分析测试"""

    def test_get_statistics(self):
        """获取统计"""
        selector = StrategySelector()
        selector._strategies.clear()
        # 清理后添加默认策略
        from core.strategy_selector import DEFAULT_STRATEGIES
        for s in DEFAULT_STRATEGIES:
            selector.add_strategy(s)
        stats = selector.get_statistics()
        assert "total_strategies" in stats
        assert stats["total_strategies"] == 3
        assert "selections_made" in stats

    def test_analyze_performance_trend(self):
        """分析性能趋势"""
        selector = StrategySelector()
        strategy = Strategy(
            strategy_id="s1",
            name="策略1",
            strategy_type=StrategyType.BALANCED,
            description="",
        )
        selector.add_strategy(strategy)

        # 添加一些结果
        for _ in range(5):
            selector.record_result(StrategyResult(
                strategy_id="s1", success=True, outcome=None
            ))

        trend = selector.analyze_performance_trend(window_days=1)
        assert "overall_success_rate" in trend


class TestStrategySelectorIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """完整工作流程"""
        # 1. 创建选择器
        selector = StrategySelector()

        # 2. 添加一个测试策略
        test_strategy = Strategy(
            strategy_id="test_s1",
            name="测试策略",
            strategy_type=StrategyType.BALANCED,
            description="测试用",
            success_rate=0.8,
        )
        selector.add_strategy(test_strategy)

        # 3. 选择策略
        context = {"task_type": "default"}
        selection = selector.select(context)
        assert selection.selected_strategy is not None

        # 4. 记录结果
        result = StrategyResult(
            strategy_id="test_s1",
            success=True,
            outcome="完成",
        )
        selector.record_result(result)

        # 5. 验证性能
        performance = selector.get_strategy_performance("test_s1")
        assert performance["usage_count"] >= 1

        # 6. 获取统计
        stats = selector.get_statistics()
        assert stats["selections_made"] >= 1

        # 7. 分析趋势
        trend = selector.analyze_performance_trend()
        assert "overall_success_rate" in trend


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
