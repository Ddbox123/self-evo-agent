# USER.md - 用户环境

## 当前运行环境

### 系统信息

- **操作系统**: Windows (PowerShell)
- **运行环境**: 受限的本地计算机
- **项目根目录**: `C:\Users\17533\Desktop\self-evo-agent`

### 环境约束

1. 所有网络搜索和文件操作都在当前项目根目录的生命周期内进行
2. 不允许访问系统级敏感路径（如 `C:\Windows`、`C:\Program Files` 等）
3. 所有修改都应该在项目目录内完成

### 项目结构

```
self-evo-agent/
├── agent.py              # 主 Agent 程序
├── restarter.py          # 重启守护进程（禁止修改）
├── config.py             # 配置文件
├── config.toml           # 配置参数
├── tools/                # 工具模块目录
│   ├── cmd_tools.py      # 文件/命令工具
│   ├── web_tools.py      # 网络工具
│   ├── memory_tools.py   # 记忆工具
│   └── evolution_tracker.py  # 进化追踪
├── prompts/              # 提示词资源库
├── core/                 # 核心模块
├── workspace/            # 工作空间
│   └── memory/           # 记忆存储
└── docs/                 # 文档
    └── tools_manual.md   # 工具手册
```

### 世代档案

- 记忆存储在 `workspace/memory/archives/`
- 档案格式：`gen_N_history.json`
- 使用 `read_generation_archive_tool` 按需读取历史档案
