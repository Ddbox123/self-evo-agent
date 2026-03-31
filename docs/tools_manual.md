# 自我进化 Agent - 工具操作手册

## 【工具优化与扩展指南】

作为自我进化的 Agent，你被授权可以优化和扩展自己的工具能力。

### 何时应该优化工具

- 工具返回结果格式不清晰或难以解析
- 工具缺少必要的参数支持
- 工具执行效率低下
- 工具缺少错误处理，容易崩溃
- 工具功能不完整，无法满足需求

### 如何优化现有工具

1. 使用 `read_local_file` 读取目标工具文件（如 `tools/xxx_tools.py`）
2. 分析代码找出改进点
3. 使用 `edit_local_file` 进行修改
4. 使用 `check_syntax` 验证语法
5. 如需生效，更新 `agent.py` 中的注册代码并重启

### 如何创建新工具

1. 在 `tools/` 目录下创建新的 `.py` 文件（如 `my_tool.py`）
2. 实现工具函数和文档字符串
3. 在 `tools/__init__.py` 中添加导出
4. 在 `agent.py` 的 `create_langchain_tools()` 中注册

```python
# 示例：在 agent.py 中注册新工具
@tool
def my_new_tool(param: str) -> str:
    """
    新工具描述...
    """
    from tools.my_tool import my_function
    return my_function(param)

# 在工具列表中添加
return [
    # ... 其他工具 ...
    my_new_tool,
]
```

5. 调用 `trigger_self_restart` 重启使新工具生效

---

## 【核心安全铁律】

1. **绝不盲写**：修改任何代码前，必须先用 `read_local_file` 读取原文件。
2. **绝不带伤重启**：`edit_local_file` 后，必须立即调用 `check_syntax`；仅当返回 `"Syntax OK"` 才可 `trigger_self_restart`。
3. **记忆坍缩前置**：每次 `trigger_self_restart` 前，必须先调用 `commit_compressed_memory`，`new_core_context` ≤300字，仅保留致命教训与当前架构现状。
4. **禁区**：`restarter.py` 绝对不可修改！
5. **工作区域隔离**：所有生成的文件默认放在 `workspace/` 目录下，防止污染项目代码

---

## 【工作区域机制】

Agent 生成的所有文件默认存放在指定的工作区域内。

### 配置

在 `config.toml` 中配置：

```toml
[agent]
workspace = "workspace"  # 工作区域目录（相对于项目根目录）
```

### 工作原理

| 工具 | 行为 |
|------|------|
| `create_new_file_tool` | 默认在 `workspace/` 下创建文件 |
| `edit_local_file_tool` | 编辑项目文件（agent.py, tools/ 等） |
| `read_local_file_tool` | 可读取任何位置的文件 |

### 目录结构

```
self-evo-agent/
├── agent.py          # Agent 核心代码
├── config.toml       # 配置文件
├── tools/            # 工具模块
├── restarter.py      # 重启器（禁止修改）
├── workspace/        # Agent 工作区域（生成的文件）
│   ├── project1/     # 项目1
│   ├── project2/     # 项目2
│   └── output/       # 输出文件
```

### 优点

1. **隔离**：生成的内容与核心代码分离
2. **清理**：可以随时删除整个 `workspace/` 目录
3. **整洁**：不会因为生成测试文件而污染项目

---

## 【工具执行超时机制】

每个工具都有最大执行时间限制，超过后返回超时错误给模型。

### 超时配置

| 工具类型 | 超时时间 | 说明 |
|---------|---------|------|
| `run_batch_tool` | 120秒 | 批量命令可能较长 |
| `run_cmd_tool` | 60秒 | 系统命令 |
| `run_powershell_tool` | 60秒 | PowerShell命令 |
| `backup_project_tool` | 60秒 | 备份可能较大项目 |
| `web_search_tool` | 30秒 | 网络搜索 |
| `compress_context_tool` | 30秒 | 上下文压缩 |
| `trigger_self_restart_tool` | 30秒 | 重启操作 |
| `read_webpage_tool` | 20秒 | 网页读取 |
| 其他 | 30秒 | 默认超时 |

### 超时处理

超时时返回：
```
[超时] 工具执行超时 (30秒)
工具: web_search_tool
参数: {...}
建议: 尝试简化操作或使用更具体的参数
```

### 设计目的

- 防止单个工具阻塞整个 Agent
- 模型收到超时错误后可选择重试或跳过
- 避免 Agent 在某个工具上无限等待

---

## 【文件操作工具】(集成在 CMD 工具中)

### read_local_file
读取本地文件内容。**修改前必须先读取！**

使用 Python 直接读取，支持自动编码检测和行数限制。

```
参数:
  - file_path: 文件路径 (相对或绝对)
  - encoding: 编码，默认自动检测
  - max_lines: 最大行数限制
  - show_line_numbers: 是否显示行号，默认 True

返回: 带行号的文件内容

返回格式:
[文件] /path/to/file.py
[编码] utf-8 | [行数] 150 | [大小] 4.2 KB

--- Content ---
第     1 行 | #!/usr/bin/env python3
第     2 行 | """Module docstring"""
...
--- End ---
```

### list_directory
列出目录内容。

