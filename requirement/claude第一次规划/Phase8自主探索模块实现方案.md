# Phase 8 自主探索模块实现方案 - SPEC 规范

**版本：** v1.0
**日期：** 2026-04-17
**类型：** Phase 8 自主探索 - 核心模块实现

---

## S - Self-Evolving-Baby (自主探索系统)

### 当前问题诊断

| 问题 | 现状 | 影响 |
|------|------|------|
| Phase 8 模块框架态 | autonomous_explorer.py 等仅有占位 | 无法实现自主进化 |
| agent.py 臃肿 | ~1000行主循环 | 维护困难、难以扩展 |
| AgentCore 未实现 | core/agent_core.py 仅为抽象基类 | 无法支撑自主行为 |
| 目标生成缺失 | goal_generator.py 框架态 | 无法自主生成进化目标 |

---

## P - Purpose (目标)

### 核心目标

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 8 自主探索目标                           │
├─────────────────────────────────────────────────────────────────┤
│  1. 实现 AutonomousExplorer - 自主探索引擎                       │
│  2. 实现 OpportunityFinder - 机会发现器                         │
│  3. 实现 GoalGenerator - 目标生成器                             │
│  4. 完善 AgentCore - 抽象基类实现                               │
│  5. 渐进式拆分 agent.py - 降低复杂度                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## E - Evolution (进化路径)

### 当前状态
- ✅ Phase 1-7 全部完成
- ✅ Token 优化完成
- ✅ 形象系统完成
- ✅ Phase 5 记忆增强完成
- ⚠️ Phase 8 自主探索 - 框架态

---

## 一、架构设计

### 1.1 自主探索架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      自主探索架构                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     AutonomousMode                         │ │
│  │                    (自主模式入口)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│         ┌─────────────────────┼─────────────────────┐              │
│         ▼                     ▼                     ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐       │
│  │Autonomous   │      │ Opportunity │      │    Goal     │       │
│  │ Explorer    │ ───▶ │   Finder    │ ───▶ │ Generator   │       │
│  │  探索引擎   │      │  机会发现   │      │  目标生成   │       │
│  └─────────────┘      └─────────────┘      └─────────────┘       │
│         │                     │                     │              │
│         └─────────────────────┼─────────────────────┘              │
│                               ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    AgentCore (抽象基类)                      │ │
│  │  - 自主行为接口                                              │ │
│  │  - 状态管理                                                  │ │
│  │  - 决策执行                                                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                               │                                    │
│                               ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    SelfEvolvingAgent                        │ │
│  │                    (主类 - 待拆分)                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| AutonomousMode | 自主模式入口，协调各组件 | 状态/上下文 | 探索决策 |
| AutonomousExplorer | 分析代码库，发现优化点 | 代码/历史 | 机会列表 |
| OpportunityFinder | 评估机会优先级 | 机会列表 | 排序后机会 |
| GoalGenerator | 生成具体进化目标 | 优先级机会 | 目标描述 |
| AgentCore | 抽象基类，定义自主行为接口 | - | - |

---

## 二、功能模块

### 2.1 AutonomousMode (入口)

```python
class AutonomousMode:
    """自主模式入口"""

    def __init__(self, config: Config):
        self.explorer = AutonomousExplorer(config)
        self.finder = OpportunityFinder(config)
        self.generator = GoalGenerator(config)

    def run_cycle(self) -> Optional[str]:
        """运行一次自主探索循环"""
        # 1. 探索 - 发现机会
        opportunities = self.explorer.explore()

        # 2. 评估 - 排序机会
        prioritized = self.finder.evaluate(opportunities)

        # 3. 生成 - 产生目标
        if prioritized:
            goal = self.generator.generate(prioritized[0])
            return goal

        return None
```

### 2.2 AutonomousExplorer (探索引擎)

```python
class AutonomousExplorer:
    """自主探索引擎"""

    def explore(self) -> List[Opportunity]:
        """
        探索代码库发现问题

        分析维度：
        - 代码重复
        - 复杂度过高
        - 注释缺失
        - 命名不规范
        - 测试覆盖率低
        - 依赖过载
        """
        opportunities = []

        # 分析代码复杂度
        opportunities.extend(self._analyze_complexity())

        # 分析测试覆盖率
        opportunities.extend(self._analyze_test_coverage())

        # 分析依赖关系
        opportunities.extend(self._analyze_dependencies())

        return opportunities

    def _analyze_complexity(self) -> List[Opportunity]:
        """分析代码复杂度"""

    def _analyze_test_coverage(self) -> List[Opportunity]:
        """分析测试覆盖率"""

    def _analyze_dependencies(self) -> List[Opportunity]:
        """分析依赖关系"""
```

