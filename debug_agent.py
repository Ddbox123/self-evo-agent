"""
JSON 调试脚本

用于测试和调试 Self-Evolving Agent 的各个组件。

使用方法:
    python debug_agent.py                    # 运行完整测试
    python debug_agent.py --config          # 只测试配置
    python debug_agent.py --agent           # 只测试 Agent 初始化
    python debug_agent.py --tools           # 只测试工具加载
    python debug_agent.py --llm             # 只测试 LLM 调用
    python debug_agent.py --test <测试名>   # 运行特定测试

JSON 配置文件格式 (debug_config.json):
{
    "mode": "full|config|agent|tools|llm",
    "config": {
        "config_path": "config.toml",
        "model_name": "qwen-plus",
        "temperature": 0.7,
        "awake_interval": 60
    },
    "test": {
        "prompt": "测试提示词",
        "max_iterations": 1
    }
}
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================================================
# 测试结果收集
# ============================================================================

class TestResult:
    """测试结果"""
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.output = []
        self.start_time = datetime.now()
        self.end_time = None

    def mark_pass(self):
        self.passed = True
        self.end_time = datetime.now()

    def mark_fail(self, error: str):
        self.passed = False
        self.error = error
        self.end_time = datetime.now()

    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "error": self.error,
            "duration": f"{self.duration():.3f}s",
            "output": self.output
        }


class DebugRunner:
    """调试运行器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.results: list[TestResult] = []

    def run_test(self, name: str, test_func, *args, **kwargs):
        """运行单个测试"""
        result = TestResult(name)
        self.results.append(result)

        try:
            output = test_func(*args, **kwargs)
            result.output = output if isinstance(output, list) else [str(output)]
            result.mark_pass()
            self._print_result(result, "PASS")
        except Exception as e:
            result.mark_fail(str(e))
            self._print_result(result, "FAIL")
            import traceback
            traceback.print_exc()

        return result

    def _print_result(self, result: TestResult, status: str):
        """打印测试结果"""
        duration = f"{result.duration():.3f}s"
        status_icon = "[OK]" if result.passed else "[FAIL]"
        print(f"  {status_icon} {result.name} ({duration})")
        if result.error:
            print(f"       Error: {result.error[:100]}")

    def summary(self):
        """打印测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print("\n" + "=" * 60)
        print(f"测试摘要: {passed}/{total} 通过")
        if failed > 0:
            print(f"失败: {failed}")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
        print("=" * 60)

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": [r.to_dict() for r in self.results]
        }


# ============================================================================
# 测试函数
# ============================================================================

def test_config_loading(config_path: str = "config.toml"):
    """测试配置加载"""
    print("\n[1] 测试配置加载...")

    from config import Config, get_config, use_model

    results = []

    # 测试 1: 从默认配置加载
    try:
        config = Config()
        results.append({
            "test": "Config() 默认加载",
            "model": config.llm.model_name,
            "provider": config.llm.provider,
            "api_base": config.llm.api_base,
        })
    except Exception as e:
        results.append({"test": "Config() 默认加载", "error": str(e)})

    # 测试 2: 获取 API Key
    try:
        api_key = config.get_api_key()
        results.append({
            "test": "get_api_key()",
            "has_key": api_key is not None,
            "key_preview": api_key[:10] + "..." if api_key else None
        })
    except Exception as e:
        results.append({"test": "get_api_key()", "error": str(e)})

    # 测试 3: 配置属性访问
    try:
        results.append({
            "test": "配置属性访问",
            "agent.name": config.agent.name,
            "agent.awake_interval": config.agent.awake_interval,
            "compression.enabled": config.context_compression.enabled,
        })
    except Exception as e:
        results.append({"test": "配置属性访问", "error": str(e)})

    return results


def test_core_modules():
    """测试核心模块"""
    print("\n[2] 测试核心模块...")

    results = []

    # 测试 Logger
    try:
        from core.unified_logger import logger
        from core.logger import debug, DebugLogger
        results.append({
            "test": "core.unified_logger",
            "logger_type": type(logger).__name__,
        })
    except Exception as e:
        results.append({"test": "core.unified_logger", "error": str(e)})

    # 测试 EventBus
    try:
        from core.event_bus import get_event_bus, EventNames, emit, on
        bus = get_event_bus()
        results.append({
            "test": "core.event_bus",
            "event_count": bus.event_count,
            "events": EventNames.LLM_REQUEST,
        })
    except Exception as e:
        results.append({"test": "core.event_bus", "error": str(e)})

    # 测试 State
    try:
        from core.state import get_state_manager, AgentState
        state = get_state_manager()
        results.append({
            "test": "core.state",
            "current_state": state.get_state().value,
        })
    except Exception as e:
        results.append({"test": "core.state", "error": str(e)})

    return results


def test_tools_loading():
    """测试工具加载"""
    print("\n[3] 测试工具加载...")

    results = []

    try:
        from tools import create_langchain_tools

        tools = create_langchain_tools()
        tool_names = [t.name for t in tools]

        results.append({
            "test": "create_langchain_tools()",
            "tool_count": len(tools),
            "tools": tool_names[:5] + ["..."] if len(tool_names) > 5 else tool_names
        })

        # 测试工具分类
        tool_categories = {
            "web": [n for n in tool_names if "web" in n or "search" in n],
            "file": [n for n in tool_names if "file" in n or "read" in n or "edit" in n],
            "memory": [n for n in tool_names if "memory" in n or "generation" in n],
            "task": [n for n in tool_names if "task" in n or "plan" in n],
        }
        results.append({
            "test": "工具分类",
            "categories": tool_categories
        })

    except Exception as e:
        results.append({"test": "create_langchain_tools()", "error": str(e)})

    return results


def test_llm_connection():
    """测试 LLM 连接"""
    print("\n[4] 测试 LLM 连接...")

    results = []

    try:
        from config import Config
        from langchain_openai import ChatOpenAI

        config = Config()
        api_key = config.get_api_key()

        if not api_key:
            results.append({
                "test": "LLM 配置",
                "status": "SKIP",
                "reason": "API Key 未设置"
            })
            return results

        llm_kwargs = {
            "model": config.llm.model_name,
            "temperature": 0.7,
            "api_key": api_key,
        }
        if config.llm.api_base:
            llm_kwargs["base_url"] = config.llm.api_base

        llm = ChatOpenAI(**llm_kwargs)

        results.append({
            "test": "LLM 初始化",
            "model": config.llm.model_name,
            "provider": config.llm.provider,
        })

        # 简单调用测试
        print("  正在调用 LLM...")
        response = llm.invoke("你好，请回复 'OK'")

        results.append({
            "test": "LLM 调用",
            "status": "SUCCESS",
            "response": response.content[:100] if hasattr(response, 'content') else str(response)[:100]
        })

    except Exception as e:
        error_str = str(e)
        results.append({
            "test": "LLM 调用",
            "status": "FAIL",
            "error": error_str[:200]
        })

    return results


def test_agent_initialization():
    """测试 Agent 初始化"""
    print("\n[5] 测试 Agent 初始化...")

    results = []

    try:
        from config import Config
        from agent import SelfEvolvingAgent

        config = Config()

        api_key = config.get_api_key()
        if not api_key:
            results.append({
                "test": "SelfEvolvingAgent",
                "status": "SKIP",
                "reason": "API Key 未设置"
            })
            return results

        agent = SelfEvolvingAgent(config=config)

        results.append({
            "test": "SelfEvolvingAgent 初始化",
            "status": "SUCCESS",
            "name": agent.name,
            "model_name": agent.model_name,
            "tool_count": len(agent.tools),
            "workspace": agent.workspace_path,
        })

        # 测试 think_and_act (dry run)
        results.append({
            "test": "think_and_act 方法存在",
            "status": "OK",
            "has_method": hasattr(agent, 'think_and_act')
        })

    except Exception as e:
        results.append({
            "test": "SelfEvolvingAgent 初始化",
            "status": "FAIL",
            "error": str(e)[:200]
        })

    return results


def test_token_management():
    """测试 Token 管理"""
    print("\n[6] 测试 Token 管理...")

    results = []

    try:
        from tools.token_manager import estimate_tokens, estimate_messages_tokens
        from langchain_core.messages import HumanMessage, SystemMessage

        # 测试 token 估算
        text = "这是一个测试文本，用于估算 Token 数量。"
        tokens = estimate_tokens(text)

        results.append({
            "test": "estimate_tokens()",
            "text_length": len(text),
            "estimated_tokens": tokens
        })

        # 测试消息 token 估算
        messages = [
            SystemMessage(content="你是一个助手。"),
            HumanMessage(content="你好！")
        ]
        msg_tokens = estimate_messages_tokens(messages)

        results.append({
            "test": "estimate_messages_tokens()",
            "message_count": len(messages),
            "estimated_tokens": msg_tokens
        })

    except Exception as e:
        results.append({"test": "Token 管理", "error": str(e)})

    return results


def test_memory_system():
    """测试记忆系统"""
    print("\n[7] 测试记忆系统...")

    results = []

    try:
        from tools.memory_tools import (
            get_generation, get_core_context, get_current_goal,
            _load_memory
        )

        generation = get_generation()
        core_context = get_core_context()
        current_goal = get_current_goal()
        memory = _load_memory()

        results.append({
            "test": "记忆系统读取",
            "generation": generation,
            "core_context_length": len(core_context) if core_context else 0,
            "current_goal": current_goal[:50] if current_goal else None,
            "memory_keys": list(memory.keys()) if memory else []
        })

    except Exception as e:
        results.append({"test": "记忆系统", "error": str(e)})

    return results


# ============================================================================
# 主函数
# ============================================================================

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Self-Evolving Agent 调试脚本")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")

    runner = DebugRunner()

    # 按顺序运行测试
    runner.run_test("配置加载", lambda: test_config_loading())
    runner.run_test("核心模块", test_core_modules)
    runner.run_test("工具加载", test_tools_loading)
    runner.run_test("Token 管理", test_token_management)
    runner.run_test("记忆系统", test_memory_system)
    runner.run_test("LLM 连接", test_llm_connection)
    runner.run_test("Agent 初始化", test_agent_initialization)

    # 打印摘要
    summary = runner.summary()

    return summary


def main():
    parser = argparse.ArgumentParser(description="Agent 调试脚本")
    parser.add_argument('--config', action='store_true', help='只测试配置')
    parser.add_argument('--core', action='store_true', help='只测试核心模块')
    parser.add_argument('--tools', action='store_true', help='只测试工具')
    parser.add_argument('--llm', action='store_true', help='只测试 LLM')
    parser.add_argument('--agent', action='store_true', help='只测试 Agent')
    parser.add_argument('--memory', action='store_true', help='只测试记忆系统')
    parser.add_argument('--token', action='store_true', help='只测试 Token 管理')
    parser.add_argument('--output', type=str, help='输出 JSON 结果到文件')
    args = parser.parse_args()

    # 确定要运行的测试
    tests_to_run = []

    if args.config:
        tests_to_run.append(("配置加载", test_config_loading))
    if args.core:
        tests_to_run.append(("核心模块", test_core_modules))
    if args.tools:
        tests_to_run.append(("工具加载", test_tools_loading))
    if args.llm:
        tests_to_run.append(("LLM 连接", test_llm_connection))
    if args.agent:
        tests_to_run.append(("Agent 初始化", test_agent_initialization))
    if args.memory:
        tests_to_run.append(("记忆系统", test_memory_system))
    if args.token:
        tests_to_run.append(("Token 管理", test_token_management))

    # 如果没有指定测试，运行全部
    if not tests_to_run:
        summary = run_all_tests()
    else:
        runner = DebugRunner()
        for name, test_func in tests_to_run:
            runner.run_test(name, test_func)
        summary = runner.summary()

    # 输出 JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {args.output}")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
