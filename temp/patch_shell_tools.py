#!/usr/bin/env python3
"""Patch shell_tools.py to integrate new security module"""

path = r"C:\Users\17533\Desktop\self-evo-baby\tools\shell_tools.py"

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function and modify it
new_lines = []
in_function = False
function_found = False

for i, line in enumerate(lines):
    if 'def _is_command_dangerous(command: str)' in line:
        function_found = True
        # Replace docstring
        new_lines.append('def _is_command_dangerous(command: str) -> tuple[bool, str]:\n')
        new_lines.append('    """Check if command is dangerous (blacklist + whitelist)"""\n')
        # Skip old docstring line
        continue
    elif function_found and 'return False, ""' in line and not any(x in ''.join(new_lines[-5:]) for x in ['validate_shell_command', 'white']):
        # Add whitelist check before final return
        indent = '    '
        new_lines.append(f'{indent}# Whitelist validation (new security module)\n')
        new_lines.append(f'{indent}try:\n')
        new_lines.append(f'{indent}    from core.security import validate_shell_command\n')
        new_lines.append(f'{indent}    is_safe, error_msg = validate_shell_command(command, "powershell")\n')
        new_lines.append(f'{indent}    if not is_safe:\n')
        new_lines.append(f'{indent}        return True, f"[Whitelist Block] {{error_msg}}"\n')
        new_lines.append(f'{indent}except Exception as e:\n')
        new_lines.append(f'{indent}    logger.warning(f"Security module load failed: {{e}}")\n')
        new_lines.append(line)  # Original return statement
        function_found = False  # Reset
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"[OK] Patched shell_tools.py")
print(f"    Added whitelist validation to _is_command_dangerous()")
