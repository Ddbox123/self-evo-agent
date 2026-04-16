# Self-Evolving Agent 测试套件

## 📊 测试覆盖总览

本测试套件为 **Self-Evolving Agent** 项目的所有核心工具模块提供全面的单元测试、集成测试、性能测试和安全测试。

---

## 📁 测试文件结构

```
tests/
├── test_shell_tools.py        # Shell 工具测试 (1300+ 行)
├── test_memory_tools.py       # 记忆与任务管理测试 (1200+ 行)
├── test_rebirth_tools.py      # 重生与休眠工具测试 (1000+ 行)
├── test_search_tools.py       # 搜索工具测试 (1100+ 行)
├── test_code_analysis_tools.py # 代码分析工具测试 (1400+ 行)
├── test_token_manager.py      # Token 压缩器测试 (1100+ 行)
└── README.md                  # 本文件
```

---

## 🧪 测试统计

### 总体数据

| 指标 | 数值 |
|------|------|
| **总测试文件数** | 6 个 |
| **总测试代码行数** | ~7100+ 行 |
| **总测试函数数** | ~350+ 个 |
| **预估总执行时间** | 3-5 分钟 |
| **最低 Python 版本** | 3.10+ |

### 分模块统计

| 测试模块 | 测试类数 | 测试函数数 | 代码行数 | 主要覆盖范围 |
|---------|---------|----------|---------|-------------|
| `test_shell_tools.py` | 14 | ~70 | 1300+ | 文件操作、命令执行、备份清理 |
| `test_memory_tools.py` | 13 | ~65 | 1200+ | 记忆索引、档案、任务管理 |
| `test_rebirth_tools.py` | 11 | ~50 | 1000+ | 重启机制、休眠、进程管理 |
| `test_search_tools.py` | 11 | ~60 | 1100+ | 正则搜索、函数查找、导入搜索 |
| `test_code_analysis_tools.py` | 12 | ~65 | 1400+ | AST 分析、Diff 编辑 |
| `test_token_manager.py` | 12 | ~60 | 1100+ | Token 估算、压缩、截断 |
| **总计** | **73** | **~370** | **7100+** | **全模块覆盖** |

---

## 🎯 测试类型

### 1. **单元测试** (约 70%)
- 每个工具函数的独立功能验证
- 边界条件测试
- 异常情况处理

### 2. **集成测试** (约 20%)
- 多工具组合工作流
- 数据流完整性
- 模块间交互

### 3. **性能测试** (约 5%)
- 大文件处理性能
- 批量操作速度
- 并发执行安全性

### 4. **安全测试** (约 5%)
- 命令注入防护
- 路径遍历攻击防护
- 敏感数据泄露防护
- DoS 攻击防护

---

## 📋 运行测试

### 运行所有测试

```bash
# 进入项目根目录
cd c:\Users\17533\Desktop\self-evo-baby

# 运行全部测试
python -m pytest tests/ -v --tb=short

# 或使用 pytest 直接
pytest tests/ -v
```

### 运行单个模块测试

```bash
# Shell 工具测试
pytest tests/test_shell_tools.py -v

# 记忆工具测试
pytest tests/test_memory_tools.py -v

# 重生工具测试
pytest tests/test_rebirth_tools.py -v

# 搜索工具测试
pytest tests/test_search_tools.py -v

# 代码分析工具测试
pytest tests/test_code_analysis_tools.py -v

# Token 管理器测试
pytest tests/test_token_manager.py -v
```

### 运行特定测试类或函数

```bash
# 运行特定测试类
pytest tests/test_shell_tools.py::TestReadFile -v

# 运行特定测试函数
pytest tests/test_shell_tools.py::TestReadFile::test_read_existing_file -v
```

### 并行运行（加速）

```bash
# 使用 pytest-xdist（需要安装）
pip install pytest-xdist
pytest tests/ -n auto  # 自动检测 CPU 核心数

# 或指定进程数
pytest tests/ -n 4
```

### 生成覆盖率报告

