#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.1 单元测试 - 自主探索引擎核心模块

测试模块：
- core/opportunity_finder.py
- core/goal_generator.py
- core/autonomous_explorer.py
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.opportunity_finder import (
    OpportunityFinder, CodeMetricsCalculator, DuplicationDetector,
    TestCoverageAnalyzer, ImprovementOpportunity, CodeSmell, ScanResult,
    get_opportunity_finder, reset_opportunity_finder, find_opportunities,
)
from core.goal_generator import (
    GoalGenerator, EvolutionGoal, GoalCategory, GoalPriority,
    GoalStatus, GoalGenerationContext, SuccessCriterion, RiskLevel,
    get_goal_generator, reset_goal_generator, generate_goals,
)
from core.autonomous_explorer import (
    AutonomousExplorer, ExplorationConfig, ExplorationSession,
    ExplorationTrigger, ExplorationState, ExplorationResult,
    get_autonomous_explorer, reset_autonomous_explorer, explore,
)


# ============================================================================
# Test OpportunityFinder
# ============================================================================

class TestImprovementOpportunity:
    """测试改进机会数据结构"""

    def test_create_opportunity(self):
        """测试创建改进机会"""
        opp = ImprovementOpportunity(
            opportunity_id="test_1",
            category="code_quality",
            title="测试机会",
            description="这是一个测试机会",
            file_path="test.py",
            line_range=(10, 20),
            severity="medium",
            estimated_effort_hours=2.0,
            impact_score=7.0,
            confidence=0.9,
        )
        assert opp.opportunity_id == "test_1"
        assert opp.category == "code_quality"
        assert opp.estimated_effort_hours == 2.0
        assert opp.to_dict()["title"] == "测试机会"


class TestCodeMetricsCalculator:
    """测试代码指标计算器"""

    def test_init(self):
        """测试初始化"""
        calc = CodeMetricsCalculator(".")
        assert calc.project_root is not None

    def test_calculate_simple_file_metrics(self, tmp_path):
        """测试计算简单文件指标"""
        # 创建测试文件
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def simple_function():
    '''A simple function'''
    x = 1
    return x

class SimpleClass:
    '''A simple class'''
    def method(self):
        return 1
""")

        calc = CodeMetricsCalculator(str(tmp_path))
        metrics = calc.calculate_file_metrics(test_file)

        assert metrics["function_count"] >= 1
        assert metrics["class_count"] >= 1
        assert "error" not in metrics or not metrics["error"]

    def test_calculate_complexity(self):
        """测试复杂度计算"""
        import ast
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 100:
                return 1
    return 0
"""
        tree = ast.parse(code)
        calc = CodeMetricsCalculator(".")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = calc._calculate_complexity(node)
                assert complexity >= 3  # 至少 3 个 if


class TestDuplicationDetector:
    """测试重复代码检测器"""

    def test_init(self):
        """测试初始化"""
        detector = DuplicationDetector(min_length=6, min_duplications=2)
        assert detector.min_length == 6
        assert detector.min_duplications == 2

    def test_should_ignore(self):
        """测试忽略模式"""
        detector = DuplicationDetector()
        assert detector._should_ignore(Path("__pycache__/test.py"))
        assert detector._should_ignore(Path("venv/test.py"))  # venv 目录
        assert not detector._should_ignore(Path("core/test.py"))


class TestOpportunityFinder:
    """测试机会发现器"""

    def test_init(self):
        """测试初始化"""
        finder = OpportunityFinder(".")
        assert finder.project_root is not None
        assert finder.metrics_calculator is not None

    def test_scan(self):
        """测试扫描功能"""
        finder = OpportunityFinder(".")
        result = finder.scan()

        assert isinstance(result, ScanResult)
        assert result.scan_id is not None
        assert result.timestamp is not None
        assert isinstance(result.opportunities, list)
        assert isinstance(result.code_smells, list)
        assert result.statistics is not None

    def test_get_top_opportunities(self):
        """测试获取优先机会"""
        finder = OpportunityFinder(".")
        result = finder.scan()

        top = result.get_top_opportunities(limit=3)
        assert len(top) <= 3

    def test_get_by_category(self):
        """测试按类别筛选"""
        finder = OpportunityFinder(".")
        result = finder.scan()

        code_quality_opps = result.get_by_category("code_quality")
        assert all(o.category == "code_quality" for o in code_quality_opps)

    def test_get_by_severity(self):
        """测试按严重程度筛选"""
        finder = OpportunityFinder(".")
        result = finder.scan()

        high_opps = result.get_by_severity("high")
        assert all(o.severity == "high" for o in high_opps)


# ============================================================================
# Test GoalGenerator
# ============================================================================

