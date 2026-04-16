# 虾宝自我进化系统 - API 设计规范

**版本：** v1.0  
**日期：** 2026-04-16  
**状态：** API 设计阶段

---

## 目录

1. [概述](#1-概述)
2. [REST API 规范](#2-rest-api-规范)
3. [内部 Python API](#3-内部-python-api)
4. [工具 API](#4-工具-api)
5. [事件 API](#5-事件-api)
6. [消息队列规范](#6-消息队列规范)
7. [错误码规范](#7-错误码规范)
8. [响应格式](#8-响应格式)
9. [版本控制](#9-版本控制)
10. [认证与授权](#10-认证与授权)

---

## 1. 概述

### 1.1 API 分层架构

```
┌─────────────────────────────────────────────────┐
│              外部 API (External)                │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  REST API   │ │  WebSocket  │ │   CLI     │ │
│  │  (HTTP)     │ │  (实时)     │ │  (交互)   │ │
│  └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────┤
│              内部 API (Internal)                │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Core API  │ │  Tool API   │ │Event API  │ │
│  │  (组件间)   │ │  (工具调用)  │ │ (事件)    │ │
│  └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────┤
│              数据 API (Data)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Memory API │ │  KG API    │ │ Config API│ │
│  │ (记忆存储)  │ │ (图谱查询)  │ │ (配置)    │ │
│  └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────┘
```

### 1.2 命名规范

| 类型 | 命名规范 | 示例 |
|------|----------|------|
| API 路径 | `snake_case` | `/api/v1/evolution_status` |
| 路径参数 | `:param` | `/agent/:agent_id` |
| 查询参数 | `snake_case` | `?max_results=10` |
| JSON 字段 | `camelCase` | `"taskId": "abc123"` |
| Python 类 | `PascalCase` | `class EvolutionEngine` |
| Python 方法 | `snake_case` | `def get_evolution_status()` |
| Python 常量 | `SCREAMING_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS = 3` |

---

## 2. REST API 规范

### 2.1 Base URL

```
生产环境: https://api.xiaobao.local/v1
开发环境: http://localhost:8080/v1
```

### 2.2 认证 Header

```
Authorization: Bearer <token>
X-Request-ID: <uuid>  # 请求追踪
X-Correlation-ID: <uuid>  # 关联追踪
```

### 2.3 API 端点

#### Agent 管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/v1/agent/status` | 获取 Agent 状态 |
| `POST` | `/api/v1/agent/start` | 启动 Agent |
| `POST` | `/api/v1/agent/stop` | 停止 Agent |
| `POST` | `/api/v1/agent/restart` | 重启 Agent |
| `GET` | `/api/v1/agent/config` | 获取配置 |
| `PUT` | `/api/v1/agent/config` | 更新配置 |

#### 任务管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/tasks` | 创建任务 |
| `GET` | `/api/v1/tasks` | 列出任务 |
| `GET` | `/api/v1/tasks/:task_id` | 获取任务详情 |
| `PUT` | `/api/v1/tasks/:task_id` | 更新任务 |
| `DELETE` | `/api/v1/tasks/:task_id` | 删除任务 |
| `POST` | `/api/v1/tasks/:task_id/cancel` | 取消任务 |

#### 进化管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/evolution/start` | 启动进化 |
| `GET` | `/api/v1/evolution/status` | 获取进化状态 |
| `GET` | `/api/v1/evolution/:evo_id` | 获取进化详情 |
| `POST` | `/api/v1/evolution/:evo_id/pause` | 暂停进化 |
| `POST` | `/api/v1/evolution/:evo_id/resume` | 恢复进化 |
| `POST` | `/api/v1/evolution/:evo_id/abort` | 中止进化 |
| `GET` | `/api/v1/evolution/history` | 获取进化历史 |

#### 目标管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/goals` | 创建目标 |
| `GET` | `/api/v1/goals` | 列出目标 |
| `GET` | `/api/v1/goals/:goal_id` | 获取目标详情 |
| `PUT` | `/api/v1/goals/:goal_id` | 更新目标 |
| `DELETE` | `/api/v1/goals/:goal_id` | 删除目标 |
| `POST` | `/api/v1/goals/:goal_id/prioritize` | 优先级排序 |

#### 工具管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/v1/tools` | 列出工具 |
| `GET` | `/api/v1/tools/:tool_name` | 获取工具详情 |
| `POST` | `/api/v1/tools` | 注册工具 |
| `PUT` | `/api/v1/tools/:tool_name` | 更新工具 |
| `DELETE` | `/api/v1/tools/:tool_name` | 删除工具 |
| `POST` | `/api/v1/tools/:tool_name/execute` | 执行工具 |

#### 记忆管理

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/v1/memory` | 获取当前记忆 |
| `POST` | `/api/v1/memory/search` | 搜索记忆 |
| `GET` | `/api/v1/memory/archives` | 获取归档列表 |
| `GET` | `/api/v1/memory/archives/:gen` | 获取特定归档 |
| `POST` | `/api/v1/memory/backup` | 创建记忆备份 |
| `POST` | `/api/v1/memory/restore` | 恢复记忆 |

#### 知识图谱

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/knowledge/query` | 图谱查询 |
| `POST` | `/api/v1/knowledge/entity` | 添加实体 |
| `GET` | `/api/v1/knowledge/entity/:id` | 获取实体 |
| `PUT` | `/api/v1/knowledge/entity/:id` | 更新实体 |
| `DELETE` | `/api/v1/knowledge/entity/:id` | 删除实体 |
| `POST` | `/api/v1/knowledge/relation` | 添加关系 |
| `POST` | `/api/v1/knowledge/semantic_search` | 语义搜索 |
| `GET` | `/api/v1/knowledge/path/:source/:target` | 查找路径 |

#### 能力画像

| 方法 | 端点 | 描述 |
|------|------|------|
| `GET` | `/api/v1/profile` | 获取能力画像 |
| `GET` | `/api/v1/profile/history` | 获取历史记录 |
| `POST` | `/api/v1/profile/evaluate` | 触发评估 |
| `GET` | `/api/v1/profile/growth` | 获取成长轨迹 |

#### 代码变更

| 方法 | 端点 | 描述 |
|------|------|------|
| `POST` | `/api/v1/code/modify` | 申请代码修改 |
| `POST` | `/api/v1/code/validate` | 验证代码变更 |
| `POST` | `/api/v1/code/rollback/:change_id` | 回滚变更 |
| `GET` | `/api/v1/code/changes` | 获取变更历史 |

### 2.4 请求/响应示例

#### 启动进化

**Request:**
```http
POST /api/v1/evolution/start
Authorization: Bearer <token>
Content-Type: application/json

{
    "focus_areas": ["CODE_QUALITY", "AUTONOMY"],
    "constraints": {
        "max_duration_seconds": 1800,
        "require_approval": true
    }
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "evolution_id": "evo_abc123",
        "status": "STARTED",
        "phase": "SELF_ANALYSIS",
        "started_at": "2026-04-16T10:00:00Z",
        "estimated_duration": "15m",
        "goals": [
            {
                "id": "goal_001",
                "title": "提升代码质量",
                "priority": 1,
                "estimated_tasks": 5
            }
        ]
    },
    "meta": {
        "request_id": "req_xyz789",
        "timestamp": "2026-04-16T10:00:00Z"
    }
}
```

#### 获取进化状态

**Request:**
```http
GET /api/v1/evolution/evo_abc123
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "evolution_id": "evo_abc123",
        "status": "IN_PROGRESS",
        "phase": "EXECUTION",
        "progress": 0.65,
        "current_goal": {
            "id": "goal_001",
            "title": "提升代码质量",
            "description": "通过重构和添加测试提升代码质量"
        },
        "completed_tasks": [
            {
                "id": "task_001",
                "name": "分析代码结构",
                "status": "COMPLETED",
                "result": "发现3个需要重构的方法"
            },
            {
                "id": "task_002",
                "name": "制定重构计划",
                "status": "COMPLETED",
                "result": "制定了详细的5步重构计划"
            }
        ],
        "in_progress_tasks": [
            {
                "id": "task_003",
                "name": "执行代码修改",
                "status": "IN_PROGRESS",
                "progress": 60,
                "current_action": "正在修改 agent.py 的 think_and_act 方法"
            }
        ],
        "pending_tasks": 2,
        "code_changes": [
            {
                "id": "change_001",
                "file": "core/agent.py",
                "type": "MODIFY",
                "status": "VALIDATED",
                "lines_modified": 45
            }
        ],
        "started_at": "2026-04-16T10:00:00Z",
        "elapsed_seconds": 450,
        "estimated_remaining_seconds": 300
    },
    "meta": {
        "request_id": "req_xyz790",
        "timestamp": "2026-04-16T10:07:30Z"
    }
}
```

#### 执行工具

**Request:**
```http
POST /api/v1/tools/read_file/execute
Authorization: Bearer <token>
Content-Type: application/json

{
    "parameters": {
        "file_path": "agent.py",
        "max_lines": 100,
        "offset": 0
    },
    "context": {
        "evolution_id": "evo_abc123",
        "task_id": "task_003"
    }
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "tool_call_id": "tc_001",
        "tool_name": "read_file",
        "status": "COMPLETED",
        "result": "#!/usr/bin/env python3\n\nfrom __future__ import annotations\n\nimport os\nimport sys\nimport time\n...",
        "metadata": {
            "execution_time_ms": 45,
            "lines_read": 100,
            "file_size": 28543
        }
    },
    "meta": {
        "request_id": "req_xyz791",
        "timestamp": "2026-04-16T10:07:35Z"
    }
}
```

---

## 3. 内部 Python API

### 3.1 模块导入规范

```python
# 标准导入
from core.evolution_engine import EvolutionEngine
from core.self_analyzer import SelfAnalyzer
from core.goal_generator import GoalGenerator
from core.task_planner import TaskPlanner
from core.code_modifier import CodeModifier
from core.knowledge_graph import KnowledgeGraph
from core.skills_profiler import SkillsProfiler
from core.memory_manager import MemoryManager

# 工具导入
from tools import ToolRegistry, BaseTool
from tools.registry import tool_registry

# 数据模型导入
from core.models import (
    EvolutionGoal,
    EvolutionPlan,
    EvolutionTask,
    CapabilityProfile,
    ToolCall,
    ToolResult,
)
```

### 3.2 核心类 API

#### EvolutionEngine

```python
from core.evolution_engine import EvolutionEngine, EvolutionContext

# 初始化
engine = EvolutionEngine(
    config=config,
    self_analyzer=self_analyzer,
    goal_generator=goal_generator,
    task_planner=task_planner,
    code_modifier=code_modifier,
    safety_gate=safety_gate,
    memory_manager=memory_manager,
    knowledge_graph=knowledge_graph,
    skills_profiler=skills_profiler,
)

# 运行进化周期
context = EvolutionContext(
    trigger_reason=EvolutionTrigger.MANUAL,
    focus_areas=[CapabilityDimension.CODE_QUALITY],
)
result = await engine.run_evolution_cycle(context)

# 查询状态
status = engine.get_evolution_status()
current_phase = engine.get_current_phase()

# 控制进化
engine.pause_evolution()
engine.resume_evolution()
engine.abort_evolution(reason="用户取消")
```

#### SelfAnalyzer

```python
from core.self_analyzer import SelfAnalyzer, AnalysisContext

analyzer = SelfAnalyzer(
    config=config,
    knowledge_graph=knowledge_graph,
    memory_manager=memory_manager,
)

# 评估能力
scores = await analyzer.assess_capabilities()
analysis_report = await analyzer.generate_analysis_report(generation=5)

# 分析代码库
code_analyses = await analyzer.analyze_codebase()

# 识别改进机会
opportunities = analyzer.identify_improvement_opportunities(analysis_report)
```

#### GoalGenerator

```python
from core.goal_generator import GoalGenerator, Mission, Constraint

generator = GoalGenerator(
    config=config,
    self_analyzer=self_analyzer,
    knowledge_graph=knowledge_graph,
    soul_reader=soul_reader,
)

# 生成目标
mission = Mission.from_file("SOUL.md")
constraints = [
    Constraint(type="MAX_DURATION", value=1800),
    Constraint(type="REQUIRE_TEST_PASS", value=True),
]
goals = await generator.generate_goals(
    analysis=analysis_report,
    mission=mission,
    constraints=constraints,
)

# 验证目标
validation = generator.validate_goal(goal=goals[0], constraints=constraints)
```

#### TaskPlanner

```python
from core.task_planner import TaskPlanner, PlanningContext

planner = TaskPlanner(
    config=config,
    tool_registry=tool_registry,
    risk_evaluator=risk_evaluator,
)

# 创建计划
context = PlanningContext(
    evolution_id="evo_abc123",
    goal_id="goal_001",
)
plan = planner.create_plan(goal=goals[0], context=context)

# 分析依赖
dep_graph = planner.analyze_dependencies(tasks=plan.tasks)
parallel_groups = planner.identify_parallel_tasks(tasks=plan.tasks)

# 调整计划
feedback = ExecutionFeedback(
    task_id="task_003",
    status="FAILED",
    error="语法错误",
)
adjusted_plan = planner.adjust_plan(plan=plan, feedback=feedback)
```

#### CodeModifier

```python
from core.code_modifier import (
    CodeModifier,
    CodeChange,
    ModificationContext,
    ModificationStrategy,
)

modifier = CodeModifier(
    config=config,
    backup_manager=backup_manager,
    validator=code_validator,
    security_validator=security_validator,
)

# 执行修改
change = CodeChange(
    id="change_001",
    strategy=ModificationStrategy.DIFF_EDIT,
    target_file="core/agent.py",
    content="""<<<<<<< SEARCH
    def think_and_act(self, user_prompt: str = None) -> bool:
=======
    async def think_and_act(self, user_prompt: str = None) -> bool:
>>>>>>> REPLACE""",
    validation_method=ValidationMethod.SYNTAX_AND_TESTS,
)
context = ModificationContext(evolution_id="evo_abc123")
result = await modifier.execute_modification(change=change, context=context)

# 选择策略
strategy = modifier.select_strategy(
    change_scope=45,
    change_type=ChangeType.MODIFY,
    risk_level=RiskLevel.MEDIUM,
)
```

#### KnowledgeGraph

```python
from core.knowledge_graph import KnowledgeGraph, GraphQuery, Entity, Relation

kg = KnowledgeGraph(
    config=config,
    storage=graph_storage,
    embedding_model=embedding_model,
)

# 添加实体
entity = Entity(
    id="agent.py",
    type=EntityType.FILE,
    name="agent.py",
    properties={
        "lines": 786,
        "complexity": 15,
        "last_modified": "2026-04-16",
    },
)
entity_id = kg.add_entity(entity)

# 添加关系
relation = Relation(
    source_id="agent.py",
    target_id="think_and_act",
    type=RelationType.CONTAINS,
)
relation_id = kg.add_relation(relation)

# 查询
query = GraphQuery(
    entity_filters=[{"type": "FUNCTION"}],
    relation_filters=[{"type": "CALLS"}],
    traversal={"start_from": "agent.py", "depth": 3},
)
result = kg.query(query)

# 语义搜索
results = await kg.semantic_search("代码分析工具", top_k=10)
```

#### SkillsProfiler

```python
from core.skills_profiler import SkillsProfiler, EvaluationContext

profiler = SkillsProfiler(
    config=config,
    storage=profile_storage,
    self_analyzer=self_analyzer,
)

# 评估能力画像
profile = await profiler.evaluate_all(
    context=EvaluationContext(generation=5)
)

# 记录快照
snapshot_id = profiler.record_snapshot(profile)

# 获取成长轨迹
trajectory = profiler.get_growth_trajectory(
    dimension=CapabilityDimension.CODE_QUALITY,
)

# 生成建议
recommendations = profiler.generate_recommendations(profile)
```

### 3.3 事件 API

```python
from core.event_bus import EventBus, Event, EventType

eb = EventBus()

# 订阅事件
def on_evolution_started(event: Event):
    print(f"进化开始: {event.data}")

subscription = eb.subscribe(
    event_type=EventType.EVOLUTION_STARTED,
    handler=on_evolution_started,
)

# 发布事件
event = Event(
    type=EventType.EVOLUTION_COMPLETED,
    timestamp=datetime.now(),
    source="evolution_engine",
    data={"evolution_id": "evo_abc123", "success": True},
)
eb.publish(event)

# 取消订阅
eb.unsubscribe(subscription)
```

### 3.4 配置 API

```python
from config import Config

# 加载配置
config = Config.from_file("config.toml")

# 访问配置
model_name = config.llm.model_name
awake_interval = config.agent.awake_interval

# 更新配置
config.agent.awake_interval = 120
config.evolution.enabled = True

# 保存配置
config.save("config.toml")
```

---

## 4. 工具 API

### 4.1 工具定义接口

```python
from tools import BaseTool, tool
from typing import TypedDict

class ToolParameter(TypedDict, total=False):
    """工具参数定义"""
    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool
    default: Any
    enum: list[str]
    minimum: float
    maximum: float
    pattern: str  # regex pattern


class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: list[ToolParameter]
    returns: dict  # return type description
    category: str
    examples: list[dict]
    constraints: list[str]
    version: str
```

### 4.2 工具装饰器

```python
from tools import tool, ToolCategory

@tool(
    name="analyze_code_complexity",
    description="分析代码文件的复杂度指标",
    category=ToolCategory.CODE_ANALYSIS,
    parameters=[
        {"name": "file_path", "type": "string", "required": True},
        {"name": "include_methods", "type": "boolean", "required": False, "default": True},
    ],
    returns={"type": "object", "properties": {"complexity": "number", "issues": "array"}},
    examples=[
        {"input": {"file_path": "agent.py"}, "output": {"complexity": 15, "issues": []}},
    ],
)
def analyze_code_complexity(file_path: str, include_methods: bool = True) -> dict:
    """工具实现"""
    ...
```

### 4.3 工具注册表接口

```python
from tools.registry import ToolRegistry, tool_registry

# 获取注册表
registry = ToolRegistry()

# 列出工具
tools = registry.list_tools(category=ToolCategory.CODE_ANALYSIS)

# 获取工具
code_tool = registry.get_tool("analyze_code_complexity")

# 注册工具
registry.register(my_tool)

# 检查工具是否存在
if registry.has_tool("my_tool"):
    ...

# 获取工具统计
stats = registry.get_usage_stats()
```

### 4.4 工具执行接口

```python
from tools.executor import ToolExecutor

executor = ToolExecutor(registry=tool_registry)

# 执行工具
result = await executor.execute(
    tool_name="read_file",
    parameters={"file_path": "agent.py", "max_lines": 50},
    context=ExecutionContext(evolution_id="evo_abc123"),
)

# 批量执行
results = await executor.execute_batch(
    tool_calls=[
        {"name": "read_file", "args": {"file_path": "agent.py"}},
        {"name": "check_syntax", "args": {"file_path": "agent.py"}},
    ],
)
```

---

## 5. 事件 API

### 5.1 事件类型

```python
from core.event_bus import EventType

class EventType(Enum):
    # Agent 事件
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_STATE_CHANGED = "agent.state_changed"

    # 进化事件
    EVOLUTION_STARTED = "evolution.started"
    EVOLUTION_PHASE_CHANGED = "evolution.phase_changed"
    EVOLUTION_TASK_COMPLETED = "evolution.task_completed"
    EVOLUTION_COMPLETED = "evolution.completed"
    EVOLUTION_FAILED = "evolution.failed"

    # 工具事件
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"

    # 记忆事件
    MEMORY_UPDATED = "memory.updated"
    MEMORY_ARCHIVED = "memory.archived"
```

### 5.2 事件订阅

```python
from core.event_bus import EventBus, event_bus

# 订阅所有工具事件
subscription = event_bus.subscribe(
    EventType.TOOL_STARTED,
    lambda e: print(f"工具执行: {e.data['tool_name']}")
)

# 使用装饰器
@event_bus.on(EventType.EVOLUTION_COMPLETED)
def on_evolution_complete(event: Event):
    logger.info(f"进化 {event.data['evolution_id']} 完成")

# 通配符订阅
event_bus.subscribe("evolution.*", handler)
```

### 5.3 自定义事件

```python
from core.event_bus import Event, EventType

# 创建自定义事件
event = Event(
    type=EventType.CUSTOM,  # 或自定义枚举值
    timestamp=datetime.now(),
    source="my_module",
    data={
        "custom_field": "value",
        "evolution_id": "evo_abc123",
    },
    correlation_id="corr_123",
)

# 发布事件
event_bus.publish(event)
```

---

## 6. 消息队列规范

### 6.1 队列定义

```python
class QueueName:
    """队列名称常量"""
    EVOLUTION_TASKS = "evolution.tasks"
    TOOL_EXECUTIONS = "tool.executions"
    CODE_MODIFICATIONS = "code.modifications"
    NOTIFICATIONS = "notifications"
    DEAD_LETTER = "dead_letter"
```

### 6.2 消息格式

```python
from dataclasses import dataclass
from typing import Any, Optional
import json

@dataclass
class Message:
    """消息格式"""
    id: str  # UUID
    queue: str
    type: str  # 消息类型
    payload: dict  # 消息内容
    headers: dict  # 消息头
    correlation_id: Optional[str]
    reply_to: Optional[str]
    timestamp: datetime
    ttl: int  # 存活时间（秒）

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "queue": self.queue,
            "type": self.type,
            "payload": self.payload,
            "headers": self.headers,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp.isoformat(),
            "ttl": self.ttl,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        data = json.loads(json_str)
        return cls(**data)
```

### 6.3 消息处理器

```python
from typing import Protocol

class MessageHandler(Protocol):
    """消息处理器接口"""

    async def handle(self, message: Message) -> None:
        """处理消息"""
        ...

    def can_handle(self, message: Message) -> bool:
        """判断是否能处理此消息"""
        ...
```

---

## 7. 错误码规范

### 7.1 错误码结构

```python
from dataclasses import dataclass
from enum import Enum

class ErrorCategory(Enum):
    """错误类别"""
    VALIDATION = "VALIDATION"
    EXECUTION = "EXECUTION"
    EVOLUTION = "EVOLUTION"
    SECURITY = "SECURITY"
    NETWORK = "NETWORK"
    SYSTEM = "SYSTEM"

@dataclass
class ErrorCode:
    """错误码定义"""
    code: str  # 如 "E1001"
    category: ErrorCategory
    message: str
    http_status: int
    retryable: bool
    suggestions: list[str]
```

### 7.2 预定义错误码

```python
ERROR_CODES = {
    # 通用错误 (E0xxx)
    "E0001": ErrorCode(
        code="E0001",
        category=ErrorCategory.SYSTEM,
        message="未知错误",
        http_status=500,
        retryable=False,
        suggestions=["联系管理员", "查看日志"],
    ),
    "E0002": ErrorCode(
        code="E0002",
        category=ErrorCategory.VALIDATION,
        message="参数验证失败",
        http_status=400,
        retryable=False,
        suggestions=["检查参数格式", "参考 API 文档"],
    ),
    "E0003": ErrorCode(
        code="E0003",
        category=ErrorCategory.SYSTEM,
        message="请求超时",
        http_status=408,
        retryable=True,
        suggestions=["重试请求", "增加超时��间"],
    ),

    # 执行错误 (E1xxx)
    "E1001": ErrorCode(
        code="E1001",
        category=ErrorCategory.EXECUTION,
        message="工具执行失败",
        http_status=500,
        retryable=True,
        suggestions=["重试", "检查工具配置"],
    ),
    "E1002": ErrorCode(
        code="E1002",
        category=ErrorCategory.EXECUTION,
        message="LLM 调用失败",
        http_status=502,
        retryable=True,
        suggestions=["重试", "检查 API 密钥", "检查网络连接"],
    ),

    # 进化错误 (E2xxx)
    "E2001": ErrorCode(
        code="E2001",
        category=ErrorCategory.EVOLUTION,
        message="进化超时",
        http_status=504,
        retryable=True,
        suggestions=["延长超时时间", "简化目标", "减少任务数"],
    ),
    "E2002": ErrorCode(
        code="E2002",
        category=ErrorCategory.EVOLUTION,
        message="进化循环中断",
        http_status=500,
        retryable=False,
        suggestions=["查看详细错误", "重置 Agent 状态"],
    ),
    "E2003": ErrorCode(
        code="E2003",
        category=ErrorCategory.EVOLUTION,
        message="代码修改失败",
        http_status=422,
        retryable=True,
        suggestions=["检查语法", "查看回滚记录"],
    ),
    "E2004": ErrorCode(
        code="E2004",
        category=ErrorCategory.EVOLUTION,
        message="测试门控未通过",
        http_status=422,
        retryable=False,
        suggestions=["修复失败的测试", "更新测试用例"],
    ),
    "E2005": ErrorCode(
        code="E2005",
        category=ErrorCategory.EVOLUTION,
        message="回滚失败",
        http_status=500,
        retryable=True,
        suggestions=["手动恢复", "联系管理员"],
    ),

    # 安全错误 (E3xxx)
    "E3001": ErrorCode(
        code="E3001",
        category=ErrorCategory.SECURITY,
        message="安全违规",
        http_status=403,
        retryable=False,
        suggestions=["检查操作权限", "联系管理员"],
    ),
    "E3002": ErrorCode(
        code="E3002",
        category=ErrorCategory.SECURITY,
        message="未授权访问",
        http_status=401,
        retryable=False,
        suggestions=["检查认证信息", "重新登录"],
    ),
    "E3003": ErrorCode(
        code="E3003",
        category=ErrorCategory.SECURITY,
        message="路径遍历攻击",
        http_status=403,
        retryable=False,
        suggestions=["检查文件路径", "联系管理员"],
    ),

    # 网络错误 (E4xxx)
    "E4001": ErrorCode(
        code="E4001",
        category=ErrorCategory.NETWORK,
        message="网络连接失败",
        http_status=503,
        retryable=True,
        suggestions=["检查网络连接", "重试请求"],
    ),
    "E4002": ErrorCode(
        code="E4002",
        category=ErrorCategory.NETWORK,
        message="服务不可用",
        http_status=503,
        retryable=True,
        suggestions=["等待服务恢复", "联系管理员"],
    ),
}
```

### 7.3 错误响应格式

```json
{
    "success": false,
    "error": {
        "code": "E2004",
        "category": "EVOLUTION",
        "message": "测试门控未通过",
        "details": {
            "failed_tests": [
                {"name": "test_agent_loop", "status": "FAILED", "error": "AssertionError"},
                {"name": "test_tool_execution", "status": "FAILED", "error": "Timeout"}
            ],
            "passed_count": 45,
            "total_count": 47
        },
        "suggestions": [
            "修复失败的测试",
            "更新测试用例"
        ]
    },
    "meta": {
        "request_id": "req_xyz789",
        "timestamp": "2026-04-16T10:00:00Z",
        "correlation_id": "evo_abc123"
    }
}
```

---

## 8. 响应格式

### 8.1 成功响应

```json
{
    "success": true,
    "data": { ... },
    "meta": {
        "timestamp": "2026-04-16T10:00:00Z",
        "request_id": "req_xyz789",
        "pagination": {  // 可选
            "page": 1,
            "limit": 20,
            "total": 100
        }
    }
}
```

### 8.2 分页响应

```json
{
    "success": true,
    "data": {
        "items": [...],
        "pagination": {
            "page": 2,
            "limit": 20,
            "total": 150,
            "total_pages": 8,
            "has_next": true,
            "has_prev": true
        }
    },
    "meta": {
        "request_id": "req_xyz789",
        "timestamp": "2026-04-16T10:00:00Z"
    }
}
```

### 8.3 批量操作响应

```json
{
    "success": true,
    "data": {
        "results": [
            {"id": "1", "status": "SUCCESS"},
            {"id": "2", "status": "SUCCESS"},
            {"id": "3", "status": "FAILED", "error": {"code": "E0002", "message": "参数错误"}}
        ],
        "summary": {
            "total": 3,
            "succeeded": 2,
            "failed": 1
        }
    },
    "meta": {
        "request_id": "req_xyz789",
        "timestamp": "2026-04-16T10:00:00Z"
    }
}
```

---

## 9. 版本控制

### 9.1 版本策略

- API 版本格式: `v1`, `v2`, `v3`
- 路径格式: `/api/v1/...`
- 版本共存: 旧版本至少维护 6 个月
- 废弃通知: 提前 3 个月发布废弃警告

### 9.2 版本检测

```http
GET /api/v1/agent/status
Accept: application/json
X-API-Version: 1.0
```

### 9.3 版本响应头

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 1
X-Rate-Limit-Remaining: 99
X-Rate-Limit-Reset: 1713261600
```

---

## 10. 认证与授权

### 10.1 认证方式

```http
# Bearer Token
Authorization: Bearer <token>

# API Key
X-API-Key: <api_key>

# Basic Auth
Authorization: Basic <base64(username:password)>
```

### 10.2 权限级别

```python
class Permission:
    """权限常量"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

class Role:
    """角色定义"""
    VIEWER = [Permission.READ]
    OPERATOR = [Permission.READ, Permission.EXECUTE]
    DEVELOPER = [Permission.READ, Permission.WRITE, Permission.EXECUTE]
    ADMIN = [Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.ADMIN]
```

### 10.3 API 权限映射

| 端点 | 权限 | 说明 |
|------|------|------|
| `GET /agent/status` | READ | 查看状态 |
| `POST /evolution/start` | EXECUTE | 启动进化 |
| `POST /code/modify` | WRITE | 修改代码 |
| `POST /tools` | ADMIN | 注册工具 |
| `DELETE /tools/:name` | ADMIN | 删除工具 |

---

## 附录 A：完整 API 端点列表

### A.1 Agent API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/agent` | READ | 获取 Agent 信息 |
| `GET` | `/api/v1/agent/status` | READ | 获取运行状态 |
| `GET` | `/api/v1/agent/config` | READ | 获取配置 |
| `PUT` | `/api/v1/agent/config` | WRITE | 更新配置 |
| `POST` | `/api/v1/agent/start` | EXECUTE | 启动 Agent |
| `POST` | `/api/v1/agent/stop` | EXECUTE | 停止 Agent |
| `POST` | `/api/v1/agent/restart` | EXECUTE | 重启 Agent |

### A.2 Evolution API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/evolution` | READ | 获取进化概览 |
| `GET` | `/api/v1/evolution/status` | READ | 获取进化状态 |
| `POST` | `/api/v1/evolution/start` | EXECUTE | 启动进化 |
| `GET` | `/api/v1/evolution/history` | READ | 获取进化历史 |
| `GET` | `/api/v1/evolution/:id` | READ | 获取进化详情 |
| `POST` | `/api/v1/evolution/:id/pause` | EXECUTE | 暂停进化 |
| `POST` | `/api/v1/evolution/:id/resume` | EXECUTE | 恢复进化 |
| `POST` | `/api/v1/evolution/:id/abort` | EXECUTE | 中止进化 |

### A.3 Goal API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/goals` | READ | 列出目标 |
| `POST` | `/api/v1/goals` | WRITE | 创建目标 |
| `GET` | `/api/v1/goals/:id` | READ | 获取目标详情 |
| `PUT` | `/api/v1/goals/:id` | WRITE | 更新目标 |
| `DELETE` | `/api/v1/goals/:id` | WRITE | 删除目标 |
| `POST` | `/api/v1/goals/:id/prioritize` | WRITE | 优先级排序 |

### A.4 Task API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/tasks` | READ | 列出任务 |
| `POST` | `/api/v1/tasks` | WRITE | 创建任务 |
| `GET` | `/api/v1/tasks/:id` | READ | 获取任务详情 |
| `PUT` | `/api/v1/tasks/:id` | WRITE | 更新任务 |
| `DELETE` | `/api/v1/tasks/:id` | WRITE | 删除任务 |
| `POST` | `/api/v1/tasks/:id/cancel` | EXECUTE | 取消任务 |

### A.5 Tools API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/tools` | READ | 列出工具 |
| `POST` | `/api/v1/tools` | ADMIN | 注册工具 |
| `GET` | `/api/v1/tools/:name` | READ | 获取工具详情 |
| `PUT` | `/api/v1/tools/:name` | ADMIN | 更新工具 |
| `DELETE` | `/api/v1/tools/:name` | ADMIN | 删除工具 |
| `POST` | `/api/v1/tools/:name/execute` | EXECUTE | 执行工具 |
| `GET` | `/api/v1/tools/:name/stats` | READ | 获取工具统计 |

### A.6 Memory API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/memory` | READ | 获取当前记忆 |
| `POST` | `/api/v1/memory/search` | READ | 搜索记忆 |
| `POST` | `/api/v1/memory/backup` | WRITE | 创建备份 |
| `POST` | `/api/v1/memory/restore` | WRITE | 恢复备份 |
| `GET` | `/api/v1/memory/archives` | READ | 列出归档 |
| `GET` | `/api/v1/memory/archives/:gen` | READ | 获取归档详情 |
| `DELETE` | `/api/v1/memory/archives/:gen` | WRITE | 删除归档 |

### A.7 Knowledge API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `POST` | `/api/v1/knowledge/query` | READ | 图谱查询 |
| `POST` | `/api/v1/knowledge/entity` | WRITE | 添加实体 |
| `GET` | `/api/v1/knowledge/entity/:id` | READ | 获取实体 |
| `PUT` | `/api/v1/knowledge/entity/:id` | WRITE | 更新实体 |
| `DELETE` | `/api/v1/knowledge/entity/:id` | WRITE | 删除实体 |
| `POST` | `/api/v1/knowledge/relation` | WRITE | 添加关系 |
| `DELETE` | `/api/v1/knowledge/relation/:id` | WRITE | 删除关系 |
| `POST` | `/api/v1/knowledge/semantic_search` | READ | 语义搜索 |
| `GET` | `/api/v1/knowledge/path/:src/:tgt` | READ | 查找路径 |

### A.8 Profile API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/profile` | READ | 获取能力画像 |
| `POST` | `/api/v1/profile/evaluate` | EXECUTE | 触发评估 |
| `GET` | `/api/v1/profile/history` | READ | 获取历史 |
| `GET` | `/api/v1/profile/growth` | READ | 获取成长轨迹 |

### A.9 Code API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `POST` | `/api/v1/code/modify` | WRITE | 申请代码修改 |
| `POST` | `/api/v1/code/validate` | WRITE | 验证修改 |
| `POST` | `/api/v1/code/rollback/:id` | WRITE | 回滚修改 |
| `GET` | `/api/v1/code/changes` | READ | 获取变更历史 |

### A.10 System API

| 方法 | 端点 | 权限 | 描述 |
|------|------|------|------|
| `GET` | `/api/v1/health` | READ | 健康检查 |
| `GET` | `/api/v1/version` | READ | 版本信息 |
| `GET` | `/api/v1/metrics` | READ | 系统指标 |

---

## 附录 B：Python SDK 示例

### B.1 安装 SDK

```bash
pip install xiaobao-sdk
```

### B.2 基本使用

```python
from xiaobao import Client

# 初始化客户端
client = Client(
    api_key="your-api-key",
    base_url="http://localhost:8080/v1",
)

# 获取 Agent 状态
status = client.agent.get_status()
print(f"Agent 状态: {status.state}, 世代: {status.generation}")

# 启动进化
evolution = client.evolution.start(
    focus_areas=["CODE_QUALITY", "AUTONOMY"],
    constraints={"max_duration": 1800}
)
print(f"进化 ID: {evolution.evolution_id}")

# 轮询进化状态
import asyncio
async def wait_for_evolution(client, evolution_id):
    while True:
        status = client.evolution.get_status(evolution_id)
        print(f"进度: {status.progress:.1%}, 阶段: {status.phase}")
        if status.status in ["COMPLETED", "FAILED", "ABORTED"]:
            return status
        await asyncio.sleep(10)

result = asyncio.run(wait_for_evolution(client, evolution.evolution_id))
```

---

**API 设计规范结束**