```bash
# 安装 coverage
pip install pytest-cov

# 运行并生成覆盖率
pytest tests/ --cov=tools --cov-report=html
# 报告生成在 htmlcov/ 目录
```

### 性能基准测试

```bash
# 使用 pytest-benchmark（需要安装）
pip install pytest-benchmark
pytest tests/ --benchmark-only
```

---

## ✅ 预期测试结果

所有测试都应该 **通过**。以下是各模块的关键验证点：

### Shell 工具 (`test_shell_tools.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestReadFile` | ✅ 全部通过 | 文件读取、编码检测、空文件 |
| `TestListDirectory` | ✅ 全部通过 | 目录列表、模式匹配、递归 |
| `TestCreateFile` | ✅ 全部通过 | 创建、覆盖、嵌套目录、Unicode |
| `TestEditFile` | ✅ 全部通过 | 字符串替换、多匹配、备份 |
| `TestCheckPythonSyntax` | ✅ 全部通过 | 语法检查、错误检测 |
| `TestExecuteShellCommand` | ✅ 全部通过 | 命令执行、安全拦截 |
| `TestRunPowerShell` | ✅ 全部通过 | PowerShell 命令、白名单验证 |
| `TestRunBatch` | ✅ 全部通过 | 批量执行、错误恢复 |
| `TestExtractSymbols` | ✅ 全部通过 | AST 符号提取 |
| `TestBackupProject` | ✅ 全部通过 | 项目备份创建 |
| `TestSelfTest` | ✅ 全部通过 | Agent 自检 |
| `TestGetAgentStatus` | ✅ 全部通过 | 状态获取 |
| `TestCleanupTestFiles` | ✅ 全部通过 | 临时文件清理 |
| `TestSecurityFeatures` | ✅ 全部通过 | 安全防护验证 |
| `TestIntegration` | ✅ 全部通过 | 端到端流程 |

### 记忆工具 (`test_memory_tools.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestMemoryBasics` | ✅ 全部通过 | 世代号、上下文、目标 |
| `TestMemoryIndex` | ✅ 全部通过 | 索引持久化、迁移 |
| `TestGenerationArchives` | ✅ 全部通过 | 归档、读取、列出 |
| `TestDynamicPrompt` | ✅ 全部通过 | 动态提示词 CRUD |
| `TestCodebaseInsight` | ✅ 全部通过 | 代码库洞察记录 |
| `TestTaskManagement` | ✅ 全部通过 | 计划、完成、修改 |
| `TestTaskManagementWorkflow` | ✅ 全部通过 | 完整任务流 |
| `TestCommitCompressedMemory` | ✅ 全部通过 | 记忆提交 |
| `TestMemorySummary` | ✅ 全部通过 | 摘要生成 |
| `TestRestartBlock` | ✅ 全部通过 | 重启阻塞检查 |
| `TestMemoryToolsIntegration` | ✅ 全部通过 | 集成流程 |
| `TestErrorHandling` | ✅ 全部通过 | 异常处理 |
| `TestEdgeCases` | ✅ 全部通过 | 边界情况 |

### 重生工具 (`test_rebirth_tools.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestHelperFunctions` | ✅ 全部通过 | PID、路径、分类、验证 |
| `TestTriggerSelfRestart` | ✅ 全部通过 | 重启触发、参数、验证 |
| `TestEnterHibernation` | ✅ 全部通过 | 休眠时长、原因、多周期 |
| `TestRebirthIntegration` | ✅ 全部通过 | 完整生命周期 |
| `TestPlatformCompatibility` | ✅ 全部通过 | 跨平台兼容 |
| `TestSecurity` | ✅ 全部通过 | 安全防护 |
| `TestConcurrency` | ✅ 全部通过 | 并发安全 |
| `TestErrorHandling` | ✅ 全部通过 | 错误恢复 |
| `TestPerformance` | ✅ 全部通过 | 性能基准 |
| `TestReturnFormats` | ✅ 全部通过 | 返回格式 |
| `TestParameterBoundaries` | ✅ 全部通过 | 参数边界 |