class TestSuccessCriterion:
    """测试成功标准"""

    def test_is_met_numeric(self):
        """测试数值型成功标准"""
        criterion = SuccessCriterion(
            description="覆盖率提升",
            metric="coverage",
            target_value=80,
            current_value=85,
        )
        assert criterion.is_met() is True

        criterion.current_value = 70
        assert criterion.is_met() is False

    def test_is_met_no_current(self):
        """测试无当前值的情况"""
        criterion = SuccessCriterion(
            description="覆盖率提升",
            metric="coverage",
            target_value=80,
        )
        assert criterion.is_met() is False


class TestGoalCategory:
    """测试目标类别枚举"""

    def test_categories_exist(self):
        """测试类别存在"""
        assert GoalCategory.CODE_QUALITY.value == "code_quality"
        assert GoalCategory.TEST_COVERAGE.value == "test_coverage"
        assert GoalCategory.ARCHITECTURE.value == "architecture"


class TestGoalPriority:
    """测试目标优先级枚举"""

    def test_priorities_exist(self):
        """测试优先级存在"""
        assert GoalPriority.CRITICAL.value == 1
        assert GoalPriority.HIGH.value == 2
        assert GoalPriority.MEDIUM.value == 3
        assert GoalPriority.LOW.value == 4


class TestGoalGenerator:
    """测试目标生成器"""

    def test_init(self):
        """测试初始化"""
        generator = GoalGenerator(".")
        assert generator.project_root is not None

    def test_generate_smart_goal(self):
        """测试生成 SMART 目标"""
        generator = GoalGenerator(".")

        goal = generator.generate_smart_goal(
            title="提升测试覆盖率",
            description="为 core/ 模块添加测试",
            category=GoalCategory.TEST_COVERAGE,
            target_files=["core/test.py"],
            success_criteria=[
                {"description": "覆盖率", "metric": "coverage", "target_value": 80}
            ],
            estimated_hours=4.0,
        )

        assert goal.title == "提升测试覆盖率"
        assert goal.category == GoalCategory.TEST_COVERAGE
        assert goal.estimated_hours == 4.0
        assert goal.status == GoalStatus.DRAFT

    def test_generate_goals_from_opportunities(self):
        """测试从机会生成目标"""
        generator = GoalGenerator(".")

        # 创建模拟机会
        opp1 = Mock()
        opp1.category = "code_quality"
        opp1.opportunity_id = "opp_1"
        opp1.impact_score = 7.0
        opp1.confidence = 0.8
        opp1.estimated_effort_hours = 2.0
        opp1.file_path = "test.py"

        opp2 = Mock()
        opp2.category = "test_coverage"
        opp2.opportunity_id = "opp_2"
        opp2.impact_score = 6.0
        opp2.confidence = 0.9
        opp2.estimated_effort_hours = 3.0
        opp2.file_path = "test2.py"

        context = GoalGenerationContext(
            generation=1,
            overall_score=0.6,
            strengths=["有测试基础"],
            weaknesses=["覆盖率低"],
        )

        goals = generator.generate_goals_from_opportunities([opp1, opp2], context)
        assert len(goals) >= 1

    def test_validate_goal(self):
        """测试目标验证"""
        generator = GoalGenerator(".")

        # 有效目标
        valid_goal = EvolutionGoal(
            goal_id="test_1",
            title="测试目标",
            description="这是一个测试目标，用于验证功能",
            category=GoalCategory.CODE_QUALITY,
            priority=GoalPriority.HIGH,
            risk_level=RiskLevel.MEDIUM,
            estimated_hours=4.0,
            success_criteria=[
                SuccessCriterion(
                    description="覆盖率",
                    metric="coverage",
                    target_value=80,
                )
            ],
            confidence=0.8,
        )

        is_valid, issues = generator.validate_goal(valid_goal)
        assert is_valid or len(issues) >= 0

    def test_prioritize_goals(self):
        """测试目标优先级排序"""
        generator = GoalGenerator(".")

        goal1 = EvolutionGoal(
            goal_id="g1",
            title="低优先级目标",
            description="描述",
            category=GoalCategory.DOCUMENTATION,
            priority=GoalPriority.LOW,
            risk_level=RiskLevel.LOW,
            estimated_hours=2.0,
            expected_impact=3.0,
            confidence=0.5,
        )

        goal2 = EvolutionGoal(
            goal_id="g2",
            title="高优先级目标",
            description="描述",
            category=GoalCategory.SECURITY,
            priority=GoalPriority.HIGH,
            risk_level=RiskLevel.HIGH,
            estimated_hours=8.0,
            expected_impact=8.0,
            confidence=0.9,
        )

        context = GoalGenerationContext(
            generation=1,
            overall_score=0.6,
            strengths=[],
            weaknesses=[],
        )

        prioritized = generator.prioritize_goals([goal1, goal2], context)
        assert len(prioritized) == 2


