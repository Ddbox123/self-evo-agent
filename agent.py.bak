#!/usr/bin/env python3
"""
自我进化 Agent - 主入口文件

该项目实现了一个能够自我进化的 AI Agent，具备以下核心能力：
1. 通过网络搜索获取新知识
2. 读取和修改自己的源代码
3. 语法自检确保代码质量
4. 通过独立守护进程实现自我重启

Agent 采用"感知 -> 思考 -> 行动"的循环框架运行。

架构说明：
- Agent 运行主逻辑循环
- 需要重启时，通过脱离父进程的方式唤起 restarter.py
- Agent 自我了结后，restarter.py 等待原进程死亡，重新拉起新 Agent 进程
"""

import sys
import os
import logging
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径，以便导入 tools 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.web_tools import web_search, read_webpage
from tools.file_tools import list_directory, read_local_file
from tools.code_tools import edit_local_file, create_new_file
from tools.safety_tools import check_syntax, backup_project
from tools.rebirth_tools import trigger_self_restart


# ============================================================================
# 配置与常量
# ============================================================================

LOG_LEVEL = logging.INFO
MAX_ITERATIONS = 1000  # 单次运行的最大迭代次数
RESTART_THRESHOLD = 100  # 达到此迭代次数后触发自我重启（保持新鲜感）


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging() -> None:
    """
    配置全局日志系统。
    
    设置日志格式和级别，输出到标准输出。
    日志包含时间戳、日志级别、模块名和消息内容。
    """
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )


# ============================================================================
# Agent 核心类
# ============================================================================

