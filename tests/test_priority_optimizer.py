#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优先级优化器测试

测试 core/priority_optimizer.py 中的：
- 任务管理
- 优先级计算
- 优化执行
- 约束条件
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.priority_optimizer import (
    PriorityOptimizer, Task, PriorityScore, OptimizationResult,
    get_priority_optimizer
)


class TestPriorityScore:
    """优先级分数测试"""

    def test_score_total(self):
        """总分计算"""
        score = PriorityScore(
            base=0.3,
            urgency=0.2,
            importance=0.1,
            effort_ratio=0.1,
            deadline=0.05,
            dependency=0.05,
        )
        expected = 0.3 + 0.2 + 0.1 + 0.1 + 0.05 + 0.05
        assert abs(score.total - expected) < 0.001

    def test_score_default(self):
        """默认分数"""
        score = PriorityScore()
        assert score.total == 0.0


class TestTask:
    """任务测试"""

    def test_create_task(self):
        """创建任务"""
        task = Task(
            task_id="task1",
            name="测试任务",
            description="这是一个测试",
            priority=0.8,
            estimated_time=2.0,
        )
        assert task.task_id == "task1"
        assert task.priority == 0.8
        assert task.estimated_time == 2.0
        assert task.dependencies == []

    def test_task_with_deadline(self):
        """带截止时间的任务"""
        deadline = datetime.now() + timedelta(hours=4)
        task = Task(
            task_id="task2",
            name="限时任务",
            deadline=deadline,
        )
        assert task.deadline is not None


class TestPriorityOptimizerInit:
    """初始化测试"""

    def test_init(self):
        """默认初始化"""
        optimizer = PriorityOptimizer()
        assert optimizer._tasks == {}
        assert optimizer._stats["tasks_added"] == 0

    def test_init_custom_max_time(self):
        """自定义最大时间"""
        optimizer = PriorityOptimizer(max_time_per_cycle=8.0)
        assert optimizer.max_time_per_cycle == 8.0


class TestPriorityOptimizerTaskManagement:
    """任务管理测试"""

    @pytest.fixture
    def optimizer(self):
        return PriorityOptimizer()

    def test_add_task(self, optimizer):
        """添加任务"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        assert "t1" in optimizer._tasks
        assert optimizer._stats["tasks_added"] == 1

    def test_remove_task(self, optimizer):
        """移除任务"""
        task = Task(task_id="t1", name="任务1")
        optimizer.add_task(task)
        assert optimizer.remove_task("t1") is True
        assert "t1" not in optimizer._tasks

    def test_remove_nonexistent(self, optimizer):
        """移除不存在的任务"""
        assert optimizer.remove_task("nonexistent") is False

    def test_get_task(self, optimizer):
        """获取任务"""
        task = Task(task_id="t1", name="任务1")
        optimizer.add_task(task)
        retrieved = optimizer.get_task("t1")
        assert retrieved is not None
        assert retrieved.task_id == "t1"

    def test_update_task(self, optimizer):
        """更新任务"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        optimizer.update_task("t1", priority=0.9)
        assert optimizer.get_task("t1").priority == 0.9


class TestPriorityOptimizerCalculate:
    """优先级计算测试"""

    @pytest.fixture
    def optimizer(self):
        return PriorityOptimizer()

    def test_calculate_priority_basic(self, optimizer):
        """基础优先级计算"""
        task = Task(task_id="t1", name="任务1", priority=0.8)
        optimizer.add_task(task)
        score = optimizer.calculate_priority("t1")
        assert score.base > 0
        assert isinstance(score.total, float)

    def test_calculate_priority_with_deadline(self, optimizer):
        """带截止时间的优先级"""
        task = Task(
            task_id="t1",
            name="紧急任务",
            priority=0.5,
            deadline=datetime.now() + timedelta(hours=1),
        )
        optimizer.add_task(task)
        score = optimizer.calculate_priority("t1")
        assert score.urgency > 0.5  # 紧急任务有较高紧迫性

    def test_calculate_priority_overdue(self, optimizer):
        """过期任务的优先级"""
        task = Task(
            task_id="t1",
            name="过期任务",
            priority=0.5,
            deadline=datetime.now() - timedelta(hours=1),
        )
        optimizer.add_task(task)
        score = optimizer.calculate_priority("t1")
        assert score.urgency == 1.0  # 已过期

    def test_calculate_priority_with_dependencies(self, optimizer):
        """有依赖的任务"""
        task1 = Task(task_id="t1", name="基础任务")
        task2 = Task(task_id="t2", name="依赖任务", dependencies=["t1"])
        optimizer.add_task(task1)
        optimizer.add_task(task2)
        score = optimizer.calculate_priority("t1")
        assert score.dependency > 0  # t1 被其他任务依赖

    def test_calculate_priority_cache(self, optimizer):
        """优先级缓存"""
        task = Task(task_id="t1", name="任务1", priority=0.7)
        optimizer.add_task(task)
        score1 = optimizer.calculate_priority("t1")
        score2 = optimizer.calculate_priority("t1")
        assert score1.total == score2.total


