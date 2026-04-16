#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务分析器测试

测试 core/task_analyzer.py 的功能
"""

import pytest
import sys
import os
import json
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_analyzer import (
    TaskAnalyzer,
    TaskRecord,
    TaskStatus,
    TaskAnalysisReport,
)


class TestTaskAnalyzer:
    """任务分析器测试类"""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """创建分析器实例"""
        return TaskAnalyzer(project_root=str(tmp_path))

    # =========================================================================
    # 初始化测试
    # =========================================================================

    def test_init(self, analyzer):
        """测试初始化"""
        assert analyzer is not None
        assert analyzer._task_history == []

    def test_init_creates_directory(self, tmp_path):
        """测试初始化创建目录"""
        TaskAnalyzer(project_root=str(tmp_path))
        analysis_dir = tmp_path / "workspace" / "analytics"
        assert analysis_dir.exists()

    # =========================================================================
    # 任务记录测试
    # =========================================================================

    def test_record_task_start(self, analyzer):
        """测试记录任务开始"""
        analyzer.record_task_start(
            task_id=1,
            description="测试任务",
            complexity="medium",
        )

        assert len(analyzer._task_history) == 1
        record = analyzer._task_history[0]
        assert record.task_id == 1
        assert record.description == "测试任务"
        assert record.status == TaskStatus.IN_PROGRESS.value

    def test_record_task_completion(self, analyzer):
        """测试记录任务完成"""
        analyzer.record_task_start(task_id=1, description="测试任务")
        analyzer.record_task_completion(
            task_id=1,
            insights=["成功完成"],
        )

        record = analyzer._task_history[0]
        assert record.status == TaskStatus.COMPLETED.value
        assert "成功完成" in record.insights

    def test_record_task_failure(self, analyzer):
        """测试记录任务失败"""
        analyzer.record_task_start(task_id=1, description="测试任务")
        analyzer.record_task_failure(
            task_id=1,
            error="执行失败",
        )

        record = analyzer._task_history[0]
        assert record.status == TaskStatus.FAILED.value
        assert "执行失败" in record.errors

    def test_record_tool_call(self, analyzer):
        """测试记录工具调用"""
        analyzer.record_task_start(task_id=1, description="测试任务")
        analyzer.record_tool_call(
            task_id=1,
            tool_name="read_file",
            args={"path": "test.py"},
            success=True,
        )

        record = analyzer._task_history[0]
        assert len(record.tool_calls) == 1
        assert record.tool_calls[0]["tool"] == "read_file"

    # =========================================================================
    # 分析测试
    # =========================================================================

    def test_analyze_tasks_empty(self, analyzer):
        """测试分析空任务列表"""
        report = analyzer.analyze_tasks(generation=1)

        assert report.generation == 1
        assert report.total_tasks == 0
        assert report.completion_rate == 0.0

    def test_analyze_tasks_with_records(self, analyzer):
        """测试分析有记录的任务"""
        # 添加测试记录
        analyzer.record_task_start(task_id=1, description="任务1")
        analyzer.record_task_completion(task_id=1)

        analyzer.record_task_start(task_id=2, description="任务2")
        analyzer.record_task_failure(task_id=2, error="失败")

        report = analyzer.analyze_tasks(generation=1)

        assert report.total_tasks == 2
        assert report.completed_tasks == 1
        assert report.failed_tasks == 1
        assert report.completion_rate == 0.5

    def test_analyze_tasks_with_external_records(self, analyzer):
        """测试分析外部传入的任务记录"""
        records = [
            {
                "task_id": 1,
                "description": "外部任务1",
                "status": "completed",
                "complexity": "easy",
                "duration_seconds": 60.0,
            },
            {
                "task_id": 2,
                "description": "外部任务2",
                "status": "failed",
                "complexity": "hard",
                "duration_seconds": 120.0,
                "errors": ["错误1"],
            },
        ]

        report = analyzer.analyze_tasks(generation=1, task_records=records)

        assert report.total_tasks == 2
        assert report.completed_tasks == 1
        assert report.failed_tasks == 1

    def test_analyze_tasks_with_tool_calls(self, analyzer):
        """测试分析带工具调用的任务"""
        analyzer.record_task_start(task_id=1, description="任务1")
        analyzer.record_tool_call(task_id=1, tool_name="read_file", success=True)
        analyzer.record_tool_call(task_id=1, tool_name="edit_file", success=False)
        analyzer.record_task_completion(task_id=1)

        report = analyzer.analyze_tasks(generation=1)

        assert report.success_patterns or report.failure_patterns

    # =========================================================================
    # 复盘报告测试
    # =========================================================================

    def test_generate_retrospective(self, analyzer):
        """测试生成复盘报告"""
        analyzer.record_task_start(task_id=1, description="任务1")
        analyzer.record_task_completion(task_id=1)

        report = analyzer.generate_retrospective(generation=1)

        assert "# 任务执行复盘报告" in report
        assert "G1" in report
        assert "执行概览" in report

    def test_generate_retrospective_with_failures(self, analyzer):
        """测试生成带失败的复盘报告"""
        analyzer.record_task_start(task_id=1, description="成功任务")
        analyzer.record_task_completion(task_id=1)

        analyzer.record_task_start(task_id=2, description="失败任务")
        analyzer.record_task_failure(task_id=2, error="超时错误")

        report = analyzer.generate_retrospective(generation=1)

        assert "失败模式" in report
        assert "改进建议" in report

    # =========================================================================
    # 保存报告测试
    # =========================================================================

    def test_save_analysis(self, analyzer, tmp_path):
        """测试保存分析报告"""
        analyzer.record_task_start(task_id=1, description="任务1")
        analyzer.record_task_completion(task_id=1)

        report = analyzer.analyze_tasks(generation=1)
        filepath = analyzer.save_analysis(report)

        assert os.path.exists(filepath)

        # 验证保存的内容
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["generation"] == 1
        assert data["total_tasks"] == 1

    def test_save_analysis_custom_path(self, analyzer, tmp_path):
        """测试保存到自定义路径"""
        analyzer.record_task_start(task_id=1, description="任务1")
        analyzer.record_task_completion(task_id=1)

        report = analyzer.analyze_tasks(generation=1)
        custom_path = tmp_path / "custom_analysis.json"
        filepath = analyzer.save_analysis(report, filepath=custom_path)

        assert filepath == str(custom_path)
        assert os.path.exists(custom_path)

    # =========================================================================
    # 辅助方法测试
    # =========================================================================

    def test_classify_error(self, analyzer):
        """测试错误分类"""
        assert analyzer._classify_error("timeout error") == "超时"
        assert analyzer._classify_error("语法错误") == "语法错误"
        assert analyzer._classify_error("permission denied") == "权限错误"
        assert analyzer._classify_error("file not found") == "资源不存在"
        assert analyzer._classify_error("未知错误") == "其他错误"

    def test_format_duration(self, analyzer):
        """测试时长格式化"""
        assert "秒" in analyzer._format_duration(30)
        assert "分钟" in analyzer._format_duration(120)
        assert "小时" in analyzer._format_duration(3600)

    # =========================================================================
    # 模式识别测试
    # =========================================================================

    def test_identify_success_patterns(self, analyzer):
        """测试识别成功模式"""
        analyzer.record_task_start(task_id=1, description="任务", complexity="easy")
        analyzer.record_tool_call(task_id=1, tool_name="read_file", success=True)
        analyzer.record_tool_call(task_id=1, tool_name="read_file", success=True)
        analyzer.record_tool_call(task_id=1, tool_name="read_file", success=True)
        analyzer.record_task_completion(task_id=1, insights=["学到了"])

        report = analyzer.analyze_tasks(generation=1)
        assert isinstance(report.success_patterns, list)

    def test_identify_failure_patterns(self, analyzer):
        """测试识别失败模式"""
        analyzer.record_task_start(task_id=1, description="任务")
        analyzer.record_task_failure(task_id=1, error="timeout error")

        analyzer.record_task_start(task_id=2, description="任务")
        analyzer.record_tool_call(task_id=2, tool_name="read_file", success=False)
        analyzer.record_tool_call(task_id=2, tool_name="read_file", success=False)

        report = analyzer.analyze_tasks(generation=1)
        assert isinstance(report.failure_patterns, list)


class TestTaskRecord:
    """任务记录测试"""

    def test_task_record_creation(self):
        """测试创建任务记录"""
        record = TaskRecord(
            task_id=1,
            description="测试任务",
            status="pending",
            complexity="medium",
        )

        assert record.task_id == 1
        assert record.description == "测试任务"
        assert record.status == "pending"

    def test_task_record_with_metadata(self):
        """测试带元数据的任务记录"""
        record = TaskRecord(
            task_id=1,
            description="测试任务",
            status="completed",
            complexity="hard",
            duration_seconds=120.0,
            tool_calls=[{"tool": "read_file", "success": True}],
            errors=[],
            insights=["学到了一些"],
        )

        assert record.duration_seconds == 120.0
        assert len(record.tool_calls) == 1
        assert len(record.insights) == 1
