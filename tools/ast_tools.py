#!/usr/bin/env python3
"""
AST 精准提取工具 - 基于 Python 语法树的一击必中

使用 Python 的 ast 模块直接提取类、函数、方法等代码实体，
无需逐行读取文件，大幅减少 LLM 交互轮数。

特性：
1. 按名称精准提取类和函数
2. 自动计算行号范围
3. 支持嵌套实体（类中的方法）
4. 处理装饰器和文档字符串
"""

import ast
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


class ASTEntityExtractor(ast.NodeVisitor):
    """AST 节点遍历器，用于提取代码实体"""

    def __init__(self):
        self.entities: Dict[str, List[Dict[str, Any]]] = {
            'class': [],
            'function': [],
            'async_function': [],
        }
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        """提取类定义"""
        self.current_class = node.name
        class_info = self._extract_entity_info(node, 'class')
        class_info['methods'] = self._extract_class_methods(node)
        self.entities['class'].append(class_info)

        # 临时保存当前类，继续遍历其中的方法
        old_class = self.current_class
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """提取函数定义"""
        self.entities['function'].append(self._extract_entity_info(node, 'function'))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """提取异步函数定义"""
        self.entities['async_function'].append(self._extract_entity_info(node, 'async_function'))

    def _extract_entity_info(self, node: ast.AST, entity_type: str) -> Dict[str, Any]:
        """提取实体的基本信息"""
        info = {
            'type': entity_type,
            'name': node.name,
            'lineno': node.lineno,
            'end_lineno': node.end_lineno,
            'col_offset': node.col_offset,
            'end_col_offset': node.end_col_offset if hasattr(node, 'end_col_offset') else None,
            'decorators': [self._get_decorator_name(d) for d in getattr(node, 'decorator_list', [])],
            'docstring': ast.get_docstring(node),
        }

        # 如果在类中，添加类名
        if self.current_class:
            info['class_name'] = self.current_class

        return info

    def _extract_class_methods(self, node: ast.ClassDef) -> List[Dict[str, Any]]:
        """提取类中的所有方法"""
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_entity_info(item, 'method')
                method_info['is_static'] = any(
                    self._get_decorator_name(d) == 'staticmethod'
                    for d in getattr(item, 'decorator_list', [])
                )
                method_info['is_classmethod'] = any(
                    self._get_decorator_name(d) == 'classmethod'
                    for d in getattr(item, 'decorator_list', [])
                )
                methods.append(method_info)
        return methods

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """获取装饰器名称"""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return 'unknown'


def parse_file_ast(file_path: str) -> Optional[ast.Module]:
    """解析 Python 文件为 AST"""
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        return ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return None


