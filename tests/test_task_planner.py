#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Planner 测试
"""

import pytest
from datetime import datetime, timedelta


class TestTaskStatus:
    """测试任务状态"""

    def test_task_statuses(self):
        """测试所有任务状态"""
        from core.task_planner import TaskStatus
        statuses = list(TaskStatus)
        assert len(statuses) == 6
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.COMPLETED in statuses


class TestTaskPriority:
    """测试任务优先级"""

    def test_priorities(self):
        """测试所有优先级"""
        from core.task_planner import TaskPriority
        priorities = list(TaskPriority)
        assert len(priorities) == 5
        assert TaskPriority.CRITICAL in priorities
        assert TaskPriority.HIGH in priorities


class TestRiskLevel:
    """测试风险等级"""

    def test_risks(self):
        """测试所有风险等级"""
        from core.task_planner import RiskLevel
        risks = list(RiskLevel)
        assert len(risks) == 4
        assert RiskLevel.LOW in risks
        assert RiskLevel.HIGH in risks


class TestTask:
    """测试任务"""

    def test_create_task(self):
        """测试创建任务"""
        from core.task_planner import Task, TaskStatus, TaskPriority
        task = Task(
            task_id="test_1",
            name="Test Task",
            description="A test task",
        )
        assert task.task_id == "test_1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING


class TestTaskPlan:
    """测试任务计划"""

    def test_create_plan(self):
        """测试创建计划"""
        from core.task_planner import TaskPlan
        plan = TaskPlan(plan_id="plan_1", goal="Test goal")
        assert plan.plan_id == "plan_1"
        assert plan.goal == "Test goal"


class TestTaskPlanner:
    """测试任务规划器"""

    def test_init(self):
        """测试初始化"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        assert planner._tasks == {}
        assert planner._plans == {}

    def test_create_task(self):
        """测试创建任务"""
        from core.task_planner import TaskPlanner, TaskPriority
        planner = TaskPlanner()
        task_id = planner.create_task(
            name="Test task",
            priority=TaskPriority.HIGH,
        )
        assert task_id is not None
        task = planner.get_task(task_id)
        assert task is not None
        assert task.name == "Test task"
        assert task.priority == TaskPriority.HIGH

    def test_get_task_nonexistent(self):
        """测试获取不存在的任务"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task = planner.get_task("nonexistent")
        assert task is None

    def test_start_task(self):
        """测试开始任务"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task_id = planner.create_task(name="Test task")
        result = planner.start_task(task_id)
        assert result is True
        task = planner.get_task(task_id)
        assert task.status.value == "in_progress"

    def test_complete_task(self):
        """测试完成任务"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task_id = planner.create_task(name="Test task")
        planner.start_task(task_id)
        result = planner.complete_task(task_id, "Done!")
        assert result is True
        task = planner.get_task(task_id)
        assert task.status.value == "completed"

    def test_fail_task(self):
        """测试标记任务失败"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task_id = planner.create_task(name="Test task")
        planner.start_task(task_id)
        result = planner.fail_task(task_id, "Error occurred")
        assert result is True
        task = planner.get_task(task_id)
        assert task.status.value == "failed"

    def test_list_tasks(self):
        """测试列出任务"""
        from core.task_planner import TaskPlanner, TaskStatus, TaskPriority
        planner = TaskPlanner()
        planner.create_task(name="Task 1", priority=TaskPriority.HIGH)
        planner.create_task(name="Task 2", priority=TaskPriority.LOW)

        tasks = planner.list_tasks()
        assert len(tasks) == 2

        high_tasks = planner.list_tasks(priority=TaskPriority.HIGH)
        assert len(high_tasks) == 1

    def test_create_plan(self):
        """测试创建计划"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        result = planner.create_plan(
            goal="Test goal",
            tasks=[
                {"name": "Task 1"},
                {"name": "Task 2"},
            ],
        )
        assert result is not None
        assert result.plan.goal == "Test goal"
        assert len(result.execution_order) == 2

    def test_plan_progress(self):
        """测试计划进度"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        result = planner.create_plan(
            goal="Test goal",
            tasks=[
                {"name": "Task 1"},
                {"name": "Task 2"},
            ],
        )
        progress = planner.get_plan_progress(result.plan.plan_id)
        assert progress["total_tasks"] == 2
        assert progress["completed_tasks"] == 0
        assert progress["progress_percent"] == 0

    def test_statistics(self):
        """测试统计"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        planner.create_task(name="Task 1")
        planner.create_task(name="Task 2")
        stats = planner.get_statistics()
        assert stats["total_tasks"] == 2
        assert stats["tasks_created"] == 2

    def test_suggest_next_tasks(self):
        """测试建议下一个任务"""
        from core.task_planner import TaskPlanner, TaskPriority
        planner = TaskPlanner()
        planner.create_task(name="Low priority", priority=TaskPriority.LOW)
        planner.create_task(name="High priority", priority=TaskPriority.HIGH)

        suggestions = planner.suggest_next_tasks(limit=1)
        assert len(suggestions) == 1
        assert suggestions[0].name == "High priority"


class TestTaskPlannerDependencies:
    """测试依赖管理"""

    def test_dependencies_block_start(self):
        """测试依赖阻止开始"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task1_id = planner.create_task(name="Task 1")
        task2_id = planner.create_task(
            name="Task 2",
            dependencies=[task1_id],
        )

        # Task 2 应该被阻止
        result = planner.start_task(task2_id)
        assert result is False

    def test_dependencies_allow_after_complete(self):
        """测试依赖完成后允许"""
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        task1_id = planner.create_task(name="Task 1")
        task2_id = planner.create_task(
            name="Task 2",
            dependencies=[task1_id],
        )

        # 完成 Task 1
        planner.start_task(task1_id)
        planner.complete_task(task1_id)

        # Task 2 应该可以开始
        result = planner.start_task(task2_id)
        assert result is True


class TestTaskPlannerIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        from core.task_planner import TaskPlanner, TaskPriority

        planner = TaskPlanner()

        # 创建计划
        result = planner.create_plan(
            goal="Complete project",
            tasks=[
                {"name": "Design", "priority": TaskPriority.HIGH},
                {"name": "Implement", "priority": TaskPriority.HIGH},
                {"name": "Test", "priority": TaskPriority.MEDIUM},
            ],
            success_criteria=["All tasks completed"],
        )

        plan_id = result.plan.plan_id
        assert plan_id is not None

        # 获取进度
        progress = planner.get_plan_progress(plan_id)
        assert progress["total_tasks"] == 3

        # 完成任务
        for task_id in result.execution_order:
            planner.start_task(task_id)
            planner.complete_task(task_id, "Completed")

        # 检查进度
        progress = planner.get_plan_progress(plan_id)
        assert progress["completed_tasks"] == 3
        assert progress["progress_percent"] == 100

        # 获取统计
        stats = planner.get_statistics()
        assert stats["tasks_completed"] == 3
