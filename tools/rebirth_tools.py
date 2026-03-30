"""
重生工具模块

提供 Agent 自我重启的核心功能，通过独立守护进程实现安全的进程重启。

本模块是实现"自我进化"能力的关键组件：
1. 触发自我重启 - 启动独立的 restarter.py 进程
2. 脱离父进程 - 确保重启过程不影响原 Agent
3. 跨平台兼容 - 同时支持 Windows 和 Unix 系统

架构说明：
- 当 Agent 需要重启时，调用 trigger_self_restart()
- 该函数使用 subprocess 启动 restarter.py 作为独立进程
- restarter.py 监控原 Agent 进程，等待其结束
- 原进程结束后，restarter.py 拉起新的 Agent 进程
- 当前 Agent 在启动 restarter 后执行 sys.exit(0) 自我了结

依赖：
    - os: 内置模块
    - sys: 内置模块
    - subprocess: 内置模块
    - pathlib: 内置模块
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional


# ============================================================================
# 配置常量
# ============================================================================

# 日志记录器
logger = logging.getLogger(__name__)

# Restarter 脚本路径
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
RESTARTER_SCRIPT = PROJECT_ROOT / "restarter.py"

# 重启原因分类
RESTART_REASONS = {
    'code_update': '代码更新后重启',
    'threshold_reached': '达到运行阈值重启',
    'manual': '手动触发重启',
    'error_recovery': '错误恢复重启',
    'scheduled': '定时重启',
    'maintenance': '维护重启',
}


# ============================================================================
# 辅助函数
# ============================================================================

def get_current_pid() -> int:
    """
    获取当前进程的 PID。
    
    Returns:
        当前进程的进程 ID
    """
    return os.getpid()


def get_script_path() -> str:
    """
    获取 Agent 主脚本的路径。
    
    Returns:
        agent.py 的绝对路径
    """
    return str(PROJECT_ROOT / "agent.py")


def classify_restart_reason(reason: str) -> str:
    """
    分类重启原因。
    
    Args:
        reason: 重启原因描述
        
    Returns:
        分类后的原因类别
    """
    reason_lower = reason.lower()
    
    for category, desc in RESTART_REASONS.items():
        if category in reason_lower:
            return category
    
    return 'manual'


def validate_restarter_available() -> tuple[bool, str]:
    """
    验证 restarter.py 是否可用。
    
    Returns:
        (是否可用, 错误消息) 元组
    """
    if not RESTARTER_SCRIPT.exists():
        return False, f"Restarter 脚本不存在: {RESTARTER_SCRIPT}"
    
    if not os.access(RESTARTER_SCRIPT, os.R_OK):
        return False, f"Restarter 脚本不可读: {RESTARTER_SCRIPT}"
    
    return True, ""


# ============================================================================
# 跨平台进程脱离逻辑
# ============================================================================

def spawn_detached_process_windows(command: list, env: Optional[dict] = None) -> Optional[int]:
    """
    在 Windows 上启动脱离父进程的子进程。
    
    使用 CREATE_NEW_PROCESS_GROUP 标志创建独立进程，
    使得子进程不受父进程终止影响。
    
    Args:
        command: 命令列表
        env: 可选的环境变量
        
    Returns:
        新进程的 PID，失败返回 None
    """
    try:
        import subprocess
        
        # Windows: 使用 CREATE_NO_WINDOW 避免弹出控制台窗口
        # 使用 CREATE_NEW_PROCESS_GROUP 使进程独立
        creation_flags = 0x08000000  # CREATE_NO_WINDOW
        # 在某些情况下可能需要 0x00000200 (CREATE_NEW_PROCESS_GROUP)
        
        process = subprocess.Popen(
            command,
            env=env,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=False
        )
        
        logger.info(f"Windows: 已启动脱离进程, PID: {process.pid}")
        return process.pid
        
    except Exception as e:
        logger.error(f"Windows: 启动脱离进程失败 - {e}")
        return None


def spawn_detached_process_unix(command: list, env: Optional[dict] = None) -> Optional[int]:
    """
    在 Unix 系统上启动脱离父进程的子进程。
    
    使用 double-fork 技术：
    1. 第一次 fork：子进程从父进程分离
    2. 第二次 fork：确保进程不会成为会话首进程
    3. setsid()：创建新的会话，完全脱离父进程
    
    Args:
        command: 命令列表
        env: 可选的环境变量
        
    Returns:
        新进程的 PID，失败返回 None
    """
    try:
        # 第一次 fork
        pid = os.fork()
        
        if pid == 0:
            # 子进程（第一次 fork 后）
            try:
                # 第二次 fork
                pid = os.fork()
                
                if pid == 0:
                    # 孙子进程（最终运行的进程）
                    # 创建新会话，完全脱离
                    os.setsid()
                    
                    # 执行目标命令
                    os.execvp(command[0], command)
                else:
                    # 子进程：立即退出，让孙子进程成为孤儿
                    os._exit(0)
                    
            except OSError as e:
                logger.error(f"Unix fork error: {e}")
                os._exit(1)
        else:
            # 父进程：等待子进程退出
            os.waitpid(pid, 0)
            logger.info(f"Unix: 已启动脱离进程, 中间 PID: {pid}")
            return pid
            
    except Exception as e:
        logger.error(f"Unix: 启动脱离进程失败 - {e}")
        return None


def spawn_detached_process(command: list, env: Optional[dict] = None) -> Optional[int]:
    """
    跨平台启动脱离父进程的子进程。
    
    根据操作系统自动选择合适的实现方式：
    - Windows: 使用 CREATE_NEW_PROCESS_GROUP
    - Unix/Linux/macOS: 使用 double-fork + setsid
    
    Args:
        command: 命令列表 [python, script_path, ...]
        env: 可选的环境变量
        
    Returns:
        新进程的 PID，失败返回 None
    """
    if sys.platform == 'win32':
        return spawn_detached_process_windows(command, env)
    else:
        return spawn_detached_process_unix(command, env)


# ============================================================================
# 核心功能函数
# ============================================================================

def trigger_self_restart(reason: str = "") -> str:
    """
    触发 Agent 自我重启。
    
    此函数是实现 Agent 自我进化能力的核心。它会：
    1. 验证 restarter.py 是否可用
    2. 启动 restarter.py 作为独立进程
    3. 记录重启日志
    4. 返回后调用方应该执行 sys.exit(0)
    
    重启流程：
    ```
    Agent 进程                    Restarter 进程
        |                               |
        | --- 启动 restarter.py ------> |
        |                               |
        | --- 执行 sys.exit(0) -----> X  |
        |                               |
        |           (等待原进程结束)      |
        |                               |
        |           <-- 拉起新 Agent --- |
    ```
    
    Args:
        reason: 重启原因描述。
               用于日志记录和调试。
               
               建议格式：简洁的关键词 + 简短说明
               示例：
               - "threshold_reached: 迭代次数达到 100"
               - "code_update: 代码已修改，需要重新加载"
               - "manual: 用户请求重启"
               - "scheduled: 每日定时重启"
               - "error_recovery: 发生错误后恢复"
    
    Returns:
        操作结果的描述字符串。
        
        成功时返回：
        ```
        ✓ 重启进程已触发
        PID: 12345
        原因: threshold_reached: 迭代次数达到 100
        Restarter: /path/to/restarter.py
        状态: 已脱离，正在启动守护进程
        
        当前进程将退出，请等待自动重启...
        ```
        
        失败时返回错误描述：
        - "错误: Restarter 脚本不存在"
        - "错误: 无法获取当前 PID"
        - "错误: 启动重启进程失败"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
        调用方需要检查返回值，如果有错误则不应调用 sys.exit()。
    
    Example:
        >>> result = trigger_self_restart("代码已更新")
        >>> if "成功" in result or "✓" in result:
        ...     print("即将重启...")
        ...     sys.exit(0)  # Agent 自我了结
        ... else:
        ...     print(f"重启失败: {result}")
        
        >>> # 在 Agent 类中使用
        >>> def handle_restart(self):
        ...     result = trigger_self_restart("达到重启阈值")
        ...     if "✓" in result:
        ...         return result  # 返回给调用者处理退出
        ...     return result  # 错误处理
    
    Notes:
        - 此函数不执行 sys.exit()，调用方需要自行处理
        - 启动 restarter 后，原 Agent 应尽快调用 sys.exit(0)
        - 如果不立即退出，restarter 可能无法正确接管
        - 重启是异步的，新 Agent 可能在几秒后启动
        - 可以通过 --verbose 参数查看详细日志
    """
    logger.info("=" * 60)
    logger.info("触发自我重启")
    logger.info("=" * 60)
    
    # 1. 获取必要信息
    current_pid = get_current_pid()
    script_path = get_script_path()
    
    logger.info(f"当前 PID: {current_pid}")
    logger.info(f"脚本路径: {script_path}")
    logger.info(f"重启原因: {reason}")
    
    # 2. 验证 restarter 可用性
    is_available, error_msg = validate_restarter_available()
    if not is_available:
        logger.error(f"Restarter 不可用: {error_msg}")
        return f"错误: {error_msg}"
    
    logger.info(f"Restarter 脚本: {RESTARTER_SCRIPT}")
    
    # 3. 分类重启原因
    reason_category = classify_restart_reason(reason)
    logger.info(f"原因分类: {reason_category}")
    
    # 4. 构建环境变量
    env = os.environ.copy()
    env['AGENT_RESTART_REASON'] = reason
    env['AGENT_RESTART_CATEGORY'] = reason_category
    env['AGENT_ORIGINAL_PID'] = str(current_pid)
    
    # 5. 构建命令
    command = [
        sys.executable,  # Python 解释器路径
        str(RESTARTER_SCRIPT),
        '--pid', str(current_pid),
        '--script', script_path,
    ]
    
    # 添加详细日志参数（可选）
    # command.append('--verbose')
    
    logger.info(f"执行命令: {' '.join(command)}")
    
    # 6. 启动脱离进程
    new_pid = spawn_detached_process(command, env)
    
    if new_pid:
        # 构建成功消息
        result_lines = [
            "✓ 重启进程已触发",
            f"PID: {current_pid}",
            f"原因: {reason}",
            f"Restarter: {RESTARTER_SCRIPT}",
            "",
            "状态: 已脱离父进程，正在启动守护进程",
            "",
            "当前进程将退出，请等待自动重启...",
        ]
        
        result = "\n".join(result_lines)
        
        logger.info("=" * 60)
        logger.info("重启触发成功")
        logger.info("当前 Agent 进程即将退出")
        logger.info("=" * 60)
        
        return result
    else:
        error_msg = "错误: 启动重启进程失败"
        logger.error(error_msg)
        return error_msg


def get_restart_log_path() -> Path:
    """
    获取重启日志文件的路径。
    
    Returns:
        日志文件路径
    """
    return PROJECT_ROOT / "logs" / "restart.log"


def write_restart_log(pid: int, reason: str, success: bool) -> None:
    """
    写入重启日志。
    
    Args:
        pid: 触发重启的进程 PID
        reason: 重启原因
        success: 是否成功触发
    """
    from datetime import datetime
    
    log_path = get_restart_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    status = "SUCCESS" if success else "FAILED"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} | PID:{pid} | {status} | {reason}\n")
