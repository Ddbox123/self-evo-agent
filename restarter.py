#!/usr/bin/env python3
"""
独立守护进程脚本 - restarter.py

此脚本作为独立进程运行，负责管理 Agent 的重启生命周期。

工作流程：
1. 接收原 Agent 的 PID 和脚本路径作为命令行参数
2. 使用 psutil 轮询等待原进程结束
3. 原进程死亡后，使用 subprocess 拉起新的 Agent 进程
4. 支持 Windows 和 Unix 系统

使用场景：
- 当 Agent 需要自我重启时（如代码更新后）
- Agent 出现异常需要恢复时
- 定期刷新 Agent 状态时

示例用法：
    python restarter.py --pid 12345 --script ./agent.py
    python restarter.py 12345 ./agent.py
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 跨平台支持
PLATFORM = sys.platform
IS_WINDOWS = PLATFORM == "win32"
IS_UNIX = PLATFORM in ("darwin", "linux", "freebsd")

# 尝试导入 psutil，如果失败则给出提示
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    if 'logger' in locals():
        logger.warning("psutil 未安装，restarter 功能将受限")
        logger.info("请运行: pip install psutil")
    else:
        print("警告: psutil 未安装，restarter 功能将受限")
        print("请运行: pip install psutil")


# ============================================================================
# 配置常量
# ============================================================================

# 轮询间隔（秒）- 平衡响应速度和 CPU 消耗
POLL_INTERVAL = 0.5

# 等待进程结束的最大超时时间（秒）
MAX_WAIT_TIME = 60

# 日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    配置日志系统。
    
    Args:
        verbose: 是否启用详细日志输出
        
    Returns:
        配置好的 logger 实例
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout
    )
    
    return logging.getLogger("Restarter")


# ============================================================================
# 核心功能函数
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数。
    
    支持两种格式：
    1. 命名参数: --pid 12345 --script ./agent.py
    2. 位置参数: 12345 ./agent.py
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description="Agent 进程重启守护进程",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python restarter.py --pid 12345 --script ./agent.py
  python restarter.py 12345 ./agent.py --verbose
  python restarter.py --pid 12345 --script ./agent.py --env KEY=VALUE
        """
    )
    
    parser.add_argument(
        'pid',
        nargs='?',
        type=int,
        help='要监控的原始 Agent 进程的 PID'
    )
    
    parser.add_argument(
        'script',
        nargs='?',
        type=str,
        help='Agent 脚本的路径'
    )
    
    parser.add_argument(
        '--pid',
        dest='pid_named',
        type=int,
        help='要监控的原始 Agent 进程的 PID (命名参数)'
    )
    
    parser.add_argument(
        '--script',
        dest='script_named',
        type=str,
        help='Agent 脚本的路径 (命名参数)'
    )
    
    parser.add_argument(
        '--env',
        dest='env_vars',
        action='append',
        help='传递给新进程的环境变量，格式 KEY=VALUE'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )
    
    args = parser.parse_args()
    
    # 合并位置参数和命名参数
    pid = args.pid or args.pid_named
    script = args.script or args.script_named
    
    if pid is None:
        parser.error("必须提供 PID")
    if script is None:
        parser.error("必须提供脚本路径")
    
    # 构建环境变量字典
    env_dict = {}
    if args.env_vars:
        for env_str in args.env_vars:
            if '=' in env_str:
                key, value = env_str.split('=', 1)
                env_dict[key] = value
    
    return argparse.Namespace(
        pid=pid,
        script=script,
        env_vars=env_dict,
        verbose=args.verbose
    )


def is_process_alive(pid: int) -> bool:
    """
    检查指定 PID 的进程是否仍在运行。
    
    Args:
        pid: 进程 ID
        
    Returns:
        如果进程存在且正在运行返回 True，否则返回 False
    """
    if not PSUTIL_AVAILABLE:
        # 如果没有 psutil，使用系统命令
        if IS_WINDOWS:
            import subprocess
            try:
                subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                             capture_output=True, check=False)
                # Windows 上使用 taskkill 检查进程
                result = subprocess.run(
                    ['taskkill', '/FI', f'PID eq {pid}', '/NR', 'FALSE'],
                    capture_output=True, text=True
                )
                return 'SUCCESS' in result.stdout or result.returncode == 0
            except Exception:
                return False
        else:
            import subprocess
            try:
                subprocess.run(['kill', '-0', str(pid)],
                             capture_output=True, check=False)
                return True
            except Exception:
                return False
    
    try:
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def wait_for_process_death(pid: int, timeout: float = MAX_WAIT_TIME,
                           poll_interval: float = POLL_INTERVAL,
                           logger: Optional[logging.Logger] = None) -> bool:
    """
    等待指定进程结束。
    
    Args:
        pid: 要等待的进程 ID
        timeout: 最大等待时间（秒）
        poll_interval: 轮询间隔（秒）
        logger: 可选的日志记录器
        
    Returns:
        如果进程在超时时间内结束返回 True，超时返回 False
    """
    start_time = time.time()
    last_log_time = start_time
    
    while time.time() - start_time < timeout:
        if not is_process_alive(pid):
            elapsed = time.time() - start_time
            msg = f"进程 {pid} 已结束 (耗时 {elapsed:.2f} 秒)"
            if logger:
                logger.info(msg)
            else:
                print(msg)
            return True
        
        # 每 5 秒记录一次状态，避免日志过多
        current_time = time.time()
        if current_time - last_log_time >= 5:
            elapsed = current_time - start_time
            msg = f"等待进程 {pid} 结束... (已等待 {elapsed:.1f} 秒)"
            if logger:
                logger.debug(msg)
            last_log_time = current_time
        
        time.sleep(poll_interval)
    
    msg = f"等待进程 {pid} 结束超时 ({timeout} 秒)"
    if logger:
        logger.warning(msg)
    else:
        print(f"警告: {msg}")
    return False


