#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.3 单元测试 - 策略学习器模块

测试模块：
- core/strategy_learner.py
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.strategy_learner import (
    StrategyLearner, RewardCalculator, PolicyOptimizer,
    StrategyType, ExecutionOutcome,
    StrategyContext, StrategyResult, StrategyReward, StrategyPolicy,
    get_strategy_learner, reset_strategy_learner,
    select_best_strategy, record_strategy_result,
)


# ============================================================================
# Test Data Classes
# ============================================================================

class TestStrategyContext:
    """测试策略上下文"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = StrategyContext(
            task_type="code_analysis",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )
        assert ctx.task_type == "code_analysis"
        assert ctx.task_complexity == 5.0


class TestStrategyResult:
    """测试策略结果"""

    def test_create_result(self):
        """测试创建结果"""
        result = StrategyResult(
            strategy_id="test_001",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=120.0,
            quality_score=8.5,
            resource_usage=0.5,
        )
        assert result.outcome == ExecutionOutcome.SUCCESS
        assert result.quality_score == 8.5


class TestStrategyReward:
    """测试策略回报"""

    def test_create_reward(self):
        """测试创建回报"""
        reward = StrategyReward(
            strategy_id="test_001",
            total_reward=0.8,
            success_component=1.0,
            time_component=0.8,
            quality_component=0.85,
        )
        assert reward.total_reward == 0.8
        assert reward.success_component == 1.0


class TestStrategyPolicy:
    """测试策略策略"""

    def test_create_policy(self):
        """测试创建策略"""
        policy = StrategyPolicy(
            strategy_id="direct",
            strategy_type=StrategyType.DIRECT,
            weights={"success": 0.4, "time": 0.3, "quality": 0.2, "resource": 0.1},
            thresholds={"min_confidence": 0.6},
        )
        assert policy.strategy_type == StrategyType.DIRECT
        assert policy.weights["success"] == 0.4

    def test_success_rate(self):
        """测试成功率计算"""
        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.CONSERVATIVE,
            weights={"success": 0.5},
            thresholds={},
            success_count=8,
            failure_count=2,
        )
        assert policy.success_rate == 0.8

    def test_success_rate_no_history(self):
        """测试无历史时成功率"""
        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.DIRECT,
            weights={},
            thresholds={},
        )
        assert policy.success_rate == 0.5

    def test_to_dict(self):
        """测试转换为字典"""
        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.EXPLORATORY,
            weights={"success": 0.4},
            thresholds={"min": 0.5},
            success_count=5,
            failure_count=1,
            total_reward=2.0,
        )
        d = policy.to_dict()
        assert d["strategy_id"] == "test"
        assert d["strategy_type"] == "exploratory"


# ============================================================================
# Test RewardCalculator
# ============================================================================

class TestRewardCalculator:
    """测试回报计算器"""

    def test_init(self):
        """测试初始化"""
        calc = RewardCalculator()
        assert calc.weights["success"] == 0.4

    def test_calculate_success(self):
        """测试计算成功回报"""
        calc = RewardCalculator()

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        result = StrategyResult(
            strategy_id="test",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=600.0,  # 10分钟
            quality_score=9.0,
            resource_usage=0.5,
        )

        reward = calc.calculate(result, context)
        assert reward.success_component > 0

    def test_calculate_failure(self):
        """测试计算失败回报"""
        calc = RewardCalculator()

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        result = StrategyResult(
            strategy_id="test",
            outcome=ExecutionOutcome.FAILURE,
            execution_time=100.0,
            quality_score=2.0,
            resource_usage=0.3,
        )

        reward = calc.calculate(result, context)
        assert reward.success_component < 0

    def test_calculate_partial(self):
        """测试计算部分成功回报"""
        calc = RewardCalculator()

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        result = StrategyResult(
            strategy_id="test",
            outcome=ExecutionOutcome.PARTIAL,
            execution_time=1800.0,
            quality_score=5.0,
            resource_usage=0.6,
        )

        reward = calc.calculate(result, context)
        assert reward.success_component == 0.5

    def test_time_efficiency(self):
        """测试时间效率计算"""
        calc = RewardCalculator()

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        # 提前完成
        result_early = StrategyResult(
            strategy_id="test",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=1000.0,  # 16分钟，在1小时内
            quality_score=8.0,
            resource_usage=0.5,
        )
        reward_early = calc.calculate(result_early, context)

        # 超时完成
        result_late = StrategyResult(
            strategy_id="test",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=7200.0,  # 2小时，超过1小时限制
            quality_score=8.0,
            resource_usage=0.5,
        )
        reward_late = calc.calculate(result_late, context)

        assert reward_early.time_component > reward_late.time_component


# ============================================================================
# Test PolicyOptimizer
# ============================================================================

class TestPolicyOptimizer:
    """测试策略优化器"""

    def test_init(self):
        """测试初始化"""
        optimizer = PolicyOptimizer(learning_rate=0.1, exploration_rate=0.2)
        assert optimizer.learning_rate == 0.1
        assert optimizer.exploration_rate == 0.2

    def test_update_policy_success(self):
        """测试更新成功策略"""
        optimizer = PolicyOptimizer()

        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.DIRECT,
            weights={"success": 0.4, "time": 0.3, "quality": 0.2, "resource": 0.1},
            thresholds={},
        )

        reward = StrategyReward(
            strategy_id="test",
            total_reward=0.8,
            success_component=1.0,
            time_component=0.5,
            quality_component=0.8,
        )

        updated = optimizer.update_policy(policy, reward)
        assert updated.success_count == 1
        assert updated.failure_count == 0

    def test_update_policy_failure(self):
        """测试更新失败策略"""
        optimizer = PolicyOptimizer()

        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.CONSERVATIVE,
            weights={"success": 0.4, "time": 0.3, "quality": 0.2, "resource": 0.1},
            thresholds={},
        )

        reward = StrategyReward(
            strategy_id="test",
            total_reward=-0.5,
            success_component=-0.5,
            time_component=0.0,
            quality_component=0.0,
        )

        updated = optimizer.update_policy(policy, reward)
        assert updated.success_count == 0
        assert updated.failure_count == 1

    def test_suggest_weight_adjustment_success(self):
        """测试成功时权重建议"""
        optimizer = PolicyOptimizer()

        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.ADAPTIVE,
            weights={"success": 0.4, "time": 0.3, "quality": 0.2, "resource": 0.1},
            thresholds={},
        )

        adjustments = optimizer.suggest_weight_adjustment(
            policy, ExecutionOutcome.SUCCESS
        )
        assert all(v >= 0 for v in adjustments.values())

    def test_suggest_weight_adjustment_failure(self):
        """测试失败时权重建议"""
        optimizer = PolicyOptimizer()

        policy = StrategyPolicy(
            strategy_id="test",
            strategy_type=StrategyType.ADAPTIVE,
            weights={"success": 0.4, "time": 0.4, "quality": 0.1, "resource": 0.1},
            thresholds={},
        )

        adjustments = optimizer.suggest_weight_adjustment(
            policy, ExecutionOutcome.FAILURE
        )
        # 失败时，time权重应该减少
        assert adjustments.get("time", 0) < 0 or adjustments.get("quality", 0) > 0


# ============================================================================
# Test StrategyLearner
# ============================================================================

class TestStrategyLearner:
    """测试策略学习器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        learner = StrategyLearner(str(tmp_path))
        assert learner.reward_calculator is not None
        assert learner.policy_optimizer is not None

    def test_get_statistics(self, tmp_path):
        """测试获取统计信息"""
        learner = StrategyLearner(str(tmp_path))
        stats = learner.get_statistics()

        assert "total_executions" in stats
        assert "average_reward" in stats
        assert stats["total_executions"] == 0

    def test_record_execution(self, tmp_path):
        """测试记录执行"""
        learner = StrategyLearner(str(tmp_path))

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        result = StrategyResult(
            strategy_id="direct",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=600.0,
            quality_score=8.5,
            resource_usage=0.5,
        )

        reward = learner.record_execution(context, result)
        assert reward is not None
        assert reward.success_component > 0

        stats = learner.get_statistics()
        assert stats["total_executions"] == 1

    def test_select_strategy(self, tmp_path):
        """测试选择策略"""
        learner = StrategyLearner(str(tmp_path))

        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        available = [
            StrategyType.DIRECT,
            StrategyType.CONSERVATIVE,
            StrategyType.EXPLORATORY,
        ]

        strategy, is_explore = learner.select_strategy(context, available)
        assert strategy in available
        assert isinstance(is_explore, bool)

    def test_get_policy(self, tmp_path):
        """测试获取策略"""
        learner = StrategyLearner(str(tmp_path))

        # 先记录一次执行来创建策略
        context = StrategyContext(
            task_type="test",
            task_complexity=5.0,
            time_constraint=1.0,
            risk_level=3.0,
            resource_availability=8.0,
        )

        result = StrategyResult(
            strategy_id="direct",
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=600.0,
            quality_score=8.5,
            resource_usage=0.5,
        )

        learner.record_execution(context, result)
        policy = learner.get_policy(StrategyType.DIRECT)
        assert policy is not None
        assert policy.strategy_type == StrategyType.DIRECT

    def test_multiple_executions(self, tmp_path):
        """测试多次执行"""
        learner = StrategyLearner(str(tmp_path))

        for i in range(5):
            context = StrategyContext(
                task_type=f"test_{i}",
                task_complexity=5.0,
                time_constraint=1.0,
                risk_level=3.0,
                resource_availability=8.0,
            )

            outcome = ExecutionOutcome.SUCCESS if i % 2 == 0 else ExecutionOutcome.PARTIAL

            result = StrategyResult(
                strategy_id="direct",
                outcome=outcome,
                execution_time=600.0,
                quality_score=7.5,
                resource_usage=0.5,
            )

            learner.record_execution(context, result)

        stats = learner.get_statistics()
        assert stats["total_executions"] == 5


