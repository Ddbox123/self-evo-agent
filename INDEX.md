# 虾宝自我进化系统 - 全局索引

**版本：** v3.0
**日期：** 2026-04-16
**用途：** 作为所有任务的执行参照索引

---

## ⚠️ 执行前必读

> **重要提示：** 在执行任何任务前，请先阅读本索引文件，确保使用正确的：
> - 规划文档路径
> - 测试文件位置
> - 代码模块结构
> - 命名规范

---

## 📋 任务完成报告制度

> **强制要求：** 每次完成一个任务后，必须生成任务完成报告。

### 报告存放位置
- **路径：** `cursor_report_history/`
- **命名格式：** `task_{YYYYMMDD}_{序号}_{任务摘要}.md`
- **示例：** `task_20260416_01_Phase2自我分析模块实现.md`

### 报告内容要求

每个任务完成报告**必须**包含：

| 章节 | 内容 | 必须 |
|------|------|------|
| 任务概述 | 任务名称、目标、背景 | ✅ |
| 完成情况 | 已完成功能、交付物（标注实现状态：✅完整/⚠️框架/❌未实现） | ✅ |
| 代码变更 | 新增/修改的文件列表 | ✅ |
| 测试结果 | 实际运行的测试用例数、通过率 | ✅ |
| 遇到问题 | 问题描述及解决方案 | 可选 |
| 后续计划 | 下一步工作 | 可选 |

### ⚠️ 重要声明

> 任务报告中的"完成"状态必须诚实标注：
> - **✅ 完整实现** - 功能全部完成且通过测试
> - **⚠️ 框架/部分** - 有类结构但核心逻辑未实现
> - **❌ 未实现** - 仅有占位符或完全缺失

---

## 📁 项目结构总览

