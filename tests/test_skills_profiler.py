#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
能力画像测试

测试 core/skills_profiler.py 的功能
"""

import pytest
import sys
import os
import json
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skills_profiler import (
    SkillsProfiler,
    SkillsProfile,
    SkillEntry,
    EvolutionRecord,
    DEFAULT_SKILLS_MATRIX,
)


class TestSkillsProfiler:
    """能力画像测试类"""

    @pytest.fixture
    def temp_root(self, tmp_path):
        """创建临时项目根目录"""
        # 创建必要目录
        (tmp_path / "workspace" / "memory").mkdir(parents=True)
        return tmp_path

    @pytest.fixture
    def profiler(self, temp_root):
        """创建能力画像实例"""
        return SkillsProfiler(project_root=str(temp_root))

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init_creates_default_profile(self, temp_root):
        """测试初始化创建默认画像"""
        profiler = SkillsProfiler(project_root=str(temp_root))

        profile = profiler.get_profile()
        assert profile is not None
        assert profile.current_generation >= 1
        assert len(profile.skills_matrix) > 0

    def test_init_loads_existing_profile(self, temp_root):
        """测试初始化加载已有画像"""
        # 先创建并保存画像
        profiler1 = SkillsProfiler(project_root=str(temp_root))
        profiler1.update_skill_score("code_quality", 0.9)

        # 重新创建实例
        profiler2 = SkillsProfiler(project_root=str(temp_root))
        assert profiler2.get_skill_score("code_quality") == 0.9

    # =========================================================================
    # 查询接口测试
    # =========================================================================

    def test_get_profile(self, profiler):
        """测试获取能力画像"""
        profile = profiler.get_profile()
        assert isinstance(profile, SkillsProfile)

    def test_get_skill_score(self, profiler):
        """测试获取技能评分"""
        # 默认值应该存在
        score = profiler.get_skill_score("code_quality")
        assert 0.0 <= score <= 1.0

        # 不存在的技能
        score = profiler.get_skill_score("nonexistent")
        assert score == 0.0

    def test_get_skill_entry(self, profiler):
        """测试获取技能条目"""
        entry = profiler.get_skill_entry("code_quality")
        assert isinstance(entry, SkillEntry)
        assert entry.name == "代码质量"

    def test_get_skill_entry_nonexistent(self, profiler):
        """测试获取不存在的技能条目"""
        entry = profiler.get_skill_entry("nonexistent")
        assert entry is None

    def test_get_overall_score(self, profiler):
        """测试获取综合评分"""
        score = profiler.get_overall_score()
        assert 0.0 <= score <= 1.0

    def test_get_low_score_skills(self, profiler):
        """测试获取低分技能"""
        # 更新一个低分技能
        profiler.update_skill_score("code_quality", 0.3)

        low_skills = profiler.get_low_score_skills(threshold=0.6)
        assert "code_quality" in low_skills

    def test_get_next_targets(self, profiler):
        """测试获取下一阶段目标"""
        targets = profiler.get_next_targets()
        assert isinstance(targets, list)

    # =========================================================================
    # 更新接口测试
    # =========================================================================

    def test_update_skill_score(self, profiler):
        """测试更新技能评分"""
        result = profiler.update_skill_score("code_quality", 0.85)

        assert result is True
        assert profiler.get_skill_score("code_quality") == 0.85

        # 测试边界
        profiler.update_skill_score("code_quality", 1.5)
        assert profiler.get_skill_score("code_quality") == 1.0

        profiler.update_skill_score("code_quality", -0.5)
        assert profiler.get_skill_score("code_quality") == 0.0

    def test_update_skill_score_with_evidence(self, profiler):
        """测试更新技能评分并添加证据"""
        profiler.update_skill_score(
            "code_quality",
            0.8,
            evidence=["添加了单元测试"],
            weaknesses=["文档不足"],
        )

        entry = profiler.get_skill_entry("code_quality")
        assert "添加了单元测试" in entry.evidence
        assert "文档不足" in entry.weaknesses

    def test_update_skill_score_new_skill(self, profiler):
        """测试更新新技能"""
        result = profiler.update_skill_score("new_skill", 0.5)
        assert result is True
        assert profiler.get_skill_score("new_skill") == 0.5

    def test_update_next_targets(self, profiler):
        """测试更新下一阶段目标"""
        new_targets = ["目标1", "目标2", "目标3"]
        result = profiler.update_next_targets(new_targets)

        assert result is True
        assert profiler.get_next_targets() == new_targets

    def test_update_next_targets_limit(self, profiler):
        """测试目标数量限制"""
        many_targets = [f"目标{i}" for i in range(20)]
        profiler.update_next_targets(many_targets)

        targets = profiler.get_next_targets()
        assert len(targets) <= 10

    def test_mark_target_achieved(self, profiler):
        """测试标记目标已达成"""
        targets = ["目标1", "目标2"]
        profiler.update_next_targets(targets)

        result = profiler.mark_target_achieved("目标1")
        assert result is True
        assert "目标1" not in profiler.get_next_targets()

    def test_mark_target_not_found(self, profiler):
        """测试标记不存在的目标"""
        result = profiler.mark_target_achieved("不存在的目标")
        assert result is False

    def test_advance_generation(self, profiler):
        """测试推进世代"""
        initial_gen = profiler.get_profile().current_generation

        profiler.advance_generation()
        assert profiler.get_profile().current_generation == initial_gen + 1

    # =========================================================================
    # 进化历史测试
    # =========================================================================

    def test_add_evolution_record(self, profiler):
        """测试添加进化记录"""
        result = profiler.add_evolution_record(
            generation=1,
            focus="代码质量",
            improvement="添加单元测试",
            score_change=0.1,
        )

        assert result is True

        history = profiler.get_evolution_history()
        assert len(history) >= 1
        assert history[-1].focus == "代码质量"

    def test_get_evolution_history_limit(self, profiler):
        """测试获取进化历史限制"""
        # 添加多条记录
        for i in range(15):
            profiler.add_evolution_record(
                generation=i,
                focus=f"进化{i}",
                improvement=f"改进{i}",
            )

        history = profiler.get_evolution_history(limit=5)
        assert len(history) <= 5

    # =========================================================================
    # 报告生成测试
    # =========================================================================

    def test_generate_report(self, profiler):
        """测试生成能力画像报告"""
        report = profiler.generate_report()

        assert "# 虾宝能力画像" in report
        assert "能力矩阵" in report
        assert "下一步目标" in report

    def test_generate_report_has_scores(self, profiler):
        """测试报告包含评分信息"""
        report = profiler.generate_report()

        assert "代码质量" in report
        assert "综合评分" in report

    def test_export_json(self, profiler):
        """测试导出 JSON"""
        json_str = profiler.export_json()
        data = json.loads(json_str)

        assert "current_generation" in data
        assert "skills_matrix" in data
        assert "next_targets" in data

    # =========================================================================
    # 持久化测试
    # =========================================================================

    def test_profile_saved_to_file(self, temp_root):
        """测试画像保存到文件"""
        profiler = SkillsProfiler(project_root=str(temp_root))
        profiler.update_skill_score("code_quality", 0.95)

        # 检查文件存在
        profile_file = temp_root / "workspace" / "memory" / "skills_profile.json"
        assert profile_file.exists()

        # 重新加载验证
        profiler2 = SkillsProfiler(project_root=str(temp_root))
        assert profiler2.get_skill_score("code_quality") == 0.95

    # =========================================================================
    # 数据结构测试
    # =========================================================================

    def test_skill_entry_to_dict(self):
        """测试技能条目转字典"""
        entry = SkillEntry(
            name="代码质量",
            score=0.8,
            evidence=["测试通过"],
            weaknesses=["文档不足"],
        )

        data = entry.to_dict()
        assert data["name"] == "代码质量"
        assert data["score"] == 0.8

    def test_skills_profile_to_dict(self):
        """测试能力画像转字典"""
        profile = SkillsProfile(
            current_generation=1,
            skills_matrix={},
            evolution_history=[],
            next_targets=["目标1"],
        )

        data = profile.to_dict()
        assert data["current_generation"] == 1
        assert data["next_targets"] == ["目标1"]

    def test_evolution_record_to_dict(self):
        """测试进化记录转字典"""
        record = EvolutionRecord(
            generation=1,
            timestamp="2026-04-16",
            focus="代码质量",
            improvement="添加测试",
            score_change=0.1,
        )

        data = record.to_dict()
        assert data["generation"] == 1
        assert data["focus"] == "代码质量"


class TestDefaultSkillsMatrix:
    """默认技能矩阵测试"""

    def test_default_matrix_has_all_dimensions(self):
        """测试默认矩阵包含所有维度"""
        required_dims = [
            "code_quality",
            "test_coverage",
            "tool_usage",
            "autonomy",
            "memory_management",
            "security",
            "architecture",
            "learning",
            "planning",
            "execution",
        ]

        for dim in required_dims:
            assert dim in DEFAULT_SKILLS_MATRIX

    def test_default_scores_valid(self):
        """测试默认评分有效"""
        for name, entry in DEFAULT_SKILLS_MATRIX.items():
            assert 0.0 <= entry.score <= 1.0
            assert isinstance(entry.evidence, list)
            assert isinstance(entry.weaknesses, list)
