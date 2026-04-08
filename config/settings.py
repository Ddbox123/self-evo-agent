"""
配置加载与单例管理

负责从 TOML 配置文件、环境变量加载配置，并对外提供统一的单例访问接口。
支持配置热更新和环境变量覆盖。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from .models import (
    AppConfig,
    LLMConfig,
    AgentConfig,
    ContextCompressionConfig,
    ToolConfig,
    LogConfig,
    NetworkConfig,
)
from .providers import (
    MODEL_PRESETS,
    get_model_preset,
    resolve_model_alias,
    list_models,
    show_model_info,
)

# TOML 库兼容处理
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None


# ============================================================================
# 配置文件路径
# ============================================================================

DEFAULT_CONFIG_PATH = "config.toml"


# ============================================================================
# 全局单例
# ============================================================================

_settings: Optional[AppConfig] = None
_config_path: Optional[str] = None


# ============================================================================
# 配置加载器
# ============================================================================

class ConfigLoader:
    """
    配置加载器

    负责从 TOML 文件、环境变量加载配置到 Pydantic 模型。
    配置优先级：环境变量 > TOML 文件 > 默认值
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化加载器

        Args:
            config_path: 配置文件路径，为 None 时使用默认路径
        """
        self.config_path = config_path

    def _find_config_file(self) -> Optional[Path]:
        """
        查找配置文件

        查找顺序：
        1. 指定的 config_path
        2. 项目根目录的 config.toml
        3. 当前目录的 config.toml

        Returns:
            配置文件路径，不存在返回 None
        """
        # 1. 指定的路径
        if self.config_path:
            path = Path(self.config_path)
            if path.exists():
                return path.resolve()

        # 2. 项目根目录
        project_root = Path(__file__).parent.parent
        default_path = project_root / DEFAULT_CONFIG_PATH
        if default_path.exists():
            return default_path.resolve()

        # 3. 当前目录
        cwd_path = Path.cwd() / DEFAULT_CONFIG_PATH
        if cwd_path.exists():
            return cwd_path.resolve()

        return None

    def _load_from_toml(self) -> Dict[str, Any]:
        """
        从 TOML 文件加载配置

        Returns:
            配置字典
        """
        config_file = self._find_config_file()
        if not config_file:
            return {}

        if tomllib is None:
            print("警告: 需要安装 toml 库来读取配置文件 (pip install toml)")
            return {}

        try:
            with open(config_file, 'rb') as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"警告: 读取配置文件失败: {e}")
            return {}

    def _load_from_env(self, prefix: str = "AGENT_") -> Dict[str, Any]:
        """
        从环境变量加载配置

        支持的环境变量格式：
        - AGENT_LLM_MODEL_NAME -> llm.model_name
        - AGENT_LLM_TEMPERATURE -> llm.temperature
        - AGENT_AGENT_NAME -> agent.name
        - AGENT_LOG_LEVEL -> log.level

        Args:
            prefix: 环境变量前缀

        Returns:
            配置字典
        """
        config: Dict[str, Any] = {}

        # 环境变量到配置项的映射
        env_mappings = {
            # LLM 配置
            f"{prefix}LLM_PROVIDER": ("llm", "provider"),
            f"{prefix}LLM_MODEL_NAME": ("llm", "model_name"),
            f"{prefix}LLM_API_KEY": ("llm", "api_key"),
            f"{prefix}LLM_API_BASE": ("llm", "api_base"),
            f"{prefix}LLM_TEMPERATURE": ("llm", "temperature"),
            f"{prefix}LLM_MAX_TOKENS": ("llm", "max_tokens"),
            f"{prefix}LLM_API_TIMEOUT": ("llm", "api_timeout"),

            # Agent 配置
            f"{prefix}AGENT_NAME": ("agent", "name"),
            f"{prefix}AGENT_WORKSPACE": ("agent", "workspace"),
            f"{prefix}AWARE_INTERVAL": ("agent", "awake_interval"),
            f"{prefix}AGENT_MAX_ITERATIONS": ("agent", "max_iterations"),
            f"{prefix}AGENT_MAX_RUNTIME": ("agent", "max_runtime"),
            f"{prefix}AGENT_AUTO_BACKUP": ("agent", "auto_backup"),
            f"{prefix}AGENT_BACKUP_INTERVAL": ("agent", "backup_interval"),
            f"{prefix}AGENT_AUTO_RESTART_THRESHOLD": ("agent", "auto_restart_threshold"),

            # 压缩配置
            f"{prefix}COMPRESSION_ENABLED": ("context_compression", "enabled"),
            f"{prefix}COMPRESSION_MAX_TOKEN_LIMIT": ("context_compression", "max_token_limit"),
            f"{prefix}COMPRESSION_KEEP_RECENT_STEPS": ("context_compression", "keep_recent_steps"),
            f"{prefix}COMPRESSION_SUMMARY_MAX_CHARS": ("context_compression", "summary_max_chars"),
            f"{prefix}COMPRESSION_MODEL": ("context_compression", "compression_model"),

            # 日志配置
            f"{prefix}LOG_LEVEL": ("log", "level"),
            f"{prefix}LOG_FILE_ENABLED": ("log", "file_enabled"),

            # 网络配置
            f"{prefix}NETWORK_TIMEOUT": ("network", "timeout"),
            f"{prefix}NETWORK_MAX_RETRIES": ("network", "max_retries"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                if section not in config:
                    config[section] = {}

                # 类型转换
                if key == "temperature":
                    value = float(value)
                elif key in ("max_tokens", "api_timeout", "awake_interval",
                            "max_iterations", "max_runtime", "backup_interval",
                            "auto_restart_threshold", "timeout", "max_retries",
                            "max_token_limit", "keep_recent_steps",
                            "summary_max_chars"):
                    value = int(value)
                elif key in ("auto_backup", "file_enabled", "enabled"):
                    value = value.lower() in ("true", "1", "yes", "on")

                config[section][key] = value

        # API Keys (从常见环境变量直接读取)
        api_key_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DEEPSEEK_API_KEY",
            "DASHSCOPE_API_KEY",
            "ZHIPU_API_KEY",
            "GOOGLE_API_KEY",
            "SILICONFLOW_API_KEY",
            "GROQ_API_KEY",
        ]
        for var in api_key_vars:
            if os.environ.get(var):
                if "llm" not in config:
                    config["llm"] = {}
                config["llm"]["api_key"] = os.environ.get(var)
                break

        return config

    def load(self) -> AppConfig:
        """
        加载完整配置

        优先级：环境变量 > TOML > 默认值

        Returns:
            AppConfig 实例
        """
        # 1. 创建默认配置
        config = AppConfig()

        # 2. 从 TOML 加载
        toml_config = self._load_from_toml()
        if toml_config:
            config = self._apply_dict(config, toml_config)

        # 3. 从环境变量加载
        env_config = self._load_from_env()
        if env_config:
            config = self._apply_dict(config, env_config)

        return config

    def _apply_dict(self, config: AppConfig, data: Dict[str, Any]) -> AppConfig:
        """
        将字典应用到配置对象（深度合并）

        Args:
            config: 原始配置
            data: 要应用的数据

        Returns:
            更新后的配置
        """
        # 深度合并字典
        current = config.model_dump()

        def deep_merge(base: Dict, update: Dict) -> Dict:
            """深度合并两个字典"""
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(current, data)

        if merged != current:
            config = AppConfig.model_validate(merged)

        return config


# ============================================================================
# 配置管理器
# ============================================================================

class Settings:
    """
    配置管理器

    提供配置的单例访问，支持动态更新和模型切换。
    这是新架构中的主要配置访问入口。

    Example:
        # 获取配置
        settings = Settings()
        config = settings.config

        # 访问 LLM 配置
        print(config.llm.model_name)

        # 切换模型
        settings.use_model("gpt-4")
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self._loader = ConfigLoader(config_path)
        self._config: Optional[AppConfig] = None

    @property
    def config(self) -> AppConfig:
        """获取当前配置（延迟加载）"""
        if self._config is None:
            self._config = self._loader.load()
        return self._config

    def reload(self, config_path: Optional[str] = None) -> AppConfig:
        """
        重新加载配置

        Args:
            config_path: 新的配置文件路径

        Returns:
            重新加载后的配置
        """
        if config_path:
            self._loader = ConfigLoader(config_path)
        self._config = self._loader.load()
        return self._config

    def use_model(
        self,
        model_id: str,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
    ) -> AppConfig:
        """
        切换到指定模型

        Args:
            model_id: 模型 ID（如 "gpt-4", "claude-3.5", "deepseek"）
            temperature: 可选的温度参数，会覆盖默认值
            api_key: 可选的 API Key

        Returns:
            更新后的配置

        Raises:
            ValueError: 模型 ID 不存在或缺少 API Key
        """
        # 解析别名
        resolved_id = resolve_model_alias(model_id)

        # 获取预设
        preset = get_model_preset(resolved_id)
        if not preset:
            available = ", ".join(MODEL_PRESETS.keys())
            raise ValueError(
                f"未知模型: {model_id}\n"
                f"可用模型: {available}\n\n"
                f"查看所有模型: python -c \"from config.providers import list_models; print(list_models())\""
            )

        # 检查 API Key
        effective_api_key = api_key
        if preset.api_key_env and not effective_api_key:
            effective_api_key = os.environ.get(preset.api_key_env)

        if preset.api_key_env and not effective_api_key:
            raise ValueError(
                f"模型 {preset.name} 需要 API Key。\n"
                f"请设置环境变量: export {preset.api_key_env}='your-api-key'\n"
                f"或传入参数: use_model('{model_id}', api_key='your-api-key')"
            )

        # 设置环境变量
        if effective_api_key and preset.api_key_env:
            os.environ[preset.api_key_env] = effective_api_key

        # 更新配置
        self.config.llm.provider = preset.provider
        self.config.llm.model_name = preset.model_name
        self.config.llm.api_base = preset.api_base
        self.config.llm.max_tokens = preset.max_tokens
        self.config.llm.temperature = (
            temperature if temperature is not None else preset.default_temperature
        )

        return self.config

    def get_api_key(self) -> Optional[str]:
        """
        获取当前配置的 API Key

        Returns:
            API Key，未设置返回 None
        """
        # 1. 优先从配置读取
        if self.config.llm.api_key:
            return self.config.llm.api_key

        # 2. 从环境变量读取
        provider = self.config.llm.provider
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

    def __repr__(self) -> str:
        return f"Settings(model={self.config.llm.model_name}, provider={self.config.llm.provider})"


