# Token 压缩机制优化规划

**版本：** v1.0  
**日期：** 2026-04-16  
**状态：** 规划中

---

## 一、现状分析

### 1.1 当前实现

当前 Token 压缩机制位于 `tools/token_manager.py` 和 `agent.py` 中：

| 组件 | 文件 | 当前状态 |
|------|------|----------|
| Token 预算管理 | `token_manager.py` | ✅ 基础实现 |
| 压缩策略 | `token_manager.py` - `compress()` | ⚠️ 简单策略 |
| 摘要生成 | `token_manager.py` - `_generate_summary()` | ⚠️ 200字符限制 |
| 压缩触发 | `agent.py` - `_check_and_compress()` | ⚠️ 固定阈值 |
| 压缩执行 | `agent.py` - `_compress_context()` | ⚠️ 基础实现 |

### 1.2 当前配置 (config.toml)

```toml
[context_compression]
max_token_limit = 16000       # 触发压缩阈值
keep_recent_steps = 2         # 保留最近工具调用数
summary_max_chars = 200        # 摘要最大字符数 ⚠️ 过小
compression_model = "qwen-32b-awq"  # 使用同一模型
```

### 1.3 发现的问题

| # | 问题 | 影响 | 优先级 |
|---|------|------|--------|
| 1 | `summary_max_chars=200` 过小 | 摘要信息量严重不足 | P0 |
| 2 | 压缩策略单一 | 无法应对不同场景 | P1 |
| 3 | 保留 3 条 AI 消息不合理 | 应保留关键决策点 | P1 |
| 4 | 无限压缩风险 | 已添加基础保护但需完善 | P0 |
| 5 | 压缩质量无评估 | 无法判断压缩有效性 | P2 |
| 6 | 使用同一模型压缩 | 资源浪费 | P2 |

---

## 二、优化目标

### 2.1 功能目标

1. **动态摘要长度** - 根据压缩强度动态调整摘要字数
2. **多级压缩策略** - 轻量/标准/深度三档压缩
3. **智能内容保留** - 优先保留关键决策、错误信息、工具调用结果
4. **压缩保护机制** - 防止无限压缩、压缩无效回退
5. **压缩质量评估** - 评估压缩前后信息损失度

### 2.2 性能目标

- 压缩后 Token 减少 ≥ 40%
- 压缩后信息保留率 ≥ 80%
- 单次压缩耗时 < 5 秒

---

## 三、详细设计

### 3.1 架构设计

```
消息列表 → Token 预算检查 → {正常/预压缩/强制压缩/紧急}
                    ↓
              选择压缩级别
                    ↓
              生成摘要 + 关键信息提取
                    ↓
              质量评估
                    ↓
              有效? → 应用压缩 → 更新消息列表
                    ↓
              无效 → 保留原始消息
```

### 3.2 新增模块

#### 3.2.1 压缩策略管理器 `CompressionStrategy`

**文件：** `tools/compression_strategy.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

class CompressionLevel(Enum):
    LIGHT = "light"           # 轻度压缩：保留 80% 内容
    STANDARD = "standard"     # 标准压缩：保留 50% 内容
    DEEP = "deep"            # 深度压缩：保留 30% 内容 + 关键信息
    EMERGENCY = "emergency"   # 紧急压缩：只保留最新消息

@dataclass
class CompressionConfig:
    """压缩配置"""
    level: CompressionLevel
    summary_max_chars: int
    keep_ai_messages: int
    keep_tool_results: bool
    extract_key_decisions: bool
    preserve_errors: bool

class CompressionStrategy:
    """压缩策略管理器"""
    
    def get_config(self, level: CompressionLevel, current_tokens: int, max_tokens: int) -> CompressionConfig:
        """根据当前状态获取压缩配置"""
        
    def calculate_compression_ratio(self, level: CompressionLevel) -> float:
        """计算目标压缩比"""
        
    def should_preserve_message(self, msg: Any, level: CompressionLevel) -> bool:
        """判断是否应保留某条消息"""
```

#### 3.2.2 关键信息提取器 `KeyInfoExtractor`

**文件：** `tools/key_info_extractor.py`

```python
class KeyInfoExtractor:
    """从消息历史中提取关键信息"""
    
    def extract_key_decisions(self, messages: List[Any]) -> List[Dict]:
        """提取关键决策点"""
        
    def extract_errors(self, messages: List[Any]) -> List[str]:
        """提取错误信息"""
        
    def extract_tool_results(self, messages: List[Any]) -> List[Dict]:
        """提取重要的工具调用结果"""
        
    def extract_learning_insights(self, messages: List[Any]) -> List[str]:
        """提取学习洞察"""
```

#### 3.2.3 压缩质量评估器 `CompressionQualityEvaluator`

