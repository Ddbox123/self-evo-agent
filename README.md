# Self-Evolving Agent

一个能够通过网络搜索获取新知识、读取和修改自己源代码、进行语法自检、并通过独立守护进程实现自我重启的 AI Agent 系统。

## 项目架构

```
self-evo-agent/
├── agent.py              # Agent 主入口
├── restarter.py          # 独立守护进程脚本
├── requirements.txt      # Python 依赖
├── README.md             # 项目文档
├── tools/                # 工具模块
│   ├── __init__.py       # 模块初始化
│   ├── web_tools.py      # 网络搜索和网页读取
│   ├── file_tools.py     # 文件和目录操作
│   ├── code_tools.py     # 代码编辑工具
│   ├── safety_tools.py   # 语法检查和备份
│   └── rebirth_tools.py  # 自我重启触发
└── backups/              # 项目备份目录
```

## 核心能力

### 1. Agent 循环框架
采用"感知 -> 思考 -> 行动"的架构模式运行：
- **感知**：收集当前状态、环境信息
- **思考**：分析状态，决定下一步行动
- **行动**：执行工具调用，完成任务

### 2. 网络工具
- `web_search(query)` - 搜索引擎查询
- `read_webpage(url)` - 读取网页内容

### 3. 文件工具
- `list_directory(path)` - 列出目录内容
- `read_local_file(file_path)` - 读取文件

### 4. 代码工具
- `edit_local_file(file, search, replace)` - 编辑代码
- `create_new_file(file, content)` - 创建新文件

### 5. 安全工具
- `check_syntax(file)` - 语法检查
- `backup_project(note)` - 项目备份

### 6. 重生工具
- `trigger_self_restart(reason)` - 触发自我重启

## 进程接力模式

Agent 运行主逻辑，需要重启时：
1. 通过脱离父进程的方式唤起 `restarter.py`
2. Agent 执行 `sys.exit(0)` 自我了结
3. `restarter.py` 轮询等待原进程结束
4. 原进程死亡后，拉起新的 Agent 进程

```
┌─────────────────────────────────────────────────────┐
│                    Agent 进程                        │
│                                                     │
│   Agent Loop                                        │
│   ├── perceive()                                    │
│   ├── think()                                       │
│   └── act() ───> trigger_self_restart()           │
│                                    │                │
│                                    ▼                │
│                          spawn restarter.py         │
│                                    │                │
│                                    ▼                │
│                          sys.exit(0)  ──── X       │
└─────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────┐
│                  Restarter 进程                       │
│                                                     │
│   wait_for_process_death(pid)                       │
│   └── [等待原进程结束]                               │
│                                                     │
│   spawn_new_process(agent.py)                       │
│   └── [拉起新 Agent]                                │
└─────────────────────────────────────────────────────┘
```

## 安装

```bash
# 克隆项目
cd self-evo-agent

# 安装依赖
pip install -r requirements.txt

# 运行 Agent
python agent.py
```

## 使用示例

```python
from tools import (
    web_search,
    read_webpage,
    list_directory,
    read_local_file,
    edit_local_file,
    create_new_file,
    check_syntax,
    backup_project,
    trigger_self_restart,
)

# 搜索网络
result = web_search("Python 异步编程最佳实践")

# 读取文件
result = read_local_file("agent.py", max_lines=50)

# 编辑代码
result = edit_local_file(
    "agent.py",
    "def main():",
    "async def main():"
)

# 语法检查
result = check_syntax("tools/web_tools.py")

# 备份项目
result = backup_project("添加新功能 v1.0")

# 触发重启
result = trigger_self_restart("代码已更新，需要重新加载")
```

## 注意事项

- 所有工具函数都有详细的 docstring，可供 LLM 理解工具用途
- 使用类型提示（Type Hints）提高代码可读性
- 支持 Windows 和 Unix 系统
- 敏感文件访问受限

## License

MIT