def spawn_new_process(script_path: str, env: Optional[dict] = None,
                      logger: Optional[logging.Logger] = None) -> Optional[int]:
    """
    启动新的 Agent 进程。
    
    Args:
        script_path: Agent 脚本的路径
        env: 可选的环境变量字典
        logger: 可选的日志记录器
        
    Returns:
        新进程的 PID，失败返回 None
    """
    script_abs = os.path.abspath(script_path)
    
    if not os.path.exists(script_abs):
        msg = f"脚本文件不存在: {script_abs}"
        if logger:
            logger.error(msg)
        else:
            print(f"错误: {msg}")
        return None
    
    msg = f"启动新进程: {script_abs}"
    if logger:
        logger.info(msg)
    else:
        print(msg)
    
    try:
        # 构建环境变量
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # 日志文件路径
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'agent_realtime.log')
        
        if IS_WINDOWS:
            # Windows: 使用 pythonw.exe 后台运行，或使用 CREATE_NEW_PROCESS_GROUP
            # 这样可以让子进程独立于父进程
            creation_flags = 0x08000000  # CREATE_NO_WINDOW
            
            process = __import__('subprocess').Popen(
                [sys.executable, script_abs],
                env=process_env,
                creationflags=creation_flags,
                stdout=open(log_file, 'a', encoding='utf-8'),
                stderr=subprocess.STDOUT
            )
        else:
            # Unix: 使用 os.setsid 创建新的会话组
            import subprocess
            
            # 第一次 fork: 脱离父进程
            pid = os.fork()
            if pid == 0:
                # 子进程
                try:
                    # 第二次 fork: 确保进程不会成为会话首进程
                    pid = os.fork()
                    if pid == 0:
                        # 孙子进程：执行目标脚本，输出到日志文件
                        os.setsid()  # 创建新的会话
                        os.chdir(log_dir)
                        with open(log_file, 'a') as f:
                            os.dup2(f.fileno(), 1)  # stdout -> log file
                            os.dup2(f.fileno(), 2)  # stderr -> log file
                        os.execvp(sys.executable, [sys.executable, script_abs])
                    else:
                        # 子进程：立即退出
                        os._exit(0)
                except OSError as e:
                    os._exit(f"Fork failed: {e}")
            else:
                # 父进程：等待子进程退出
                os.waitpid(pid, 0)
                return None
        
        # 对于 Windows 或非 fork 方式，使用标准 subprocess
        if not IS_UNIX or IS_WINDOWS:
            import subprocess
            process = subprocess.Popen(
                [sys.executable, script_abs],
                env=process_env,
                stdout=open(log_file, 'a', encoding='utf-8'),
                stderr=subprocess.STDOUT,
                start_new_session=True if not IS_WINDOWS else False
            )
            new_pid = process.pid
            
            msg = f"新进程已启动，PID: {new_pid}"
            if logger:
                logger.info(msg)
            else:
                print(msg)
            
            return new_pid
        
    except Exception as e:
        msg = f"启动新进程失败: {e}"
        if logger:
            logger.error(msg)
        else:
            print(f"错误: {msg}")
        return None


def run_restarter(pid: int, script_path: str, env_vars: Optional[dict] = None,
                 verbose: bool = False) -> int:
    """
    运行重启守护进程的主要逻辑。
    
    Args:
        pid: 要监控的原始进程 PID
        script_path: Agent 脚本路径
        env_vars: 传递给新进程的环境变量
        verbose: 是否输出详细日志
        
    Returns:
        退出状态码: 0 表示成功，非 0 表示失败
    """
    logger = setup_logging(verbose)
    
    logger.info("=" * 60)
    logger.info("Restarter 守护进程启动")
    logger.info("=" * 60)
    logger.info(f"监控进程 PID: {pid}")
    logger.info(f"目标脚本: {script_path}")
    
    if env_vars:
        logger.info(f"环境变量: {env_vars}")
    
    # 检查进程是否已经在运行
    if is_process_alive(pid):
        logger.info(f"进程 {pid} 仍在运行，等待其结束...")
        
        # 等待进程结束
        if not wait_for_process_death(pid, logger=logger):
            logger.warning("等待超时，但将继续启动新进程")
    else:
        logger.info(f"进程 {pid} 已经不存在")
    
    # 额外等待一小段时间，确保进程完全清理
    logger.info("等待进程资源释放...")
    time.sleep(1)
    
    # 启动新进程
    logger.info("-" * 40)
    new_pid = spawn_new_process(script_path, env_vars, logger)
    
    if new_pid:
        logger.info("-" * 40)
        logger.info(f"重启完成！新进程 PID: {new_pid}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("重启失败")
        logger.info("=" * 60)
        return 1


# ============================================================================
# 主入口
# ============================================================================

def main() -> int:
    """
    程序主入口点。
    
    Returns:
        退出状态码
    """
    try:
        args = parse_arguments()
        return run_restarter(
            pid=args.pid,
            script_path=args.script,
            env_vars=args.env_vars,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        print("\n收到中断信号，守护进程退出")
        return 130
    except Exception as e:
        print(f"守护进程异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
