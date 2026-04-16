#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构规划器测试

测试 core/refactoring_planner.py 的功能
"""

import pytest
import sys
import os
import ast

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.refactoring_planner import (
    RefactoringPlanner,
    RefactoringOpportunity,
    RefactoringTask,
    RefactoringPlan,
    CODE_SMELLS,
)


class TestRefactoringPlanner:
    """重构规划器测试类"""

    @pytest.fixture
    def planner(self, tmp_path):
        """创建重构规划器实例"""
        return RefactoringPlanner(project_root=str(tmp_path))

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, planner):
        """测试初始化"""
        assert planner is not None
        assert planner.project_root is not None
        assert planner._opportunities == []

    # =========================================================================
    # 任务生成测试
    # =========================================================================

    def test_generate_tasks(self, planner):
        """测试生成重构任务"""
        opportunities = [
            RefactoringOpportunity(
                opportunity_id="opp_1",
                file_path="test.py",
                code_smell="god_class",
                severity="high",
                description="文件过长",
                estimated_lines=0,
                estimated_effort=2.0,
            ),
            RefactoringOpportunity(
                opportunity_id="opp_2",
                file_path="test2.py",
                code_smell="long_method",
                severity="medium",
                description="方法过长",
                estimated_lines=0,
                estimated_effort=1.5,
            ),
        ]

        tasks = planner._generate_tasks(opportunities)

        assert len(tasks) == 2
        assert tasks[0].priority == "high"
        assert tasks[1].priority == "medium"

    def test_generate_tasks_limit(self, planner):
        """测试任务数量限制"""
        opportunities = [
            RefactoringOpportunity(
                opportunity_id=f"opp_{i}",
                file_path=f"test{i}.py",
                code_smell="god_class",
                severity="high",
                description="测试",
                estimated_lines=0,
                estimated_effort=1.0,
            )
            for i in range(20)
        ]

        tasks = planner._generate_tasks(opportunities)
        assert len(tasks) == 10  # 限制为10个

    # =========================================================================
    # 风险评估测试
    # =========================================================================

    def test_assess_risk_level_high(self, planner):
        """测试高风险评估"""
        opportunities = [
            RefactoringOpportunity(
                opportunity_id=f"opp_{i}",
                file_path=f"test{i}.py",
                code_smell="god_class",
                severity="high",
                description="测试",
                estimated_lines=0,
                estimated_effort=1.0,
            )
            for i in range(10)
        ]

        risk = planner._assess_risk_level(opportunities)
        assert risk == "high"

    def test_assess_risk_level_medium(self, planner):
        """测试中等风险评估"""
        opportunities = [
            RefactoringOpportunity(
                opportunity_id=f"opp_{i}",
                file_path=f"test{i}.py",
                code_smell="god_class",
                severity="high",
                description="测试",
                estimated_lines=0,
                estimated_effort=1.0,
            )
            for i in range(3)
        ]

        risk = planner._assess_risk_level(opportunities)
        assert risk == "medium"

    def test_assess_risk_level_low(self, planner):
        """测试低风险评估"""
        opportunities = [
            RefactoringOpportunity(
                opportunity_id="opp_1",
                file_path="test.py",
                code_smell="magic_numbers",
                severity="low",
                description="测试",
                estimated_lines=0,
                estimated_effort=0.5,
            )
        ]

        risk = planner._assess_risk_level(opportunities)
        assert risk == "low"

    # =========================================================================
    # 复杂度计算测试
    # =========================================================================

    def test_calculate_complexity_simple(self, planner):
        """测试简单复杂度计算"""
        code = """
def foo():
    if a:
        return 1
    return 0
"""
        tree = ast.parse(code)
        complexity = planner._calculate_complexity(tree)
        assert complexity >= 2

    def test_calculate_complexity_nested(self, planner):
        """测试嵌套复杂度计算"""
        code = """
def foo():
    if a:
        if b:
            if c:
                while True:
                    break
    return 0