def get_file_entities(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    获取文件中的所有实体（类和函数）

    Args:
        file_path: Python 文件路径

    Returns:
        包含所有实体的字典
    """
    tree = parse_file_ast(file_path)
    if tree is None:
        return {}

    extractor = ASTEntityExtractor()
    extractor.visit(tree)
    return extractor.entities


def get_code_entity(file_path: str, entity_name: str, include_imports: bool = False) -> str:
    """
    根据名称提取代码实体

    一击必中：直接提取类或函数的完整源代码。

    Args:
        file_path: Python 文件路径
        entity_name: 要提取的实体名称（类名或函数名）
        include_imports: 是否包含文件的 import 语句

    Returns:
        实体代码文本，包含行号范围
    """
    path = Path(file_path)
    if not path.exists():
        return f"[AST] 错误: 文件不存在 - {file_path}"

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return f"[AST] 错误: 无法读取文件（编码问题）- {file_path}"

    # 解析 AST
    tree = parse_file_ast(file_path)
    if tree is None:
        return f"[AST] 错误: 无法解析 AST - {file_path}"

    # 先在实体列表中查找
    extractor = ASTEntityExtractor()
    extractor.visit(tree)

    # 查找匹配的实体
    target_entity = None

    for entity_list in [extractor.entities['class'], extractor.entities['function'], extractor.entities['async_function']]:
        for entity in entity_list:
            if entity['name'] == entity_name:
                target_entity = entity
                break
        if target_entity:
            break

    # 如果没找到，可能需要通过文本搜索
    if target_entity is None:
        return _search_entity_by_text(lines, entity_name, file_path)

    # 提取实体代码
    start_line = target_entity['lineno']
    end_line = target_entity['end_lineno']

    # 获取代码
    entity_lines = lines[start_line - 1:end_line]
    code = ''.join(entity_lines)

    # 构建输出
    result = [
        f"[AST] 实体: {target_entity['name']}",
        f"[AST] 类型: {target_entity['type']}" + (f" (方法)" if 'class_name' in target_entity else ""),
        f"[AST] 位置: 第 {start_line} - {end_line} 行",
    ]

    if target_entity.get('decorators'):
        result.append(f"[AST] 装饰器: {', '.join(target_entity['decorators'])}")

    if target_entity.get('docstring'):
        result.append(f"[AST] 文档:\n\"\"\"{target_entity['docstring']}\"\"\"")

    result.append(f"\n[AST] 代码:\n```python")
    result.append(code.rstrip())
    result.append("```")

    return '\n'.join(result)


def _search_entity_by_text(lines: List[str], entity_name: str, file_path: str) -> str:
    """通过文本搜索实体（当 AST 解析失败时的备选方案）"""

    patterns = [
        rf'^class\s+{entity_name}\s*[:(]',
        rf'^def\s+{entity_name}\s*\(',
        rf'^async\s+def\s+{entity_name}\s*\(',
    ]

    import re
    start_line = None
    end_line = None
    indent_level = None

    for i, line in enumerate(lines):
        for pattern in patterns:
            if re.match(pattern, line):
                start_line = i
                indent_level = len(line) - len(line.lstrip())
                break
        if start_line is not None:
            break

    if start_line is None:
        return f"[AST] 错误: 未找到实体 '{entity_name}' - {file_path}"

    # 找到结束行（同级别缩进或更少缩进）
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        if line.strip():  # 非空行
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level:
                end_line = i
                break
    else:
        end_line = len(lines)

    code = ''.join(lines[start_line:end_line])

    return (
        f"[AST] 实体: {entity_name}\n"
        f"[AST] 位置: 第 {start_line + 1} - {end_line} 行\n"
        f"\n[AST] 代码:\n```python\n{code.rstrip()}\n```"
    )


def list_file_entities(file_path: str, entity_type: str = None) -> str:
    """
    列出文件中的所有实体

    Args:
        file_path: Python 文件路径
        entity_type: 过滤类型 ('class', 'function', None 表示全部)

    Returns:
        实体列表
    """
    entities = get_file_entities(file_path)

    if not entities:
        return f"[AST] 错误: 无法解析或文件为空 - {file_path}"

    result = [
        f"[AST] 文件: {file_path}",
        f"[AST] 概览:\n",
    ]

    all_entities = []
    if entity_type is None or entity_type == 'class':
        for cls in entities['class']:
            all_entities.append(('class', cls))
    if entity_type is None or entity_type == 'function':
        for func in entities['function'] + entities['async_function']:
            all_entities.append(('function', func))

    for etype, entity in all_entities:
        location = f"第 {entity['lineno']} 行"
        if 'class_name' in entity:
            location = f"{entity['class_name']}.{entity['name']} ({location})"

        doc = ""
        if entity.get('docstring'):
            doc = f" - {entity['docstring'][:50]}..."

        result.append(f"  📦 {entity['name']} ({etype}) {location}{doc}")

        # 如果是类，显示方法
        if etype == 'class' and entity.get('methods'):
            for method in entity['methods']:
                method_type = 'classmethod' if method.get('is_classmethod') else 'staticmethod' if method.get('is_static') else 'method'
                result.append(f"      └─ {method['name']} ({method_type}) 第 {method['lineno']} 行")

    return '\n'.join(result)


def extract_method_from_class(file_path: str, class_name: str, method_name: str) -> str:
    """
    从类中提取特定方法

    Args:
        file_path: Python 文件路径
        class_name: 类名
        method_name: 方法名

    Returns:
        方法代码
    """
    entity_info = f"{class_name}.{method_name}"
    return get_code_entity(file_path, method_name)


# 导出工具函数
def create_ast_tools():
    """创建 AST 工具集"""
    return {
        'get_code_entity': get_code_entity,
        'list_file_entities': list_file_entities,
        'get_file_entities': get_file_entities,
    }