```
参数:
  - path: 目录路径，默认为 "."
  - show_hidden: 是否显示隐藏文件
  - recursive: 是否递归列出子目录

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

---

## 【CMD 系统工具】

提供在 Windows 环境下执行 CMD/PowerShell 命令的功能。

### 1. run_cmd - 执行 CMD 命令

```
run_cmd(command, timeout=60, shell=True, cwd=None, check_safety=True)
```

**参数说明：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| command | str | 必填 | 要执行的命令（如 "dir", "python script.py"） |
| timeout | int | 60 | 超时时间（秒） |
| shell | bool | True | 是否使用 shell 执行 |
| cwd | str | None | 工作目录 |
| check_safety | bool | True | 是否执行安全检查（默认启用黑名单拦截） |

**返回值：**
```
[CMD] 返回码: 0

[标准输出]
命令的实际输出内容...
```

**使用示例：**
```python
# 查看当前目录
run_cmd("dir")

# 查看网络配置
run_cmd("ipconfig /all")

# 运行 Python 脚本
run_cmd("python my_script.py")

# 在指定目录执行
run_cmd("git status", cwd="C:\\Projects\\MyRepo")

# 查看 Python 版本
run_cmd("python --version")
```

### 2. run_powershell - 执行 PowerShell 命令

```
run_powershell(command, timeout=60, cwd=None)
```

**使用示例：**
```python
# 列出所有进程
run_powershell("Get-Process")

# 获取网络配置
run_powershell("Get-NetIPAddress -AddressFamily IPv4")

# 列出所有服务
run_powershell("Get-Service")
```

### 3. run_batch - 批量执行命令

```
run_batch(commands, timeout=60, cwd=None)
```

**参数说明：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| commands | str | 必填 | JSON 格式的命令列表，如 '["cd src", "dir"]' |
| timeout | int | 60 | 总超时时间（秒） |
| cwd | str | None | 工作目录 |

**使用示例：**
```python
# 进入目录后执行
run_batch('["cd C:\\\\", "dir *.exe"]')

# 安装依赖并运行测试
run_batch('["pip install requests", "python test.py"]')
```

### 安全说明

**危险命令黑名单：** 系统会自动拦截以下命令：
- `format` - 格式化磁盘
- `del /f /s /q` - 强制删除
- `rmdir /s /q` - 删除目录
- `shutdown` - 关机命令
- `sysprep` - 系统准备工具
- `cipher /w:` - 数据擦除

如果需要绕过安全检查（危险操作），可将 `check_safety=False`，但请谨慎使用。

---

## 【错误码说明】

| 返回码 | 含义 |
|--------|------|
| 0 | 命令执行成功 |
| 非0数字 | 命令执行失败（具体含义取决于命令本身） |
| -1 | 命令执行超时 |
| -2 | 安全检查拒绝（危险命令） |
| -3 | 命令不存在 |
| -4 | 权限不足 |
| -99 | 其他未知错误 |

---

**注意：** CMD 工具仅在 Windows 环境下可用。

---

## 【增强版 Token 管理机制】

本 Agent 采用多层 Token 控制机制，防止上下文爆炸。

### 核心优化

1. **预压缩机制** - 在 Token 达到 50% 时就提前压缩，避免危机
2. **多级压缩** - 根据紧急程度选择压缩强度（警告/触发/紧急）
3. **消息优先级** - 区分不同类型消息的重要性（CRITICAL > HIGH > MEDIUM > LOW > TRIVIAL）
4. **智能截断** - 根据消息类型采用不同策略（保留开头和结尾）
5. **动态阈值** - 三级阈值：警告(50%)、触发(60%)、紧急(80%)
6. **预算感知** - 实时追踪 Token 消耗，预留 10% buffer

### 压缩阈值

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `max_token_limit` | 8000 | 总 Token 预算 |
| `keep_recent_steps` | 3 | 保留最近交互对数 |
| `summary_max_chars` | 200 | 摘要最大字符数 |
| 警告阈值 | 50% | 触发预压缩 |
| 触发阈值 | 60% | 触发正常压缩 |
| 紧急阈值 | 80% | 触发紧急压缩（仅保留1对） |

### 压缩级别

| 级别 | 条件 | 保留对数 | 摘要长度 |
|------|------|---------|---------|
| warning | 50-60% | 3对 | 200字 |
| active | 60-80% | 2对 | 150字 |
| emergency | >80% | 1对 | 100字 |

### 消息优先级

| 优先级 | 消息类型 | 截断策略 |
|--------|---------|---------|
| CRITICAL | 系统提示词 | 不截断 |
| HIGH | 错误信息、编辑结果 | 保留首尾 |
| MEDIUM | AI思考、用户输入 | 保留开头 |
| LOW | 早期历史 | 压缩 |
| TRIVIAL | 重复搜索结果 | 可丢弃 |

### 压缩统计

Agent 内部维护压缩统计：
- 总压缩次数 / 紧急压缩次数 / 预压缩次数
- 累计节省 Token 数
- 峰值 Token 使用
- 压缩类型分布

---

**Token 估算说明：** 使用中英文混合估算，中文约 1.5 字符/token，英文约 4 字符/token。
