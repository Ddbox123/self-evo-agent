# Observer Dashboard - 自我进化 Agent 监控面板

## 简介

Observer Dashboard 是一个轻量级的实时 Web 监控面板，用于可视化自我进化 Agent 的思考、规划和进化过程。

## 功能特性

- **实时状态监控** - 观察 Agent 当前状态（思考、搜索、编码、测试等）
- **呼吸指示灯** - 霓虹风格的实时状态指示
- **世代追踪** - 记录 Agent 进化代数
- **日志流** - WebSocket 实时推送 Agent 日志
- **核心智慧展示** - 显示 Agent 记忆摘要
- **计划面板** - 渲染 Agent 的当前计划

## 界面预览

```
┌─────────────────────────────────────────────────────────────────┐
│ OBSERVER                              G1    ●    Iter: 5       │
│ Self-Evolving Agent Dashboard         THINKING       Tools: 23 │
├──────────────┬──────────────────────────────┬──────────────────┤
│ THE MIND     │ THE PLAN                     │ THE MATRIX       │
│              │                              │                  │
│ 核心上下文   │ Agent 当前计划内容           │ 实时日志流      │
│ 摘要显示     │                              │                  │
│              │                              │ [20:14:55][INFO] │
│              │                              │ [20:14:56][TOOL] │
├──────────────┤                              │ ...              │
│ GOAL         │                              │                  │
│ 当前目标     │                              │                  │
├──────────────┤                              │                  │
│ TOKEN        │                              │                  │
│ 预算使用情况 │                              │                  │
└──────────────┴──────────────────────────────┴──────────────────┘
```

## 快速开始

### 方式一：一键启动（推荐）

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动全部服务（Agent + Dashboard）
python start_all.py

# 仅启动 Dashboard
python start_all.py --web-only

# 指定端口
python start_all.py --port 8888

# 不自动打开浏览器
python start_all.py --no-browser
```

### 方式二：独立启动

**启动 Dashboard：**
```bash
python dashboard/server.py --port 8000
```

**启动 Agent：**
```bash
python agent.py
```

## 访问地址

- Dashboard 主页: http://localhost:8080
- API 端点: http://localhost:8080/api/state
- WebSocket 日志: ws://localhost:8080/ws/logs
- WebSocket 状态: ws://localhost:8080/ws/state

## 技术架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Observer Dashboard                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│   │  State UI   │  │  Plan UI    │  │    Log Stream UI    │   │
│   └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
│          │                │                     │               │
│          └────────────────┼─────────────────────┘               │
│                           │                                     │
│                    ┌──────┴──────┐                              │
│                    │  WebSocket  │                              │
│                    │  Client     │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ agent_state.json │  │  plan.md     │  │ logs/agent_realtime.log │
│   (状态文件)   │  │   (计划)     │  │   (日志文件)   │
└───────────────┘  └───────────────┘  └───────────────┘
        ▲                   ▲                   ▲
        │                   │                   │
┌───────┴───────────────────┴───────────────────┴───────┐
│                    Agent Process                      │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ StateBroadcaster│  │ PlanGenerator │  │ DebugLogger│  
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────────────────────────────┘
```

## 状态类型

| 状态 | 说明 |
|------|------|
| IDLE | 空闲/等待 |
| AWAKENING | 苏醒中 |
| THINKING | 思考中 |
| SEARCHING | 搜索知识 |
| PLANNING | 制定计划 |
| CODING | 编写代码 |
| TESTING | 沙盒测试 |
| COMPRESSING | 上下文压缩 |
| RESTARTING | 重启中 |
| HIBERNATING | 休眠中 |
| ERROR | 错误状态 |

## API 文档

启动 Dashboard 后访问: http://localhost:8000/docs

## 文件结构

```
self-evo-agent/
├── dashboard/
│   ├── __init__.py          # 模块入口
│   ├── server.py             # FastAPI 后端
│   └── templates/
│       └── index.html        # 前端页面
├── tools/
│   └── state_broadcaster.py  # 状态广播模块
├── logs/
│   └── agent_realtime.log    # 实时日志
├── agent_state.json           # 状态文件
├── start_all.py              # 一键启动脚本
└── agent.py                  # Agent 主程序
```

## 开发模式

```bash
# 热重载模式
python dashboard/server.py --reload --port 8000
```

## 注意事项

1. 确保 `agent_state.json` 和 `logs/` 目录有写入权限
2. Dashboard 不影响 Agent 的主循环和重启机制
3. 日志文件会持续增长，建议定期清理
