# -*- coding: utf-8 -*-
"""
Observer Dashboard 后端服务

轻量级异步 Web 服务器，提供：
- GET /: 返回前端页面
- GET /api/data: 返回 memory.json 和 plan.md 内容
- WS /ws/logs: WebSocket 实时推送日志
- WS /ws/state: WebSocket 实时推送状态更新
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Set

# FastAPI 相关
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("[Dashboard] FastAPI 未安装，请运行: pip install fastapi uvicorn")

# Uvicorn (ASGI 服务器)
try:
    import uvicorn
    HAS_UVICORN = True
except ImportError:
    HAS_UVICORN = False

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
STATE_FILE = PROJECT_ROOT / "agent_state.json"
LOG_FILE = PROJECT_ROOT / "logs" / "agent_realtime.log"
MEMORY_FILE = PROJECT_ROOT / "workspace" / "memory.json"
PLAN_FILE = PROJECT_ROOT / "plan.md"

# 确保日志文件存在
LOG_FILE.parent.mkdir(exist_ok=True)
if not LOG_FILE.exists():
    LOG_FILE.touch()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ObserverDashboard")


class DashboardServer:
    """仪表板服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(title="Observer Dashboard", version="1.0.0")
        self.log_connections: Set[WebSocket] = set()
        self.state_connections: Set[WebSocket] = set()
        self._setup_routes()
        self._log_broadcast_task: Optional[asyncio.Task] = None
        self._state_broadcast_task: Optional[asyncio.Task] = None
        self._shutdown_flag = False
        self._server = None

    def shutdown(self):
        """请求关闭服务器"""
        self._shutdown_flag = True
        if self._server:
            self._server.should_exit = True

    def _setup_routes(self):
        """设置路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """返回前端页面"""
            template_path = Path(__file__).parent / "templates" / "index.html"
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return """
                <html><head><title>Observer Dashboard</title></head>
                <body><h1>Dashboard Template Not Found</h1></body>
                </html>
                """

        @self.app.get("/api/data")
        async def get_data():
            """获取 Agent 数据"""
            data = {
                "state": self._read_state(),
                "memory": self._read_memory(),
                "plan": self._read_plan(),
                "timestamp": datetime.now().isoformat(),
            }
            return JSONResponse(content=data)

        @self.app.get("/api/state")
        async def get_state():
            """获取 Agent 状态"""
            return JSONResponse(content=self._read_state())

        @self.app.websocket("/ws/logs")
        async def websocket_logs(websocket: WebSocket):
            """WebSocket 日志流"""
            await websocket.accept()
            self.log_connections.add(websocket)
            logger.info(f"日志 WebSocket 连接: {websocket.client}")

            # 发送欢迎消息
            await websocket.send_json({
                "type": "connected",
                "message": "已连接到日志流",
                "timestamp": datetime.now().isoformat(),
            })

            # 发送最近的日志
            recent_logs = self._read_recent_logs(50)
            for log in recent_logs:
                await websocket.send_text(log)

            try:
                # 保持连接并监听新日志
                last_pos = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0

                while True:
                    # 检查新日志
                    if LOG_FILE.exists():
                        current_size = LOG_FILE.stat().st_size
                        if current_size > last_pos:
                            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                                f.seek(last_pos)
                                new_lines = f.readlines()
                                last_pos = current_size
                                for line in new_lines:
                                    if line.strip():
                                        await websocket.send_text(line.strip())

                    await asyncio.sleep(0.5)

            except WebSocketDisconnect:
                logger.info(f"日志 WebSocket 断开: {websocket.client}")
            except Exception as e:
                logger.error(f"日志 WebSocket 错误: {e}")
            finally:
                self.log_connections.discard(websocket)

        @self.app.websocket("/ws/state")
        async def websocket_state(websocket: WebSocket):
            """WebSocket 状态流"""
            await websocket.accept()
            self.state_connections.add(websocket)
            logger.info(f"状态 WebSocket 连接: {websocket.client}")

            # 发送当前状态
            await websocket.send_json(self._read_state())

            try:
                last_mtime = 0
                if STATE_FILE.exists():
                    last_mtime = STATE_FILE.stat().st_mtime

                while True:
                    # 检查状态文件变化
                    if STATE_FILE.exists():
                        current_mtime = STATE_FILE.stat().st_mtime
                        if current_mtime > last_mtime:
                            last_mtime = current_mtime
                            state = self._read_state()
                            await websocket.send_json(state)

                    await asyncio.sleep(1)

            except WebSocketDisconnect:
                logger.info(f"状态 WebSocket 断开: {websocket.client}")
            except Exception as e:
                logger.error(f"状态 WebSocket 错误: {e}")
            finally:
                self.state_connections.discard(websocket)

        @self.app.get("/health")
        async def health():
            """健康检查"""
            return {"status": "ok", "timestamp": datetime.now().isoformat()}

        @self.app.post("/api/shutdown")
        async def shutdown_server():
            """关闭服务器（用于页面关闭时自动停止）"""
            logger.info("收到关闭请求，正在停止服务器...")
            # 设置 shutdown 标志
            self._shutdown_flag = True
            if self._server:
                self._server.should_exit = True
            # 发送响应后，服务器将优雅关闭
            return {"status": "shutdown", "message": "服务器即将关闭"}

        @self.app.get("/api/shutdown")
        async def shutdown_server_get():
            """关闭服务器（GET 方法）"""
            logger.info("收到关闭请求 (GET)，正在停止服务器...")
            self._shutdown_flag = True
            if self._server:
                self._server.should_exit = True
            return {"status": "shutdown", "message": "服务器即将关闭"}

        # ========== Agent 控制 API ==========

        @self.app.get("/api/agent/status")
        async def get_agent_process_status():
            """获取 Agent 进程状态"""
            import psutil
            agent_running = False
            agent_pid = None

            # 检查是否有 Agent 进程运行
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'agent.py' in cmdline and proc.info['pid'] != os.getpid():
                            agent_running = True
                            agent_pid = proc.info['pid']
                            break
                except:
                    pass

            return JSONResponse(content={
                "running": agent_running,
                "pid": agent_pid,
                "can_start": not agent_running,
                "can_stop": agent_running,
            })

        @self.app.post("/api/agent/start")
        async def start_agent():
            """启动 Agent 进程"""
            import psutil
            import subprocess

            # 检查是否已有 Agent 运行
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'agent.py' in cmdline and proc.info['pid'] != os.getpid():
                            return JSONResponse(content={
                                "status": "error",
                                "message": "Agent 已在运行中",
                                "pid": proc.info['pid']
                            })
                except:
                    pass

            # 启动 Agent
            try:
                agent_script = PROJECT_ROOT / "agent.py"
                process = subprocess.Popen(
                    [sys.executable, str(agent_script)],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
                )
                logger.info(f"Agent 已启动 (PID: {process.pid})")

                # 写入 PID 到文件
                pid_file = PROJECT_ROOT / "agent.pid"
                with open(pid_file, 'w') as f:
                    f.write(str(process.pid))

                return JSONResponse(content={
                    "status": "started",
                    "message": "Agent 已启动",
                    "pid": process.pid
                })
            except Exception as e:
                logger.error(f"启动 Agent 失败: {e}")
                return JSONResponse(content={
                    "status": "error",
                    "message": f"启动失败: {str(e)}"
                }, status_code=500)

        @self.app.post("/api/agent/stop")
        async def stop_agent():
            """停止 Agent 进程"""
            import psutil

            stopped = []
            failed = []

            # 查找并停止所有 Agent 进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'agent.py' in cmdline and proc.info['pid'] != os.getpid():
                            p = psutil.Process(proc.info['pid'])
                            p.terminate()  # 发送 SIGTERM
                            stopped.append(proc.info['pid'])
                            logger.info(f"Agent 进程已终止 (PID: {proc.info['pid']})")
                except psutil.NoSuchProcess:
                    pass
                except Exception as e:
                    failed.append({"pid": proc.info['pid'], "error": str(e)})

            # 清理 PID 文件
            pid_file = PROJECT_ROOT / "agent.pid"
            if pid_file.exists():
                pid_file.unlink()

            if stopped:
                return JSONResponse(content={
                    "status": "stopped",
                    "message": f"已停止 {len(stopped)} 个 Agent 进程",
                    "stopped_pids": stopped,
                    "failed": failed
                })
            else:
                return JSONResponse(content={
                    "status": "not_running",
                    "message": "没有运行的 Agent 进程",
                    "failed": failed
                })

    def _read_state(self) -> dict:
        """读取 Agent 状态"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取状态文件失败: {e}")

        return {
            "status": "UNKNOWN",
            "current_action": "状态文件不存在",
            "generation": 0,
            "token_budget": 0,
            "current_goal": "",
            "core_context_preview": "",
            "uptime_seconds": 0,
            "last_update": datetime.now().isoformat(),
            "iteration_count": 0,
            "tools_executed": 0,
        }

    def _read_memory(self) -> dict:
        """读取记忆文件"""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取记忆文件失败: {e}")

        return {}

    def _read_plan(self) -> str:
        """读取计划文件"""
        if PLAN_FILE.exists():
            try:
                with open(PLAN_FILE, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"读取计划文件失败: {e}")

        return "暂无计划"

    def _read_recent_logs(self, lines: int = 50) -> list:
        """读取最近的日志"""
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    return [line.strip() for line in all_lines[-lines:] if line.strip()]
            except Exception as e:
                logger.error(f"读取日志文件失败: {e}")

        return []

    async def broadcast_log(self, message: str):
        """广播日志到所有连接"""
        disconnected = set()
        for ws in self.log_connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        # 清理断开的连接
        self.log_connections -= disconnected

    async def broadcast_state(self, state: dict):
        """广播状态到所有连接"""
        disconnected = set()
        for ws in self.state_connections:
            try:
                await ws.send_json(state)
            except Exception:
                disconnected.add(ws)

        # 清理断开的连接
        self.state_connections -= disconnected

    def run(self, reload: bool = False):
        """运行服务器"""
        logger.info(f"启动 Dashboard 服务器: http://{self.host}:{self.port}")
        logger.info(f"状态文件: {STATE_FILE}")
        logger.info(f"日志文件: {LOG_FILE}")

        # 创建 uvicorn 配置
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            reload=reload,
        )
        self._server = uvicorn.Server(config)

        # 检查关闭标志
        if self._shutdown_flag:
            logger.info("服务器已请求关闭")
            return

        # 运行服务器
        import asyncio
        asyncio.run(self._server.serve())


def create_app() -> FastAPI:
    """创建 FastAPI 应用（用于集成）"""
    server = DashboardServer()
    return server.app


def main():
    """主入口"""
    if not HAS_FASTAPI:
        print("[错误] FastAPI 未安装")
        print("请运行: pip install fastapi uvicorn")
        return

    import argparse
    parser = argparse.ArgumentParser(description="Observer Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8080, help="监听端口 (默认: 8080)")
    parser.add_argument("--reload", action="store_true", help="开发模式热重载")

    args = parser.parse_args()

    server = DashboardServer(host=args.host, port=args.port)
    server.run(reload=args.reload)


if __name__ == "__main__":
    main()
