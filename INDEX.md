# 虾宝自我进化系统 - 全局索引

**版本：** v4.1
**日期：** 2026-04-17
**版本迭代：** 11次重大更新
**用途：** 作为所有任务的执行参照索引

---

## 快速导航

| 目标 | 章节 |
|------|------|
| 理解项目结构 | [📁 项目结构总览](#项目结构总览) |
| 查找规划文档 | [📚 规划文档索引](#规划文档索引) |
| 了解当前进度 | [📊 实施路线图](#实施路线图) |
| 执行开发任务 | [🚀 开发流程准则](#开发流程准则) |
| 运行测试 | [🧪 测试执行指南](#测试执行指南) |
| 查阅代码规范 | [🔧 命名规范](#命名规范) |

---

## 核心设计规范 (SPEC)

> **SPEC = Self-evo-baby, Purpose, Evolution**
> 这是一个自我进化的 AI Agent 系统，核心理念是"持续优化、主动进化"

### 设计原则

```
┌─────────────────────────────────────────────────────────────────┐
│                      虾宝自我进化系统 SPEC                         │
├─────────────────────────────────────────────────────────────────┤
│  S - Self-evo-baby                                              │
│     ├─ 形象系统：可切换的 ASCII Art 角色（龙虾/小虾/螃蟹/猫猫/小鸡）│
│     ├─ 记忆系统：三层记忆（短期/中期/长期）                        │
│     └─ 进化系统：8+2 阶段持续进化                                │
│                                                                  │
│  P - Purpose (目标)                                              │
│     ├─ 自主决策：无需人工干预的任务执行                          │
│     ├─ 自我优化：代码质量和性能持续改进                          │
│     └─ 持续学习：从每次执行中提取模式和洞察                      │
│                                                                  │
│  E - Evolution (进化)                                            │
│     ├─ 阶段进化：Phase 1→8 渐进式架构升级                        │
│     ├─ 增量优化：Token压缩、能力画像、策略选择                  │
│     └─ 主动探索：Phase 8+ 自主发现问题并优化                    │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块职责

```
┌──────────────────────────────────────────────────────────────────┐
│                    SelfEvolvingAgent (agent.py)                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   形象系统   │    │   记忆系统   │    │   工具系统   │       │
│  │  ASCII Art  │    │  3层记忆     │    │  50+工具     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    决策与执行引擎                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │DecisionTree│  │ Priority │  │ Strategy │  │TaskPlanner│ │ │
│  │  │  决策树   │  │Optimizer │  │Selector  │  │ 任务规划  │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    进化与学习系统                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │Evolution  │  │ Learning │  │ Feedback │  │ Insight  │  │ │
│  │  │ Engine   │  │ Engine   │  │ Loop     │  │ Tracker  │  │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 执行前必读

> **重要提示：** 在执行任何任务前，请先阅读本索引文件，确保使用正确的：
> - 规划文档路径
> - 测试文件位置
> - 代码模块结构
> - 命名规范

---

## 任务完成报告制度

> **强制要求：** 每次完成一个任务后，必须生成任务完成报告。

### 报告存放位置

- **路径：** `cursor_report_history/`
- **命名格式：** `task_{YYYYMMDD}_{序号}_{任务摘要}.md`
- **示例：** `task_20260417_01_Phase8自主探索模块实现.md`

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

### 实现状态标注规则

> **重要声明：** 任务报告中的"完成"状态必须诚实标注：

| 状态 | 含义 | 标注 |
|------|------|------|
| 完整实现 | 功能全部完成且通过测试 | ✅ |
| 框架/部分 | 有类结构但核心逻辑未实现 | ⚠️ |
| 未实现 | 仅有占位符或完全缺失 | ❌ |

---

## 项目结构总览

```
self-evo-baby/                    # 项目根目录
├── agent.py                      # Agent 主程序 (~1000行)
├── config.toml                  # 配置文件 (TOML格式，所有配置项)
│
├── config/                      # 配置模块（统一配置入口）
│   ├── __init__.py              # 主入口，导出所有配置类和函数
│   ├── models.py                 # Pydantic 数据模型定义
│   ├── providers.py             # LLM 模型预设注册表
│   └── settings.py               # 配置加载与单例管理
│
├── restarter.py                 # 自我重启守护进程
│
├── core/                         # 核心模块 (47个文件)
│   │
│   ├── ━━━ Phase 1-2: 基础设施 ━━━
│   ├── tool_executor.py         # ✅ 完整 - 工具注册、超时、重试
│   ├── state.py                 # ✅ 完整 - 单例、线程安全
│   ├── event_bus.py             # ✅ 完整 - 发布订阅、通配符
│   ├── security.py              # ✅ 完整 - 白名单+黑名单
│   ├── model_discovery.py       # ✅ 完整 - 动态模型发现
│   │
│   ├── ━━━ Phase 3: 进化能力 ━━━
│   ├── evolution_engine.py       # ✅ 完整 - 8阶段进化引擎
│   ├── self_analyzer.py         # ✅ 完整 - 10维度能力分析
│   ├── refactoring_planner.py   # ✅ 完整 - 坏味道识别
│   ├── code_generator.py       # ✅ 完整 - 模板生成
│   │
│   ├── ━━━ Phase 4: 知识系统 ━━━
│   ├── agent_core.py            # ⚠️ 框架 - 抽象基类，需子类实现
│   ├── knowledge_graph.py        # ✅ 完整 - 代码实体关系
│   ├── message_bus.py           # ✅ 完整 - 发布订阅通信
│   ├── codebase_analyzer.py      # ✅ 完整 - AST分析
│   ├── semantic_search.py       # ✅ 完整 - 语义搜索
│   │
│   ├── ━━━ Phase 5: 持续学习 ━━━
│   ├── learning_engine.py        # ✅ 完整 - 模式提取学习
│   ├── feedback_loop.py          # ✅ 完整 - 多源反馈聚合
│   ├── insight_tracker.py         # ✅ 完整 - 洞察分类管理
│   ├── strategy_learner.py       # ✅ 完整 - 策略学习
│   │
│   ├── ━━━ Phase 6: 自主决策 ━━━
│   ├── decision_tree.py          # ✅ 完整 - 基于规则决策
│   ├── priority_optimizer.py     # ✅ 完整 - 智能任务排序
│   ├── strategy_selector.py       # ✅ 完整 - 策略切换优化
│   │
│   ├── ━━━ Phase 7: 模块化重构 ━━━
│   ├── llm_orchestrator.py       # ✅ 完整 - LLM调用协调
│   ├── tool_registry.py          # ✅ 完整 - 工具注册表
│   ├── memory_manager.py         # ✅ 完整 - 三层记忆管理
│   ├── task_planner.py           # ✅ 完整 - 智能任务规划
│   │
│   ├── ━━━ Phase 8: 自主探索 ━━━
│   ├── autonomous_mode.py        # ⚠️ 框架 - 自主模式入口
│   ├── autonomous_explorer.py    # ⚠️ 框架 - 探索引擎
│   ├── opportunity_finder.py     # ⚠️ 框架 - 机会发现
│   ├── goal_generator.py         # ⚠️ 框架 - 目标生成
│   │
│   ├── ━━━ 工具与UI ━━━
│   ├── ascii_art.py              # ✅ 完整 - 多角色ASCII Art
│   ├── cli_ui.py                 # ✅ 完整 - CLI UI组件
│   ├── interactive_cli.py        # ✅ 完整 - 交互式CLI
│   ├── prompt_builder.py         # ✅ 完整 - 提示词构建
│   ├── workspace_manager.py       # ✅ 完整 - SQLite工作区
│   ├── task_manager.py           # ✅ 完整 - 任务管理
│   ├── skills_profiler.py        # ✅ 完整 - 能力画像
│   ├── tool_tracker.py           # ✅ 完整 - 工具追踪
│   ├── logger.py                 # ✅ 完整 - 调试日志
│   ├── unified_logger.py         # ✅ 完整 - 统一日志
│   ├── transcript_logger.py       # ✅ 完整 - 转录日志
│   ├── restarter.py              # ✅ 完整 - 重启管理
│   ├── pet_system.py             # ⚠️ 宠物系统 (占位)
│   ├── self_refactoror.py        # ⚠️ 自我重构器
│   ├── theme.py                  # ⚠️ 主题系统
│   ├── tool_ecosystem.py         # ⚠️ 工具生态系统
│   ├── pattern_library.py        # ⚠️ 模式库
│   │
│   └── __init__.py
│
├── tools/                        # 工具集 (12个文件)
│   ├── shell_tools.py            # ✅ 完整 (12个工具)
│   ├── memory_tools.py           # ✅ 完整 (15个工具)
│   ├── code_analysis_tools.py    # ✅ 完整 (6个工具)
│   ├── search_tools.py           # ✅ 完整 (5个工具)
│   ├── rebirth_tools.py          # ✅ 完整 (6个工具)
│   ├── token_manager.py          # ✅ 完整 (含压缩器)
│   ├── key_info_extractor.py     # ✅ 完整 (Token优化)
│   ├── compression_strategy.py    # ✅ 完整 (4级压缩)
│   ├── compression_quality.py     # ✅ 完整 (质量评估)
│   ├── state_broadcaster.py       # ⚠️ 状态广播
│   ├── Key_Tools.py              # ✅ 完整 (工具注册)
│   └── __init__.py
│
├── tests/                        # 测试套件 (46个文件)
│   ├── conftest.py               # ✅ pytest配置
│   ├── test_shell_tools.py       # ✅ 完整
│   ├── test_memory_tools.py      # ✅ 完整
│   ├── test_code_analysis_tools.py # ✅ 完整
│   ├── test_search_tools.py       # ✅ 完整
│   ├── test_rebirth_tools.py     # ✅ 完整
│   ├── test_token_manager.py     # ✅ 完整
│   ├── test_security.py          # ✅ 完整
│   ├── test_tool_executor.py     # ✅ 完整
│   ├── test_evolution_engine.py  # ✅ 完整 (Phase 3)
│   ├── test_self_analyzer.py     # ✅ 完整 (Phase 2)
│   ├── test_agent_core.py        # ✅ 完整 (Phase 4)
│   ├── test_message_bus.py       # ✅ 完整 (Phase 4)
│   ├── test_knowledge_graph.py   # ✅ 完整 (Phase 4)
│   ├── test_learning_engine.py   # ✅ 完整 (Phase 5)
│   ├── test_feedback_loop.py     # ✅ 完整 (Phase 5)
│   ├── test_insight_tracker.py   # ✅ 完整 (Phase 5)
│   ├── test_decision_tree.py     # ✅ 完整 (Phase 6)
│   ├── test_priority_optimizer.py # ✅ 完整 (Phase 6)
│   ├── test_strategy_selector.py  # ✅ 完整 (Phase 6)
│   ├── test_llm_orchestrator.py  # ✅ 完整 (Phase 7)
│   ├── test_tool_registry.py     # ✅ 完整 (Phase 7)
│   ├── test_memory_manager.py   # ✅ 完整 (Phase 7)
│   ├── test_task_planner.py     # ✅ 完整 (Phase 7)
│   ├── test_compression_strategy.py # ✅ 完整 (Token优化)
│   ├── test_key_info_extractor.py # ✅ 完整 (Token优化)
│   ├── test_compression_quality.py # ✅ 完整 (Token优化)
│   ├── test_autonomous_explorer.py # ⚠️ (Phase 8)
│   ├── test_tool_tracker.py     # ✅ 完整
│   ├── test_task_analyzer.py     # ✅ 完整
│   ├── test_refactoring_planner.py # ✅ 完整
│   ├── test_codebase_analyzer.py # ✅ 完整
│   ├── test_skills_profiler.py   # ✅ 完整
│   ├── test_semantic_search.py   # ✅ 完整
│   ├── test_strategy_learner.py  # ✅ 完整
│   ├── test_self_refactoror.py  # ⚠️
│   ├── test_tool_ecosystem.py    # ⚠️
│   ├── test_pattern_library.py   # ⚠️
│   ├── test_code_generator.py    # ✅ 完整
│   ├── test_memory.py            # ⚠️
│   ├── test_runner.py            # ⚠️ 测试运行器
│   ├── run_tests.py              # ⚠️ 测试脚本
│   ├── simulate_lifecycle.py     # ⚠️ 生命周期模拟
│   └── compression_benchmark.py # ⚠️ 压缩基准
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
│   ├── logs/                     # 日志
│   └── analytics/                # 分析结果
│
├── cursor_report_history/        # 任务完成报告 (11个)
├── backups/                      # 备份
└── logs/                         # 日志
```

---

## 开发流程准则

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

### 开发禁区（必须避免）

1. **禁止创建空壳模块** - 声明实现但无实际逻辑
2. **禁止修改 INDEX.md 伪装完成** - 必须诚实反映状态
3. **禁止删除测试文件** - tests/test_tools.py 被删除问题需修复
4. **禁止提交未运行测试的代码** - 必须实际执行 pytest

---

## 实施路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                      虾宝进化路线图 v4.0                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 基础工具整合 ✅ 完成                                    │
│  ├── Shell 工具 ✅ 12个                                          │
│  ├── 记忆工具 ✅ 15个                                             │
│  ├── 搜索工具 ✅ 5个                                              │
│  ├── Token 管理 ✅                                               │
│  └── 重启工具 ✅ 6个                                              │
│                                                                  │
│  Phase 2: 自我分析能力 ✅ 完成                                    │
│  ├── 10维度能力评估 ✅                                            │
│  ├── 代码认知地图 ✅                                              │
│  ├── 能力画像系统 ✅                                              │
│  └── 任务分析器 ✅                                                │
│                                                                  │
│  Phase 3: 进化引擎核心 ✅ 完成                                    │
│  ├── 8阶段进化流程 ✅                                             │
│  ├── 自我重构规划 ✅                                              │
│  └── 代码生成器 ✅                                                │
│                                                                  │
│  Phase 4: 知识系统 ✅ 完成                                        │
│  ├── 知识图谱 ✅                                                  │
│  ├── 消息总线 ✅                                                   │
│  ├── 语义搜索 ✅                                                  │
│  └── Agent 核心框架 ✅                                            │
│                                                                  │
│  Phase 5: 持续学习 ✅ 完成                                        │
│  ├── 学习引擎 ✅                                                  │
│  ├── 反馈循环 ✅                                                  │
│  ├── 洞察追踪 ✅                                                  │
│  └── 策略学习器 ✅                                                 │
│                                                                  │
│  Phase 6: 自主决策 ✅ 完成                                       │
│  ├── 决策树 ✅                                                    │
│  ├── 优先级优化器 ✅                                               │
│  └── 策略选择器 ✅                                                 │
│                                                                  │
│  Phase 7: 模块化重构 ✅ 完成 (2026-04-16)                         │
│  ├── LLM Orchestrator ✅ 12测试                                  │
│  ├── Tool Registry ✅ 20测试                                     │
│  ├── Memory Manager ✅ 20测试                                    │
│  └── Task Planner ✅ 19测试                                      │
│                                                                  │
│  Phase 8: 自主探索 ⚠️ 进行中                                     │
│  ├── 自主模式入口 ⚠️ 框架                                        │
│  ├── 探索引擎 ⚠️ 框架                                            │
│  ├── 机会发现 ⚠️ 框架                                            │
│  └── 目标生成 ⚠️ 框架                                            │
│                                                                  │
│  Token 优化 ✅ 完成 (2026-04-16)                                  │
│  ├── 4级压缩策略 ✅                                               │
│  ├── 关键信息提取 ✅                                              │
│  └── 压缩质量评估 ✅                                               │
│                                                                  │
│  形象系统 ✅ 完成 (2026-04-16)                                    │
│  ├── 5套ASCII Art ✅                                              │
│  ├── AvatarManager ✅                                            │
│  └── /avatar 命令 ✅                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 当前实现状态

### 核心模块状态 (2026-04-17)

#### Phase 1-2: 基础设施

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 工具执行 | 工具执行器 | `core/tool_executor.py` | ✅ 完整 | 工具注册、超时、重试 |
| 工具执行 | 工具注册表 | `core/tool_registry.py` | ✅ 完整 | 动态注册、分类、搜索 |
| 状态管理 | 状态管理 | `core/state.py` | ✅ 完整 | 单例、线程安全 |
| 事件系统 | 事件总线 | `core/event_bus.py` | ✅ 完整 | 发布订阅、通配符 |
| 事件系统 | 消息总线 | `core/message_bus.py` | ✅ 完整 | 发布订阅通信 |
| 安全 | 安全模块 | `core/security.py` | ✅ 完整 | 白名单+黑名单 |
| 模型发现 | 模型动态发现 | `core/model_discovery.py` | ✅ 完整 | 运行时获取 max_model_len |
| 工作区 | 工作区管理 | `core/workspace_manager.py` | ✅ 完整 | SQLite 数据库 |

#### Phase 3: 进化能力

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 进化引擎 | 进化引擎 | `core/evolution_engine.py` | ✅ 完整 | 8阶段进化流程 |
| 进化引擎 | 自我分析器 | `core/self_analyzer.py` | ✅ 完整 | 10维度能力分析 |
| 进化引擎 | 重构规划器 | `core/refactoring_planner.py` | ✅ 完整 | 坏味道识别 |
| 进化引擎 | 代码生成器 | `core/code_generator.py` | ✅ 完整 | 模板生成 |
| 进化引擎 | 自我重构器 | `core/self_refactoror.py` | ⚠️ 框架 | 待实现 |

#### Phase 4: 知识系统

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 知识 | 知识图谱 | `core/knowledge_graph.py` | ✅ 完整 | 代码实体关系 |
| 知识 | 代码库分析 | `core/codebase_analyzer.py` | ✅ 完整 | AST 分析 |
| 知识 | 语义搜索 | `core/semantic_search.py` | ✅ 完整 | 语义检索 |
| Agent框架 | Agent 核心基类 | `core/agent_core.py` | ⚠️ 框架 | 抽象基类，需子类实现 |

#### Phase 5: 持续学习

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 学习 | 学习引擎 | `core/learning_engine.py` | ✅ 完整 | 模式提取学习 |
| 学习 | 策略学习器 | `core/strategy_learner.py` | ✅ 完整 | 策略学习 |
| 反馈 | 反馈循环 | `core/feedback_loop.py` | ✅ 完整 | 多源反馈聚合 |
| 洞察 | 洞察追踪 | `core/insight_tracker.py` | ✅ 完整 | 洞察分类管理 |
| 洞察 | 机会发现 | `core/opportunity_finder.py` | ⚠️ 框架 | Phase 8 相关 |

#### Phase 6: 自主决策

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 决策 | 决策树 | `core/decision_tree.py` | ✅ 完整 | 基于规则决策系统 |
| 决策 | 优先级优化器 | `core/priority_optimizer.py` | ✅ 完整 | 智能任务排序 |
| 决策 | 策略选择器 | `core/strategy_selector.py` | ✅ 完整 | 策略切换优化 |
| 决策 | 目标生成 | `core/goal_generator.py` | ⚠️ 框架 | Phase 8 相关 |

#### Phase 7: 模块化重构

| 类别 | 模块 | 文件 | 状态 | 测试数 |
|------|------|------|------|--------|
| LLM | LLM 协调器 | `core/llm_orchestrator.py` | ✅ 完整 | 12 |
| 记忆 | 记忆管理器 | `core/memory_manager.py` | ✅ 完整 | 20 |
| 规划 | 任务规划器 | `core/task_planner.py` | ✅ 完整 | 19 |
| 工具 | 工具注册表 | `core/tool_registry.py` | ✅ 完整 | 20 |

#### Phase 8: 自主探索 ⚠️ 进行中

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 探索 | 自主模式入口 | `core/autonomous_mode.py` | ⚠️ 框架 | 入口点已存在 |
| 探索 | 探索引擎 | `core/autonomous_explorer.py` | ⚠️ 框架 | 核心逻辑待实现 |
| 探索 | 机会发现器 | `core/opportunity_finder.py` | ⚠️ 框架 | 优化点识别 |
| 探索 | 目标生成器 | `core/goal_generator.py` | ⚠️ 框架 | 自主目标生成 |

#### Token 优化模块

| 类别 | 模块 | 文件 | 状态 | 测试数 |
|------|------|------|------|--------|
| 压缩 | 压缩策略 | `tools/compression_strategy.py` | ✅ 完整 | 24 |
| 压缩 | 关键信息提取 | `tools/key_info_extractor.py` | ✅ 完整 | 16 |
| 压缩 | 压缩质量评估 | `tools/compression_quality.py` | ✅ 完整 | 18 |
| Token | Token 管理器 | `tools/token_manager.py` | ✅ 完整 | 含增强压缩 |

#### 形象与 UI

| 类别 | 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|------|
| 形象 | ASCII Art | `core/ascii_art.py` | ✅ 完整 | 5套角色 |
| 形象 | Avatar 管理器 | (在ascii_art.py) | ✅ 完整 | 统一管理 |
| UI | CLI UI | `core/cli_ui.py` | ✅ 完整 | UI组件 |
| UI | 交互式 CLI | `core/interactive_cli.py` | ✅ 完整 | 用户交互 |
| UI | 主题系统 | `core/theme.py` | ⚠️ 框架 | 待实现 |

#### 待重构 ⚠️

| 模块 | 文件 | 状态 | 说明 |
|------|------|------|------|
| Agent 主类 | `agent.py` | ⚠️ 重构中 | ~1000行，需模块化拆分 |
| Agent 核心基类 | `core/agent_core.py` | ⚠️ 框架 | 抽象基类，需子类实现 |
| 宠物系统 | `core/pet_system.py` | ⚠️ 占位 | 预留功能 |

---

## 规划文档索引

### 1. 虾宝自我进化系统完整规划.md

**路径：** `requirement/cursor第一次规划/虾宝自我进化系统完整规划.md`

| 章节 | 内容 | 状态 |
|------|------|------|
| 一、项目愿景 | 自我进化 Agent 概述 | ✅ 参考 |
| 二、现状分析 | 10维度能力评估表 | ✅ 已更新 |
| 三、进化方向规划 | 8大进化方向 | ✅ Phase 1-8 进行中 |
| 四、进化引擎设计 | EvolutionEngine 模块 | ✅ 完整实现 |
| 五、自我分析能力 | SelfAnalyzer 模块 | ✅ 完整实现 |

### 2. 技术设计文档.md

**路径：** `requirement/cursor第一次规划/技术设计文档.md`

**核心架构（当前状态）：**

```
SelfEvolvingAgent (主控 - agent.py)
    │
    ├── Phase 1-2: 基础设施
    │   ├── ToolExecutor ✅
    │   ├── StateManager ✅
    │   ├── EventBus ✅
    │   ├── WorkspaceManager ✅
    │   ├── Security ✅
    │   └── ModelDiscovery ✅ (动态获取 max_model_len)
    │
    ├── Phase 3: 进化能力
    │   ├── EvolutionEngine ✅
    │   ├── SelfAnalyzer ✅
    │   ├── RefactoringPlanner ✅
    │   └── CodeGenerator ✅
    │
    ├── Phase 4: 知识系统
    │   ├── KnowledgeGraph ✅
    │   ├── CodebaseAnalyzer ✅
    │   ├── SemanticSearch ✅
    │   └── AgentCore ⚠️ 框架
    │
    ├── Phase 5: 持续学习
    │   ├── LearningEngine ✅
    │   ├── FeedbackLoop ✅
    │   ├── InsightTracker ✅
    │   └── StrategyLearner ✅
    │
    ├── Phase 6: 自主决策
    │   ├── DecisionTree ✅
    │   ├── PriorityOptimizer ✅
    │   └── StrategySelector ✅
    │
    ├── Phase 7: 模块化重构 ✅
    │   ├── LLMOrchestrator ✅
    │   ├── ToolRegistry ✅
    │   ├── MemoryManager ✅
    │   └── TaskPlanner ✅
    │
    ├── Phase 8: 自主探索 ⚠️ 进行中
    │   ├── AutonomousMode ⚠️ 框架
    │   ├── AutonomousExplorer ⚠️ 框架
    │   ├── OpportunityFinder ⚠️ 框架
    │   └── GoalGenerator ⚠️ 框架
    │
    └── Token 优化 ✅
        ├── CompressionStrategy ✅
        ├── KeyInfoExtractor ✅
        └── CompressionQuality ✅
```

---

## 测试执行指南

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

# 运行 Phase 7 模块测试
pytest tests/test_llm_orchestrator.py tests/test_tool_registry.py \
       tests/test_memory_manager.py tests/test_task_planner.py -v

# 运行 Token 优化测试
pytest tests/test_compression*.py tests/test_key_info_extractor.py -v
```

### 测试统计

| Phase | 测试文件数 | 预计测试数 | 状态 |
|-------|-----------|-----------|------|
| Phase 1-2 | 7 | 150+ | ✅ 完整 |
| Phase 3 | 2 | 50+ | ✅ 完整 |
| Phase 4 | 4 | 70+ | ✅ 完整 |
| Phase 5 | 4 | 80+ | ✅ 完整 |
| Phase 6 | 3 | 60+ | ✅ 完整 |
| Phase 7 | 4 | 71 | ✅ 完整 |
| Token 优化 | 3 | 58 | ✅ 完整 |
| Phase 8 | 1 | - | ⚠️ 框架 |

### ⚠️ 测试现状警告

```
已知问题：
1. tests/test_tools.py 被删除 - 需重建或确认删除原因
2. test_memory_tools.py - 存在导入错误（预先问题）
3. test_token_manager.py - 存在测试失败（预先问题）
```

> **重要**：测试通过 ≠ 功能实现。需要人工审核测试是否真正验证了核心逻辑。

---

## 命名规范

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

## 任务完成报告索引

| 序号 | 报告名称 | 完成时间 | Phase |
|------|----------|----------|-------|
| 01 | [Phase 2 - 自我分析模块实现](cursor_report_history/task_20260416_01_Phase2自我分析模块实现.md) | 2026-04-16 15:30 | Phase 2 |
| 02 | [Phase 3 - 进化引擎核心实现](cursor_report_history/task_20260416_02_Phase3进化引擎核心实现.md) | 2026-04-16 16:00 | Phase 3 |
| 03 | [Phase 4 - 模块化Agent实现](cursor_report_history/task_20260416_03_Phase4模块化Agent实现.md) | 2026-04-16 16:30 | Phase 4 |
| 04 | [Phase 5 - 持续学习机制实现](cursor_report_history/task_20260416_04_Phase5持续学习机制实现.md) | 2026-04-16 17:00 | Phase 5 |
| 05 | [Phase 6 - 自主决策模块集成](cursor_report_history/task_20260416_05_Phase6自主决策模块集成.md) | 2026-04-16 19:00 | Phase 6 |
| 06 | [Phase 7 - 模块化Agent架构第一阶段](cursor_report_history/task_20260416_06_Phase7模块化Agent架构第一阶段.md) | 2026-04-16 19:30 | Phase 7 |
| 07 | [Phase 7 - 模块化Agent架构第二阶段](cursor_report_history/task_20260416_07_Phase7模块化Agent架构第二阶段.md) | 2026-04-16 20:30 | Phase 7 |
| 08 | [Phase 7 - 模块化Agent架构完成](cursor_report_history/task_20260416_08_Phase7模块化Agent架构完成.md) | 2026-04-16 21:00 | Phase 7 |
| 09 | [Token 压缩机制优化](cursor_report_history/task_20260416_09_Token压缩机制优化.md) | 2026-04-16 22:00 | Token |
| 10 | [形象选择系统实现](cursor_report_history/task_20260416_10_形象选择系统实现.md) | 2026-04-16 21:30 | UI |

---

## 修改日志

| 日期 | 版本 | 修改内容 |
|------|------|---------|
| 2026-04-16 | v1.0 | 初始创建索引文档 |
| 2026-04-16 | v2.0 | 修订实现状态，区分完整/框架/未实现，添加开发禁区 |
| 2026-04-16 | v3.0 | 更新 Phase 1-6 完成状态，新增 Phase 6/7 模块索引 |
| 2026-04-17 | v4.0 | 全面重构：SPEC设计规范、Phase 8规划、Token优化、形象系统 |
| 2026-04-17 | v4.1 | 配置系统重构：整合config.py和config/模块，新增local provider，添加配置系统说明 |

---

## 常见问题

**Q: 模块声称已完成但运行报错？**
A: 检查 INDEX.md 中的状态标注，⚠️ 框架表示有结构但未完全实现。

**Q: 如何确定任务优先级？**
A: 查看"实施路线图"，Phase 8 为当前进行中。

**Q: 发现文档与代码不符？**
A: 以代码实际执行为准，文档描述可能过时。请更新 INDEX.md 的状态标注。

**Q: Token 使用过高怎么办？**
A: 使用 4 级压缩策略（light/standard/deep/emergency），配置在 `config.toml` 的 `[context_compression]` 节。

**Q: 如何切换 ASCII 形象？**
A: 修改 `config.toml` 的 `[avatar] preset = "lobster"` 或使用命令 `/avatar shrimp`。

---

## 配置系统说明

### 配置文件结构

```
config/                         # 配置模块
├── __init__.py                # 主入口，统一导出
├── models.py                   # Pydantic 数据模型
├── providers.py                # LLM 模型预设
└── settings.py                # 配置加载与单例管理

config.toml                     # TOML 配置文件
```

### 配置节一览

| 配置节 | 说明 |
|--------|------|
| `[llm]` | LLM 配置：提供商、模型、温度、超时 |
| `[llm.discovery]` | 模型动态发现配置 |
| `[llm.local]` | 本地部署配置（Ollama/LM Studio/vLLM） |
| `[agent]` | Agent 行为：名称、工作区、苏醒间隔 |
| `[context_compression]` | 上下文压缩：阈值、摘要字数、保留策略 |
| `[tools.file]` | 文件操作：编辑、语法检查、编码 |
| `[tools.shell]` | Shell 执行：超时、安全检查 |
| `[tools.search]` | 搜索工具：目录过滤、扩展名 |
| `[tools.web]` | 网络工具：搜索启用、结果数 |
| `[security]` | 安全：目录限制、危险命令 |
| `[log]` | 日志：级别、文件、第三方库 |
| `[network]` | 网络：超时、重试、SSL |
| `[evolution]` | 进化引擎：测试门控、归档 |
| `[memory]` | 记忆系统：存储路径、条目数 |
| `[strategy]` | 策略系统：探索率、学习 |
| `[analysis]` | 代码分析：数据目录 |
| `[ui]` | CLI UI：主题、刷新频率 |
| `[debug]` | 调试：详细日志、调用跟踪 |

### 使用方式

```python
# 方式1: 从 config.toml 读取（推荐）
from config import Config, get_config
config = Config()
config = get_config()

# 方式2: 使用 Settings（单例）
from config import get_settings
settings = get_settings()
settings.config.llm.model_name = "gpt-4"

# 方式3: 从字典创建
from config import Config
config = Config.from_dict({'llm.temperature': 0.5})

# 方式4: 切换模型
from config import use_model
config = use_model("gpt-4")
```

### 环境变量覆盖

所有配置项都支持环境变量覆盖，格式为 `AGENT_` 前缀 + 配置路径：

```bash
# LLM 配置
export AGENT_LLM_PROVIDER=local
export AGENT_LLM_MODEL_NAME=qwen2.5:7b
export AGENT_LLM_TEMPERATURE=0.3

# Agent 配置
export AGENT_AGENT_AWAKE_INTERVAL=60
export AGENT_AGENT_MAX_ITERATIONS=10

# 本地 LLM 配置
export AGENT_LLM_LOCAL_URL=http://localhost:11434/v1
export AGENT_LLM_LOCAL_MODEL=qwen2.5:7b

# 日志配置
export AGENT_LOG_LEVEL=DEBUG
```

### 本地 Provider 配置

当 `provider = "local"` 时，系统自动使用 `[llm.local]` 配置：

```toml
[llm]
provider = "local"

[llm.local]
url = "http://localhost:11434/v1"    # Ollama/LM Studio/vLLM
model = "qwen2.5:7b"                # 本地模型名称
require_api_key = false              # 大多数本地部署不需要
streaming = true                      # 流式响应
context_window = 8192                  # 上下文窗口
auto_detect_model = true             # 自动检测可用模型
```

### Provider 列表

| Provider | 说明 |
|----------|------|
| `aliyun` | 阿里云百炼（默认） |
| `openai` | OpenAI GPT 系列 |
| `anthropic` | Anthropic Claude 系列 |
| `deepseek` | DeepSeek 系列 |
| `google` | Google Gemini 系列 |
| `zhipu` | 智谱 GLM 系列 |
| `ollama` | Ollama 本地部署 |
| `siliconflow` | SiliconFlow API |
| `groq` | Groq API |
| `local` | 其他本地部署（Ollama/LM Studio/vLLM） |

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
