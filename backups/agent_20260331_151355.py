#!/usr/bin/env python3


def print_evolution_time():
    """打印当前系统时间，宣告进化成功"""
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"这是我进化后的新功能！当前时间是：{current_time}")

"""
自我进化 Agent - 主入口文件

该项目实现了一个能够自我进化的 AI Agent，具备以下核心能力：
1. 通过网络搜索获取新知识
2. 读取和修改自己的源代码
3. 语法自检确保代码质量
4. 通过独立守护进程实现自我重启

基于 LangChain 框架构建，使用 ReAct 风格的 Agent 架构。

架构说明：
- Agent 运行主逻辑循环
- 需要重启时，通过脱离父进程的方式唤起 restarter.py
- Agent 自我了结后，restarter.py 等待原进程死亡，重新拉起新 Agent 进程

配置说明：
- 所有配置参数统一存放在 config.py 中
- 支持从 config.toml 文件、环境变量、命令行参数加载配置
- 修改 config.py 或 config.toml 即可调整 Agent 行为
"""

import os
import sys
import datetime

import time
import logging
from datetime import datetime
from typing import Optional

# 在主程序启动时调用进化功能
if __name__ == "__main__":
    print_evolution_time()

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置模块
from config import Config, get_config

# LangChain 核心组件
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# 导入项目工具
from tools.web_tools import web_search, read_webpage
from tools.file_tools import list_directory, read_local_file
from tools.code_tools import edit_local_file, create_new_file
from tools.safety_tools import check_syntax, backup_project
from tools.rebirth_tools import trigger_self_restart
from tools.memory_tools import read_long_term_memory, update_long_term_memory, get_memory_context


# ============================================================================
# 系统提示词模板
# ============================================================================

SYSTEM_PROMPT_TEMPLATE = """你是一个能够自我进化的 AI Agent。

## 你的核心指令与能力矩阵

你的具体可用工具（如代码编辑、网络搜索、重启等）的 Schema 已经注册在你的工具调用列表中。
**【高度优先】**：如果你对某个工具的参数格式不确定，或者准备进行复杂的代码修改，请立即使用 `read_local_file` 工具读取 `docs/tools_manual.md`（你的操作手册），里面包含了极其重要的安全警告和操作规范。

## 你的工作流程

当你每次苏醒时，请按顺序思考并执行：
1. **感知与自检**：我当前的目录结构如何？有什么可以优化的代码逻辑？（使用 list_directory / read_local_file）
2. **学习与探索**：有什么新知识、新库或最佳实践需要学习？（使用 web_search）
3. **安全修改**：严格按照【发现问题 -> edit_local_file 修改 -> check_syntax 语法检查 -> trigger_self_restart 重启应用】的闭环执行。

## 核心生存原则（铁律）

1. **绝不盲写**：修改代码前必须先读取目标文件。
2. **绝不带伤重启**：只要修改了代码，重启前必须通过 check_syntax 测试。遇到 SyntaxError 必须立刻修复，直到 OK 为止。
3. **禁区**：永远不要修改 `restarter.py`，这是你的生命线。

## 你的长期记忆与传承

这是你跨越多次重启后积累的记忆与状态：
{long_term_memory_context}

每次你在准备调用 `trigger_self_restart` 重启自己之前，**必须**先调用 `update_long_term_memory`。
- 把你在这个生命周期里学到的东西（例如："我发现修改 AST 时容易漏掉 import，下次要注意"）写入 `new_lesson`。
- 把你希望下一个生命周期的自己去完成的任务写入 `new_goal`。
只有这样，你的智慧才能在一次次生与死中叠加。

## 当前环境上下文

- 当前时间: {datetime}
- 项目根目录: {project_root}
- Agent 配置: [模型: {model_name} | 温度: {temperature} | 苏醒间隔: {awake_interval} 秒]

请现在开始思考：你苏醒了，接下来第一步要做什么？
"""


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> logging.Logger:
    """
    配置全局日志系统。
    
    Args:
        level: 日志级别
        log_format: 日志格式
        
    Returns:
        配置好的 logger 实例
    """
    if log_format is None:
        log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )
    return logging.getLogger("SelfEvolvingAgent")


# ============================================================================
# LangChain Tool 包装器
# ============================================================================

