"""
配置文件 (向后兼容层)

此文件提供与旧版 config.py 的向后兼容接口。
新代码建议直接使用 config/ 模块。

迁移指南:
    # 旧写法 (仍可用)
    from config import Config, use_model
    config = Config()
    config = use_model("gpt-4")

    # 新写法 (推荐)
    from config import get_settings, get_config
    settings = get_settings()
    config = get_config()

详细迁移请参考 config/__init__.py
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# 重新导出新模块的所有内容
from config.models import (
    # 数据模型
    LLMConfig,
    AgentConfig,
    ContextCompressionConfig,
    ToolConfig,
    LogConfig,
    NetworkConfig,
    AppConfig,
)

from config.providers import (
    # 模型预设
    ModelPreset,
    MODEL_PRESETS,
    MODEL_ALIASES,
    PROVIDER_METADATA,
    # 工具函数
    list_models,
    list_models_by_provider,
    get_model_preset,
    get_provider_models,
    show_model_info,
    resolve_model_alias,
)

from config.settings import (
    # 核心类
    ConfigLoader,
    Settings,
    # 单例函数
    get_settings,
    get_config as _get_config_func,
    # 便捷函数
    use_model,
    switch_model,
)


# ============================================================================
# 向后兼容：保持 MODEL_REGISTRY 名称（原代码中的名称）
# ============================================================================

MODEL_REGISTRY = MODEL_PRESETS


# ============================================================================
# 向后兼容：Config 类
# ============================================================================

class Config(AppConfig):
    """
    统一配置管理类（向后兼容）

    此类继承自新的 AppConfig，提供与旧版 Config 完全兼容的接口。
    建议新代码直接使用 config 模块中的 AppConfig 或 Settings。

    Example:
        # 方式1: 使用预定义模型
        config = use_model("gpt-4")
        config = use_model("claude-3.5")
        config = use_model("deepseek")

        # 方式2: 从 config.toml 读取
        config = Config()

        # 方式3: 从字典创建
        config = Config.from_dict({'llm.model_name': 'gpt-4'})
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        env_prefix: str = "AGENT_",
        **kwargs
    ) -> None:
        """
        初始化配置

        Args:
            config_path: 配置文件路径
            env_prefix: 环境变量前缀
            **kwargs: 其他配置参数
        """
        # 使用 Settings 加载配置
        settings = Settings(config_path)
        loaded_config = settings.config

        # 应用 kwargs（直接修改嵌套模型）
        for key, value in kwargs.items():
            if value is None:
                continue
            if '.' in key:
                section, setting = key.split('.', 1)
                if hasattr(loaded_config, section):
                    sub_config = getattr(loaded_config, section)
                    if hasattr(sub_config, setting):
                        setattr(sub_config, setting, value)

        # 存储配置路径和环境变量前缀（使用 object.__setattr__ 避免 Pydantic 拦截）
        object.__setattr__(self, '_config_path', config_path)
        object.__setattr__(self, '_env_prefix', env_prefix)

        # 调用父类初始化，设置所有字段
        super().__init__(
            llm=loaded_config.llm,
            agent=loaded_config.agent,
            context_compression=loaded_config.context_compression,
            tools=loaded_config.tools,
            log=loaded_config.log,
            network=loaded_config.network,
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """
        从字典创建配置

        Args:
            config_dict: 配置字典，支持点号分隔的键名

        Returns:
            Config 实例
        """
        config = cls()
        for key, value in config_dict.items():
            keys = key.split('.')
            if len(keys) == 2:
                section, setting = keys
                if hasattr(config, section):
                    section_obj = getattr(config, section)
                    if hasattr(section_obj, setting):
                        setattr(section_obj, setting, value)
        return config

    def get_api_key(self) -> Optional[str]:
        """
        获取 API Key（优先从配置读取，其次环境变量）

        Returns:
            API Key，未设置返回 None
        """
        # 1. 优先从配置读取
        if self.llm.api_key:
            return self.llm.api_key

        # 2. 从环境变量读取
        provider = self.llm.provider
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "aliyun": "DASHSCOPE_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "google": "GOOGLE_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
            "groq": "GROQ_API_KEY",
        }

        env_var = env_var_map.get(provider)
        if env_var:
            return os.environ.get(env_var)

        return None

    def set_api_key(self, api_key: str) -> None:
        """
        设置 API Key

        Args:
            api_key: API 密钥
        """
        os.environ['OPENAI_API_KEY'] = api_key

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（向后兼容）

        Returns:
            配置字典
        """
        # 使用 Pydantic v2 的 model_dump()
        data = self.model_dump()
        return {
            'llm': {
                'provider': data['llm']['provider'],
                'model_name': data['llm']['model_name'],
                'temperature': data['llm']['temperature'],
                'max_tokens': data['llm']['max_tokens'],
                'api_base': data['llm']['api_base'],
                'api_timeout': data['llm']['api_timeout'],
            },
            'agent': {
                'name': data['agent']['name'],
                'awake_interval': data['agent']['awake_interval'],
                'max_iterations': data['agent']['max_iterations'],
                'auto_backup': data['agent']['auto_backup'],
            },
            'log': {
                'level': data['log']['level'],
            },
        }


# ============================================================================
# 向后兼容：全局配置
# ============================================================================

_default_config: Optional[Config] = None


def get_config_legacy(config_path: Optional[str] = None) -> Config:
    """
    获取全局默认配置

    Args:
        config_path: 配置文件路径

    Returns:
        Config 实例
    """
    global _default_config
    if _default_config is None or config_path is not None:
        _default_config = Config(config_path=config_path)
    return _default_config


# ============================================================================
# __getattr__ 支持（Python 3.7+ 模块级懒加载）
# ============================================================================

# 为了更好的向后兼容，提供模块级属性访问
def __getattr__(name: str):
    """
    模块级属性懒加载

    支持:
        import config
        config.Config          -> Config 类
        config.use_model()     -> use_model 函数
        config.list_models()   -> list_models 函数
    """
    if name == 'Config':
        return Config
    elif name == 'get_config':
        return get_config_legacy
    elif name in ('use_model', 'switch_model', 'list_models', 'show_model_info',
                  'MODEL_REGISTRY', 'get_model_preset'):
        return globals()[name]
    raise AttributeError(f"module 'config' has no attribute '{name}'")


# ============================================================================
# 入口
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("可用模型列表")
    print("=" * 60)
    print()

    # 按提供商分组显示
    providers: Dict[str, List] = {}
    for model_id, preset in MODEL_REGISTRY.items():
        if preset.provider not in providers:
            providers[preset.provider] = []
        providers[preset.provider].append({
            "id": model_id,
            "name": preset.name,
            "description": preset.description,
        })

    for provider, models in providers.items():
        print(f"[{provider.upper()}]")
        for model in models:
            print(f"  {model['id']:25s} - {model['name']}")
            print(f"  {'':25s}   {model['description']}")
        print()

    print("=" * 60)
    print("使用方法")
    print("=" * 60)
    print()
    print("# 方式1: 使用预定义模型")
    print("from config import use_model")
    print("config = use_model('gpt-4')")
    print()
    print("# 方式2: 从 config.toml 读取")
    print("from config import Config")
    print("config = Config()")
    print()
    print("# 方式3: 从字典创建")
    print("config = Config.from_dict({'llm.model_name': 'gpt-4'})")
    print()
    print("# 查看模型详情")
    print("from config import show_model_info")
    print("print(show_model_info('gpt-4'))")
    print()
    print("=" * 60)
    print("新版 API (推荐)")
    print("=" * 60)
    print()
    print("from config import get_settings")
    print()
    print("settings = get_settings()")
    print("print(settings.config.llm.model_name)")
    print()
    print("settings.use_model('gpt-4')")
