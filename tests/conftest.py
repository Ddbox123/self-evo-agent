#!/usr/bin/env python3
"""
pytest 配置和共享 fixtures

提供测试所需的共享资源：
- workspace 临时目录
- mock LLM
- 测试配置
"""

import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """返回项目根目录"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def workspace_dir():
    """创建临时工作空间目录"""
    temp_dir = tempfile.mkdtemp(prefix="agent_test_")
    yield temp_dir
    # 清理
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_llm():
    """创建 Mock LLM"""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content="这是一个测试响应。测试完成。"
    )
    return mock


@pytest.fixture
def test_config():
    """创建测试配置"""
    class MockLLMConfig:
        model_name = "gpt-4o-mini"
        api_key = "test-key"
        api_base = None
        temperature = 0.7

    class MockCompressionConfig:
        max_token_limit = 4000
        keep_recent_steps = 3
        summary_max_chars = 300
        compression_model = "gpt-4o-mini"

    class MockAgentConfig:
        name = "TestAgent"
        awake_interval = 60
        auto_backup = False
        backup_interval = 3600
        max_iterations = 10

    class MockConfig:
        llm = MockLLMConfig()
        context_compression = MockCompressionConfig()
        agent = MockAgentConfig()

        def get_api_key(self):
            return "test-key"

    return MockConfig()


@pytest.fixture(autouse=True)
def reset_workspace_state():
    """每个测试前后重置工作空间状态"""
    yield
    # 测试后清理
    import glob
    test_files = glob.glob(os.path.join(str(PROJECT_ROOT / "workspace"), "test_*.json"))
    for f in test_files:
        try:
            os.remove(f)
        except Exception:
            pass
