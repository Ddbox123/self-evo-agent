# agent.py 模块化拆分方案 - SPEC 规范

**版本：** v1.0
**日期：** 2026-04-17
**类型：** 技术重构 - agent.py 臃肿问题解决

---

## S - Self-Evolving-Baby (agent.py 拆分)

### 当前问题诊断

| 问题 | 现状 | 影响 |
|------|------|------|
| agent.py 臃肿 | ~1000行 | 维护困难、难以扩展 |
| 职责不清 | 混合了 LLM 调用、压缩、工具执行等 | 违反单一职责原则 |
| 测试困难 | 难以单独测试各功能 | 质量难以保证 |
| 扩展困难 | 新增功能只能堆砌在主类中 | 架构腐化 |

---

## P - Purpose (目标)

### 核心目标

```
┌─────────────────────────────────────────────────────────────────┐
│                   agent.py 模块化拆分目标                         │
├─────────────────────────────────────────────────────────────────┤
│  1. 降低单一文件复杂度 (1000行 → <500行)                         │
│  2. 职责分离 - 每个模块只做一件事                               │
│  3. 可测试性 - 单元测试覆盖率 > 80%                             │
│  4. 可扩展性 - 新功能可以独立模块添加                            │
│  5. 向后兼容 - 拆分后功能完全等价于拆分前                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## E - Evolution (进化路径)

### 当前状态
- ✅ Phase 1-7 全部完成
- ✅ 新记忆组件已集成到 memory_manager
- ✅ LLM Orchestrator 已模块化
- ⚠️ agent.py 仍为单一臃肿文件

---

## 一、当前架构分析

### 1.1 agent.py 结构

```
agent.py (~1000行)
├── 导入 (30行)
├── SelfEvolvingAgent 类
│   ├── __init__ (100行)
│   │   ├── 配置初始化
│   │   ├── 本地 Provider 切换
│   │   ├── 工具创建
│   │   ├── 模型发现
│   │   ├── LLM Orchestrator 初始化
│   │   ├── 工具注册表初始化
│   │   ├── 记忆管理器初始化
│   │   └── 任务规划器初始化
│   │
│   ├── think_and_act (200行)  ◄── 主循环
│   │   ├── 构建系统提示词
│   │   ├── 决策树处理
│   │   ├── Token 检查与压缩
│   │   ├── LLM 调用
│   │   ├── 工具执行
│   │   └── 响应处理
│   │
│   ├── _build_system_prompt (50行)
│   ├── _check_and_compress (60行)
│   ├── _compress_context (80行)
│   ├── _invoke_llm (50行)
│   ├── _execute_tool (100行)
│   ├── _handle_restart (50行)
│   ├── _apply_strategy_adjustments (40行)
│   ├── _build_decision_context (30行)
│   ├── _build_strategy_context (30行)
│   └── run_loop (60行)
│
└── 辅助函数 (50行)
```

### 1.2 依赖关系分析

```
┌──────────────────────────────────────────────────────────────────┐
│                      依赖关系图                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  agent.py                                                        │
│     │                                                           │
│     ├──▶ config (配置)                                           │
│     ├──▶ llm_orchestrator (LLM 调用)  ◄── 已模块化               │
│     ├──▶ memory_manager (记忆)       ◄── 已增强                  │
│     ├──▶ tool_registry (工具注册)    ◄── 已模块化               │
│     ├──▶ task_planner (任务规划)     ◄── 已模块化               │
│     ├──▶ decision_tree (决策)                                    │
│     ├──▶ priority_optimizer (优先级)                            │
│     ├──▶ strategy_selector (策略)                               │
│     ├──▶ token_compressor (压缩)                                 │
│     │                                                           │
│     └──▶ tools (工具执行)                                        │
│           ├── shell_tools                                        │
│           ├── memory_tools                                       │
│           ├── code_analysis_tools                                │
│           ├── search_tools                                       │
│           └── rebirth_tools                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 二、拆分方案

### 2.1 拆分后的模块结构