class TestPriorityOptimizerOptimize:
    """优化执行测试"""

    @pytest.fixture
    def optimizer(self):
        return PriorityOptimizer()

    def test_optimize_empty(self, optimizer):
        """空优化"""
        result = optimizer.optimize()
        assert result.task_order == []
        assert result.constraints_satisfied is True

    def test_optimize_single_task(self, optimizer):
        """单任务优化"""
        task = Task(task_id="t1", name="任务1", priority=0.8)
        optimizer.add_task(task)
        result = optimizer.optimize()
        assert "t1" in result.task_order

    def test_optimize_multiple_tasks(self, optimizer):
        """多任务优化"""
        for i in range(5):
            task = Task(
                task_id=f"t{i}",
                name=f"任务{i}",
                priority=0.5 + i * 0.1,
            )
            optimizer.add_task(task)
        result = optimizer.optimize()
        assert len(result.task_order) > 0
        assert len(result.task_order) <= optimizer.max_time_per_cycle

    def test_optimize_with_time_constraint(self, optimizer):
        """时间约束"""
        for i in range(10):
            task = Task(
                task_id=f"t{i}",
                name=f"任务{i}",
                estimated_time=1.0,
            )
            optimizer.add_task(task)
        result = optimizer.optimize(constraints={"max_time": 3.0})
        assert result.total_time <= 3.0

    def test_optimize_respects_dependencies(self, optimizer):
        """依赖约束"""
        optimizer.add_task(Task(task_id="dep", name="依赖任务"))
        optimizer.add_task(Task(task_id="main", name="主任务", dependencies=["dep"]))
        result = optimizer.optimize()
        dep_idx = result.task_order.index("dep")
        main_idx = result.task_order.index("main")
        assert dep_idx < main_idx

    def test_optimize_updates_stats(self, optimizer):
        """优化更新统计"""
        task = Task(task_id="t1", name="任务1")
        optimizer.add_task(task)
        optimizer.optimize()
        assert optimizer._stats["optimizations_run"] == 1


class TestPriorityOptimizerAdjust:
    """优先级调整测试"""

    @pytest.fixture
    def optimizer(self):
        return PriorityOptimizer()

    def test_adjust_priority_up(self, optimizer):
        """提升优先级"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        result = optimizer.adjust_priority("t1", 0.2, "测试提升")
        assert result is True
        assert optimizer.get_task("t1").priority == 0.7

    def test_adjust_priority_down(self, optimizer):
        """降低优先级"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        optimizer.adjust_priority("t1", -0.3)
        assert optimizer.get_task("t1").priority == 0.2

    def test_adjust_priority_clamp(self, optimizer):
        """优先级限制"""
        task = Task(task_id="t1", name="任务1", priority=0.9)
        optimizer.add_task(task)
        optimizer.adjust_priority("t1", 0.5)
        assert optimizer.get_task("t1").priority <= 1.0

        task2 = Task(task_id="t2", name="任务2", priority=0.1)
        optimizer.add_task(task2)
        optimizer.adjust_priority("t2", -0.5)
        assert optimizer.get_task("t2").priority >= 0.0

    def test_boost_task(self, optimizer):
        """快速提升"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        optimizer.boost_task("t1")
        assert optimizer.get_task("t1").priority == 0.7

    def test_postpone_task(self, optimizer):
        """快速推迟"""
        task = Task(task_id="t1", name="任务1", priority=0.5)
        optimizer.add_task(task)
        optimizer.postpone_task("t1")
        assert optimizer.get_task("t1").priority == 0.4


class TestPriorityOptimizerStatistics:
    """统计分析测试"""

    @pytest.fixture
    def optimizer(self):
        return PriorityOptimizer()

    def test_get_statistics_empty(self, optimizer):
        """空统计"""
        stats = optimizer.get_statistics()
        # 有任务时返回完整统计
        assert "tasks_added" in stats
        assert "optimizations_run" in stats

    def test_get_statistics_with_tasks(self, optimizer):
        """有任务的统计"""
        optimizer.add_task(Task(task_id="t1", name="任务1", priority=0.3))
        optimizer.add_task(Task(task_id="t2", name="任务2", priority=0.7))
        stats = optimizer.get_statistics()
        assert stats["total_tasks"] == 2
        assert stats["average_priority"] == 0.5

    def test_get_priority_distribution(self, optimizer):
        """优先级分布"""
        optimizer.add_task(Task(task_id="t1", name="高", priority=0.8))
        optimizer.add_task(Task(task_id="t2", name="中", priority=0.5))
        optimizer.add_task(Task(task_id="t3", name="低", priority=0.3))
        dist = optimizer.get_priority_distribution()
        assert dist["high"] == 1
        assert dist["medium"] == 1
        assert dist["low"] == 1


class TestPriorityOptimizerIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """完整工作流程"""
        # 1. 创建优化器
        optimizer = PriorityOptimizer(max_time_per_cycle=4.0)

        # 2. 添加任务
        optimizer.add_task(Task(
            task_id="t1",
            name="紧急任务",
            priority=0.9,
            estimated_time=1.0,
        ))
        optimizer.add_task(Task(
            task_id="t2",
            name="普通任务",
            priority=0.5,
            estimated_time=2.0,
        ))

        # 3. 优化
        result = optimizer.optimize(constraints={"max_time": 3.0})

        # 4. 验证结果
        assert len(result.task_order) > 0
        assert result.constraints_satisfied is True

        # 5. 验证统计
        stats = optimizer.get_statistics()
        assert stats["total_tasks"] == 2
        assert stats["optimizations_run"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
