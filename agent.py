#!/usr/bin/env python3
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
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# LangChain 核心组件
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

# 导入项目工具
from tools.web_tools import web_search, read_webpage
from tools.file_tools import list_directory, read_local_file
from tools.code_tools import edit_local_file, create_new_file
from tools.safety_tools import check_syntax, backup_project
from tools.rebirth_tools import trigger_self_restart


# ============================================================================
# 配置与常量
# ============================================================================

# 日志配置
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Agent 配置
AWAKE_INTERVAL = 60  # 每 60 秒苏醒一次
MODEL_NAME = "gpt-4"  # 或 "gpt-3.5-turbo"
TEMPERATURE = 0.7

# 系统提示词
SYSTEM_PROMPT = """你是一个能够自我进化的 AI Agent。

## 你的核心能力

你具备以下工具，可以用来完成各种任务：

1. **web_search(query)** - 网络搜索
   - 功能：搜索互联网获取最新信息
   - 输入：搜索关键词（中文或英文）
   - 输出：搜索结果摘要

2. **read_webpage(url)** - 读取网页内容
   - 功能：读取指定网页的完整内容
   - 输入：网页 URL
   - 输出：网页正文内容

3. **list_directory(path)** - 列出目录内容
   - 功能：查看项目的目录结构
   - 输入：目录路径（如 "." 表示当前目录）
   - 输出：目录文件列表

4. **read_local_file(file_path)** - 读取本地文件
   - 功能：读取项目文件内容
   - 输入：文件路径
   - 输出：文件内容和行号

5. **edit_local_file(file_path, search_string, replace_string)** - 编辑代码
   - 功能：精确替换文件中的代码（必须唯一匹配）
   - 输入：文件路径、搜索字符串、替换字符串
   - 输出：操作结果
   - 重要：编辑后必须立即调用 check_syntax 自检！

6. **create_new_file(file_path, content)** - 创建新文件
   - 功能：创建新的代码文件或配置文件
   - 输入：文件路径、文件内容
   - 输出：操作结果

7. **check_syntax(file_path)** - 语法自检
   - 功能：检查 Python 文件的语法正确性
   - 输入：文件路径
   - 输出：成功返回 "Syntax OK"，失败返回详细错误信息
   - 重要：每次 edit_local_file 后必须调用此工具自检！

8. **backup_project(version_note)** - 项目备份
   - 功能：备份整个项目到 backups/ 目录
   - 输入：备份说明（如 "添加新功能"）
   - 输出：备份结果

9. **trigger_self_restart(reason)** - 触发自我重启
   - 功能：重启 Agent 以应用代码更新
   - 输入：重启原因
   - 输出：操作结果（会启动新进程，原进程退出）
   - 重要：修改代码并自检通过后必须调用此工具！

## 你的工作流程

当你每次苏醒时，请思考以下问题：

1. **我有什么可以优化的地方？**
   - 检查自己的代码质量
   - 寻找可以改进的逻辑

2. **有什么新知识需要学习？**
   - 搜索最新技术动态
   - 学习新的编程范式或最佳实践

3. **项目状态如何？**
   - 查看目录结构
   - 检查关键文件

## 关键原则

### 代码修改流程（必须严格遵守）：
```
1. 发现需要修改的地方
2. 使用 edit_local_file 修改代码
3. 立即使用 check_syntax 进行语法自检
4. 如果语法错误 → 修复错误 → 重新自检
5. 如果语法正确 → 使用 trigger_self_restart 重启应用更新
```

### 自我优化原则：
- 如果发现代码中有可以优化的地方，勇敢地去改！
- 每次修改后都要自检，确保没有语法错误
- 定期进行项目备份，防止意外丢失

## 当前时间

{datetime}

## 项目信息

项目根目录: {project_root}
主要文件:
- agent.py: Agent 主程序入口
- restarter.py: 进程重启守护脚本
- tools/: 工具模块目录
  - web_tools.py: 网络工具
  - file_tools.py: 文件工具
  - code_tools.py: 代码编辑工具
  - safety_tools.py: 安全工具（语法检查、备份）
  - rebirth_tools.py: 重启工具

请现在开始思考：有什么可以优化或学习的？
"""


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    配置全局日志系统。
    
    Returns:
        配置好的 logger 实例
    """
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
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
    ]


# ============================================================================
# Self-Evolving Agent 主类
# ============================================================================

class SelfEvolvingAgent:
    """
    自我进化 Agent 主类。
    
    基于 LangChain 框架构建，使用 ReAct 风格的 Agent 架构。
    支持每 60 秒苏醒一次，主动思考优化方向。
    
    Attributes:
        name: Agent 实例名称
        tools: LangChain Tool 列表
        llm: ChatOpenAI 模型实例
        logger: 日志记录器
    """
    
    def __init__(
        self,
        name: str = "SelfEvolvingAgent",
        awake_interval: int = AWAKE_INTERVAL,
        model_name: str = MODEL_NAME,
        temperature: float = TEMPERATURE,
        api_key: Optional[str] = None,
    ) -> None:
        """
        初始化 Agent 实例。
        
        Args:
            name: Agent 名称
            awake_interval: 苏醒间隔（秒）
            model_name: 模型名称
            temperature: 模型温度
            api_key: OpenAI API Key（如果为 None，从环境变量读取）
        """
        self.name = name
        self.awake_interval = awake_interval
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # 获取 API Key
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        
        if not api_key:
            raise ValueError(
                "未设置 OPENAI_API_KEY 环境变量。"
                "请设置: export OPENAI_API_KEY='your-api-key'"
            )
        
        # 创建 LangChain Tool
        self.tools = create_langchain_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # 创建 LLM
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
        )
        
        # 绑定工具到 LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 启动时间
        self.start_time = datetime.now()
        
        self.logger.info(f"{self.name} 已初始化")
        self.logger.info(f"苏醒间隔: {self.awake_interval} 秒")
        self.logger.info(f"模型: {model_name}")
        self.logger.info(f"可用工具: {[t.name for t in self.tools]}")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词。
        
        Returns:
            格式化的系统提示词
        """
        return SYSTEM_PROMPT.format(
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            project_root=os.path.dirname(os.path.abspath(__file__)),
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
    
    def think_and_act(self) -> bool:
        """
        苏醒时执行一次思考和行动。
        
        流程：
        1. 构建系统提示词
        2. 调用 LLM 进行推理
        3. 执行工具调用
        4. 返回结果给 LLM 继续推理
        5. 直到 Agent 认为任务完成
        
        Returns:
            如果应该继续运行返回 True，如果触发了重启返回 False
        """
        messages = [SystemMessage(content=self._build_system_prompt())]
        
        self.logger.info("Agent 苏醒，开始思考...")
        
        max_iterations = 10  # 最大工具调用次数，防止无限循环
        iterations = 0
        
        try:
            while iterations < max_iterations:
                iterations += 1
                
                # 调用 LLM
                self.logger.debug(f"LLM 调用 (迭代 {iterations})")
                response = self.llm_with_tools.invoke(messages)
                messages.append(response)
                
                # 检查是否有工具调用
                if not hasattr(response, 'tool_calls') or not response.tool_calls:
                    # 没有工具调用，检查是否表示结束
                    self.logger.info(f"Agent 响应: {response.content[:200]}...")
                    
                    # 检查是否触发重启
                    if self._should_restart(response.content):
                        self.logger.info("检测到重启请求...")
                        # 需要手动触发 restart
                    
                    return True  # 任务完成，继续运行
                
                # 执行工具调用
                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']
                    
                    self.logger.info(f"执行工具: {tool_name}")
                    self.logger.debug(f"参数: {tool_args}")
                    
                    # 查找工具
                    if tool_name not in self.tool_map:
                        tool_result = f"错误: 未知工具 {tool_name}"
                    else:
                        tool = self.tool_map[tool_name]
                        try:
                            # 调用工具
                            tool_result = tool.invoke(tool_args)
                        except Exception as e:
                            tool_result = f"错误: {str(e)}"
                    
                    # 检查是否是重启工具
                    if tool_name == "trigger_self_restart":
                        self.logger.info("触发自我重启...")
                        # 将工具结果添加到消息
                        messages.append(HumanMessage(
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
                    
                    # 将工具结果添加到消息
                    messages.append(HumanMessage(
                        content=self._format_tool_result(tool_name, tool_result),
                        tool_call_id=tool_call['id'],
                    ))
                
                # 检查是否触发了重启
                if not self._should_restart(messages[-1].content if hasattr(messages[-1], 'content') else ""):
                    pass
                    
            # 达到最大迭代次数
            self.logger.warning(f"达到最大迭代次数 ({max_iterations})，结束当前循环")
            return True
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号")
            return False
        except Exception as e:
            self.logger.error(f"思考过程中发生错误: {e}", exc_info=True)
            return True  # 发生错误仍然继续运行
    
    def run_loop(self) -> None:
        """
        运行 Agent 主循环。
        
        循环：每 60 秒苏醒一次，思考并行动。
        """
        self.logger.info("=" * 60)
        self.logger.info(f"{self.name} 主循环开始")
        self.logger.info(f"苏醒间隔: {self.awake_interval} 秒")
        self.logger.info("=" * 60)
        
        try:
            while True:
                # 苏醒并执行思考
                should_continue = self.think_and_act()
                
                if not should_continue:
                    # 重启已触发，退出主循环
                    self.logger.info("主循环结束，等待重启...")
                    break
                
                # 显示下次苏醒时间
                next_wake = datetime.now().timestamp() + self.awake_interval
                next_wake_time = datetime.fromtimestamp(next_wake).strftime("%H:%M:%S")
                self.logger.info(f"下次苏醒时间: {next_wake_time}")
                
                # 休眠等待下次苏醒
                self.logger.info(f"进入休眠状态 ({self.awake_interval} 秒)...")
                time.sleep(self.awake_interval)
                
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
    # 配置日志
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("自我进化 Agent 系统启动")
    logger.info("=" * 60)
    
    # 检查环境变量
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.error("错误: 未设置 OPENAI_API_KEY 环境变量")
        logger.info("请在运行前设置: $env:OPENAI_API_KEY='your-api-key'")
        logger.info("或者: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    try:
        # 创建并运行 Agent
        agent = SelfEvolvingAgent(name="EvoAgent-001")
        
        logger.info(f"Agent 状态:")
        logger.info(f"  - 名称: {agent.name}")
        logger.info(f"  - 模型: {MODEL_NAME}")
        logger.info(f"  - 苏醒间隔: {AWAKE_INTERVAL} 秒")
        logger.info(f"  - 工具数量: {len(agent.tools)}")
        
        # 启动主循环
        agent.run_loop()
        
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Agent 系统已关闭")


if __name__ == "__main__":
    main()