```
core/
├── ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│   Agent 主控层 (协调各模块)
├── ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│
├── agent.py                     # 主入口，保留核心协调逻辑 (~300行)
│
├── ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│   Agent 功能模块 (按职责拆分)
├── ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
│
├── agent_builder.py             # Agent 构建器 (~100行)
│   ├── create_agent()           # 工厂方法
│   ├── _init_components()       # 组件初始化
│   └── _setup_event_handlers()   # 事件处理设置
│
├── agent_loop.py                # 主循环逻辑 (~150行)
│   ├── run_loop()               # 主循环入口
│   ├── think_and_act()          # 思考行动循环
│   └── _process_user_input()    # 用户输入处理
│
├── agent_prompt.py              # 提示词构建 (~80行)
│   ├── build_system_prompt()    # 系统提示词
│   ├── _get_generation_context() # 世代上下文
│   └── _get_current_goal()      # 当前目标
│
├── agent_compress.py            # 压缩逻辑 (~120行)
│   ├── check_and_compress()     # Token 检查
│   ├── compress_context()       # 上下文压缩
│   └── _get_compression_level() # 压缩级别选择
│
├── agent_invoke.py              # LLM 调用 (~80行)
│   ├── invoke_llm()             # LLM 调用入口
│   ├── invoke_with_retry()      # 重试逻辑
│   └── _handle_llm_response()   # 响应处理
│
├── agent_execute.py             # 工具执行 (~150行)
│   ├── execute_tool()           # 工具执行入口
│   ├── _execute_tool_impl()     # 实际执行
│   ├── _handle_special_tools()  # 特殊工具处理
│   └── _build_strategy_context() # 策略上下文
│
├── agent_decision.py            # 决策逻辑 (~80行)
│   ├── make_decision()          # 决策入口
│   ├── _build_decision_context() # 构建决策上下文
│   └── _apply_strategy()        # 应用策略
│
└── agent_restart.py             # 重启逻辑 (~60行)
    ├── handle_restart()         # 处理重启
    └── enter_hibernation()      # 休眠处理
```

### 2.2 模块职责

| 模块 | 职责 | 公开 API |
|------|------|---------|
| agent.py | 主入口，协调各子模块 | SelfEvolvingAgent |
| agent_builder.py | 创建和初始化 Agent | create_agent() |
| agent_loop.py | 主循环控制 | run_loop(), think_and_act() |
| agent_prompt.py | 提示词管理 | build_system_prompt() |
| agent_compress.py | Token 压缩 | check_and_compress(), compress_context() |
| agent_invoke.py | LLM 调用 | invoke_llm() |
| agent_execute.py | 工具执行 | execute_tool() |
| agent_decision.py | 自主决策 | make_decision() |
| agent_restart.py | 重启管理 | handle_restart() |

---

## 三、拆分步骤

### Phase 1: 准备 (0.5天)

| 任务 | 说明 | 验证 |
|------|------|------|
| 备份 agent.py | 保留原始文件 | - |
| 分析依赖关系 | 确认拆分边界 | - |
| 创建模块骨架 | 空的函数框架 | import 成功 |

### Phase 2: 按依赖顺序拆分 (2-3天)

**拆分顺序遵循依赖方向：远离主循环的先拆**

| 顺序 | 模块 | 依赖关系 | 拆分理由 |
|------|------|---------|---------|
| 1 | agent_prompt.py | 无依赖其他 agent 模块 | 独立功能 |
| 2 | agent_compress.py | 依赖 memory_manager | 已解耦 |
| 3 | agent_restart.py | 无依赖 | 独立功能 |
| 4 | agent_decision.py | 依赖 decision_tree | 已模块化 |
| 5 | agent_invoke.py | 依赖 llm_orchestrator | 已模块化 |
| 6 | agent_execute.py | 依赖 tool_registry | 已模块化 |
| 7 | agent_loop.py | 依赖所有其他 | 最后拆分 |
| 8 | agent_builder.py | 依赖所有配置 | 初始化逻辑 |

### Phase 3: 整合测试 (1天)

| 任务 | 说明 |
|------|------|
| 逐个模块测试 | 确保每个拆分模块可独立导入 |
| 集成测试 | 确保拆分后功能等价 |
| 性能测试 | 确保拆分无性能损失 |

### Phase 4: 清理 (0.5天)

| 任务 | 说明 |
|------|------|
| 删除旧代码 | 从 agent.py 删除已迁移代码 |
| 更新导入 | 更新所有 import 语句 |
| 更新文档 | 更新 INDEX.md |

---

## 四、关键设计决策

### 4.1 为什么不完全删除 agent.py？

