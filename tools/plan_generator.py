#!/usr/bin/env python3
"""
进化规划系统 - 多步推理与副作用分析

在执行任何重大代码修改之前，必须先生成 plan.md 文件。
这确保 Agent 在动手前进行完整的深度模拟。

使用方式：
    python -m tools.plan_generator --task "添加新功能" --files "agent.py,tools/test.py"
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent


class EvolutionPlan:
    """进化规划生成器"""

    def __init__(self, task: str, files_to_modify: List[str]):
        self.task = task
        self.files = files_to_modify
        self.created_at = datetime.now()
        self.plan_id = self._generate_id()

    def _generate_id(self) -> str:
        """生成唯一计划 ID"""
        content = f"{self.task}:{self.created_at.isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def analyze_dependencies(self) -> List[Dict]:
        """分析文件依赖关系"""
        deps = []
        for f in self.files:
            filepath = PROJECT_ROOT / f
            if not filepath.exists():
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as fp:
                    content = fp.read()

                # 简单的 import 分析
                imports = []
                for line in content.split("\n"):
                    if line.strip().startswith("import ") or line.strip().startswith("from "):
                        imports.append(line.strip()[:60])

                deps.append({
                    "file": f,
                    "imports": imports[:10],  # 只取前 10 个
                    "lines": len(content.split("\n")),
                })
            except Exception:
                pass

        return deps

    def generate_plan(self) -> str:
        """生成完整的进化计划"""

        deps = self.analyze_dependencies()

        plan = f"""# 进化计划 #{self.plan_id}

**生成时间**: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**任务**: {self.task}
**计划 ID**: {self.plan_id}

---

## 1. 任务目标

{self.task}

---

## 2. 目标文件分析

| 文件 | 行数 | 依赖模块 |
|------|------|----------|
"""

        for dep in deps:
            imports = ", ".join(dep["imports"][:3]) if dep["imports"] else "无"
            plan += f"| `{dep['file']}` | {dep['lines']} | {imports} |\n"

        plan += f"""

---

## 3. 修改顺序

"""

        for i, f in enumerate(self.files, 1):
            plan += f"{i}. 修改 `{f}`\n"

        plan += """

---

## 4. 潜在副作用分析

"""

        for f in self.files:
            risks = []

            # 静态分析潜在风险
            if "agent.py" in f:
                risks.append("影响主循环执行")
                risks.append("可能导致启动失败")
            if "memory" in f.lower():
                risks.append("影响记忆持久化")
                risks.append("可能导致世代信息丢失")
            if "tools" in f.lower():
                risks.append("影响工具执行")
                risks.append("可能导致功能不可用")

            plan += f"### `{f}`\n"
            if risks:
                for r in risks:
                    plan += f"- ⚠️ {r}\n"
            else:
                plan += "- ✅ 低风险：独立模块\n"
            plan += "\n"

        plan += """---

## 5. 回滚方案

| 阶段 | 操作 | 回滚方法 |
|------|------|----------|
| 修改前 | 自动备份 | `git checkout <file>` |
| 修改中 | 保留旧版本 | 旧版本在 backup/ 目录 |
| 修改后 | 测试验证 | `pytest tests/` |
| 验证失败 | 恢复 | `git restore <file>` |

---

## 6. 测试策略

1. **语法检查**: 每个文件修改后运行 `python -m py_compile <file>`
2. **单元测试**: `pytest tests/test_*.py`
3. **集成测试**: `python tests/run_tests.py`
4. **功能验证**: 手动或自动触发关键路径

---

## 7. 执行检查清单

- [ ] 已阅读目标文件当前代码
- [ ] 已分析依赖关系
- [ ] 已识别潜在风险
- [ ] 已确认回滚方案
- [ ] 已准备测试用例
- [ ] **已通过所有单元测试**
- [ ] **已验证语法正确**

---

## 8. 批准与执行

**执行条件**: 所有检查清单项必须为 `[x]`

**执行命令**:
```bash
# 1. 运行测试
pytest tests/ -v

# 2. 语法检查
python -m py_compile agent.py

# 3. 触发重启
trigger_self_restart(reason="已完成进化计划 #{}")
```

---

*此文件由 Self-Evolving Agent 自动生成*
""".format(self.plan_id)

        return plan

    def save_plan(self, path: Optional[str] = None) -> str:
        """保存计划到文件"""
        if path is None:
            path = PROJECT_ROOT / "workspace" / f"plan_{self.plan_id}.md"
        else:
            path = PROJECT_ROOT / path

        os.makedirs(os.path.dirname(path), exist_ok=True)

        plan_content = self.generate_plan()

        with open(path, "w", encoding="utf-8") as f:
            f.write(plan_content)

        return str(path)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "task": self.task,
            "files": self.files,
            "created_at": self.created_at.isoformat(),
            "status": "pending",
        }


def create_plan(task: str, files: List[str]) -> Tuple[str, Dict]:
    """
    创建进化计划的便捷函数。

    Args:
        task: 任务描述
        files: 要修改的文件列表

    Returns:
        (计划文件路径, 计划摘要)
    """
    plan = EvolutionPlan(task, files)
    filepath = plan.save_plan()

    # 同时保存到根目录的 plan.md
    root_plan_path = PROJECT_ROOT / "plan.md"
    with open(root_plan_path, "w", encoding="utf-8") as f:
        f.write(plan.generate_plan())

    return str(root_plan_path), plan.to_dict()


def check_plan_approved(plan_path: str = None) -> bool:
    """
    检查计划是否已批准。

    Args:
        plan_path: 计划文件路径，默认检查根目录 plan.md

    Returns:
        True 如果所有检查清单项都已勾选
    """
    if plan_path is None:
        plan_path = PROJECT_ROOT / "plan.md"

    if not os.path.exists(plan_path):
        return False

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否有未完成的检查清单
        unchecked = "- [ ]" in content
        return not unchecked
    except Exception:
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="进化计划生成器")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--files", required=True, help="要修改的文件，逗号分隔")
    args = parser.parse_args()

    files = [f.strip() for f in args.files.split(",")]
    plan_path, summary = create_plan(args.task, files)

    print(f"Plan created: {plan_path}")
    print(f"Plan ID: {summary['plan_id']}")