```
self-evo-baby/                    # 项目根目录
├── agent.py                      # Agent 主程序 (959行) ⚠️ 需重构为模块化
├── config.py                     # 配置文件
├── restarter.py                  # 自我重启守护进程
│
├── core/                         # 核心模块
│   ├── agent_core.py             # ⚠️ 框架 - 抽象基类，子类需实现核心方法
│   ├── autonomous_mode.py        # ⚠️ 框架 - 自主模式入口
│   ├── cli_ui.py                 # ✅ 完整 - CLI UI 组件
│   ├── event_bus.py              # ✅ 完整 - 事件总线
│   ├── evolution_engine.py        # ✅ 完整 - 8阶段进化引擎
│   ├── interactive_cli.py        # ✅ 完整 - 交互式 CLI
│   ├── logger.py                 # ✅ 完整 - 调试日志
│   ├── prompt_builder.py         # ✅ 完整 - 提示词构建
│   ├── restarter.py              # ✅ 完整 - 重启管理器
│   ├── security.py               # ✅ 完整 - 安全验证
│   ├── self_analyzer.py          # ✅ 完整 - 10维度能力分析
│   ├── state.py                  # ✅ 完整 - 状态管理
│   ├── task_analyzer.py          # ✅ 完整 - 任务复盘分析
│   ├── task_manager.py           # ✅ 完整 - 任务管理
│   ├── tool_executor.py          # ✅ 完整 - 工具执行器
│   ├── transcript_logger.py      # ✅ 完整 - 转录日志
│   ├── unified_logger.py          # ✅ 完整 - 统一日志
│   ├── workspace_manager.py       # ✅ 完整 - 工作区管理
│   ├── codebase_analyzer.py       # ✅ 完整 - 代码库分析
│   ├── skills_profiler.py         # ✅ 完整 - 能力画像
│   ├── tool_tracker.py            # ✅ 完整 - 工具追踪
│   ├── code_generator.py         # ✅ 完整 - 代码生成
│   ├── refactoring_planner.py    # ✅ 完整 - 重构规划
│   ├── knowledge_graph.py         # ✅ 完整 - 知识图谱 (Phase 4)
│   ├── message_bus.py             # ✅ 完整 - 消息总线 (Phase 4)
│   ├── learning_engine.py         # ✅ 完整 - 学习引擎 (Phase 5)
│   ├── feedback_loop.py           # ✅ 完整 - 反馈循环 (Phase 5)
│   ├── insight_tracker.py         # ✅ 完整 - 洞察追踪 (Phase 5)
│   ├── decision_tree.py           # ✅ 完整 - 决策树 (Phase 6)
│   ├── priority_optimizer.py      # ✅ 完整 - 优先级优化器 (Phase 6)
│   ├── strategy_selector.py       # ✅ 完整 - 策略选择器 (Phase 6)
│   ├── llm_orchestrator.py       # ✅ 完整 - LLM 调用协调 (Phase 7)
│   ├── tool_registry.py           # ✅ 完整 - 工具注册表 (Phase 7)
│   ├── memory_manager.py         # ✅ 完整 - 记忆管理器 (Phase 7)
│   └── task_planner.py           # ✅ 完整 - 任务规划器 (Phase 7)
│
├── tools/                        # 工具集 ✅ 完善
│   ├── shell_tools.py            # ✅ 完整 (12个工具)
│   ├── memory_tools.py           # ✅ 完整 (15个工具)
│   ├── code_analysis_tools.py    # ✅ 完整 (6个工具)
│   ├── search_tools.py           # ✅ 完整 (5个工具)
│   ├── rebirth_tools.py           # ✅ 完整 (6个工具)
│   ├── token_manager.py          # ✅ 完整
│   └── __init__.py
│
├── tests/                        # 测试套件
│   ├── test_shell_tools.py       # ✅ 完整
│   ├── test_security.py          # ✅ 完整
│   ├── test_memory_tools.py      # ✅ 完整
│   ├── test_tool_executor.py     # ✅ 完整
│   ├── test_code_analysis_tools.py # ✅ 完整
│   ├── test_rebirth_tools.py     # ✅ 完整
│   ├── test_token_manager.py     # ✅ 完整
│   ├── test_search_tools.py       # ✅ 完整
│   ├── test_decision_tree.py     # ✅ 完整 (Phase 6)
│   ├── test_priority_optimizer.py # ✅ 完整 (Phase 6)
│   ├── test_strategy_selector.py  # ✅ 完整 (Phase 6)
│   ├── test_llm_orchestrator.py  # ✅ 完整 (Phase 7)
│   ├── test_tool_registry.py     # ✅ 完整 (Phase 7)
│   ├── test_memory_manager.py   # ✅ 完整 (Phase 7)
│   ├── test_task_planner.py     # ✅ 完整 (Phase 7)
│   ├── test_agent_core.py        # ✅ 完整 (Phase 4)
│   ├── test_message_bus.py       # ✅ 完整 (Phase 4)
│   ├── test_knowledge_graph.py   # ✅ 完整 (Phase 4)
│   ├── test_learning_engine.py   # ✅ 完整 (Phase 5)
│   ├── test_feedback_loop.py     # ✅ 完整 (Phase 5)
│   ├── test_insight_tracker.py   # ✅ 完整 (Phase 5)
│   ├── test_evolution_engine.py   # ✅ 完整 (Phase 3)
│   ├── test_self_analyzer.py     # ✅ 完整 (Phase 2)
│   └── conftest.py               # ✅ 完整
│
├── requirement/                   # 规划文档
│   └── cursor第一次规划/
│       ├── 虾宝自我进化系统完整规划.md
│       ├── 技术设计文档.md
│       ├── API设计规范.md
│       └── 单元测试规划.md
│
├── workspace/                    # 工作区
│   ├── memory/                   # 记忆存储
│   ├── prompts/                  # 提示词
│   └── logs/                     # 日志
│
├── cursor_report_history/        # 任务完成报告
├── backups/                      # 备份
└── logs/                         # 日志
```

---

## 🚀 开发流程准则

### 开发检查清单

