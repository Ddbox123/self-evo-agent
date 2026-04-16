#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自我分析器测试

测试 core/self_analyzer.py 的功能
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.self_analyzer import (
    SelfAnalyzer,
    CapabilityDimension,
    CapabilityScore,
    DIMENSION_WEIGHTS,
    SCORE_THRESHOLDS,
)


class TestSelfAnalyzer:
    """自我分析器测试类"""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """创建分析器实例"""
        return SelfAnalyzer(project_root=str(tmp_path))

    @pytest.fixture
    def project_analyzer(self):
        """创建使用实际项目的分析器"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return SelfAnalyzer(project_root=project_root)

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, analyzer):
        """测试初始化"""
        assert analyzer is not None
        assert analyzer.project_root is not None
        assert isinstance(analyzer._score_history, dict)
        assert len(analyzer._score_history) == 0

    def test_init_with_project_root(self, tmp_path):
        """测试使用指定项目根目录初始化"""
        analyzer = SelfAnalyzer(project_root=str(tmp_path))
        assert analyzer.project_root == tmp_path

    # =========================================================================
    # 能力维度测试
    # =========================================================================

    def test_capability_dimension_enum(self):
        """测试能力维度枚举"""
        assert CapabilityDimension.CODE_QUALITY.value == "code_quality"
        assert CapabilityDimension.TEST_COVERAGE.value == "test_coverage"
        assert CapabilityDimension.TOOL_USAGE.value == "tool_usage"
        assert CapabilityDimension.AUTONOMY.value == "autonomy"

    def test_dimension_weights(self):
        """测试维度权重"""
        assert len(DIMENSION_WEIGHTS) == 10
        total_weight = sum(DIMENSION_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01  # 权重总和应为 1

    def test_score_thresholds(self):
        """测试评分阈值"""
        assert SCORE_THRESHOLDS["excellent"] == 0.85
        assert SCORE_THRESHOLDS["good"] == 0.70
        assert SCORE_THRESHOLDS["fair"] == 0.50
        assert SCORE_THRESHOLDS["poor"] == 0.30

    # =========================================================================
    # CapabilityScore 测试
    # =========================================================================

    def test_capability_score_to_dict(self):
        """测试能力评分转换为字典"""
        score = CapabilityScore(
            dimension="code_quality",
            score=0.8,
            evidence=["代码规范"],
            weaknesses=["文档不足"],
        )
        data = score.to_dict()

        assert data["dimension"] == "code_quality"
        assert data["score"] == 0.8
        assert "代码规范" in data["evidence"]
        assert "文档不足" in data["weaknesses"]
        assert "last_updated" in data

    # =========================================================================
    # 辅助方法测试
    # =========================================================================

    def test_calculate_overall_score(self, analyzer):
        """测试综合得分计算"""
        scores = [
            CapabilityScore(dimension="code_quality", score=0.8),
            CapabilityScore(dimension="test_coverage", score=0.6),
            CapabilityScore(dimension="tool_usage", score=0.9),
        ]

        overall = analyzer._calculate_overall_score(scores)

        # 应该接近加权平均
        assert 0.0 <= overall <= 1.0

    def test_calculate_dimension_score(self, analyzer):
        """测试维度得分计算"""
        # 正信号多
        score1 = analyzer._calculate_dimension_score(3, 0, 0.5)
        assert score1 > 0.5

        # 负信号多
        score2 = analyzer._calculate_dimension_score(0, 3, 0.5)
        assert score2 < 0.5

        # 边界测试
        score3 = analyzer._calculate_dimension_score(0, 0, 0.5)
        assert score3 == 0.5

    def test_identify_strengths(self, analyzer):
        """测试优势识别"""
        scores = [
            CapabilityScore(dimension="code_quality", score=0.9),  # 优秀
            CapabilityScore(dimension="test_coverage", score=0.75),  # 良好
            CapabilityScore(dimension="tool_usage", score=0.5),  # 一般
        ]

        strengths = analyzer._identify_strengths(scores)

        assert len(strengths) >= 1
        assert any("code_quality" in s for s in strengths)

    def test_identify_weaknesses(self, analyzer):
        """测试劣势识别"""
        scores = [
            CapabilityScore(dimension="code_quality", score=0.3),  # 较差
            CapabilityScore(dimension="test_coverage", score=0.55),  # 一般
            CapabilityScore(dimension="tool_usage", score=0.8),  # 良好
        ]

        weaknesses = analyzer._identify_weaknesses(scores)

        assert len(weaknesses) >= 1
        assert any("code_quality" in w for w in weaknesses)

    def test_get_dimension_suggestions(self, analyzer):
        """测试获取维度建议"""
        suggestions = analyzer._get_dimension_suggestions("code_quality")
        assert len(suggestions) > 0
        assert any("文档" in s for s in suggestions)

        suggestions = analyzer._get_dimension_suggestions("nonexistent")
        assert len(suggestions) == 0

    def test_calculate_priority(self, analyzer):
        """测试优先级计算"""
        # 低于阈值
        priority = analyzer._calculate_priority(0.2, [])
        assert priority == "high"

        # 低于阈值
        priority = analyzer._calculate_priority(0.4, [])
        assert priority == "medium"

        # 高于阈值
        priority = analyzer._calculate_priority(0.6, [])
        assert priority == "low"

    # =========================================================================
    # 分析方法测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_analyze_code_quality(self, analyzer):
        """测试代码质量分析"""
        score = await analyzer._analyze_code_quality()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "code_quality"
        assert 0.0 <= score.score <= 1.0
        assert isinstance(score.evidence, list)

    @pytest.mark.asyncio
    async def test_analyze_test_coverage(self, analyzer):
        """测试测试覆盖分析"""
        score = await analyzer._analyze_test_coverage()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "test_coverage"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_tool_usage(self, analyzer):
        """测试工具使用分析"""
        score = await analyzer._analyze_tool_usage()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "tool_usage"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_autonomy(self, analyzer):
        """测试自主性分析"""
        score = await analyzer._analyze_autonomy()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "autonomy"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_memory_management(self, analyzer):
        """测试记忆管理分析"""
        score = await analyzer._analyze_memory_management()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "memory_management"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_security(self, analyzer):
        """测试安全性分析"""
        score = await analyzer._analyze_security()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "security"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_architecture(self, analyzer):
        """测试架构设计分析"""
        score = await analyzer._analyze_architecture()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "architecture"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_learning(self, analyzer):
        """测试学习能力分析"""
        score = await analyzer._analyze_learning()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "learning"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_planning(self, analyzer):
        """测试规划能力分析"""
        score = await analyzer._analyze_planning()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "planning"
        assert 0.0 <= score.score <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_execution(self, analyzer):
        """测试执行能力分析"""
        score = await analyzer._analyze_execution()

        assert isinstance(score, CapabilityScore)
        assert score.dimension == "execution"
        assert 0.0 <= score.score <= 1.0

    # =========================================================================
    # 综合分析测试
    # =========================================================================

    @pytest.mark.asyncio
    async def test_assess_capabilities(self, analyzer):
        """测试评估所有能力"""
        scores = await analyzer.assess_capabilities()

        assert len(scores) == 10  # 应该有 10 个维度
        assert all(isinstance(s, CapabilityScore) for s in scores)

        # 验证所有维度都有
        dimensions = {s.dimension for s in scores}
        expected_dimensions = {d.value for d in CapabilityDimension}
        assert dimensions == expected_dimensions

    @pytest.mark.asyncio
    async def test_generate_analysis_report(self, analyzer):
        """测试生成分析报告"""
        report = await analyzer.generate_analysis_report(generation=1)

        assert report.generation == 1
        assert isinstance(report.timestamp, str)
        assert 0.0 <= report.overall_score <= 1.0
        assert len(report.dimension_scores) == 10
        assert isinstance(report.strengths, list)
        assert isinstance(report.weaknesses, list)
        assert isinstance(report.recommendations, list)

    @pytest.mark.asyncio
    async def test_identify_improvement_opportunities(self, analyzer):
        """测试识别改进机会"""
        scores = await analyzer.assess_capabilities()
        opportunities = await analyzer.identify_improvement_opportunities(scores)

        assert isinstance(opportunities, list)
        # 低分维度应该有改进机会
        for opp in opportunities:
            assert "dimension" in opp
            assert "suggestions" in opp
            assert "priority" in opp

    @pytest.mark.asyncio
    async def test_analyze_codebase(self, analyzer):
        """测试代码库分析"""
        analysis = await analyzer.analyze_codebase()

        assert isinstance(analysis, dict)
        assert "total_files" in analysis
        assert "total_lines" in analysis
        assert "high_complexity_files" in analysis

    # =========================================================================
    # 复杂度计算测试
    # =========================================================================

    def test_calculate_complexity_simple(self, analyzer):
        """测试简单代码复杂度计算"""
        code = """