# ============================================================================
# 全局单例访问
# ============================================================================

def get_settings(config_path: Optional[str] = None) -> Settings:
    """
    获取 Settings 单例

    Args:
        config_path: 配置文件路径，首次调用后忽略

    Returns:
        Settings 实例
    """
    global _settings, _config_path

    if _settings is None or config_path is not None:
        _settings = Settings(config_path)
        _config_path = config_path

    return _settings


def get_config() -> AppConfig:
    """
    获取当前配置（便捷函数）

    Returns:
        AppConfig 实例
    """
    return get_settings().config


# ============================================================================
# 旧版兼容接口
# ============================================================================

def use_model(
    model_id: str,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
) -> AppConfig:
    """
    快速切换到指定模型（旧版兼容）

    这是最简单的方式来切换 LLM 模型。

    Args:
        model_id: 模型 ID（如 "gpt-4", "claude-3.5", "deepseek"）
        temperature: 可选的温度参数，会覆盖默认值
        api_key: 可选的 API Key

    Returns:
        配置好的 AppConfig 实例

    Raises:
        ValueError: 模型 ID 不存在或缺少 API Key
    """
    settings = get_settings()
    return settings.use_model(model_id, temperature, api_key)


def switch_model(model_id: str, **kwargs) -> AppConfig:
    """
    切换模型（use_model 的别名）

    Args:
        model_id: 模型 ID
        **kwargs: 传递给 use_model 的其他参数

    Returns:
        AppConfig 实例
    """
    return use_model(model_id, **kwargs)


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    # 核心类
    "AppConfig",
    "ConfigLoader",
    "Settings",
    # 函数
    "get_settings",
    "get_config",
    "use_model",
    "switch_model",
    # 从 providers 导出
    "MODEL_PRESETS",
    "get_model_preset",
    "list_models",
    "show_model_info",
    "resolve_model_alias",
]