```
✅ 步骤 1: 理解任务
   - 阅读用户需求
   - 确定涉及的功能模块
   - 检查模块当前实现状态（✅/⚠️/❌）

✅ 步骤 2: 查找规划
   - 涉及核心模块 → 参考 技术设计文档.md
   - 涉及进化功能 → 参考 虾宝自我进化系统完整规划.md
   - 涉及 API 设计 → 参考 API设计规范.md

✅ 步骤 3: 检查现有代码
   - core/ 模块 → 检查是否已有实现，避免重复
   - tools/ 模块 → 直接使用
   - tests/ 模块 → 是否有相关测试

✅ 步骤 4: 编写/修改代码
   - 遵循命名规范
   - 添加类型注解
   - 包含中英文文档字符串

✅ 步骤 5: 编写测试
   - 先写测试再写代码（TDD 推荐）
   - 测试必须实际运行通过
   - 覆盖率 >= 80%

✅ 步骤 6: 更新报告
   - 更新 cursor_report_history/
   - 诚实标注实现状态
```

### ⚠️ 开发禁区（必须避免）

1. **禁止创建空壳模块** - 声明实现但无实际逻辑
2. **禁止修改 INDEX.md 伪装完成** - 必须诚实反映状态
3. **禁止删除测试文件** - tests/test_tools.py 被删除问题需修复
4. **禁止提交未运行测试的代码** - 必须实际执行 pytest

---

## 📊 当前实现状态

### 核心模块状态 (2026-04-16)

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| **基础设施** | | | |
| 工具执行器 | `core/tool_executor.py` | ✅ 完整 | 工具注册、超时、重试 |
| 状态管理 | `core/state.py` | ✅ 完整 | 单例、线程安全 |
| 事件总线 | `core/event_bus.py` | ✅ 完整 | 发布订阅、通配符 |
| 工作区管理 | `core/workspace_manager.py` | ✅ 完整 | SQLite 数据库 |
| 安全模块 | `core/security.py` | ✅ 完整 | 白名单+黑名单 |
| **进化能力** | | | |
| 进化引擎 | `core/evolution_engine.py` | ✅ 完整 | 8阶段进化流程 |
| 自我分析器 | `core/self_analyzer.py` | ✅ 完整 | 10维度能力分析 |
| 重构规划器 | `core/refactoring_planner.py` | ✅ 完整 | 坏味道识别 |
| 代码生成器 | `core/code_generator.py` | ✅ 完整 | 模板生成 |
| **知识系统** | | | |
| 知识图谱 | `core/knowledge_graph.py` | ✅ 完整 | 代码实体关系 |
| 消息总线 | `core/message_bus.py` | ✅ 完整 | 发布订阅通信 |
| 代码库分析 | `core/codebase_analyzer.py` | ✅ 完整 | AST 分析 |
| **持续学习** | | | |
| 学习引擎 | `core/learning_engine.py` | ✅ 完整 | 模式提取学习 |
| 反馈循环 | `core/feedback_loop.py` | ✅ 完整 | 多源反馈聚合 |
| 洞察追踪 | `core/insight_tracker.py` | ✅ 完整 | 洞察分类管理 |
| **自主决策** | | | |
| 决策树 | `core/decision_tree.py` | ✅ 完整 | 基于规则决策系统 |
| 优先级优化器 | `core/priority_optimizer.py` | ✅ 完整 | 智能任务排序 |
| 策略选择器 | `core/strategy_selector.py` | ✅ 完整 | 策略切换优化 |
| **Agent 基础设施** | | | |
| 任务管理 | `core/task_manager.py` | ✅ 完整 | 打勾收网机制 |
| 能力画像 | `core/skills_profiler.py` | ✅ 完整 | 能力矩阵管理 |
| 工具追踪 | `core/tool_tracker.py` | ✅ 完整 | 使用统计分析 |
| 任务分析 | `core/task_analyzer.py` | ✅ 完整 | 复盘报告生成 |
| **待重构** | | | |
| Agent 主类 | `agent.py` | ⚠️ 重构中 | 959行，需模块化拆分 |
| Agent 核心基类 | `core/agent_core.py` | ⚠️ 框架 | 抽象基类，需子类实现 |

### 实施路线图（修订）