### 搜索工具 (`test_search_tools.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestGrepSearch` | ✅ 全部通过 | 正则搜索、过滤、上下文 |
| `TestFindFunctionCalls` | ✅ 全部通过 | 函数调用查找 |
| `TestFindDefinitions` | ✅ 全部通过 | 符号定义查找 |
| `TestSearchImports` | ✅ 全部通过 | Import 语句搜索 |
| `TestSearchAndRead` | ✅ 全部通过 | 搜索+读取一体化 |
| `TestSearchIntegration` | ✅ 全部通过 | 工具间一致性 |
| `TestSpecialScenarios` | ✅ 全部通过 | 特殊场景 |
| `TestSearchPerformance` | ✅ 全部通��� | 大规模搜索性能 |
| `TestSearchSecurity` | ✅ 全部通过 | DoS、路径遍历防护 |
| `TestReturnFormats` | ✅ 全部通过 | 返回格式规范化 |
| `TestParameterCombinations` | ✅ 全部通过 | 参数组合 |

### 代码分析工具 (`test_code_analysis_tools.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestGetCodeEntity` | ✅ 全部通过 | 实体提取（类、函数、方法） |
| `TestGetFileEntities` | ✅ 全部通过 | 文件所有实体 |
| `TestListFileEntities` | ✅ 全部通过 | 格式化实体列表 |
| `TestExtractMethodFromClass` | ✅ 全部通过 | 类方法提取 |
| `TestValidateDiffFormat` | ✅ 全部通过 | Diff 格式验证 |
| `TestApplyDiffEdit` | ✅ 全部通过 | Diff 应用、备份 |
| `TestPreviewDiff` | ✅ 全部通过 | Diff 预览 |
| `TestCodeAnalysisIntegration` | ✅ 全部通过 | 完整工作流 |
| `TestErrorHandling` | ✅ 全部通过 | 语法错误、权限 |
| `TestPerformance` | ✅ 全部通过 | 大文件、批量操作 |
| `TestDataIntegrity` | ✅ 全部通过 | 数据完整性 |
| `TestSpecialScenarios` | ✅ 全部通过 | Unicode、长文件 |

### Token 管理器 (`test_token_manager.py`)

| 测试类 | 预期结果 | 说明 |
|--------|---------|------|
| `TestEstimateTokensPrecise` | ✅ 全部通过 | 中英文 Token 估算 |
| `TestEstimateMessagesTokens` | ✅ 全部通过 | 消息列表估算 |
| `TestGetMessagePriority` | ✅ 全部通过 | 优先级推断 |
| `TestTruncateToolResult` | ✅ 全部通过 | 工具结果截断 |
| `TestTruncateAIResponse` | ✅ 全部通过 | AI 响应截断 |
| `TestSmartCompressMessage` | ✅ 全部通过 | 智能压缩 |
| `TestEnhancedTokenCompressor` | ✅ 全部通过 | 压缩器核心功能 |
| `TestTruncateByPriority` | ✅ 全部通过 | 按优先级截断 |
| `TestFormatCompressionReport` | ✅ 全部通过 | 报告格式化 |
| `TestTokenBudget` | ✅ 全部通过 | 预算管理 |
| `TestCompressionRecord` | ✅ 全部通过 | 压缩记录 |
| `TestTokenManagerIntegration` | ✅ 全部通过 | 完整压缩流程 |
| `TestErrorHandling` | ✅ 全部通过 | 异常处理 |
| `TestPerformance` | ✅ 全部通过 | 大规模消息处理 |
| `TestSpecialScenarios` | ✅ 全部通过 | Unicode、边界情况 |

---

## 🔧 测试覆盖率

### 覆盖的工具函数列表

#### Shell 工具 (15个)
- ✅ `read_file`
- ✅ `list_directory`
- ✅ `create_file`
- ✅ `edit_file`
- ✅ `check_python_syntax`
- ✅ `execute_shell_command`
- ✅ `run_powershell`
- ✅ `run_batch`
- ✅ `extract_symbols`
- ✅ `backup_project`
- ✅ `cleanup_test_files`
- ✅ `self_test`
- ✅ `get_agent_status`
- ✅ `quick_ping`
- ✅ `run_pytest`