# ============================================================================
# Test Integration
# ============================================================================

class TestStrategyLearnerIntegration:
    """测试策略学习器集成"""

    def test_full_learning_cycle(self, tmp_path):
        """测试完整学习周期"""
        learner = StrategyLearner(str(tmp_path))

        # 1. 选择策略
        context = StrategyContext(
            task_type="code_analysis",
            task_complexity=6.0,
            time_constraint=2.0,
            risk_level=4.0,
            resource_availability=7.0,
        )

        available = [StrategyType.DIRECT, StrategyType.EXPLORATORY]
        strategy, _ = learner.select_strategy(context, available)

        # 2. 执行（模拟）
        result = StrategyResult(
            strategy_id=strategy.value,
            outcome=ExecutionOutcome.SUCCESS,
            execution_time=3600.0,
            quality_score=8.5,
            resource_usage=0.6,
        )

        # 3. 记录结果
        reward = learner.record_execution(context, result)

        # 4. 获取更新后的策略
        updated_policy = learner.get_policy(strategy)
        assert updated_policy.success_count >= 1

    def test_singleton_behavior(self, tmp_path):
        """测试单例行为"""
        learner1 = get_strategy_learner(str(tmp_path))
        learner2 = get_strategy_learner(str(tmp_path))
        assert learner1 is learner2

        reset_strategy_learner()

        learner3 = get_strategy_learner(str(tmp_path))
        assert learner3 is not learner1


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup():
    """每个测试后清理"""
    yield
    reset_strategy_learner()