```
Phase 1: 基础工具整合 ✅ 完成
  - Shell 工具 ✅ 12个
  - 记忆工具 ✅ 15个
  - 搜索工具 ✅ 5个
  - Token 管理 ✅

Phase 2: 核心基础设施 ✅ 完成
  - 工具执行器 ✅
  - 状态管理 ✅
  - 事件总线 ✅
  - 工作区管理 ✅
  - 安全验证 ✅

Phase 3: 进化能力开发 ✅ 完成
  - 进化引擎 ✅ 8阶段完整实现
  - 自我分析器 ✅ 10维度分析
  - 重构规划器 ✅ 坏味道识别
  - 代码生成器 ✅ 模板生成

Phase 4: 知识系统 ✅ 完成
  - 知识图谱 ✅ 代码实体关系
  - 消息总线 ✅ 发布订阅通信
  - Agent 核心 ✅ 模块化架构

Phase 5: 持续学习机制 ✅ 完成
  - 学习引擎 ✅ 模式提取
  - 反馈循环 ✅ 多源反馈聚合
  - 洞察追踪 ✅ 洞察分类管理

Phase 6: 自主决策优化 ✅ 完成
  - 决策树 ✅ 基于规则决策
  - 优先级优化器 ✅ 任务排序
  - 策略选择器 ✅ 策略切换
  - 模块集成 ✅ 集成到 agent.py

Phase 7: 模块化 Agent 重构 ✅ 完成
  - Phase 7.1 ✅ INDEX.md 更新 (v3.0)
  - Phase 7.2 ✅ 框架模块审计 (13/14 完整)
  - Phase 7.3 ✅ LLM Orchestrator 创建 (12 测试)
  - Phase 7.4 ✅ Tool Registry 创建 (20 测试)
  - Phase 7.5 ✅ Memory Manager 创建 (20 测试)
  - Phase 7.6 ✅ Task Planner 创建 (19 测试)
  - Phase 7.7 ✅ 新模块集成到 agent.py
  - Phase 7.8 ✅ 测试验证 (71/71 通过)
```

---

## 💻 核心代码模块索引

### ✅ 已完成模块

#### core/tool_executor.py
```python
class ToolExecutor:
    def execute(tool_name, tool_args) -> tuple  # (result, action)
    def register_tool(name, func, timeout)

# 全局单例
get_tool_executor() -> ToolExecutor
```

#### core/event_bus.py
```python
class EventBus:
    def subscribe(event_name, handler, priority) -> callback_id
    def publish(event_name, data, source, blocking) -> List[result]
    def unsubscribe(event_name, handler)

# 全局单例
get_event_bus() -> EventBus
```

#### core/state.py
```python
class StateManager:
    def set_state(state, action, **metadata)
    def get_state() -> AgentState
    def add_recent_action(action)
    def is_action_recent(action, threshold) -> bool

# 全局单例
get_state_manager() -> StateManager
```

#### core/workspace_manager.py
```python
class WorkspaceManager:
    def get_db_connection()  # SQLite 上下文管理器
    def record_codebase_insight(module_path, insight, generation) -> bool
    def generate_codebase_map() -> str

# 全局单例
get_workspace() -> WorkspaceManager
```

### Phase 6 模块

#### core/decision_tree.py
```python
class DecisionTree:
    def make_decision(context) -> DecisionResult
    def add_node(node) -> None
    def trace_decision_path(context) -> List

# 全局单例
get_decision_tree() -> DecisionTree
```

#### core/priority_optimizer.py
```python
class PriorityOptimizer:
    def calculate_priority(task_id, context) -> PriorityScore
    def optimize(context, constraints) -> OptimizationResult
    def adjust_priority(task_id, adjustment, reason) -> bool

# 全局单例
get_priority_optimizer() -> PriorityOptimizer
```

#### core/strategy_selector.py
```python
class StrategySelector:
    def select(context) -> StrategySelection
    def should_switch(current_id, results) -> Tuple[bool, str]
    def record_result(result) -> None

# 全局单例
get_strategy_selector() -> StrategySelector
```

---

## 📚 规划文档索引

### 1. 虾宝自我进化系统完整规划.md

**路径：** `requirement/cursor第一次规划/虾宝自我进化系统完整规划.md`

**核心内容：**