"""
        tree = ast.parse(code)
        complexity = planner._calculate_complexity(tree)
        assert complexity >= 4

    # =========================================================================
    # 获取 Python 文件测试
    # =========================================================================

    def test_get_python_files(self, planner, tmp_path):
        """测试获取 Python 文件"""
        # 创建测试文件
        (tmp_path / "test1.py").write_text("def foo(): pass")
        (tmp_path / "test2.py").write_text("def bar(): pass")
        (tmp_path / "test.md").write_text("# Test")

        files = planner._get_python_files()
        assert len(files) >= 2
        assert all(str(f).endswith('.py') for f in files)


class TestCodeSmells:
    """代码坏味道定义测试"""

    def test_all_smells_defined(self):
        """测试所有坏味道都已定义"""
        expected_smells = [
            "god_class", "long_method", "high_complexity",
            "duplicated_code", "dead_code", "magic_numbers",
            "long_parameter_list"
        ]
        for smell in expected_smells:
            assert smell in CODE_SMELLS

    def test_smell_structure(self):
        """测试坏味道结构"""
        for smell_name, smell_info in CODE_SMELLS.items():
            assert "name" in smell_info
            assert "description" in smell_info
            assert "threshold" in smell_info
            assert "approach" in smell_info


class TestRefactoringOpportunity:
    """重构机会测试"""

    def test_opportunity_creation(self):
        """测试创建重构机会"""
        opp = RefactoringOpportunity(
            opportunity_id="opp_1",
            file_path="test.py",
            code_smell="god_class",
            severity="high",
            description="文件过长",
            estimated_lines=100,
            estimated_effort=2.0,
            benefits=["提高可维护性"],
            risks=["可能引入错误"],
        )
        assert opp.opportunity_id == "opp_1"
        assert opp.severity == "high"


class TestRefactoringTask:
    """重构任务测试"""

    def test_task_creation(self):
        """测试创建重构任务"""
        task = RefactoringTask(
            task_id="task_1",
            description="重构测试",
            file_path="test.py",
            estimated_time=1.0,
            priority="high",
        )
        assert task.task_id == "task_1"
        assert task.priority == "high"


class TestRefactoringPlan:
    """重构计划测试"""

    def test_plan_creation(self):
        """测试创建重构计划"""
        goal = RefactoringOpportunity(
            opportunity_id="opp_1",
            file_path="test.py",
            code_smell="god_class",
            severity="high",
            description="文件过长",
            estimated_lines=0,
            estimated_effort=2.0,
        )

        plan = RefactoringPlan(
            plan_id="plan_1",
            goal_description="改进代码质量",
            opportunities=[goal],
            total_estimated_time=2.0,
            risk_level="medium",
        )
        assert plan.plan_id == "plan_1"
        assert len(plan.opportunities) == 1


class TestOpportunitiesSummary:
    """重构机会摘要测试"""

    def test_empty_summary(self, tmp_path):
        """测试空摘要"""
        planner = RefactoringPlanner(project_root=str(tmp_path))
        summary = planner.get_opportunities_summary()
        assert summary["total"] == 0

    def test_summary_with_opportunities(self, tmp_path):
        """测试带机会的摘要"""
        planner = RefactoringPlanner(project_root=str(tmp_path))
        opportunities = [
            RefactoringOpportunity(
                opportunity_id="opp_1",
                file_path="test.py",
                code_smell="god_class",
                severity="high",
                description="测试",
                estimated_lines=0,
                estimated_effort=2.0,
            ),
            RefactoringOpportunity(
                opportunity_id="opp_2",
                file_path="test2.py",
                code_smell="long_method",
                severity="medium",
                description="测试",
                estimated_lines=0,
                estimated_effort=1.0,
            ),
        ]
        planner._opportunities = opportunities

        summary = planner.get_opportunities_summary()
        assert summary["total"] == 2
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["medium"] == 1
        assert summary["estimated_total_time"] == 3.0
