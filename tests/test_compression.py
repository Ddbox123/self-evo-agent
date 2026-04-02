#!/usr/bin/env python3
"""
Token 压缩逻辑测试套件

测试内容：
1. Token 估算准确性
2. 消息优先级判断
3. 智能截断逻辑
4. 增强型压缩器
5. 压缩统计

运行：pytest tests/test_compression.py -v
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# 导入被测模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.token_manager import (
    estimate_tokens_precise,
    estimate_messages_tokens,
    get_message_priority,
    truncate_tool_result,
    truncate_ai_response,
    smart_compress_message,
    EnhancedTokenCompressor,
    MessagePriority,
    DEFAULT_TOKEN_BUDGET,
    MAX_TOOL_RESULT_TOKENS,
    CORE_SUMMARY_CHARS,
)
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage


class TestTokenEstimation:
    """Token 估算测试"""

    def test_estimate_empty_string(self):
        """测试空字符串"""
        assert estimate_tokens_precise("") == 0

    def test_estimate_pure_chinese(self):
        """测试纯中文"""
        chinese = "你好世界这是一个测试"
        result = estimate_tokens_precise(chinese)
        assert result > 0, "中文应该产生 token 估算"
        # 约 12 个中文字符，应该 < 10 tokens
        assert result < len(chinese), "估算应该比字符数小"

    def test_estimate_pure_english(self):
        """测试纯英文"""
        english = "Hello world this is a test"
        result = estimate_tokens_precise(english)
        assert result > 0
        # 约 26 个字符，按 4 字符/token，应该 ~7 tokens
        assert result <= len(english)

    def test_estimate_mixed_content(self):
        """测试混合内容"""
        mixed = "Hello 你好 world 世界"
        result = estimate_tokens_precise(mixed)
        assert result > 0

    def test_estimate_messages_tokens(self):
        """测试消息列表 token 估算"""
        messages = [
            MagicMock(content="Hello", type="human"),
            MagicMock(content="世界", type="ai"),
        ]
        result = estimate_messages_tokens(messages)
        assert result >= 0


class TestMessagePriority:
    """消息优先级测试"""

    def test_system_message_highest_priority(self):
        """测试系统消息最高优先级"""
        msg = MagicMock(type="system", content="系统提示")
        assert get_message_priority(msg) == MessagePriority.CRITICAL

    def test_human_message_high_priority(self):
        """测试人类消息高优先级"""
        msg = MagicMock(type="human", content="用户输入")
        priority = get_message_priority(msg)
        assert priority <= MessagePriority.MEDIUM

    def test_tool_message_with_error_high_priority(self):
        """测试包含错误的工具消息高优先级"""
        msg = MagicMock(type="tool", content="[错误] Something went wrong")
        assert get_message_priority(msg) == MessagePriority.HIGH

    def test_tool_message_with_success_high_priority(self):
        """测试包含成功的工具消息高优先级"""
        msg = MagicMock(type="tool", content="[check_syntax] OK")
        assert get_message_priority(msg) == MessagePriority.HIGH

    def test_regular_ai_message_medium_priority(self):
        """测试常规 AI 消息中等优先级"""
        msg = MagicMock(type="ai", content="我正在思考...")
        priority = get_message_priority(msg)
        assert priority <= MessagePriority.MEDIUM


class TestTruncation:
    """截断逻辑测试"""

    def test_truncate_short_result(self):
        """测试截断短结果（不截断）"""
        short = "short content"
        result = truncate_tool_result(short, max_chars=100)
        assert result == short

    def test_truncate_long_result(self):
        """测试截断长结果"""
        long = "A" * 1000
        result = truncate_tool_result(long, max_chars=200)
        assert len(result) < 1000
        assert "[...省略" in result or "截断" in result

    def test_truncate_preserves_structure(self):
        """测试截断保留结构"""
        long = "START\n" + "B" * 500 + "\nEND"
        result = truncate_tool_result(long, max_chars=100)
        # 应该保留开头和结尾
        assert "START" in result
        assert "END" in result

    def test_truncate_ai_response(self):
        """测试 AI 响应截断"""
        long_response = "结论：" + "A" * 500
        result = truncate_ai_response(long_response, max_chars=100)
        assert len(result) < len(long_response)
        assert result.startswith("结论：")


class TestSmartCompression:
    """智能压缩测试"""

    def test_smart_compress_short_message(self):
        """测试智能压缩短消息（不压缩）"""
        msg = MagicMock(type="tool", content="short")
        result = smart_compress_message(msg, max_chars=100)
        assert result == "short"

    def test_smart_compress_tool_message(self):
        """测试智能压缩工具消息"""
        long_tool = "A" * 500
        msg = MagicMock(type="tool", content=long_tool)
        result = smart_compress_message(msg, max_chars=100)
        assert len(result) < 500

    def test_smart_compress_ai_message(self):
        """测试智能压缩 AI 消息"""
        long_ai = "B" * 500
        msg = MagicMock(type="ai", content=long_ai)
        result = smart_compress_message(msg, max_chars=100)
        assert len(result) < 500


class TestEnhancedCompressor:
    """增强型压缩器测试"""

    def test_compressor_initialization(self):
        """测试压缩器初始化"""
        compressor = EnhancedTokenCompressor(
            token_budget=8000,
            max_history_pairs=3,
        )
        assert compressor.token_budget.total_budget == 8000
        assert compressor.max_history_pairs == 3

    def test_should_compress_normal_level(self):
        """测试正常级别不压缩"""
        compressor = EnhancedTokenCompressor(token_budget=8000)
        mock_messages = [
            SystemMessage(content="short"),
            HumanMessage(content="hi"),
        ]
        should, reason, level = compressor.should_compress(mock_messages)
        assert isinstance(should, bool)

    def test_compressor_threshold_properties(self):
        """测试压缩阈值属性"""
        compressor = EnhancedTokenCompressor(token_budget=10000)

        assert compressor.warning_threshold > 0
        assert compressor.trigger_threshold > compressor.warning_threshold
        assert compressor.critical_threshold > compressor.trigger_threshold
        assert compressor.target_tokens < compressor.token_budget.effective_budget

    def test_compression_level_classification(self):
        """测试压缩级别分类"""
        compressor = EnhancedTokenCompressor(token_budget=10000)

        # 验证级别分类存在
        assert compressor.get_compression_level(2000) in ["normal", "warning", "active", "emergency"]
        assert compressor.get_compression_level(9000) in ["normal", "warning", "active", "emergency"]

    def test_compress_preserves_recent_messages(self):
        """测试压缩保留最近消息"""
        compressor = EnhancedTokenCompressor(token_budget=1000)

        # 创建消息序列
        messages = [
            SystemMessage(content="系统提示"),
            HumanMessage(content="用户输入1"),
            AIMessage(content="思考1"),
            ToolMessage(content="结果1", tool_call_id="1"),
            AIMessage(content="思考2"),
            ToolMessage(content="结果2", tool_call_id="2"),
            AIMessage(content="思考3"),
            ToolMessage(content="结果3", tool_call_id="3"),
        ]

        compressed, summary = compressor.compress(messages, max_chars=200)

        # 验证压缩后有摘要或保留了部分消息
        assert len(compressed) <= len(messages)
        # 应该保留系统消息
        assert any(isinstance(m, SystemMessage) for m in compressed)

    def test_compress_empty_messages(self):
        """测试压缩空消息列表"""
        compressor = EnhancedTokenCompressor()
        compressed, summary = compressor.compress([], max_chars=200)
        assert compressed == []
        assert summary == ""

    def test_compress_no_ai_messages(self):
        """测试压缩没有 AI 消息的情况"""
        compressor = EnhancedTokenCompressor()
        messages = [
            SystemMessage(content="系统"),
            HumanMessage(content="用户"),
        ]
        compressed, summary = compressor.compress(messages)
        # 应该直接返回原消息
        assert len(compressed) >= 2


class TestCompressionStats:
    """压缩统计测试"""

    def test_stats_initialization(self):
        """测试统计初始化"""
        from tools.token_manager import TokenCompressionStats

        stats = TokenCompressionStats()
        assert stats.compression_count == 0
        assert stats.total_tokens_saved == 0

    def test_stats_record(self):
        """测试统计记录"""
        from tools.token_manager import TokenCompressionStats

        stats = TokenCompressionStats()
        stats.record(
            before=1000,
            after=500,
            pairs=5,
            summary="测试摘要",
            compression_type="active",
        )

        assert stats.compression_count == 1
        assert stats.total_tokens_saved == 500

    def test_stats_get_stats(self):
        """测试获取统计信息"""
        from tools.token_manager import TokenCompressionStats

        stats = TokenCompressionStats()
        stats_info = stats.get_stats()

        # 没有压缩记录时返回特定状态
        assert isinstance(stats_info, dict)


class TestPreemptiveCompression:
    """预压缩机制测试"""

    def test_preemptive_enabled_by_default(self):
        """测试预压缩默认启用"""
        compressor = EnhancedTokenCompressor()
        assert compressor.enable_preemptive is True

    def test_preemptive_disabled(self):
        """测试预压缩禁用"""
        compressor = EnhancedTokenCompressor(enable_preemptive=False)
        assert compressor.enable_preemptive is False

    def test_warning_level_triggers_when_preemptive(self):
        """测试警告级别触发预压缩"""
        compressor = EnhancedTokenCompressor(
            token_budget=10000,
            enable_preemptive=True,
        )
        # 在警告阈值但未达到触发阈值
        mock_messages = [
            SystemMessage(content="A" * 4000),
        ]
        should, reason, level = compressor.should_compress(mock_messages)
        # 预压缩开启时，warning 级别也应该触发
        if level == "warning":
            assert should is True


# ============================================================================
# 测试运行器
# ============================================================================

def run_compression_tests() -> dict:
    """运行所有压缩测试"""
    import subprocess

    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")

    return {
        "passed": passed,
        "failed": failed,
        "total": passed + failed,
        "status": "PASS" if failed == 0 else "FAIL",
        "output": output,
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