| 章节 | 内容 | 状态 |
|------|------|------|
| 一、项目愿景 | 自我进化 Agent 概述 | ✅ 参考 |
| 二、现状分析 | 10维度能力评估表 | ✅ 已更新 |
| 三、进化方向规划 | 8大进化方向 | ✅ Phase 1-6 完成 |
| 四、进化引擎设计 | EvolutionEngine 模块 | ✅ 完整实现 |
| 五、自我分析能力 | SelfAnalyzer 模块 | ✅ 完整实现 |

### 2. 技术设计文档.md

**路径：** `requirement/cursor第一次规划/技术设计文档.md`

**核心架构（当前状态）：**

```
SelfEvolvingAgent (主控 - agent.py)
    ├── ToolExecutor ✅
    ├── StateManager ✅
    ├── EventBus ✅
    ├── WorkspaceManager ✅
    ├── DecisionTree ✅ (Phase 6)
    ├── PriorityOptimizer ✅ (Phase 6)
    ├── StrategySelector ✅ (Phase 6)
    ├── EvolutionEngine ✅ (Phase 3)
    │   ├── SelfAnalyzer ✅
    │   ├── RefactoringPlanner ✅
    │   └── CodeGenerator ✅
    ├── KnowledgeGraph ✅ (Phase 4)
    ├── LearningEngine ✅ (Phase 5)
    ├── FeedbackLoop ✅ (Phase 5)
    ├── InsightTracker ✅ (Phase 5)
    ├── LLMOrchestrator ✅ (Phase 7) [新建]
    ├── ToolRegistry ✅ (Phase 7) [新建]
    ├── MemoryManager ✅ (Phase 7) [新建]
    └── TaskPlanner ✅ (Phase 7) [新建]
```

---

## 🧪 测试执行指南

### 运行测试命令

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_shell_tools.py -v

# 运行带覆盖率
pytest tests/ --cov=core --cov=tools --cov-fail-under=80

# 只运行失败的测试
pytest tests/ --lf

# 运行快速测试（跳过慢速）
pytest tests/ -m "not slow" -v
```

### ⚠️ 测试现状警告

```
已知问题：
1. tests/test_tools.py 被删除 - 需重建或确认删除原因
2. test_memory_tools.py - 存在导入错误（预先问题）
3. test_token_manager.py - 存在测试失败（预先问题）
```

**重要**：测试通过 ≠ 功能实现。需要人工审核测试是否真正验证了核心逻辑。

---

## 🔧 命名规范

```python
# 文件命名
模块文件: snake_case.py (e.g., evolution_engine.py)
测试文件: test_*.py (e.g., test_evolution_engine.py)

# 类命名
Python 类: PascalCase (e.g., EvolutionEngine)
内部类: _PascalCase (e.g., _EvolutionContext)

# 函数命名
公开函数: snake_case (e.g., get_evolution_status)
私有函数: _snake_case (e.g., _run_phase)

# 常量命名
SCREAMING_SNAKE_CASE (e.g., MAX_RETRY = 3)

# 测试命名
测试类: TestClassName (e.g., TestEvolutionEngine)
测试函数: test_功能_场景 (e.g., test_run_evolution_success)
```

---

## 📝 修改日志

| 日期 | 版本 | 修改内容 |
|------|------|---------|
| 2026-04-16 | v1.0 | 初始创建索引文档 |
| 2026-04-16 | v2.0 | 修订实现状态，区分完整/框架/未实现，添加开发禁区 |
| 2026-04-16 | v3.0 | 更新 Phase 1-6 完成状态，新增 Phase 6/7 模块索引，更新技术设计文档架构图 |

---

## ❓ 常见问题

**Q: 模块声称已完成但运行报错？**
A: 检查 INDEX.md 中的状态标注，⚠️ 框架表示有结构但未完全实现。

**Q: 如何确定任务优先级？**
A: 查看"实施路线图"，Phase 7 为当前进行中。

**Q: 发现文档与代码不符？**
A: 以代码实际执行为准，文档描述可能过时。请更新 INDEX.md 的状态标注。

---

<!--
使用说明：
1. 执行任何任务前，先阅读本文件
2. 根据任务类型，找到对应的规划文档
3. 确认模块当前实现状态（✅/⚠️/❌）
4. 参考相关章节执行具体实现
5. 完成后更新 cursor_report_history/
6. 更新 INDEX.md 相关状态（如有变化）
-->