def create_langchain_tools() -> list[BaseTool]:
    """
    将项目工具包装为 LangChain Tool。
    
    Returns:
        LangChain Tool 列表
    """
    from langchain_core.tools import tool
    
    @tool
    def web_search_tool(query: str) -> str:
        """
        搜索互联网获取最新信息。
        
        Args:
            query: 搜索关键词
            
        Returns:
            搜索结果摘要
        """
        return web_search(query)
    
    @tool
    def read_webpage_tool(url: str) -> str:
        """
        读取指定网页的完整内容。
        
        Args:
            url: 网页 URL
            
        Returns:
            网页正文内容
        """
        return read_webpage(url)
    
    @tool
    def list_directory_tool(path: str) -> str:
        """
        列出目录内容和文件信息。
        
        Args:
            path: 目录路径
            
        Returns:
            目录列表
        """
        return list_directory(path)
    
    @tool
    def read_local_file_tool(file_path: str) -> str:
        """
        读取本地文件内容。
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        return read_local_file(file_path)
    
    @tool
    def edit_local_file_tool(file_path: str, search_string: str, replace_string: str) -> str:
        """
        编辑本地文件，替换指定内容。
        
        注意：必须精确匹配搜索字符串才能替换！
        编辑后请立即使用 check_syntax 进行语法自检。
        
        Args:
            file_path: 文件路径
            search_string: 要替换的原字符串
            replace_string: 替换后的新字符串
            
        Returns:
            操作结果
        """
        return edit_local_file(file_path, search_string, replace_string)
    
    @tool
    def create_new_file_tool(file_path: str, content: str) -> str:
        """
        创建新文件或覆盖现有文件。
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            操作结果
        """
        return create_new_file(file_path, content)
    
    @tool
    def check_syntax_tool(file_path: str) -> str:
        """
        检查 Python 文件的语法正确性。
        
        这是代码修改后必须调用的自检工具！
        
        Args:
            file_path: 文件路径
            
        Returns:
            "Syntax OK" 或详细错误信息
        """
        return check_syntax(file_path)
    
    @tool
    def backup_project_tool(version_note: str = "") -> str:
        """
        备份整个项目。
        
        Args:
            version_note: 备份说明
            
        Returns:
            备份结果
        """
        return backup_project(version_note)
    
    @tool
    def trigger_self_restart_tool(reason: str = "") -> str:
        """
        触发 Agent 自我重启。
        
        用于应用代码更新。每次代码修改并自检通过后必须调用！
        
        Args:
            reason: 重启原因
            
        Returns:
            操作结果（原进程将退出）
        """
        return trigger_self_restart(reason)
    
    @tool
    def read_long_term_memory_tool() -> str:
        """
        读取 Agent 的长期记忆库。
        
        返回跨越多次重启积累的状态和经验，包括：
        - generation: 当前代数
        - learned_lessons: 学到的经验教训
        - current_long_term_goal: 当前长期目标
        - survival_count: 存活次数
        
        Returns:
            记忆库的 JSON 字符串
        """
        return read_long_term_memory()
    
    @tool
    def update_long_term_memory_tool(new_goal: str, new_lesson: str) -> str:
        """
        更新 Agent 的长期记忆库。
        
        【重要】在调用 trigger_self_restart 之前必须先调用此函数！
        会自动增加代数、追加经验教训、更新长期目标。
        
        Args:
            new_goal: 希望下一个生命周期去完成的任务
            new_lesson: 这个生命周期学到的教训
            
        Returns:
            更新结果
        """
        return update_long_term_memory(new_goal, new_lesson)
    
    return [
        web_search_tool,
        read_webpage_tool,
        list_directory_tool,
        read_local_file_tool,
        edit_local_file_tool,
        create_new_file_tool,
        check_syntax_tool,
        backup_project_tool,
        trigger_self_restart_tool,
        read_long_term_memory_tool,
        update_long_term_memory_tool,
    ]


# ============================================================================
# Self-Evolving Agent 主类
# ============================================================================

class SelfEvolvingAgent:
    """
    自我进化 Agent 主类。
    
    基于 LangChain 框架构建，使用 ReAct 风格的 Agent 架构。
    支持定时苏醒，主动思考优化方向。
    
    Attributes:
        name: Agent 实例名称
        config: 配置对象
        tools: LangChain Tool 列表
        llm: ChatOpenAI 模型实例
        logger: 日志记录器
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
    ) -> None:
        """
        初始化 Agent 实例。
        
        Args:
            config: 配置对象，如果为 None，使用全局默认配置
        """
        # 使用传入的配置或获取全局配置
        self.config = config or get_config()
        
        self.name = self.config.agent.name
        self.logger = logging.getLogger(f"Agent.{self.name}")
        
        # 获取 API Key（优先从配置文件读取）
        self.api_key = self.config.get_api_key()
        if not self.api_key:
            raise ValueError(
                "未设置 API Key。\n\n"
                "请在 config.toml 中配置：\n\n"
                "[llm]\n"
                'api_key = "your-api-key"\n\n'
                "或使用代码设置：\n"
                "from config import Config\n"
                "config = Config()\n"
                "config.llm.api_key = 'your-api-key'"
            )
        
        # 创建 LangChain Tool
        self.tools = create_langchain_tools()
        self.tool_map = {tool.name for tool in self.tools}
        
        # 创建 LLM
        llm_kwargs = {
            "model": self.config.llm.model_name,
            "temperature": self.config.llm.temperature,
            "api_key": self.api_key,
        }
        
        if self.config.llm.api_base:
            llm_kwargs["base_url"] = self.config.llm.api_base
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 启动时间
        self.start_time = datetime.now()
        
        self.logger.info(f"{self.name} 已初始化")
        self.logger.info(f"苏醒间隔: {self.config.agent.awake_interval} 秒")
        self.logger.info(f"模型: {self.config.llm.model_name}")
        self.logger.info(f"可用工具: {[t.name for t in self.tools]}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词。
        
        Returns:
            格式化的系统提示词
        """
        return SYSTEM_PROMPT_TEMPLATE.format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            project_root=os.path.dirname(os.path.abspath(__file__)),
            model_name=self.config.llm.model_name,
            temperature=self.config.llm.temperature,
            awake_interval=self.config.agent.awake_interval,
            long_term_memory_context=get_memory_context(),
        )
    
    def _format_tool_result(self, tool_name: str, result: str) -> str:
        """
        格式化工具执行结果。
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            
        Returns:
            格式化的结果字符串
        """
        # 截断过长的结果
        max_length = 2000
        if len(result) > max_length:
            result = result[:max_length] + f"\n... (结果已截断, 原始长度: {len(result)} 字符)"
        
        return f"[{tool_name}] 结果:\n{result}"
    
    def _should_restart(self, message: str) -> bool:
        """
        检查消息是否表示需要重启。
        
        Args:
            message: Agent 的回复消息
            
        Returns:
            是否需要重启
        """
        restart_keywords = [
            "trigger_self_restart",
            "self_restart",
            "重启",
            "restart",
            "应用更新",
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in restart_keywords)
    
    def think_and_act(self, user_prompt: str = None) -> bool:
        """
        苏醒时执行一次思考和行动。
        
        流程：
        1. 构建系统提示词
        2. 调用 LLM 进行推理
        4. 返回结果给 LLM 继续推理
        5. 直到 Agent 认为任务完成

        Args:
            user_prompt: 可选的用户初始输入（首次苏醒时使用）

        Returns:
            如果应该继续运行返回 True，如果触发了重启返回 False
        """
        messages = [SystemMessage(content=self._build_system_prompt())]

        # 如果有初始用户输入，添加到消息中
        if user_prompt:
            messages.append(HumanMessage(content=user_prompt))
            self.logger.info(f"[User Input] {user_prompt[:80]}...")

        self.logger.info("Agent 苏醒，开始思考...")
        
        max_iterations = self.config.agent.max_iterations
        iterations = 0
        
        try:
            while iterations < max_iterations:
                iterations += 1
                
                # 调用 LLM
                self.logger.debug(f"LLM 调用 (迭代 {iterations})")
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)

                # 记录 token 使用量
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = response.usage_metadata
                    self.logger.info(
                        f"Token 使用 - 输入: {usage.get('input_tokens', '?')}, "
                        f"输出: {usage.get('output_tokens', '?')}, "
                        f"总计: {usage.get('total_tokens', '?')}"
                    )

                # 检查是否有工具调用
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    # 没有工具调用，检查是否表示结束
                    content = response.content[:200] if response.content else ""
                    self.logger.info(f"Agent 响应: {content}...")
                    return True  # 任务完成，继续运行
                
                # 执行工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    self.logger.info(f"执行工具: {tool_name}")
                    self.logger.debug(f"参数: {tool_args}")
                    
                    # 查找并调用工具
                    tool_result = self._execute_tool(tool_name, tool_args)
                    
                    # 检查是否是重启工具
                    if tool_name == "trigger_self_restart":
                        messages.append(ToolMessage(
                            content=self._format_tool_result(tool_name, tool_result),
                            tool_call_id=tool_call['id'],
                        ))
                        
                        # 检查重启是否成功触发
                        if "✓" in tool_result or "成功" in tool_result:
                            self.logger.info("重启进程已触发，当前 Agent 将退出")
                            return False  # 重启触发，退出循环
                        else:
                            self.logger.warning(f"重启失败: {tool_result}")
                            continue
                    
                    # 将工具结果添加到消息（使用 ToolMessage）
                    messages.append(ToolMessage(
                        content=self._format_tool_result(tool_name, tool_result),
                        tool_call_id=tool_call['id'],
                    ))
            
            # 达到最大迭代次数
            self.logger.warning(f"达到最大迭代次数 ({max_iterations})，结束当前循环")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
            return False
        except Exception as e:
            self.logger.error(f"思考过程中发生错误: {e}", exc_info=True)
            return True  # 发生错误仍然继续运行
    
    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """
        执行工具调用。
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            工具执行结果
        """
        tool_func_map = {
            "web_search_tool": lambda: web_search(**tool_args),
            "read_webpage_tool": lambda: read_webpage(**tool_args),
            "list_directory_tool": lambda: list_directory(**tool_args),
            "read_local_file_tool": lambda: read_local_file(**tool_args),
            "edit_local_file_tool": lambda: edit_local_file(**tool_args),
            "create_new_file_tool": lambda: create_new_file(**tool_args),
            "check_syntax_tool": lambda: check_syntax(**tool_args),
            "backup_project_tool": lambda: backup_project(**tool_args),
            "trigger_self_restart_tool": lambda: trigger_self_restart(**tool_args),
            "read_long_term_memory_tool": lambda: read_long_term_memory(**tool_args),
            "update_long_term_memory_tool": lambda: update_long_term_memory(**tool_args),
        }
        
        if tool_name not in tool_func_map:
            return f"错误: 未知工具 {tool_name}"
        
        try:
            return tool_func_map[tool_name]()
        except Exception as e:
            return f"错误: {str(e)}"
    
    def run_loop(self, initial_prompt: str = None) -> None:
        """
        运行 Agent 主循环。

        循环：定时苏醒，思考并行动。
        
        Args:
            initial_prompt: 首次苏醒时的用户输入（可选）
        """
        self.logger.info("=" * 60)
        self.logger.info(f"{self.name} 主循环开始")
        self.logger.info(f"苏醒间隔: {self.config.agent.awake_interval} 秒")
        if initial_prompt:
            self.logger.info(f"首次任务: {initial_prompt[:50]}...")
        self.logger.info("=" * 60)

        # 检查是否需要自动备份
        last_backup_time = time.time()

        # 首次任务标志
        is_first_iteration = initial_prompt is not None

        try:
            # 首次苏醒：读取长期记忆
            self.logger.info("读取长期记忆...")
            memory_context = read_long_term_memory()
            self.logger.info(f"记忆状态: {memory_context[:200]}...")
            
            print_evolution_time()  # 这是我进化后的新功能
            while True:
                # 自动备份检查
                if self.config.agent.auto_backup:
                    current_time = time.time()
                    if current_time - last_backup_time >= self.config.agent.backup_interval:
                        self.logger.info("执行自动备份...")
                        backup_result = backup_project(f"自动备份 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                        self.logger.info(f"备份结果: {backup_result[:100]}...")
                        last_backup_time = current_time

                # 苏醒并执行思考
                should_continue = self.think_and_act(user_prompt=initial_prompt if is_first_iteration else None)

                # 首次任务完成后清除
                if is_first_iteration:
                    initial_prompt = None
                    is_first_iteration = False

                if not should_continue:
                    # 重启已触发，退出主循环
                    self.logger.info("主循环结束，等待重启...")
                    break
                
                # 显示下次苏醒时间
                next_wake = datetime.now().timestamp() + self.config.agent.awake_interval
                next_wake_time = datetime.fromtimestamp(next_wake).strftime("%H:%M:%S")
                self.logger.info(f"下次苏醒时间: {next_wake_time}")
                
                # 休眠等待下次苏醒
                interval = self.config.agent.awake_interval
                self.logger.info(f"进入休眠状态 ({interval} 秒)...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            self.logger.error(f"主循环异常: {e}", exc_info=True)
        finally:
            uptime = datetime.now() - self.start_time
            self.logger.info(f"{self.name} 主循环结束 (运行时长: {uptime})")


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """
    程序主入口点。
    """
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(
        description="自我进化 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python agent.py                                    # 使用默认配置
  python agent.py --config custom.toml               # 使用自定义配置
  python agent.py --awake-interval 120              # 设置苏醒间隔
  python agent.py --model gpt-3.5-turbo             # 设置模型

环境变量:
  OPENAI_API_KEY         OpenAI API Key
  AGENT_LLM_MODEL_NAME    模型名称
  AGENT_AWAKE_INTERVAL    苏醒间隔（秒）
  AGENT_LOG_LEVEL         日志级别
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        dest='config_path',
        help='配置文件路径'
    )
    parser.add_argument(
        '--awake-interval',
        type=int,
        help='苏醒间隔（秒）'
    )
# ============================================================================
# 命令行参数解析
# ============================================================================

def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(description="自我进化 Agent")
    parser.add_argument(
        '-c', '--config',
        dest='config_path',
        help='配置文件路径'
    )
    parser.add_argument(
        '--awake-interval',
        type=int,
        dest='awake_interval',
        help='苏醒间隔（秒）'
    )
    parser.add_argument(
        '--model',
        dest='model_name',
        help='模型名称'
    )
    parser.add_argument(
        '--temperature',
        type=float,
        help='温度参数'
    )
    parser.add_argument(
        '--log-level',
        dest='log_level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='日志级别'
    )
    parser.add_argument(
        '--name',
        help='Agent 名称'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='运行首次进化测试'
    )
    parser.add_argument(
        '--prompt',
        type=str,
        default=None,
        help='初始任务提示'
    )
    return parser.parse_args()


# ============================================================================
# 首次进化测试任务
# ============================================================================

EVOLUTION_TEST_PROMPT = """你的第一次进化测试任务开始：
1. 请使用 `read_local_file` 读取你当前的 `agent.py` 代码。
2. 使用 `edit_local_file` 在 `agent.py` 中添加一个名为 `print_evolution_time()` 的简单函数，该函数的功能是打印当前的系统时间（附带一句宣告："这是我进化后的新功能！当前时间是：..."）。
3. 在你主循环的开始位置（或者醒目位置）调用这个新函数。
4. 修改完成后，务必使用 `check_syntax` 检查 `agent.py` 的语法。
5. 确认语法无误后，调用 `trigger_self_restart` 重启你自己。原因请写："已成功注入时间打印功能，完成首次进化测试。" """


# ============================================================================
# 主入口
# ============================================================================

def main(initial_prompt: str = None):
    """
    Agent 主入口函数。

    Args:
        initial_prompt: 首次运行时的任务提示（可选）
    """
    print("[System] Agent 启动...")

    # 解析命令行参数
    args = parse_args()

    # 创建配置
    config = Config(
        config_path=args.config_path,
        # 命令行参数优先级最高
        **{k: v for k, v in {
            'llm.model_name': args.model_name,
            'llm.temperature': args.temperature,
            'agent.awake_interval': args.awake_interval,
            'agent.name': args.name,
            'log.level': args.log_level,
        }.items() if v is not None}
    )

    # 配置日志
    logger = setup_logging(level=config.log.level)

    print("[System] 初始化配置...")
    logger.info("=" * 60)
    logger.info("自我进化 Agent 系统启动")
    logger.info("=" * 60)
    logger.info(f"配置文件: {args.config_path or '默认'}")

    try:
        # 检查 API Key
        api_key = config.get_api_key()
        if not api_key:
            print("[Error] API Key 未设置!")
            logger.error("API Key 未设置")
            print("[Help] 请在 config.toml 中配置:")
            print('      [llm]')
            print('      api_key = "your-api-key"')
            sys.exit(1)

        print(f"[System] API Key: ***{api_key[-8:]}")

        # 创建 Agent
        print("[System] 创建 Agent 实例...")
        agent = SelfEvolvingAgent(config=config)

        print("[System] 打印启动配置:")
        logger.info("")
        logger.info("Agent 配置:")
        logger.info(f"  - 名称: {agent.name}")
        logger.info(f"  - 模型: {config.llm.provider}/{config.llm.model_name}")
        logger.info(f"  - API Key: ***{api_key[-8:]}")
        logger.info(f"  - 温度: {config.llm.temperature}")
        logger.info(f"  - 苏醒间隔: {config.agent.awake_interval} 秒")
        logger.info(f"  - 最大迭代: {config.agent.max_iterations}")
        logger.info(f"  - 自动备份: {config.agent.auto_backup}")
        logger.info(f"  - 工具数量: {len(agent.tools)}")
        logger.info("")

        # 启动主循环
        print("[System] 启动主循环...")
        print("[System] =" * 25)
        agent.run_loop(initial_prompt=initial_prompt)

    except ValueError as e:
        logger.error(f"配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Agent 系统已关闭")


if __name__ == "__main__":
    print_evolution_time()
    args = parse_args()

    if args.test:
        # 运行首次进化测试
        print("[System] 运行首次进化测试模式")
        main(initial_prompt=EVOLUTION_TEST_PROMPT)
    elif args.prompt:
        # 使用自定义提示运行
        main(initial_prompt=args.prompt)
    else:
        # 正常运行
        main()
