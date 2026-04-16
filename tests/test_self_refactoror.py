#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 8.6 单元测试 - 自我重构系统模块
"""

import pytest
import sys
import os
from pathlib import Path

test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(test_dir)
sys.path.insert(0, project_root)

from core.self_refactoror import (
    RefactorType, RefactorStatus,
    RefactorOpportunity, RefactorPlan, RefactorResult, EvolutionRecord,
    RefactorValidator, SelfRefactoror, EvolutionTracker,
    get_refactoror, get_validator, get_tracker, reset_refactor_modules,
)


class TestDataClasses:
    def test_refactor_opportunity(self):
        opp = RefactorOpportunity(
            opportunity_id="ref_001",
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test.py",
            location=(10, 20),
            description="Test opportunity",
            original_code="def test(): pass",
            confidence=0.9,
            estimated_hours=1.0,
        )
        assert opp.opportunity_id == "ref_001"
        assert opp.refactor_type == RefactorType.EXTRACT_METHOD

    def test_refactor_result(self):
        result = RefactorResult(
            opportunity_id="ref_001",
            status=RefactorStatus.PENDING,
            success=False,
        )
        assert result.opportunity_id == "ref_001"
        assert result.status == RefactorStatus.PENDING

    def test_evolution_record(self):
        record = EvolutionRecord(
            record_id="evo_001",
            timestamp="2026-04-16T10:00:00",
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test.py",
            before_metrics={"lines": 100},
            after_metrics={"lines": 80},
            improvements=["lines reduced"],
            success=True,
        )
        assert record.record_id == "evo_001"
        assert record.success is True


class TestRefactorValidator:
    def test_init(self):
        validator = RefactorValidator(".")
        assert validator.project_root is not None

    def test_validate_valid_syntax(self):
        validator = RefactorValidator(".")
        is_valid, error = validator.validate_syntax("def test(): pass")
        assert is_valid is True
        assert error is None

    def test_validate_invalid_syntax(self):
        validator = RefactorValidator(".")
        is_valid, error = validator.validate_syntax("def test(: pass")
        assert is_valid is False
        assert error is not None

    def test_validate_imports(self, tmp_path):
        validator = RefactorValidator(str(tmp_path))
        test_file = tmp_path / "test_imports.py"
        test_file.write_text("import os\nimport sys\n")

        is_valid, errors = validator.validate_imports(str(test_file))
        assert is_valid is True


class TestSelfRefactoror:
    def test_init(self):
        refactoror = SelfRefactoror(".")
        assert refactoror.project_root is not None
        assert refactoror.validator is not None

    def test_find_opportunities(self):
        refactoror = SelfRefactoror(".")
        opportunities = refactoror.find_opportunities()
        assert isinstance(opportunities, list)

    def test_should_ignore(self):
        refactoror = SelfRefactoror(".")
        assert refactoror._should_ignore(Path("__pycache__/test.py")) is True
        assert refactoror._should_ignore(Path("tests/test.py")) is True
        assert refactoror._should_ignore(Path("core/test.py")) is False

    def test_apply_refactor_dry_run(self, tmp_path):
        refactoror = SelfRefactoror(str(tmp_path))

        test_file = tmp_path / "test_code.py"
        test_file.write_text("def test_function():\n    pass\n")

        opp = RefactorOpportunity(
            opportunity_id="dry_001",
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path=str(test_file),
            location=(1, 2),
            description="Test dry run",
            original_code="def test_function():\n    pass",
        )

        result = refactoror.apply_refactor(opp, dry_run=True)
        assert result.success is True
        assert result.status == RefactorStatus.VALIDATED

    def test_apply_refactor_invalid_opportunity(self, tmp_path):
        refactoror = SelfRefactoror(str(tmp_path))

        test_file = tmp_path / "test_code.py"
        test_file.write_text("valid code\n")

        opp = RefactorOpportunity(
            opportunity_id="invalid_001",
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path=str(test_file),
            location=(1, 0),
            description="Invalid opportunity",
            original_code="",
        )

        result = refactoror.apply_refactor(opp, dry_run=False)
        assert result.status == RefactorStatus.FAILED


class TestEvolutionTracker:
    def test_init(self, tmp_path):
        tracker = EvolutionTracker(str(tmp_path / "records.json"))
        assert tracker.storage_path.parent.exists()

    def test_record_refactor(self, tmp_path):
        tracker = EvolutionTracker(str(tmp_path / "records.json"))

        record_id = tracker.record_refactor(
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test.py",
            before_metrics={"lines": 100, "complexity": 15},
            after_metrics={"lines": 80, "complexity": 10},
            success=True,
        )

        assert record_id is not None
        history = tracker.get_history()
        assert len(history) == 1

    def test_get_history(self, tmp_path):
        tracker = EvolutionTracker(str(tmp_path / "records.json"))

        tracker.record_refactor(
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test1.py",
            before_metrics={"lines": 100},
            after_metrics={"lines": 80},
            success=True,
        )
        tracker.record_refactor(
            refactor_type=RefactorType.RENAME_VARIABLE,
            file_path="test2.py",
            before_metrics={"lines": 50},
            after_metrics={"lines": 50},
            success=True,
        )

        history = tracker.get_history()
        assert len(history) == 2

        filtered = tracker.get_history(refactor_type=RefactorType.EXTRACT_METHOD)
        assert len(filtered) == 1

    def test_get_statistics(self, tmp_path):
        tracker = EvolutionTracker(str(tmp_path / "records.json"))

        tracker.record_refactor(
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test.py",
            before_metrics={},
            after_metrics={},
            success=True,
        )
        tracker.record_refactor(
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path="test2.py",
            before_metrics={},
            after_metrics={},
            success=False,
        )

        stats = tracker.get_statistics()
        assert stats["total_refactors"] == 2
        assert stats["successful"] == 1
        assert stats["failed"] == 1
        assert stats["by_type"]["extract_method"] == 2


class TestIntegration:
    def test_singleton_behavior(self):
        r1 = get_refactoror()
        r2 = get_refactoror()
        assert r1 is r2

        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2

        t1 = get_tracker()
        t2 = get_tracker()
        assert t1 is t2

        reset_refactor_modules()

        r3 = get_refactoror()
        assert r3 is not r1

    def test_full_refactor_flow(self, tmp_path):
        refactoror = SelfRefactoror(str(tmp_path))
        tracker = EvolutionTracker(str(tmp_path / "records.json"))

        test_file = tmp_path / "flow_test.py"
        test_file.write_text("def long_function():\n    pass\n")

        opp = RefactorOpportunity(
            opportunity_id="flow_001",
            refactor_type=RefactorType.EXTRACT_METHOD,
            file_path=str(test_file),
            location=(1, 2),
            description="Test flow",
            original_code="def long_function():\n    pass",
        )

        result = refactoror.apply_refactor(opp, dry_run=True)
        assert result.success is True

        tracker.record_refactor(
            refactor_type=opp.refactor_type,
            file_path=str(test_file),
            before_metrics={"lines": 10},
            after_metrics={"lines": 8},
            success=True,
        )

        history = tracker.get_history()
        assert len(history) == 1
        assert history[0].success is True


@pytest.fixture(autouse=True)
def cleanup():
    yield
    reset_refactor_modules()