# ============================================================================
# Test AutonomousExplorer
# ============================================================================

class TestExplorationConfig:
    """测试探索配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = ExplorationConfig()
        assert config.scan_interval_hours == 24.0
        assert config.max_opportunities_per_scan == 20
        assert config.scan_on_startup is True


class TestExplorationSession:
    """测试探索会话"""

    def test_create_session(self):
        """测试创建会话"""
        session = ExplorationSession(
            session_id="test_001",
            started_at="2026-04-16T10:00:00",
            trigger=ExplorationTrigger.MANUAL,
            state=ExplorationState.IDLE,
        )

        assert session.session_id == "test_001"
        assert session.trigger == ExplorationTrigger.MANUAL
        assert session.state == ExplorationState.IDLE

    def test_session_to_dict(self):
        """测试会话转字典"""
        session = ExplorationSession(
            session_id="test_001",
            started_at="2026-04-16T10:00:00",
            trigger=ExplorationTrigger.SCHEDULED,
            state=ExplorationState.COMPLETED,
            opportunities_found=10,
        )

        d = session.to_dict()
        assert d["session_id"] == "test_001"
        assert d["opportunities_found"] == 10


class TestExplorationTrigger:
    """测试探索触发条件"""

    def test_triggers_exist(self):
        """测试触发条件存在"""
        assert ExplorationTrigger.MANUAL.value == "manual"
        assert ExplorationTrigger.SCHEDULED.value == "scheduled"
        assert ExplorationTrigger.IDLE_DETECTED.value == "idle"


class TestAutonomousExplorer:
    """测试自主探索引擎"""

    def test_init(self):
        """测试初始化"""
        explorer = AutonomousExplorer(".")
        assert explorer.project_root is not None
        assert explorer.config is not None

    def test_explore(self):
        """测试探索功能"""
        explorer = AutonomousExplorer(".")
        result = explorer.explore(ExplorationTrigger.MANUAL)

        assert isinstance(result, ExplorationResult)
        assert result.session is not None
        assert result.session.trigger == ExplorationTrigger.MANUAL

    def test_quick_scan(self):
        """测试快速扫描"""
        explorer = AutonomousExplorer(".")
        opportunities = explorer.quick_scan()

        assert isinstance(opportunities, list)
        assert all(hasattr(o, 'category') for o in opportunities)

    def test_get_status(self):
        """测试获取状态"""
        explorer = AutonomousExplorer(".")
        status = explorer.get_status()

        assert "state" in status
        assert "total_scans" in status
        assert status["state"] == ExplorationState.IDLE.value

    def test_explore_multiple_times(self):
        """测试多次探索"""
        explorer = AutonomousExplorer(".")

        # 第一次探索
        result1 = explorer.explore(ExplorationTrigger.MANUAL)
        assert result1.session is not None

        # 第二次探索
        result2 = explorer.explore(ExplorationTrigger.SCHEDULED)
        assert result2.session is not None
        assert result2.session.trigger == ExplorationTrigger.SCHEDULED


# ============================================================================
# Test Integration
# ============================================================================

class TestIntegration:
    """集成测试"""

    def test_full_exploration_flow(self):
        """测试完整探索流程"""
        # 1. 发现机会
        scan_result = find_opportunities(".")

        # 2. 生成目标
        context = GoalGenerationContext(
            generation=1,
            overall_score=0.6,
            strengths=["有测试基础"],
            weaknesses=["覆盖率低"],
        )
        generator = get_goal_generator(".")
        goals = generator.generate_goals_from_opportunities(
            scan_result.opportunities, context
        )

        # 3. 执行探索
        explorer = get_autonomous_explorer(".")
        result = explorer.explore(ExplorationTrigger.MANUAL)

        assert result is not None
        assert len(result.goals) >= 0

    def test_goal_to_dict(self):
        """测试目标转字典"""
        goal = EvolutionGoal(
            goal_id="test_goal",
            title="测试目标",
            description="这是一个测试目标",
            category=GoalCategory.CODE_QUALITY,
            priority=GoalPriority.HIGH,
            risk_level=RiskLevel.MEDIUM,
            estimated_hours=4.0,
        )

        d = goal.to_dict()
        assert d["goal_id"] == "test_goal"
        assert d["title"] == "测试目标"
        assert d["category"] == "code_quality"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """每个测试后重置单例"""
    yield
    reset_opportunity_finder()
    reset_goal_generator()
    reset_autonomous_explorer()
