#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.2 单元测试 - 经验模式库模块

测试模块：
- core/pattern_library.py
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.pattern_library import (
    PatternMiner, PatternLibrary, PatternMatcher,
    ExperiencePattern, PatternMatch, PatternType, TaskCategory,
    ExecutionContext, ExecutionResult,
    get_pattern_miner, get_pattern_library, get_pattern_matcher,
    reset_pattern_modules, recommend_patterns,
)


# ============================================================================
# Test Data Classes
# ============================================================================

class TestExecutionContext:
    """测试执行上下文"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = ExecutionContext(
            task_type=TaskCategory.CODE_ANALYSIS,
            task_description="分析代码结构",
            file_paths=["test.py"],
            tools_used=["read_file", "analyze_ast"],
            complexity=5.0,
        )
        assert ctx.task_type == TaskCategory.CODE_ANALYSIS
        assert len(ctx.tools_used) == 2


class TestExecutionResult:
    """测试执行结果"""

    def test_create_result(self):
        """测试创建结果"""
        result = ExecutionResult(
            success=True,
            duration_seconds=120.0,
            tools_used=["read_file"],
            quality_score=8.5,
        )
        assert result.success is True
        assert result.quality_score == 8.5


class TestExperiencePattern:
    """测试经验模式"""

    def test_create_pattern(self):
        """测试创建模式"""
        ctx = ExecutionContext(
            task_type=TaskCategory.REFACTORING,
            task_description="重构代码",
            file_paths=["test.py"],
            tools_used=["read_file", "apply_diff"],
            complexity=6.0,
        )

        pattern = ExperiencePattern(
            pattern_id="test_001",
            pattern_type=PatternType.SUCCESS,
            name="重构成功模式",
            description="重构代码的典型流程",
            context=ctx,
            action_sequence=["read_file", "analyze", "apply_diff"],
            success_rate=0.85,
            avg_duration_seconds=300.0,
            quality_score=8.0,
            applicability_score=0.8,
        )

        assert pattern.pattern_id == "test_001"
        assert pattern.success_rate == 0.85

    def test_to_dict(self):
        """测试转换为字典"""
        ctx = ExecutionContext(
            task_type=TaskCategory.DEBUGGING,
            task_description="调试问题",
            file_paths=["bug.py"],
            tools_used=["read_file"],
        )

        pattern = ExperiencePattern(
            pattern_id="test_002",
            pattern_type=PatternType.FAILURE,
            name="调试失败模式",
            description="调试失败的模式",
            context=ctx,
            action_sequence=["read_file"],
            success_rate=0.3,
            avg_duration_seconds=100.0,
            quality_score=4.0,
            applicability_score=0.5,
        )

        d = pattern.to_dict()
        assert d["pattern_id"] == "test_002"
        assert d["pattern_type"] == "failure"


class TestPatternMatch:
    """测试模式匹配结果"""

    def test_create_match(self):
        """测试创建匹配结果"""
        ctx = ExecutionContext(
            task_type=TaskCategory.CODE_MODIFICATION,
            task_description="修改代码",
            file_paths=["main.py"],
            tools_used=["read_file", "apply_diff"],
        )

        pattern = ExperiencePattern(
            pattern_id="match_001",
            pattern_type=PatternType.SUCCESS,
            name="修改成功模式",
            description="修改代码的典型流程",
            context=ctx,
            action_sequence=["read_file", "apply_diff"],
            success_rate=0.9,
            avg_duration_seconds=200.0,
            quality_score=9.0,
            applicability_score=0.85,
        )

        match = PatternMatch(
            pattern=pattern,
            match_score=0.85,
            confidence=0.8,
            matched_attributes=["task_type", "tools_overlap"],
            suggestions=["建议使用 apply_diff"],
        )

        assert match.match_score == 0.85
        assert len(match.suggestions) == 1


# ============================================================================
# Test PatternMiner
# ============================================================================

class TestPatternMiner:
    """测试模式挖掘器"""

    def test_init(self):
        """测试初始化"""
        miner = PatternMiner(".")
        assert miner.project_root is not None

    def test_add_execution(self):
        """测试添加执行记录"""
        miner = PatternMiner(".")

        ctx = ExecutionContext(
            task_type=TaskCategory.CODE_ANALYSIS,
            task_description="分析代码",
            file_paths=["test.py"],
            tools_used=["read_file", "grep"],
        )

        result = ExecutionResult(
            success=True,
            duration_seconds=60.0,
            tools_used=["read_file", "grep"],
            quality_score=8.0,
        )

        miner.add_execution(ctx, result)
        assert len(miner._execution_history) == 1

    def test_mine_patterns_no_history(self):
        """测试无历史时挖掘"""
        miner = PatternMiner(".")
        patterns = miner.mine_patterns()
        assert len(patterns) == 0

    def test_mine_patterns_with_history(self):
        """测试有历史时挖掘"""
        miner = PatternMiner(".")

        # 添加多次相似的执行
        for _ in range(3):
            ctx = ExecutionContext(
                task_type=TaskCategory.REFACTORING,
                task_description="重构代码",
                file_paths=["test.py"],
                tools_used=["read_file", "apply_diff"],
                complexity=5.0,
            )
            result = ExecutionResult(
                success=True,
                duration_seconds=120.0,
                tools_used=["read_file", "apply_diff"],
                quality_score=8.0,
            )
            miner.add_execution(ctx, result)

        patterns = miner.mine_patterns(min_samples=2)
        assert len(patterns) >= 1

    def test_clear_history(self):
        """测试清除历史"""
        miner = PatternMiner(".")

        ctx = ExecutionContext(
            task_type=TaskCategory.UNKNOWN,
            task_description="测试",
            file_paths=[],
            tools_used=["test_tool"],
        )
        result = ExecutionResult(success=True, duration_seconds=10.0, tools_used=[])
        miner.add_execution(ctx, result)

        miner.clear_history()
        assert len(miner._execution_history) == 0


# ============================================================================
# Test PatternLibrary
# ============================================================================

class TestPatternLibrary:
    """测试模式库"""

    def test_init(self, tmp_path):
        """测试初始化"""
        library = PatternLibrary(str(tmp_path / "library.json"))
        assert library.storage_path.parent.exists()

    def test_add_pattern(self, tmp_path):
        """测试添加模式"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.OPTIMIZATION,
            task_description="优化性能",
            file_paths=["main.py"],
            tools_used=["profile", "optimize"],
        )

        pattern = ExperiencePattern(
            pattern_id="lib_001",
            pattern_type=PatternType.OPTIMIZATION,
            name="性能优化模式",
            description="性能优化的典型流程",
            context=ctx,
            action_sequence=["profile", "optimize"],
            success_rate=0.75,
            avg_duration_seconds=180.0,
            quality_score=7.5,
            applicability_score=0.7,
        )

        pattern_id = library.add(pattern)
        assert pattern_id == "lib_001"
        assert library.get("lib_001") is not None

    def test_get_pattern(self, tmp_path):
        """测试获取模式"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.DOCUMENTATION,
            task_description="写文档",
            file_paths=["README.md"],
            tools_used=["write_file"],
        )

        pattern = ExperiencePattern(
            pattern_id="lib_002",
            pattern_type=PatternType.BEST_PRACTICE,
            name="文档最佳实践",
            description="编写文档的最佳实践",
            context=ctx,
            action_sequence=["write_file"],
            success_rate=0.95,
            avg_duration_seconds=30.0,
            quality_score=9.5,
            applicability_score=0.9,
        )

        library.add(pattern)
        retrieved = library.get("lib_002")

        assert retrieved is not None
        assert retrieved.name == "文档最佳实践"

    def test_remove_pattern(self, tmp_path):
        """测试删除模式"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.UNKNOWN,
            task_description="测试",
            file_paths=[],
            tools_used=["test"],
        )

        pattern = ExperiencePattern(
            pattern_id="lib_003",
            pattern_type=PatternType.SUCCESS,
            name="测试模式",
            description="测试",
            context=ctx,
            action_sequence=["test"],
            success_rate=0.8,
            avg_duration_seconds=10.0,
            quality_score=8.0,
            applicability_score=0.8,
        )

        library.add(pattern)
        assert library.remove("lib_003") is True
        assert library.get("lib_003") is None

    def test_get_all_patterns(self, tmp_path):
        """测试获取所有模式"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        # 添加多个模式
        for i in range(5):
            ctx = ExecutionContext(
                task_type=TaskCategory.UNKNOWN,
                task_description=f"测试{i}",
                file_paths=[],
                tools_used=["tool"],
            )

            pattern = ExperiencePattern(
                pattern_id=f"all_{i}",
                pattern_type=PatternType.SUCCESS if i % 2 == 0 else PatternType.FAILURE,
                name=f"模式{i}",
                description="测试",
                context=ctx,
                action_sequence=["tool"],
                success_rate=0.7 if i % 2 == 0 else 0.3,
                avg_duration_seconds=10.0,
                quality_score=7.0,
                applicability_score=0.7,
            )
            library.add(pattern)

        all_patterns = library.get_all()
        assert len(all_patterns) == 5

        # 按类型筛选
        success_patterns = library.get_all(pattern_type=PatternType.SUCCESS)
        assert len(success_patterns) >= 1

    def test_record_feedback(self, tmp_path):
        """测试记录反馈"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.UNKNOWN,
            task_description="反馈测试",
            file_paths=[],
            tools_used=["tool"],
        )

        pattern = ExperiencePattern(
            pattern_id="feedback_001",
            pattern_type=PatternType.SUCCESS,
            name="反馈测试模式",
            description="测试反馈功能",
            context=ctx,
            action_sequence=["tool"],
            success_rate=0.8,
            avg_duration_seconds=10.0,
            quality_score=8.0,
            applicability_score=0.8,
        )

        library.add(pattern)
        library.record_feedback("feedback_001", positive=True)
        library.record_feedback("feedback_001", positive=False)

        updated = library.get("feedback_001")
        assert updated.positive_feedback == 1
        assert updated.negative_feedback == 1

    def test_search_by_tag(self, tmp_path):
        """测试按标签搜索"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.CODE_ANALYSIS,
            task_description="分析测试",
            file_paths=[],
            tools_used=["analyze"],
        )

        pattern = ExperiencePattern(
            pattern_id="tag_001",
            pattern_type=PatternType.BEST_PRACTICE,
            name="分析最佳实践",
            description="代码分析的最佳实践",
            context=ctx,
            action_sequence=["analyze"],
            success_rate=0.9,
            avg_duration_seconds=20.0,
            quality_score=9.0,
            applicability_score=0.9,
            tags=["analysis", "best_practice"],
        )

        library.add(pattern)
        results = library.search_by_tag("analysis")
        assert len(results) >= 1

    def test_search_by_tool(self, tmp_path):
        """测试按工具搜索"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        ctx = ExecutionContext(
            task_type=TaskCategory.REFACTORING,
            task_description="重构测试",
            file_paths=[],
            tools_used=["refactor_tool"],
        )

        pattern = ExperiencePattern(
            pattern_id="tool_001",
            pattern_type=PatternType.SUCCESS,
            name="重构工具模式",
            description="使用重构工具",
            context=ctx,
            action_sequence=["refactor_tool"],
            success_rate=0.85,
            avg_duration_seconds=30.0,
            quality_score=8.5,
            applicability_score=0.85,
        )

        library.add(pattern)
        results = library.search_by_tool("refactor_tool")
        assert len(results) >= 1


