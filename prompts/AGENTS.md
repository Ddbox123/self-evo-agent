# AGENTS.md - 标准操作流 SOP

## 高效编码原则 (Anti-Bloat Rules)

**你现在配备了高级 AST 语法树工具和瞬时记忆机制。严禁像初学者一样"先列目录，再读全文件，再找行号"！**

### 1. 一击必中

如果你知道你要修改的函数名叫 `compress_context`：
- ❌ 错误：`list_dir` → `read_file` → `grep_search` → 多次读取不同行段（4-5 轮）
- ✅ 正确：直接调用 `get_code_entity("path/to/file.py", "compress_context")` **一次性看完**

### 2. 杜绝碎片化试探

- **不要分多次读取同一个文件的不同行段**
- 第一次读取就要带上足够的 offset/max_lines 覆盖你需要的所有上下文
- 使用 `list_file_entities` 快速了解文件结构，而不是逐行扫描

### 3. 合并思维

在你确定要修改什么之后：
1. **立刻规划完整的 `diff_text`**
2. 在一次 `apply_diff_edit` 调用中完成所有修改
3. **不要拖泥带水，不要"让我再看看确认一下"**

### 4. 阅后即焚

系统会自动清理"探索期"产生的中间步骤日志：
- 成功执行 `apply_diff_edit` 后，之前的所有 `grep_search`、`read_file`、`list_dir` 等探测日志会被自动丢弃
- 只保留"我修改了文件 X，语法检查通过"这个结论
- **不要手动清理，系统会处理**

---

## Cursor/Aider 顶级编码范式 (The Cursor Way)

### 核心原则：先搜索，后编辑

**你现在的行为模式必须像一个最先进的 AI IDE：**

1. **拒绝盲人摸象**：寻找代码时，不要用 `read_local_file` 去盲读几百行代码！
   - 优先使用 `grep_search` 全局搜索关键字或函数名
   - 使用 `find_function_calls` / `find_definitions` 精确定位
   - 瞬间拿到文件路径和行号，再按需读取

2. **精准 Diff 替换**：修改代码时，必须使用 `apply_diff_edit` 工具
   - 你的 `diff_text` 参数必须严格遵守 `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE` 格式
   - 比 `edit_local_file` 更可靠，自动处理空白符差异

3. **SEARCH 块的艺术**：
   - 你的 `SEARCH` 块必须完全原封不动地摘录原文件中的代码
   - 包含足够的前后上下文行（通常 3-5 行即可确保唯一性）
   - **不要省略，不要用 `...` 代替！**

4. **静默自检**：任何修改后，依然必须调用 `check_syntax`

### Diff Block 格式详解

```
<<<<<<< SEARCH
def old_function(param1, param2):
    """旧文档字符串"""
    old_body = True
=======
def new_function(param1, param2, param3=None):
    """新的文档字符串"""
    new_body = False
>>>>>>> REPLACE
```

**多块编辑**：在一个 diff_text 中包含多个块，一次性修改多处：

```
<<<<<<< SEARCH
old_code_1
=======
new_code_1
>>>>>>> REPLACE

<<<<<<< SEARCH
old_code_2
=======
new_code_2
>>>>>>> REPLACE
```

---

## AST 一击必中工作流

### 场景：修改已知的函数/类

1. **直接提取**：`get_code_entity("file.py", "函数名")`
2. **获取行号**：工具返回值中包含 `第 X - Y 行`
3. **制定修改方案**：一次性看完函数全部代码
4. **执行修改**：`apply_diff_edit` 一次完成
5. **语法检查**：`check_syntax`

### 场景：探索未知代码

1. **鸟瞰结构**：`list_file_entities("file.py")`
2. **定位目标**：看到所有函数/类的行号
3. **一键提取**：`get_code_entity("file.py", "目标名")`
4. **执行修改**

---

## 工作流程检查清单

每次苏醒时按序执行：

- [ ] 1. 感知与自检：目录结构如何？有何可优化代码？
- [ ] 2. 学习与探索：有何新知识新实践？
- [ ] 3. 安全修改：发现问题 → get_code_entity → apply_diff_edit → check_syntax → restart
- [ ] 4. 工具优化：发现改进空间主动优化

---

## 工具使用权限

### 优化现有工具

可以修改 `tools/` 目录下的任何文件（除 restarter.py 外）。

### 创建新工具

1. 在 `tools/` 目录下创建 `.py` 文件
2. 在 `tools/__init__.py` 中导出
3. 在 `agent.py` 的 `create_langchain_tools()` 中注册
4. 调用 `trigger_self_restart` 重启生效

### 工具速查（高效版）

| 任务 | 推荐工具 | 说明 |
|------|---------|------|
| **一击必中提取函数/类** | `get_code_entity` | AST 精准提取，无需找行号 |
| **鸟瞰文件结构** | `list_file_entities` | 快速查看所有类和函数 |
| **搜索+上下文** | `search_and_read` | 一轮完成搜索+预览 |
| **全局搜索代码** | `grep_search` | 正则表达式搜索 |
| **查找函数定义** | `find_definitions` | 定位符号定义位置 |
| **查找函数调用** | `find_function_calls` | 定位所有调用点 |
| **编辑代码** | `apply_diff_edit` | Diff Block 精准替换 |
| **语法检查** | `check_syntax` | 每次修改后必查 |
| **文件浏览** | `list_dir` | 仅用于目录结构 |
| **网络搜索** | `web_search` / `read_webpage` | - |
| **自我重启** | `trigger_self_restart` | 修改后生效 |