保留 agent.py 作为**主入口和协调器**：
- 保留 `SelfEvolvingAgent` 类作为门面 (Facade)
- 各子模块通过组合方式被引用
- 对外接口不变，保持向后兼容

### 4.2 模块间通信

采用**依赖注入**方式，避免循环依赖：

```python
class SelfEvolvingAgent:
    def __init__(self, config):
        # 注入依赖
        self.builder = AgentBuilder(config, self)
        self.loop = AgentLoop(self)
        self.compress = AgentCompress(self)
        # ...

    def think_and_act(self):
        # 协调各模块
        self.loop.think_and_act()
```

### 4.3 错误处理

每个模块独立处理错误，向上传播但不直接处理：

```python
# agent_compress.py
def compress_context(self, messages, level):
    try:
        return self._do_compress(messages, level)
    except CompressionError:
        raise  # 向上传播，让调用者处理
```

---

## 五、测试策略

### 5.1 单元测试

每个拆分模块独立测试：

```python
# tests/test_agent_prompt.py
def test_build_system_prompt():
    """测试提示词构建"""

# tests/test_agent_compress.py
def test_check_and_compress():
    """测试 Token 检查"""

def test_compression_level_selection():
    """测试压缩级别选择"""

# tests/test_agent_invoke.py
def test_invoke_llm():
    """测试 LLM 调用"""

# tests/test_agent_execute.py
def test_execute_tool():
    """测试工具执行"""

# tests/test_agent_decision.py
def test_make_decision():
    """测试决策"""

# tests/test_agent_restart.py
def test_handle_restart():
    """测试重启处理"""
```

### 5.2 集成测试

保留现有 `test_agent.py` 作为端到端测试：

```python
# tests/test_agent.py
def test_full_cycle():
    """测试完整思考-行动循环"""

def test_restart_flow():
    """测试重启流程"""
```

---

## 六、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 拆分破坏现有功能 | Agent 无法启动 | 逐步拆分，每步验证 |
| 循环依赖 | 模块无法导入 | 遵循依赖顺序 |
| 接口不一致 | 外部调用失败 | 保持门面接口不变 |
| 性能下降 | 响应变慢 | 基准测试对比 |

---

## 七、验证清单

拆分完成的标准：

```
✅ agent.py 行数 < 500
✅ 所有子模块可独立导入
✅ 单元测试覆盖率 > 80%
✅ 集成测试全部通过
✅ 功能等价于拆分前
✅ 无新增依赖关系
✅ 代码可读性提升
```

---

## 八、文件清单

```
core/
├── agent.py                     # [重构] 主入口 (~300行)
├── agent_builder.py             # [新增] Agent 构建器
├── agent_loop.py                # [新增] 主循环逻辑
├── agent_prompt.py              # [新增] 提示词构建
├── agent_compress.py            # [新增] 压缩逻辑
├── agent_invoke.py              # [新增] LLM 调用
├── agent_execute.py             # [新增] 工具执行
├── agent_decision.py            # [新增] 决策逻辑
└── agent_restart.py             # [新增] 重启管理

tests/
├── test_agent_builder.py        # [新增] 构建器测试
├── test_agent_loop.py           # [新增] 主循环测试
├── test_agent_prompt.py         # [新增] 提示词测试
├── test_agent_compress.py       # [新增] 压缩测试
├── test_agent_invoke.py         # [新增] LLM 调用测试
├── test_agent_execute.py        # [新增] 工具执行测试
├── test_agent_decision.py       # [新增] 决策测试
├── test_agent_restart.py        # [新增] 重启测试
└── test_agent.py                # [已有] 端到端测试
```

---

## 九、里程碑

| 阶段 | 完成标准 | 预计时间 |
|------|----------|----------|
| Phase 1 | 准备与骨架 | 0.5天 |
| Phase 2 | 拆分 8 个模块 | 3天 |
| Phase 3 | 集成测试 | 1天 |
| Phase 4 | 清理与文档 | 0.5天 |
| **Total** | **agent.py 拆分完成** | **5天** |

---

**下一步行动：**
1. 创建 `core/agent_prompt.py` - 提示词构建模块
2. 创建 `core/agent_compress.py` - 压缩逻辑模块
3. 创建 `core/agent_restart.py` - 重启管理模块
4. 逐步重构 agent.py
5. 编写单元测试
