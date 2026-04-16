#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进化引擎测试

测试 core/evolution_engine.py 的功能
"""

import pytest
import sys
import os
import ast

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.evolution_engine import (
    EvolutionEngine,
    EvolutionPhase,
    EvolutionStatus,
    EvolutionPriority,
    Bottleneck,
    EvolutionGoal,
    EvolutionPlan,
    EvolutionContext,
    EvolutionResult,
    CodeModification,
)


class TestEvolutionEngine:
    """进化引擎测试类"""

    @pytest.fixture
    def engine(self, tmp_path):
        """创建进化引擎实例"""
        return EvolutionEngine(project_root=str(tmp_path))

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, engine):
        """测试初始化"""
        assert engine is not None
        assert engine._status == EvolutionStatus.IDLE
        assert engine._current_phase == EvolutionPhase.AWAKENING

    def test_init_creates_config(self, tmp_path):
        """测试初始化创建配置"""
        engine = EvolutionEngine(project_root=str(tmp_path))
        config_path = tmp_path / "workspace" / "evolution_config.json"
        # 配置文件不会立即创建，只在保存时创建
        assert engine._config is not None

    # =========================================================================
    # 状态管理测试
    # =========================================================================

    def test_get_evolution_status_idle(self, engine):
        """测试获取空闲状态"""
        status = engine.get_evolution_status()
        assert status["status"] == "idle"
        assert status["current_phase"] == "awakening"

    def test_pause_evolution(self, engine):
        """测试暂停进化"""
        engine._status = EvolutionStatus.RUNNING
        result = engine.pause_evolution()
        assert result is True
        assert engine._status == EvolutionStatus.PAUSED

    def test_pause_evolution_idle_fails(self, engine):
        """测试空闲状态暂停失败"""
        result = engine.pause_evolution()
        assert result is False

    def test_resume_evolution(self, engine):
        """测试恢复进化"""
        engine._status = EvolutionStatus.PAUSED
        result = engine.resume_evolution()
        assert result is True
        assert engine._status == EvolutionStatus.RUNNING

    def test_resume_evolution_not_paused_fails(self, engine):
        """测试非暂停状态恢复失败"""
        result = engine.resume_evolution()
        assert result is False

    def test_abort_evolution(self, engine):
        """测试中止进化"""
        engine._status = EvolutionStatus.RUNNING
        result = engine.abort_evolution("测试中止")
        assert result is True
        assert engine._status == EvolutionStatus.ABORTED

    # =========================================================================
    # 配置测试
    # =========================================================================

    def test_default_config(self, engine):
        """测试默认配置"""
        config = engine._config
        assert config["max_evolution_time"] == 1800
        assert config["max_modifications_per_cycle"] == 10
        assert config["min_success_rate"] == 0.8
        assert config["auto_verify"] is True
        assert config["backup_before_modify"] is True

    def test_load_config_from_file(self, tmp_path):
        """测试从文件加载配置"""
        config_file = tmp_path / "workspace" / "evolution_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)

        custom_config = {
            "max_evolution_time": 3600,
            "custom_setting": True,
        }
        import json
        with open(config_file, 'w') as f:
            json.dump(custom_config, f)

        engine = EvolutionEngine(project_root=str(tmp_path))
        assert engine._config["max_evolution_time"] == 3600
        assert engine._config["custom_setting"] is True

    # =========================================================================
    # 上下文测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_init_context(self, engine, tmp_path):
        """测试初始化上下文"""
        # 创建必要的文件
        (tmp_path / "workspace").mkdir(parents=True, exist_ok=True)
        memory_dir = tmp_path / "workspace" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # 创建简单的 memory.json
        import json
        with open(memory_dir / "memory.json", 'w') as f:
            json.dump({"current_generation": 1}, f)

        # 暂时替换 get_generation_tool
        import core.evolution_engine as ev
        original_import = ev.__dict__.get('get_generation_tool')

        def mock_get_generation():
            return 1

        ev.__dict__['get_generation_tool'] = mock_get_generation

        try:
            context = await engine._init_context()
            assert context.generation == 1
            assert context.current_phase == EvolutionPhase.AWAKENING
        finally:
            if original_import:
                ev.__dict__['get_generation_tool'] = original_import


class TestEvolutionPhase:
    """进化阶段测试"""

    def test_all_phases_defined(self):
        """测试所有阶段都已定义"""
        expected_phases = [
            "awakening", "self_analysis", "bottleneck_identification",
            "goal_generation", "planning", "execution", "verification",
            "memory_archive", "restart", "completed"
        ]
        actual_phases = [p.value for p in EvolutionPhase]
        for phase in expected_phases:
            assert phase in actual_phases


class TestEvolutionStatus:
    """进化状态测试"""

    def test_all_statuses_defined(self):
        """测试所有状态都已定义"""
        expected_statuses = ["idle", "running", "paused", "completed", "failed", "aborted"]
        actual_statuses = [s.value for s in EvolutionStatus]
        for status in expected_statuses:
            assert status in actual_statuses


class TestEvolutionPriority:
    """进化优先级测试"""

    def test_all_priorities_defined(self):
        """测试所有优先级都已定义"""
        expected_priorities = ["critical", "high", "medium", "low"]
        actual_priorities = [p.value for p in EvolutionPriority]
        for priority in expected_priorities:
            assert priority in actual_priorities


class TestBottleneck:
    """瓶颈测试"""

    def test_bottleneck_creation(self):
        """测试创建瓶颈"""
        bottleneck = Bottleneck(
            dimension="code_quality",
            description="代码质量不足",
            severity=0.7,
            evidence=["缺少文档", "无类型注解"],
        )
        assert bottleneck.dimension == "code_quality"
        assert bottleneck.severity == 0.7


class TestEvolutionGoal:
    """进化目标测试"""

    def test_goal_creation(self):
        """测试创建目标"""
        goal = EvolutionGoal(
            goal_id="goal_test_1",
            description="改进代码质量",
            target_dimension="code_quality",
            priority=EvolutionPriority.HIGH,
            estimated_effort=2.0,
        )
        assert goal.goal_id == "goal_test_1"
        assert goal.priority == EvolutionPriority.HIGH
        assert goal.status == "pending"

    def test_goal_with_criteria(self):
        """测试带成功标准的目标"""
        goal = EvolutionGoal(
            goal_id="goal_test_2",
            description="改进测试覆盖",
            target_dimension="test_coverage",
            priority=EvolutionPriority.MEDIUM,
            estimated_effort=3.0,
            success_criteria=["覆盖率 > 80%", "所有测试通过"],
        )
        assert len(goal.success_criteria) == 2


class TestEvolutionPlan:
    """进化计划测试"""

    def test_plan_creation(self):
        """测试创建计划"""
        goal = EvolutionGoal(
            goal_id="goal_test_1",
            description="测试目标",
            target_dimension="code_quality",
            priority=EvolutionPriority.HIGH,
            estimated_effort=2.0,
        )
        plan = EvolutionPlan(
            plan_id="plan_test_1",
            goal=goal,
            tasks=[
                {"id": "task_1", "description": "分析代码"},
            ],
        )
        assert plan.plan_id == "plan_test_1"
        assert len(plan.tasks) == 1


class TestEvolutionResult:
    """进化结果测试"""

    def test_result_success(self):
        """测试成功结果"""
        result = EvolutionResult(
            success=True,
            generation=1,
            goals_achieved=["goal_1", "goal_2"],
            summary="进化完成",
        )
        assert result.success is True
        assert len(result.goals_achieved) == 2

    def test_result_failure(self):
        """测试失败结果"""
        result = EvolutionResult(
            success=False,
            generation=1,
            summary="进化失败",
            details={"error": "测试错误"},
        )
        assert result.success is False
        assert result.details["error"] == "测试错误"


class TestCodeModification:
    """代码修改测试"""

    def test_modification_creation(self):
        """测试创建代码修改"""
        modification = CodeModification(
            file_path="test.py",
            modification_type="diff_edit",
            description="添加注释",
        )
        assert modification.file_path == "test.py"
        assert modification.verified is False

    def test_modification_with_diff(self):
        """测试带差异的修改"""
        modification = CodeModification(
            file_path="test.py",
            modification_type="diff_edit",
            description="添加注释",
            diff_content="+ # 新注释",
        )
        assert modification.diff_content is not None