def foo():
    if a:
        return 1
    else:
        return 2
"""
        complexity = analyzer._calculate_complexity(code)
        assert complexity >= 1

    def test_calculate_complexity_with_loops(self, analyzer):
        """测试带循环的代码复杂度计算"""
        code = """
def foo():
    for i in range(10):
        if i > 5:
            while True:
                break
"""
        complexity = analyzer._calculate_complexity(code)
        assert complexity >= 2

    # =========================================================================
    # 历史追踪测试
    # =========================================================================

    def test_get_capability_trend(self, analyzer):
        """测试获取能力趋势"""
        # 添加测试数据
        score1 = CapabilityScore(dimension="code_quality", score=0.5)
        score2 = CapabilityScore(dimension="code_quality", score=0.6)

        analyzer._score_history["code_quality"] = [score1, score2]

        trend = analyzer.get_capability_trend("code_quality", limit=2)
        assert len(trend) == 2
        assert trend[-1].score == 0.6

    def test_get_capability_trend_empty(self, analyzer):
        """测试获取空能力趋势"""
        trend = analyzer.get_capability_trend("nonexistent")
        assert len(trend) == 0

    def test_get_improvement_rate(self, analyzer):
        """测试获取改进率"""
        # 添加测试数据
        score1 = CapabilityScore(dimension="code_quality", score=0.5)
        score2 = CapabilityScore(dimension="code_quality", score=0.6)

        analyzer._score_history["code_quality"] = [score1, score2]

        rate = analyzer.get_improvement_rate("code_quality")
        assert abs(rate - 0.1) < 0.001

    def test_get_improvement_rate_single(self, analyzer):
        """测试单条记录时无改进率"""
        score1 = CapabilityScore(dimension="code_quality", score=0.5)
        analyzer._score_history["code_quality"] = [score1]

        rate = analyzer.get_improvement_rate("code_quality")
        assert rate is None


class TestSelfAnalyzerIntegration:
    """自我分析器集成测试"""

    @pytest.fixture
    def analyzer(self):
        """创建使用实际项目的分析器"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return SelfAnalyzer(project_root=project_root)

    @pytest.mark.asyncio
    async def test_full_analysis_cycle(self, analyzer):
        """测试完整分析周期"""
        # 1. 评估能力
        scores = await analyzer.assess_capabilities()
        assert len(scores) == 10

        # 2. 生成报告
        report = await analyzer.generate_analysis_report(generation=1)
        assert report.overall_score > 0

        # 3. 识别改进机会
        opportunities = await analyzer.identify_improvement_opportunities(scores)
        assert isinstance(opportunities, list)

        # 4. 分析代码库
        code_insights = await analyzer.analyze_codebase()
        assert code_insights is not None

    @pytest.mark.asyncio
    async def test_report_to_dict(self, analyzer):
        """测试报告转换为字典"""
        report = await analyzer.generate_analysis_report(generation=1)
        data = report.to_dict()

        assert "generation" in data
        assert "overall_score" in data
        assert "dimension_scores" in data
        assert "strengths" in data
        assert "weaknesses" in data