#### 记忆工具 (18个)
- ✅ `read_memory_tool`
- ✅ `get_memory_summary_tool`
- ✅ `get_generation_tool`
- ✅ `get_current_goal_tool`
- ✅ `get_core_context_tool`
- ✅ `archive_generation_history`
- ✅ `read_generation_archive_tool`
- ✅ `list_archives_tool`
- ✅ `commit_compressed_memory_tool`
- ✅ `force_save_current_state`
- ✅ `advance_generation`
- ✅ `read_dynamic_prompt_tool`
- ✅ `update_generation_task_tool`
- ✅ `add_insight_to_dynamic_tool`
- ✅ `clear_generation_task`
- ✅ `record_codebase_insight_tool`
- ✅ `get_global_codebase_map_tool`
- ✅ `set_plan_tool`, `tick_subtask_tool`, `modify_task_tool`, `add_task_tool`, `remove_task_tool`, `get_task_status_tool`, `check_restart_block_tool`

#### 重生工具 (2个)
- ✅ `trigger_self_restart_tool`
- ✅ `enter_hibernation_tool`

#### 搜索工具 (5个)
- ✅ `grep_search_tool`
- ✅ `find_function_calls_tool`
- ✅ `find_definitions_tool`
- ✅ `search_imports_tool`
- ✅ `search_and_read_tool`

#### 代码分析工具 (8个)
- ✅ `get_code_entity`
- ✅ `get_file_entities`
- ✅ `list_file_entities`
- ✅ `extract_method_from_class`
- ✅ `apply_diff_edit`
- ✅ `validate_diff_format`
- ✅ `preview_diff`

#### Token 管理器 (12个)
- ✅ `estimate_tokens_precise`
- ✅ `estimate_messages_tokens`
- ✅ `get_message_priority`
- ✅ `truncate_tool_result`
- ✅ `truncate_ai_response`
- ✅ `smart_compress_message`
- ✅ `create_compressor`
- ✅ `truncate_by_priority`
- ✅ `format_compression_report`
- ✅ `EnhancedTokenCompressor` 类
- ✅ `TokenCompressionStats` 类
- ✅ `MessagePriority` 枚举

---

## 🛡️ 安全测试覆盖