**文件：** `tools/compression_quality.py`

```python
@dataclass
class QualityReport:
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    info_preservation_rate: float  # 0.0 - 1.0
    key_info_preserved: List[str]
    key_info_lost: List[str]
    quality_score: float  # 0.0 - 1.0

class CompressionQualityEvaluator:
    """评估压缩质量"""
    
    def evaluate(self, original: List[Any], compressed: List[Any]) -> QualityReport:
        """评估压缩质量"""
        
    def is_compression_effective(self, report: QualityReport) -> bool:
        """判断压缩是否有效"""
```

### 3.3 改进现有模块

#### 3.3.1 增强 `token_manager.py`

新增配置项：

```python
@dataclass
class CompressionThresholds:
    light_threshold: float = 0.6   # 60% 开始轻度压缩
    standard_threshold: float = 0.8  # 80% 标准压缩
    deep_threshold: float = 0.9   # 90% 深度压缩
    emergency_threshold: float = 0.95  # 95% 紧急压缩
```

增强 `EnhancedTokenCompressor` 类：

```python
class EnhancedTokenCompressor:
    """增强版 Token 压缩器"""
    
    # 新增属性
    strategy: CompressionStrategy
    key_extractor: KeyInfoExtractor
    quality_evaluator: CompressionQualityEvaluator
    compression_count: int = 0
    max_compressions_per_session: int = 5
    
    # 改进方法
    def compress(
        self,
        messages: List[Any],
        max_chars: int = None,  # 动态调整
        level: CompressionLevel = CompressionLevel.STANDARD,
    ) -> Tuple[List[Any], str]:
        """增强版压缩 - 支持多级压缩"""
        
    def _smart_truncate(self, content: str, max_chars: int) -> str:
        """智能截断 - 保留完整句子"""
        
    def _preserve_essential_info(self, messages: List[Any]) -> List[Dict]:
        """保留关键信息的辅助方法"""
```

#### 3.3.2 增强 `agent.py`

改进压缩触发逻辑：

```python
def _check_and_compress(self, messages: list, iteration: int) -> list:
    """增强版 Token 检查与压缩"""
    current_tokens = estimate_messages_tokens(messages)
    max_budget = self.config.context_compression.max_token_limit
    ratio = current_tokens / max_budget
    
    # 1. 防止无限压缩
    if iteration > self.max_safe_iterations:
        _debug_logger.warning("[Token] 迭代过多，跳过压缩")
        return messages
    
    # 2. 计算压缩次数
    compression_count = getattr(self, 'compression_count', 0)
    
    # 3. 选择压缩级别
    if ratio > 0.95:
        level = "emergency"
    elif ratio > 0.9:
        level = "deep" if compression_count < 2 else "standard"
    elif ratio > 0.8:
        level = "standard"
    elif ratio > 0.6 and iteration > 1:
        level = "light"
    else:
        return messages
    
    # 4. 执行压缩
    messages = self._compress_context(messages, level)
    
    # 5. 评估压缩效果
    if self._is_compression_ineffective():
        _debug_logger.warning("[Token] 压缩无效，回退原始消息")
        return getattr(self, '_last_messages', messages)
    
    self.compression_count = compression_count + 1
    return messages
```

### 3.4 配置改进

**文件：** `config.toml`

```toml
[context_compression]
enabled = true
max_token_limit = 16000

# 新增配置项
[context_compression.strategy]
# 压缩阈值（相对于 max_token_limit）
light_threshold = 0.6    # 轻度压缩阈值
standard_threshold = 0.8 # 标准压缩阈值
deep_threshold = 0.9     # 深度压缩阈值

# 摘要配置
light_summary_chars = 500
standard_summary_chars = 1000
deep_summary_chars = 2000

# 保留策略
keep_ai_messages = 5        # 保留最近 5 条 AI 消息
keep_tool_results = true     # 保留工具调用结果
preserve_errors = true       # 保留错误信息
extract_key_decisions = true # 提取关键决策

# 安全限制
max_compressions_per_session = 5
compression_effectiveness_threshold = 0.7  # 压缩效率阈值
```

---

## 四、实施计划

### Phase 1: 核心架构 (基础改进)

| 任务 | 文件 | 优先级 | 工作量 |
|------|------|--------|--------|
| 1.1 创建 `CompressionLevel` 枚举和配置类 | `tools/compression_strategy.py` | P0 | 1h |
| 1.2 实现 `CompressionStrategy.get_config()` | `tools/compression_strategy.py` | P0 | 1h |
| 1.3 改进 `summary_max_chars` 动态计算 | `tools/token_manager.py` | P0 | 0.5h |
| 1.4 添加迭代过多保护 | `agent.py` | P0 | 0.5h |
| 1.5 添加压缩无效回退 | `agent.py` | P0 | 1h |

