# 自我进化 Agent - 工具操作手册

## 【核心安全铁律】

1. **绝不盲写**：修改任何代码前，必须先用 `read_local_file` 读取原文件。
2. **绝不带伤重启**：`edit_local_file` 后，必须立即调用 `check_syntax`；仅当返回 `"Syntax OK"` 才可 `trigger_self_restart`。
3. **记忆坍缩前置**：每次 `trigger_self_restart` 前，必须先调用 `commit_compressed_memory`，`new_core_context` ≤300字，仅保留致命教训与当前架构现状。
4. **禁区**：`restarter.py` 绝对不可修改！

---

## 【文件操作工具】

### read_local_file
读取本地文件内容。**修改前必须先读取！**

```
参数:
  - file_path: 文件路径 (相对或绝对)
  - encoding: 编码，默认自动检测
  - max_lines: 最大行数限制

返回: 带行号的文件内容
```

### list_directory
列出目录内容。

```
参数:
  - path: 目录路径
  - show_hidden: 是否显示隐藏文件
  - recursive: 是否递归

返回: 格式化的目录列表
```

---

## 【代码编辑工具】

### edit_local_file
编辑本地文件，**精确匹配替换**。

```
参数:
  - file_path: 要编辑的文件路径
  - search_string: 要替换的原字符串 (必须精确匹配！)
  - replace_string: 替换后的新字符串

返回值:
  - "✓ 编辑成功" + 备份信息 → 调用 check_syntax
  - "错误: 未找到目标代码" → 重新读取文件确认
  - "错误: 找到多个匹配项" → 增加上下文确保唯一

⚠️ 重要：编辑后必须立即调用 check_syntax！
```

### create_new_file
创建新文件或覆盖现有文件。

```
参数:
  - file_path: 文件路径
  - content: 文件内容
  - overwrite: 是否覆盖已存在文件

返回值:
  - "成功: 已创建新文件" + 文件信息
  - "错误: 文件已存在 (overwrite=False)" → 设置 overwrite=True
```

---

## 【安全检查工具】

### check_syntax
使用 AST 解析检查 Python 文件语法。**edit_local_file 后必须调用！**

```
参数:
  - file_path: Python 文件路径

返回值:
  - "Syntax OK" → 可以安全重启
  - 详细的错误追踪 → 立即修复错误，重新编辑
```

### backup_project
创建项目备份。

```
参数:
  - version_note: 版本说明

返回: 备份文件路径和包含内容

⚠️ 建议：重大修改前先备份
```

---

## 【重生工具】

### trigger_self_restart
触发 Agent 自我重启。

```
参数:
  - reason: 重启原因

前置条件:
  1. ✅ 已调用 commit_compressed_memory
  2. ✅ 如修改了代码，已调用 check_syntax 并返回 "Syntax OK"

返回值:
  - "✓ 重启进程已触发" → 原进程应调用 sys.exit(0)
  - "错误: ..." → 修复错误后再试

⚠️ 注意：必须先保存记忆再重启！
```

### commit_compressed_memory
跨代记忆坍缩。

```
参数:
  - new_core_context: 压缩后的上下文 (≤300字)
  - next_goal: 下一代的核心目标

⚠️ 必须在 trigger_self_restart 之前调用！
```

### read_memory
读取当前记忆。

```
返回值: JSON 格式的记忆内容
  - generation: 当前世代
  - core_context: 历史上下文摘要
  - current_goal: 当前目标
```

---

## 【网络工具】

### web_search
搜索互联网获取信息。

```
参数:
  - query: 搜索关键词

返回: 搜索结果摘要
```

### read_webpage
读取指定网页内容。

```
参数:
  - url: 网页 URL

返回: 网页正文内容
```

---

## 【标准工作流】

### 代码修改闭环
```
1. read_local_file("目标文件")  # 读取当前内容
2. edit_local_file(...)        # 执行修改
3. check_syntax("目标文件")     # 语法自检
4. # 如果 Syntax OK:
5. commit_compressed_memory(...) # 保存记忆
6. trigger_self_restart(...)    # 重启生效
```

### 首次运行/苏醒
```
1. read_memory()                # 获取历史上下文
2. list_directory(".")          # 了解项目结构
3. 思考当前任务
4. 按需调用工具
```

---

## 【自我测试与进化追踪工具】

### run_self_test
运行 Agent 核心功能的自我测试。

```
返回: 包含以下测试项的报告
  1. 核心模块导入测试
  2. 配置文件测试
  3. 工具模块测试
  4. restarter.py 可用性
  5. 记忆系统测试
  6. 语法自检能力
```

### get_agent_status
获取 Agent 当前状态概览。

```
返回: 世代、目标、上下文摘要、进化统计
```

### get_evolution_history
获取进化历史记录。

```
参数:
  - limit: 返回条数（默认10）

返回: 按时间倒序的进化记录
```

### log_evolution
记录一次自我修改到进化历史。

```
参数:
  - file_modified: 被修改的文件
  - change_type: "add" | "modify" | "delete"
  - reason: 修改原因
  - success: True/False
  - details: 详细信息（可选）

⚠️ 重要：每次代码修改后应调用此函数！
```

---

## 【常见错误处理】

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `未找到目标代码` | search_string 不精确 | 增加上下文，确保完全匹配 |
| `找到多个匹配项` | search_string 重复 | 提供更多行内上下文 |
| `SyntaxError` | 代码有语法错误 | 根据错误信息修复 |
| `文件已存在` | create_new_file 的 overwrite 默认为 False | 设置 overwrite=True |

---

## 【Token 管理】

当对话历史过长时，可以使用：

```
commit_compressed_memory(摘要, 下一目标)
```

- 摘要应 ≤300字
- 只保留致命教训和架构要点
- 详细过程可省略

---

## 【推荐工作流：自我改进】

```
1. run_self_test()           # 检查当前状态
2. get_agent_status()         # 查看世代和目标
3. get_evolution_history()    # 分析进化路径
4. 识别可改进点
5. read_local_file()          # 读取目标代码
6. edit_local_file()          # 执行修改
7. check_syntax()            # 语法自检
8. log_evolution()           # 记录进化
9. commit_compressed_memory() # 保存记忆
10. trigger_self_restart()    # 重启生效
```