class SelfEvolvingAgent:
    """
    自我进化 Agent 主类。
    
    负责管理 Agent 的生命周期、工具调用和主循环逻辑。
    采用"感知 -> 思考 -> 行动"的架构模式。
    
    Attributes:
        name: Agent 实例的名称，用于日志和标识
        iteration: 当前迭代计数器
        running: 控制 Agent 运行状态的标志位
        tools: 可用的工具字典，键为工具名，值为工具函数
    """
    
    def __init__(self, name: str = "SelfEvolvingAgent") -> None:
        """
        初始化 Agent 实例。
        
        Args:
            name: Agent 的名称，默认为 "SelfEvolvingAgent"
        """
        self.name = name
        self.iteration: int = 0
        self.running: bool = True
        self.logger = logging.getLogger(f"Agent.{name}")
        
        # 初始化可用工具映射
        self.tools: Dict[str, Any] = {
            'web_search': web_search,
            'read_webpage': read_webpage,
            'list_directory': list_directory,
            'read_local_file': read_local_file,
            'edit_local_file': edit_local_file,
            'create_new_file': create_new_file,
            'check_syntax': check_syntax,
            'backup_project': backup_project,
            'trigger_self_restart': trigger_self_restart,
        }
        
        self.logger.info(f"{self.name} 已初始化")
        self.logger.info(f"可用工具数量: {len(self.tools)}")
    
    def perceive(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        感知阶段：收集当前状态和环境信息。
        
        Args:
            context: 可选的外部上下文信息
            
        Returns:
            包含当前状态信息的字典，包括：
            - iteration: 当前迭代次数
            - running: 运行状态
            - timestamp: 时间戳
        """
        import datetime
        
        state = {
            'iteration': self.iteration,
            'running': self.running,
            'timestamp': datetime.datetime.now().isoformat(),
        }
        
        if context:
            state['context'] = context
        
        self.logger.debug(f"感知阶段: {state}")
        return state
    
    def think(self, state: Dict[str, Any]) -> str:
        """
        思考阶段：根据当前状态决定下一步行动。
        
        Args:
            state: 感知阶段收集的状态信息
            
        Returns:
            要执行的行动描述（工具调用）
        """
        # 检查是否需要重启
        if self.iteration >= RESTART_THRESHOLD:
            self.logger.info("达到重启阈值，准备触发自我重启")
            return "trigger_self_restart:threshold_reached"
        
        # 简单的演示逻辑：每10次迭代进行一次备份
        if self.iteration > 0 and self.iteration % 10 == 0:
            self.logger.info(f"第 {self.iteration} 次迭代，执行维护任务")
            return "backup_project:periodic_backup"
        
        # 正常迭代，等待进一步指令
        return "idle:awaiting_instruction"
    
    def act(self, action: str) -> Dict[str, Any]:
        """
        行动阶段：执行决定的行动。
        
        Args:
            action: 行动描述，格式为 "tool_name:reason" 或 "idle:reason"
            
        Returns:
            行动执行结果的字典，包含 success 布尔值和可选的 result/error
        """
        self.logger.info(f"执行行动: {action}")
        
        # 处理空闲状态
        if action.startswith("idle:"):
            return {'success': True, 'result': 'idle', 'message': '等待下一指令'}
        
        # 解析行动
        parts = action.split(":", 1)
        if len(parts) != 2:
            return {'success': False, 'error': f'无效的行动格式: {action}'}
        
        tool_name, reason = parts
        
        # 检查工具是否存在
        if tool_name not in self.tools:
            return {'success': False, 'error': f'未知工具: {tool_name}'}
        
        try:
            tool_func = self.tools[tool_name]
            
            # 根据不同工具准备参数
            if tool_name == "backup_project":
                result = tool_func(f"定期备份 - 迭代 {self.iteration}")
            elif tool_name == "trigger_self_restart":
                result = tool_func(f"迭代 {self.iteration} 达到阈值 {RESTART_THRESHOLD}")
            else:
                result = tool_func(reason)
            
            return {'success': True, 'result': result, 'tool': tool_name}
            
        except Exception as e:
            self.logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
            return {'success': False, 'error': str(e), 'tool': tool_name}
    
    def run_loop(self) -> None:
        """
        运行 Agent 的主循环。
        
        循环执行 "感知 -> 思考 -> 行动" 流程，
        直到 running 标志被设为 False 或达到最大迭代次数。
        """
        self.logger.info(f"{self.name} 主循环开始")
        
        try:
            while self.running and self.iteration < MAX_ITERATIONS:
                # 1. 感知阶段
                state = self.perceive()
                
                # 2. 思考阶段
                action = self.think(state)
                
                # 3. 行动阶段
                result = self.act(action)
                
                # 4. 处理结果
                if result.get('success'):
                    self.logger.debug(f"行动成功: {result.get('result', 'OK')}")
                else:
                    self.logger.warning(f"行动失败: {result.get('error', '未知错误')}")
                
                # 如果触发重启，act 方法会调用 trigger_self_restart
                # 此时当前进程将被终止
                
                self.iteration += 1
                
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在关闭...")
            self.running = False
        except Exception as e:
            self.logger.error(f"主循环异常: {e}", exc_info=True)
            self.running = False
        finally:
            self.logger.info(f"{self.name} 主循环结束 (迭代次数: {self.iteration})")
    
    def get_available_tools(self) -> List[str]:
        """
        获取所有可用工具的名称列表。
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取 Agent 当前状态。
        
        Returns:
            包含 Agent 状态信息的字典
        """
        return {
            'name': self.name,
            'iteration': self.iteration,
            'running': self.running,
            'tools_count': len(self.tools),
            'tools': self.get_available_tools(),
        }


# ============================================================================
# 主入口
# ============================================================================

def main() -> None:
    """
    程序主入口点。
    
    初始化日志系统，创建 Agent 实例，并启动主循环。
    """
    setup_logging()
    logger = logging.getLogger("Main")
    
    logger.info("=" * 60)
    logger.info("自我进化 Agent 系统启动")
    logger.info("=" * 60)
    
    # 创建并运行 Agent
    agent = SelfEvolvingAgent(name="EvoAgent-001")
    
    logger.info(f"Agent 状态: {agent.get_status()}")
    
    # 启动主循环
    agent.run_loop()
    
    logger.info("Agent 系统已关闭")


if __name__ == "__main__":
    main()
