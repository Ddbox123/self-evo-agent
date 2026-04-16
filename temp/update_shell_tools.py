#!/usr/bin/env python3
"""更新 shell_tools.py 集成新的安全模块"""

path = r"C:\Users\17533\Desktop\self-evo-baby\tools\shell_tools.py"

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_func = '''def _is_command_dangerous(command: str) -> tuple[bool, str]:
    """检查命令是否危险"""
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True, f"危险命令拦截：{pattern}"
    return False, ""'''

new_func = '''def _is_command_dangerous(command: str) -> tuple[bool, str]:
    """检查命令是否危险（黑名单 + 白名单双层验证）"""
    cmd_lower = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.lower() in cmd_lower:
            return True, f"危险命令拦截：{pattern}"
    
    # 第二层：使用新的白名单安全模块验证
    try:
        from core.security import validate_shell_command
        is_safe, error_msg = validate_shell_command(command, "powershell")
        if not is_safe:
            return True, f"[白名单拦截] {error_msg}"
    except Exception as e:
        logger.warning(f"安全模块加载失败，使用黑名单验证：{e}")
    
    return False, ""'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] 修改成功：shell_tools.py 已集成白名单安全验证")
else:
    print("[WARN] 未找到目标函数，可能已修改")