### Phase 2: 智能内容保留

| 任务 | 文件 | 优先级 | 工作量 |
|------|------|--------|--------|
| 2.1 创建 `KeyInfoExtractor` 类 | `tools/key_info_extractor.py` | P1 | 2h |
| 2.2 实现关键决策提取 | `tools/key_info_extractor.py` | P1 | 1h |
| 2.3 实现错误信息提取 | `tools/key_info_extractor.py` | P1 | 1h |
| 2.4 集成到压缩流程 | `tools/token_manager.py` | P1 | 1h |

### Phase 3: 压缩质量评估

| 任务 | 文件 | 优先级 | 工作量 |
|------|------|--------|--------|
| 3.1 创建 `CompressionQualityEvaluator` | `tools/compression_quality.py` | P2 | 2h |
| 3.2 实现信息保留率计算 | `tools/compression_quality.py` | P2 | 1h |
| 3.3 集成质量评估到压缩流程 | `tools/token_manager.py` | P2 | 1h |
| 3.4 根据质量决定是否回退 | `agent.py` | P2 | 1h |

### Phase 4: 配置与测试

| 任务 | 文件 | 优先级 | 工作量 |
|------|------|--------|--------|
| 4.1 更新 `config.toml` 配置 | `config.toml` | P0 | 0.5h |
| 4.2 创建 `test_compression_strategy.py` | `tests/test_compression_strategy.py` | P1 | 2h |
| 4.3 创建 `test_key_info_extractor.py` | `tests/test_key_info_extractor.py` | P1 | 2h |
| 4.4 更新 `test_token_manager.py` | `tests/test_token_manager.py` | P1 | 1h |
| 4.5 集成测试验证 | - | P0 | 2h |

---

## 五、测试计划

### 5.1 单元测试

**文件：** `tests/test_compression_strategy.py`

```python
class TestCompressionStrategy:
    def test_light_threshold_returns_light_config(self): ...
    def test_deep_threshold_returns_deep_config(self): ...
    def test_emergency_threshold_returns_emergency_config(self): ...
    def test_compression_ratio_calculation(self): ...
```

**文件：** `tests/test_key_info_extractor.py`

```python
class TestKeyInfoExtractor:
    def test_extract_errors_from_messages(self): ...
    def test_extract_tool_results(self): ...
    def test_extract_key_decisions(self): ...
    def test_empty_messages_returns_empty(self): ...
```

**文件：** `tests/test_compression_quality.py`

```python
class TestCompressionQualityEvaluator:
    def test_evaluate_returns_quality_report(self): ...
    def test_is_effective_with_high_preservation(self): ...
    def test_is_ineffective_with_low_preservation(self): ...
```

### 5.2 集成测试

**文件：** `tests/test_enhanced_compression.py`

```python
class TestEnhancedCompression:
    def test_light_compression_preserves_most_content(self): ...
    def test_deep_compression_reduces_significantly(self): ...
    def test_compression_quality_evaluation(self): ...
    def test_compression_ineffective_rolls_back(self): ...
    def test_max_compressions_limit(self): ...
```

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 压缩丢失关键信息 | 高 | 关键信息提取器 + 质量评估 |
| 压缩后 Token 反而增加 | 中 | 压缩前检查预估大小 |
| LLM 调用超时 | 低 | 回退到规则摘要 |
| 配置文件迁移 | 低 | 保持向后兼容 |

---

## 七、验收标准

1. **压缩效率** - 压缩后 Token 减少 ≥ 40%
2. **信息保留** - 关键信息保留率 ≥ 80%
3. **稳定性** - 不会无限压缩
4. **可配置** - 所有参数可通过 config.toml 配置
5. **测试覆盖** - 新增测试用例 ≥ 30 个

---

## 八、相关文件索引

| 文件 | 作用 |
|------|------|
| `tools/token_manager.py` | Token 管理器 - 需增强压缩逻辑 |
| `tools/compression_strategy.py` | 新增 - 压缩策略管理器 |
| `tools/key_info_extractor.py` | 新增 - 关键信息提取器 |
| `tools/compression_quality.py` | 新增 - 压缩质量评估器 |
| `agent.py` | Agent 主程序 - 需增强压缩触发逻辑 |
| `config.toml` | 配置文件 - 需新增配置项 |
| `tests/test_token_manager.py` | 现有测试 - 需更新 |
| `tests/test_compression_strategy.py` | 新增 - 压缩策略测试 |
| `tests/test_key_info_extractor.py` | 新增 - 关键信息提取测试 |
| `tests/test_enhanced_compression.py` | 新增 - 增强压缩集成测试 |
