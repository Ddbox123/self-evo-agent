"""
工具模块初始化文件

本包导出所有可用的 Agent 工具，供主程序导入使用。

工具分类：
- 网络工具 (web_tools): 网页搜索、内容读取
- 文件工具 (file_tools): 目录列表、文件读取
- 代码工具 (code_tools): 文件编辑、代码创建
- 安全工具 (safety_tools): 语法检查、项目备份
- 重生工具 (rebirth_tools): 自我重启触发

使用示例：
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
"""

# 网络工具
from tools.web_tools import (
    web_search,
    read_webpage,
    extract_links,
)

# 文件工具
from tools.file_tools import (
    list_directory,
    read_local_file,
)

# 代码工具
from tools.code_tools import (
    edit_local_file,
    create_new_file,
)

# 安全工具
from tools.safety_tools import (
    check_syntax,
    backup_project,
)

# 重生工具
from tools.rebirth_tools import (
    trigger_self_restart,
)

# 工具元数据
__all__ = [
    # 网络工具
    'web_search',
    'read_webpage',
    'extract_links',
    
    # 文件工具
    'list_directory',
    'read_local_file',
    
    # 代码工具
    'edit_local_file',
    'create_new_file',
    
    # 安全工具
    'check_syntax',
    'backup_project',
    
    # 重生工具
    'trigger_self_restart',
]


# 工具描述映射（用于动态文档生成）
TOOL_DESCRIPTIONS = {
    'web_search': {
        'name': 'web_search',
        'category': '网络工具',
        'description': '通过搜索引擎查询相关信息',
        'params': 'query: str, max_results: int = 5',
        'returns': 'str',
    },
    'read_webpage': {
        'name': 'read_webpage',
        'category': '网络工具',
        'description': '读取指定网页的完整内容',
        'params': 'url: str, max_length: Optional[int] = None',
        'returns': 'str',
    },
    'list_directory': {
        'name': 'list_directory',
        'category': '文件工具',
        'description': '列出目录内容和文件信息',
        'params': 'path: str, show_hidden: bool = False, recursive: bool = False',
        'returns': 'str',
    },
    'read_local_file': {
        'name': 'read_local_file',
        'category': '文件工具',
        'description': '读取本地文件的内容',
        'params': 'file_path: str, encoding: Optional[str] = None, max_lines: Optional[int] = None',
        'returns': 'str',
    },
    'edit_local_file': {
        'name': 'edit_local_file',
        'category': '代码工具',
        'description': '编辑现有文件，替换指定内容',
        'params': 'file_path: str, search_string: str, replace_string: str, create_backup_first: bool = True',
        'returns': 'str',
    },
    'create_new_file': {
        'name': 'create_new_file',
        'category': '代码工具',
        'description': '创建新文件或覆盖现有文件',
        'params': 'file_path: str, content: str = "", overwrite: bool = False',
        'returns': 'str',
    },
    'check_syntax': {
        'name': 'check_syntax',
        'category': '安全工具',
        'description': '检查代码文件的语法正确性',
        'params': 'file_path: str, language: Optional[str] = None',
        'returns': 'str',
    },
    'backup_project': {
        'name': 'backup_project',
        'category': '安全工具',
        'description': '创建项目完整备份',
        'params': 'version_note: str = ""',
        'returns': 'str',
    },
    'trigger_self_restart': {
        'name': 'trigger_self_restart',
        'category': '重生工具',
        'description': '触发 Agent 自我重启',
        'params': 'reason: str = ""',
        'returns': 'str',
    },
}


def get_tool_info(tool_name: str) -> dict:
    """
    获取指定工具的详细信息。
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具信息字典，如果工具不存在返回空字典
    """
    return TOOL_DESCRIPTIONS.get(tool_name, {})


def list_tools_by_category(category: str) -> list:
    """
    按类别列出所有工具。
    
    Args:
        category: 工具类别
        
    Returns:
        该类别下的工具列表
    """
    return [
        info for info in TOOL_DESCRIPTIONS.values()
        if info['category'] == category
    ]


def get_all_categories() -> list:
    """
    获取所有工具类别。
    
    Returns:
        类别列表
    """
    return list(set(info['category'] for info in TOOL_DESCRIPTIONS.values()))