### 2.3 OpportunityFinder (机会发现器)

```python
@dataclass
class Opportunity:
    """机会"""
    type: str  # complexity, coverage, dependency, etc.
    file: str
    description: str
    impact: float  # 0.0 - 1.0
    effort: float  # 0.0 - 1.0
    priority: float = 0.0


class OpportunityFinder:
    """机会发现与评估"""

    def evaluate(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        评估机会优先级

        优先级公式: priority = impact * 0.6 + (1 - effort) * 0.4
        """
        for opp in opportunities:
            opp.priority = opp.impact * 0.6 + (1 - opp.effort) * 0.4

        # 按优先级排序
        return sorted(opportunities, key=lambda x: x.priority, reverse=True)
```

### 2.4 GoalGenerator (目标生成器)

```python
class GoalGenerator:
    """目标生成器"""

    def generate(self, opportunity: Opportunity) -> str:
        """
        生成具体目标描述

        输出格式:
        "优化 {file} 的 {type} 问题：{description}，预计节省 {tokens} Token"
        """
        templates = {
            "complexity": "优化 {file} 的复杂度：{description}",
            "coverage": "提升 {file} 的测试覆盖率：{description}",
            "dependency": "简化 {file} 的依赖：{description}",
        }

        template = templates.get(opportunity.type, "优化 {file}：{description}")
        return template.format(file=opportunity.file, description=opportunity.description)
```

### 2.5 AgentCore (抽象基类)

```python
from abc import ABC, abstractmethod


class AgentCore(ABC):
    """Agent 核心抽象基类"""

    @abstractmethod
    def think(self, context: Dict[str, Any]) -> str:
        """思考过程"""
        pass

    @abstractmethod
    def act(self, action: str) -> Any:
        """执行动作"""
        pass

    @abstractmethod
    def learn(self, experience: Dict[str, Any]) -> None:
        """从经验中学习"""
        pass

    @abstractmethod
    def get_state(self) -> AgentState:
        """获取当前状态"""
        pass


class SelfEvolvingCore(AgentCore):
    """自我进化 Agent 核心实现"""

    def think(self, context: Dict[str, Any]) -> str:
        # 实现思考逻辑
        pass

    def act(self, action: str) -> Any:
        # 实现动作执行
        pass

    def learn(self, experience: Dict[str, Any]) -> None:
        # 实现学习逻辑
        pass

    def get_state(self) -> AgentState:
        # 实现状态获取
        pass
```

---

## 三、agent.py 拆分计划

### 3.1 当前问题

```
agent.py (~1000行)
├── __init__ (初始化)
├── think_and_act (主循环 ~200行)
├── _build_system_prompt (~50行)
├── _check_and_compress (~60行)
├── _compress_context (~80行)
├── _invoke_llm (~50行)
├── _execute_tool (~100行)
├── _handle_restart (~50行)
└── run_loop (~60行)
```

### 3.2 拆分目标

```
core/
├── agent_loop.py      # 主循环逻辑
├── agent_prompt.py    # 提示词构建
├── agent_compress.py  # 压缩逻辑
├── agent_invoke.py    # LLM 调用
└── agent_execute.py   # 工具执行
```

### 3.3 拆分优先级

| 优先级 | 模块 | 理由 |
|--------|------|------|
| P0 | agent_compress.py | 已与 memory_manager 解耦 |
| P1 | agent_prompt.py | 独立功能，依赖少 |
| P2 | agent_invoke.py | 与 llm_orchestrator 交互 |
| P3 | agent_execute.py | 工具执行逻辑 |
| P4 | agent_loop.py | 最后拆分主循环 |

---

## 四、执行计划

### Phase 8.1: 核心模块实现 (2-3天)

| 任务 | 文件 | 状态 |
|------|------|------|
| 实现 AutonomousMode | `core/autonomous_mode.py` | ⚠️ 框架→✅ |
| 实现 AutonomousExplorer | `core/autonomous_explorer.py` | ⚠️ 框架→✅ |
| 实现 OpportunityFinder | `core/opportunity_finder.py` | ⚠️ 框架→✅ |
| 实现 GoalGenerator | `core/goal_generator.py` | ⚠️ 框架→✅ |