### 命令安全
- ✅ 黑名单命令拦截 (`format`, `fdisk`, `sudo`, `netcat` 等)
- ✅ 白名单验证 (`PowerShell` 命令)
- ✅ 危险字符检测 (`|`, `;`, `&&`, `||`, `` ` ``)
- ✅ 命令注入防护

### 路径安全
- ✅ 路径遍历攻击防护 (`..` 检测)
- ✅ 沙箱限制（仅限项目目录）
- ✅ 系统目录保护 (`C:\Windows`, `C:\Program Files`)
- ✅ 敏感文件扩展名拦截 (`.exe`, `.dll`, `.bat`, `.ps1`)

### 内容安全
- ✅ 危险代码模式检测 (`os.system`, `subprocess`, `eval`, `exec`)
- ✅ 文件操作权限验证

### 其他安全
- ✅ 正则表达式 DoS 防护
- ✅ 大文件拒绝服务防护 (>10MB)
- ✅ 敏感信息泄露检查

---

## ⚡ 性能基准

| 操作 | 目标时间 | 说明 |
|------|---------|------|
| 读取文件 (1MB) | < 1s | 带编码检测 |
| 列出目录 (1000文件) | < 2s | 递归关闭 |
| 正则搜索 (100文件) | < 5s | 默认限制 500 结果 |
| 函数调用查找 | < 3s | 全项目范围 |
| AST 实体提取 | < 1s | 中等文件 |
| Diff 应用 | < 0.5s | 小文件 |
| Token 估算 (10k 字符) | < 10ms | 精确模式 |
| Token 压缩 (50消息) | < 2s | 到 50% 压缩比 |
| 重启触发 | < 1s | 启动 restarter 进程 |
| 休眠 (2秒) | 2s ± 0.5s | 实际休眠时间 |

---

## 📈 测试质量保证

### 测试设计原则

1. **隔离性**：每个测试独立运行，不依赖外部状态
2. **可重复性**：相同输入始终产生相同结果
3. **明确性**：测试失败时能快速定位问题
4. **完整性**：覆盖正常流程、边界、异常
5. **性能意识**：包含性能测试，防止退化

### Mock 和 Fixture 策略

- **`temp_test_dir`**: 临时目录，自动清理
- **`sample_py_file`**: 标准 Python 示例文件
- **`sample_project`**: 完整项目结构（多语言、嵌套目录）
- **`isolate_memory_workspace`**: 隔离记忆工作区，避免污染真实数据

### 异常测试覆盖

- ✅ 文件不存在
- ✅ 目录不存在
- ✅ 权限不足
- ✅ 语法错误
- ✅ 编码错误
- ✅ 网络超时（��拟）
- ✅ 无效参数
- ✅ 资源耗尽（大文件、超长内容）

---

## 🐛 已知问题和限制

### 1. 重启测试限制
- `test_trigger_restart_*` 测试不会真正重启测试进程（因为会结束 pytest）
- 仅验证 `trigger_self_restart_tool` 函数返回有效响应
- `restarter.py` 的实际启动在测试环境中被安全禁用

### 2. 休眠测试时间
- 休眠测试实际等待指定时间，可能会使总测试时间变长
- 使用较短的休眠时间（0.1-2秒）以平衡测试速度

### 3. 文件系统依赖
- 部分测试依赖实际文件 I/O（已使用临时目录隔离）
- Windows 路径分隔符问题已在代码中处理

### 4. 编码假设
- 测试假设 UTF-8 为默认编码
- Windows 控制台编码已在 `agent.py` 中修复

---

## 📝 测试开发规范

### 新增测试指南

当向项目中添加新的工具函数时，请遵循以下规范：

1. **文件名**: `tests/test_<module_name>.py`
2. **测试类**: 按功能分组，命名为 `Test<Feature>`
3. **测试函数**: 命名为 `test_<specific_behavior>`
4. **Fixtures**: 复用通用 fixture，必要时创建专用 fixture
5. **断言**: 使用明确的 `assert` 语句，包含错误消息
6. **文档字符串**: 为每个测试类/函数添加 docstring 说明测试目的
7. **异常测试**: 使用 `pytest.raises()` 验证异常
8. **参数化**: 使用 `@pytest.mark.parametrize` 进行多参数测试

示例：

```python
class TestMyTool:
    """测试 my_tool 功能"""
    
    def test_basic_functionality(self):
        """测试基本功能"""
        result = my_tool(param="value")
        assert result == expected, "基本功能应返回预期值"
    
    @pytest.mark.parametrize("input,expected", [
        ("case1", "result1"),
        ("case2", "result2"),
    ])
    def test_multiple_cases(self, input, expected):
        """参数化测试"""
        assert my_tool(input) == expected
```

---

## 🔄 持续集成

建议在 CI/CD 流程中加入以下步骤：

```yaml
# .github/workflows/test.yml 示例
- name: Run Tests
  run: |
    pytest tests/ -v --tb=short --cov=tools --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

---

## 📚 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [Python AST 模块](https://docs.python.org/3/library/ast.html)
- [LangChain 消息类型](https://python.langchain.com/docs/concepts/messages/)
- [Token 估算最佳实践](https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb)

---

## 📞 反馈和支持

如遇到测试问题或有改进建议，请：

1. 查看失败测试的详细输出（`-vv` 参数）
2. 检查 `tests/` 目录中的具体测试代码
3. 参考项目的其他文档（`docs/` 目录）
4. 提交 Issue 或 Pull Request

---

**最后更新**: 2026-04-15  
**测试套件版本**: v1.0  
**维护者**: Self-Evolving Agent Dev Team
