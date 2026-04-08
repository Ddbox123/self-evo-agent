#!/usr/bin/env python3
"""
进程重启守护进程 - restarter.py

此文件作为兼容层存在，实际功能已迁移到 core/restarter.py

使用方式：
    python restarter.py --pid 12345 --script ./agent.py
    或
    python -m core.restarter --pid 12345 --script ./agent.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 转发到 core.restarter
from core.restarter import (
    main,
    run_restarter,
    spawn_new_process,
    wait_for_process_death,
    is_process_alive,
    parse_arguments,
)

if __name__ == "__main__":
    sys.exit(main())
