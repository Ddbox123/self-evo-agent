"""
配置模块 (config/)

提供现代化的配置管理，基于 Pydantic v2 实现。
支持从 TOML 文件、环境变量加载配置，提供严格的类型校验。

模块结构：
- models: Pydantic 数据模型定义
- providers: LLM 模型预设注册表
- settings: 配置加载与单例管理

快速开始：
    from config import get_settings, use_model

    # 获取配置
    settings = get_settings()
    print(settings.config.llm.model_name)

    # 切换模型
    use_model("gpt-4")

    # 从 providers 获取信息
    from config import list_models, show_model_info
    print(show_model_info("gpt-4"))
"""

from .models import (
    # 数据模型
    LLMConfig,
    AgentConfig,
    ContextCompressionConfig,
    ToolConfig,
    LogConfig,
    NetworkConfig,
    AppConfig,
)

from .providers import (
    # 模型预设
    ModelPreset,
    MODEL_PRESETS,
    PROVIDER_METADATA,
    MODEL_ALIASES,
    # 工具函数
    list_models,
    list_models_by_provider,
    get_model_preset,
    get_provider_models,
    show_model_info,
    resolve_model_alias,
)

from .settings import (
    # 核心
    AppConfig,
    ConfigLoader,
    Settings,
    # 单例
    get_settings,
    get_config,
    # 便捷函数
    use_model,
    switch_model,
)

# 导入根目录 config.py 中的自定义 Config 类（绕过循环导入）
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
_root_config = project_root / "config.py"

if _root_config.exists():
    # 读取并执行根目录的 config.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("root_config", _root_config)
    if spec and spec.loader:
        root_module = importlib.util.module_from_spec(spec)
        sys.modules['root_config_module'] = root_module
        spec.loader.exec_module(root_module)
        RootConfig = getattr(root_module, 'Config', None)
        if RootConfig is not None:
            Config = RootConfig
        else:
            Config = AppConfig
    else:
        Config = AppConfig
else:
    Config = AppConfig

__all__ = [
    # 数据模型
    "AppConfig",
    "LLMConfig",
    "AgentConfig",
    "ContextCompressionConfig",
    "ToolConfig",
    "LogConfig",
    "NetworkConfig",
    # 别名（向后兼容）
    "Config",
    # 提供商
    "ModelPreset",
    "MODEL_PRESETS",
    "PROVIDER_METADATA",
    "MODEL_ALIASES",
    # 工具函数
    "list_models",
    "list_models_by_provider",
    "get_model_preset",
    "get_provider_models",
    "show_model_info",
    "resolve_model_alias",
    # 核心类
    "ConfigLoader",
    "Settings",
    # 单例和便捷函数
    "get_settings",
    "get_config",
    "use_model",
    "switch_model",
]