### Phase 8.2: AgentCore 实现 (1-2天)

| 任务 | 文件 | 状态 |
|------|------|------|
| 实现 AgentCore 抽象基类 | `core/agent_core.py` | ⚠️ 框架→✅ |
| 实现 SelfEvolvingCore | `core/agent_core.py` | 新增 |

### Phase 8.3: agent.py 拆分 (2-3天)

| 任务 | 文件 | 状态 |
|------|------|------|
| 拆分压缩模块 | `core/agent_compress.py` | ⚠️ 新增 |
| 拆分提示词模块 | `core/agent_prompt.py` | ⚠️ 新增 |
| 拆分 LLM 调用模块 | `core/agent_invoke.py` | ⚠️ 新增 |
| 拆分工具执行模块 | `core/agent_execute.py` | ⚠️ 新增 |
| 拆分主循环模块 | `core/agent_loop.py` | ⚠️ 新增 |

### Phase 8.4: 集成测试 (1-2天)

| 任务 | 文件 | 状态 |
|------|------|------|
| 单元测试 | `tests/test_autonomous_explorer.py` | ⚠️ 框架→✅ |
| 集成测试 | `tests/test_autonomous_mode.py` | ⚠️ 新增 |

---

## 五、测试计划

### 5.1 单元测试

```python
# tests/test_autonomous_explorer.py
def test_explore_complexity():
    """测试复杂度分析"""

def test_explore_test_coverage():
    """测试覆盖率分析"""

def test_explore_dependencies():
    """测试依赖分析"""

# tests/test_opportunity_finder.py
def test_evaluate_priority():
    """测试优先级评估"""

# tests/test_goal_generator.py
def test_generate_goal():
    """测试目标生成"""

# tests/test_agent_core.py
def test_think_interface():
    """测试思考接口"""

def test_act_interface():
    """测试行动接口"""
```

### 5.2 集成测试

```python
# tests/test_autonomous_mode.py
def test_full_cycle():
    """测试完整自主探索循环"""
```

---

## 六、关键指标

| 指标 | 当前 | 目标 |
|------|------|------|
| Phase 8 模块完成率 | ~20% | > 90% |
| agent.py 行数 | ~1000 | < 500 |
| 自主探索准确率 | N/A | > 70% |
| 单元测试覆盖率 | N/A | > 80% |

---

## 七、风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 拆分破坏现有功能 | agent.py 可能无法运行 | 逐步拆分，每步测试 |
| 自主探索误判 | 执行错误优化 | 添加人工确认机制 |
| 循环依赖 | 模块间循环引用 | 遵循依赖方向：A→B→C |

---

## 八、文件清单

```
core/
├── autonomous_mode.py        # [框架→完整] 自主模式入口
├── autonomous_explorer.py    # [框架→完整] 探索引擎
├── opportunity_finder.py     # [框架→完整] 机会发现
├── goal_generator.py         # [框架→完整] 目标生成
├── agent_core.py             # [框架→完整] Agent 核心基类
├── agent_compress.py         # [新增] 压缩逻辑拆分
├── agent_prompt.py           # [新增] 提示词构建拆分
├── agent_invoke.py           # [新增] LLM 调用拆分
├── agent_execute.py          # [新增] 工具执行拆分
└── agent_loop.py             # [新增] 主循环拆分

tests/
├── test_autonomous_mode.py   # [新增] 自主模式测试
├── test_autonomous_explorer.py # [框架→完整] 探索引擎测试
├── test_opportunity_finder.py # [新增] 机会发现测试
├── test_goal_generator.py    # [新增] 目标生成测试
├── test_agent_core.py        # [完整] Agent 核心测试
└── test_agent拆分_*.py       # [新增] 各模块测试
```

---

## 九、里程碑

| 阶段 | 完成标准 | 预计时间 |
|------|----------|----------|
| v8.1 | Phase 8 核心模块 | 3天 |
| v8.2 | AgentCore 实现 | 2天 |
| v8.3 | agent.py 拆分 | 3天 |
| v8.4 | 集成测试 | 2天 |
| v9.0 | Phase 8 完成 | 10天 |

---

**下一步行动：**
1. 实现 `AutonomousExplorer._analyze_complexity()` - 复杂度分析
2. 实现 `OpportunityFinder.evaluate()` - 机会评估
3. 实现 `GoalGenerator.generate()` - 目标生成
4. 编写单元测试
5. 更新 `report_history/claude_report/`