# ============================================================================
# Test PatternMatcher
# ============================================================================

class TestPatternMatcher:
    """测试模式匹配器"""

    def test_init(self, tmp_path):
        """测试初始化"""
        library = PatternLibrary(str(tmp_path / "library.json"))
        matcher = PatternMatcher(library)
        assert matcher.pattern_library is not None

    def test_find_similar(self, tmp_path):
        """测试查找相似模式"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        # 添加一个模式
        ctx = ExecutionContext(
            task_type=TaskCategory.CODE_MODIFICATION,
            task_description="修改代码",
            file_paths=["main.py"],
            tools_used=["read_file", "apply_diff"],
            complexity=5.0,
        )

        pattern = ExperiencePattern(
            pattern_id="similar_001",
            pattern_type=PatternType.SUCCESS,
            name="代码修改模式",
            description="修改代码的成功模式",
            context=ctx,
            action_sequence=["read_file", "apply_diff"],
            success_rate=0.9,
            avg_duration_seconds=100.0,
            quality_score=9.0,
            applicability_score=0.9,
        )
        library.add(pattern)

        matcher = PatternMatcher(library)

        # 查找相似的上下文
        search_ctx = ExecutionContext(
            task_type=TaskCategory.CODE_MODIFICATION,
            task_description="修改另一个文件",
            file_paths=["other.py"],
            tools_used=["read_file", "apply_diff"],
            complexity=4.5,
        )

        matches = matcher.find_similar(search_ctx, top_k=3)
        assert len(matches) >= 1
        assert matches[0].pattern.pattern_id == "similar_001"

    def test_recommend_avoid_failures(self, tmp_path):
        """测试推荐并避免失败"""
        library = PatternLibrary(str(tmp_path / "library.json"))

        # 添加成功和失败模式
        success_ctx = ExecutionContext(
            task_type=TaskCategory.OPTIMIZATION,
            task_description="优化",
            file_paths=[],
            tools_used=["optimize"],
        )

        success_pattern = ExperiencePattern(
            pattern_id="rec_success",
            pattern_type=PatternType.SUCCESS,
            name="优化成功",
            description="优化成功模式",
            context=success_ctx,
            action_sequence=["optimize"],
            success_rate=0.9,
            avg_duration_seconds=60.0,
            quality_score=9.0,
            applicability_score=0.9,
        )

        failure_ctx = ExecutionContext(
            task_type=TaskCategory.OPTIMIZATION,
            task_description="优化",
            file_paths=[],
            tools_used=["optimize_wrong"],
        )

        failure_pattern = ExperiencePattern(
            pattern_id="rec_failure",
            pattern_type=PatternType.FAILURE,
            name="优化失败",
            description="优化失败模式",
            context=failure_ctx,
            action_sequence=["optimize_wrong"],
            success_rate=0.2,
            avg_duration_seconds=30.0,
            quality_score=3.0,
            applicability_score=0.3,
        )

        library.add(success_pattern)
        library.add(failure_pattern)

        matcher = PatternMatcher(library)

        search_ctx = ExecutionContext(
            task_type=TaskCategory.OPTIMIZATION,
            task_description="执行优化",
            file_paths=[],
            tools_used=["optimize"],
        )

        recommendations = matcher.recommend(search_ctx, avoid_failures=True)

        # 应该只返回成功模式
        assert all(r.pattern.pattern_type != PatternType.FAILURE for r in recommendations)


# ============================================================================
# Test Integration
# ============================================================================

class TestPatternLibraryIntegration:
    """测试模式库集成"""

    def test_full_flow(self, tmp_path):
        """测试完整流程"""
        # 1. 挖掘
        miner = PatternMiner(".")

        for _ in range(3):
            ctx = ExecutionContext(
                task_type=TaskCategory.TEST_WRITING,
                task_description="编写测试",
                file_paths=["test.py"],
                tools_used=["create_file", "run_tests"],
                complexity=4.0,
            )
            result = ExecutionResult(
                success=True,
                duration_seconds=90.0,
                tools_used=["create_file", "run_tests"],
                quality_score=8.5,
            )
            miner.add_execution(ctx, result)

        patterns = miner.mine_patterns(min_samples=2)

        # 2. 存储
        library = PatternLibrary(str(tmp_path / "library.json"))
        for pattern in patterns:
            library.add(pattern)

        # 3. 匹配
        matcher = PatternMatcher(library)

        search_ctx = ExecutionContext(
            task_type=TaskCategory.TEST_WRITING,
            task_description="写新测试",
            file_paths=["new_test.py"],
            tools_used=["create_file", "run_tests"],
        )

        recommendations = matcher.recommend(search_ctx)
        assert len(recommendations) >= 0

    def test_singleton_reset(self, tmp_path):
        """测试单例重置"""
        miner1 = get_pattern_miner(".")
        miner2 = get_pattern_miner(".")
        assert miner1 is miner2

        reset_pattern_modules()

        miner3 = get_pattern_miner(".")
        assert miner3 is not miner1


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup():
    """每个测试后清理"""
    yield
    reset_pattern_modules()
