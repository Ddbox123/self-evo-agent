"""
配置文件

存放所有可配置参数，包括 API 密钥、模型设置、Agent 行为参数等。
修改此文件即可调整 Agent 的行为，无需改动核心代码。

使用方法：
    from config import Config, use_model
    
    # 方式1: 使用预定义模型
    config = use_model("gpt-4")
    config = use_model("claude-3")
    config = use_model("deepseek")
    
    # 方式2: 从 config.toml 读取
    config = Config()
    
    # 方式3: 从字典创建
    config = Config.from_dict({'llm.model_name': 'gpt-4'})
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field


# ============================================================================
# 配置文件路径
# ============================================================================

DEFAULT_CONFIG_PATH = "config.toml"


# ============================================================================
# LLM 模型预设注册表
# ============================================================================

@dataclass
class ModelPreset:
    """模型预设"""
    name: str                    # 显示名称
    provider: str                # 提供商
    model_name: str              # 模型名称
    api_base: Optional[str]      # API 端点
    api_key_env: str             # API Key 环境变量名
    default_temperature: float    # 默认温度
    max_tokens: int             # 最大 tokens
    description: str             # 描述
    supports_function_call: bool = True  # 是否支持函数调用


# 预定义模型注册表
MODEL_REGISTRY: Dict[str, ModelPreset] = {
    # ========== OpenAI 系列 ==========
    "gpt-4o": ModelPreset(
        name="GPT-4o",
        provider="openai",
        model_name="gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="OpenAI 最新旗舰模型，支持函数调用，速度更快",
    ),
    "gpt-4-turbo": ModelPreset(
        name="GPT-4 Turbo",
        provider="openai",
        model_name="gpt-4-turbo",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="OpenAI 高性能 GPT-4 模型",
    ),
    "gpt-4": ModelPreset(
        name="GPT-4",
        provider="openai",
        model_name="gpt-4",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="OpenAI 最强模型，适合复杂推理",
    ),
    "gpt-3.5-turbo": ModelPreset(
        name="GPT-3.5 Turbo",
        provider="openai",
        model_name="gpt-3.5-turbo",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="快速、便宜的 ChatGPT 模型",
    ),
    
    # ========== Anthropic 系列 ==========
    "claude-3-opus": ModelPreset(
        name="Claude 3 Opus",
        provider="anthropic",
        model_name="claude-3-opus-20240229",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_temperature=1.0,
        max_tokens=4096,
        description="Anthropic 最强模型，适合复杂任务",
    ),
    "claude-3-sonnet": ModelPreset(
        name="Claude 3 Sonnet",
        provider="anthropic",
        model_name="claude-3-sonnet-20240229",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_temperature=1.0,
        max_tokens=4096,
        description="Anthropic 平衡模型，性价比高",
    ),
    "claude-3": ModelPreset(
        name="Claude 3",
        provider="anthropic",
        model_name="claude-3-haiku-20240307",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_temperature=1.0,
        max_tokens=4096,
        description="Anthropic 快速模型",
    ),
    "claude-3.5": ModelPreset(
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
        default_temperature=1.0,
        max_tokens=8192,
        description="Anthropic 最新模型，能力超越 GPT-4",
    ),
    
    # ========== Google 系列 ==========
    "gemini-pro": ModelPreset(
        name="Gemini Pro",
        provider="google",
        model_name="gemini-pro",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GOOGLE_API_KEY",
        default_temperature=0.9,
        max_tokens=4096,
        description="Google Gemini Pro 模型",
    ),
    "gemini-2": ModelPreset(
        name="Gemini 2.0 Flash",
        provider="google",
        model_name="gemini-2.0-flash",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GOOGLE_API_KEY",
        default_temperature=0.9,
        max_tokens=8192,
        description="Google 最新 Gemini 模型",
    ),
    
    # ========== DeepSeek 系列 ==========
    "deepseek": ModelPreset(
        name="DeepSeek V3",
        provider="deepseek",
        model_name="deepseek-chat",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="深度求索大模型，性价比高",
    ),
    "deepseek-coder": ModelPreset(
        name="DeepSeek Coder",
        provider="deepseek",
        model_name="deepseek-coder",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="深度求索代码模型",
    ),
    
    # ========== 通义千问 (阿里云百炼) ==========
    # 阿里云百炼 API 参考: https://help.aliyun.com/model-studio/getting-started/models
    "qwen-plus": ModelPreset(
        name="Qwen Plus (通义千问 Plus)",
        provider="aliyun",
        model_name="qwen-plus",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云百炼 Qwen Plus，性能均衡",
    ),
    "qwen-plus-rear": ModelPreset(
        name="Qwen Plus (兜底)",
        provider="aliyun",
        model_name="qwen-plus-rear",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云百炼 Qwen Plus 兜底版本",
    ),
    "qwen-turbo": ModelPreset(
        name="Qwen Turbo (通义千问 Turbo)",
        provider="aliyun",
        model_name="qwen-turbo",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云百炼 Qwen Turbo，速度更快",
    ),
    "qwen-max": ModelPreset(
        name="Qwen Max (通义千问 Max)",
        provider="aliyun",
        model_name="qwen-max",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云百炼 Qwen Max，最强版本",
    ),
    "qwen-max-longcontext": ModelPreset(
        name="Qwen Max (长上下文)",
        provider="aliyun",
        model_name="qwen-max-longcontext",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=8192,
        description="阿里云百炼 Qwen Max，支持长上下文",
    ),
    "qwen-coder-plus": ModelPreset(
        name="Qwen Coder Plus (通义千问 Coder)",
        provider="aliyun",
        model_name="qwen-coder-plus",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云百炼代码模型，专为编程优化",
    ),
    "qwen": ModelPreset(
        name="Qwen Plus (qwen 别名)",
        provider="aliyun",
        model_name="qwen-plus",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="阿里云通义千问 Plus (qwen 别名)",
    ),
    
    # ========== 智谱 GLM ==========
    "glm": ModelPreset(
        name="GLM-4",
        provider="zhipu",
        model_name="glm-4",
        api_base="https://open.bigmodel.cn/api/paas/v4",
        api_key_env="ZHIPU_API_KEY",
        default_temperature=0.9,
        max_tokens=4096,
        description="智谱 GLM-4 大模型",
    ),
    
    # ========== 本地模型 (Ollama) ==========
    "ollama-llama3": ModelPreset(
        name="Ollama Llama3",
        provider="ollama",
        model_name="llama3",
        api_base="http://localhost:11434/v1",
        api_key_env="",  # 本地模型不需要 API Key
        default_temperature=0.7,
        max_tokens=4096,
        description="Ollama 本地 Llama3 模型",
        supports_function_call=False,
    ),
    "ollama-qwen": ModelPreset(
        name="Ollama Qwen",
        provider="ollama",
        model_name="qwen2.5",
        api_base="http://localhost:11434/v1",
        api_key_env="",
        default_temperature=0.7,
        max_tokens=4096,
        description="Ollama 本地 Qwen 模型",
        supports_function_call=False,
    ),
    "ollama-codellama": ModelPreset(
        name="Ollama CodeLlama",
        provider="ollama",
        model_name="codellama",
        api_base="http://localhost:11434/v1",
        api_key_env="",
        default_temperature=0.7,
        max_tokens=4096,
        description="Ollama 本地代码模型",
        supports_function_call=False,
    ),
    
    # ========== SiliconFlow / 硅基流动 ==========
    "siliconflow-gpt": ModelPreset(
        name="SiliconFlow GPT",
        provider="siliconflow",
        model_name="gpt-4o",
        api_base="https://api.siliconflow.cn/v1",
        api_key_env="SILICONFLOW_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="硅基流动平台 GPT-4o",
    ),
    "siliconflow-deepseek": ModelPreset(
        name="SiliconFlow DeepSeek",
        provider="siliconflow",
        model_name="deepseek-ai/DeepSeek-V3",
        api_base="https://api.siliconflow.cn/v1",
        api_key_env="SILICONFLOW_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="硅基流动平台 DeepSeek",
    ),
    
    # ========== Groq ==========
    "groq-llama3": ModelPreset(
        name="Groq Llama3",
        provider="groq",
        model_name="llama-3.1-70b-versatile",
        api_base="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_temperature=0.7,
        max_tokens=4096,
        description="Groq 超快 Llama 模型",
    ),
}


def list_models() -> List[Dict[str, str]]:
    """
    列出所有可用模型。
    
    Returns:
        模型信息列表
    """
    return [
        {
            "id": key,
            "name": preset.name,
            "provider": preset.provider,
            "description": preset.description,
        }
        for key, preset in MODEL_REGISTRY.items()
    ]


def show_model_info(model_id: str) -> Optional[str]:
    """
    显示模型详细信息。
    
    Args:
        model_id: 模型 ID
        
    Returns:
        格式化的模型信息，未找到返回 None
    """
    if model_id not in MODEL_REGISTRY:
        return None
    
    preset = MODEL_REGISTRY[model_id]
    
    lines = [
        f"模型: {preset.name}",
        f"ID: {model_id}",
        f"提供商: {preset.provider}",
        f"模型名: {preset.model_name}",
        f"API 端点: {preset.api_base or '(默认)'}",
        f"API Key 环境变量: {preset.api_key_env or '(无需)'}",
        f"默认温度: {preset.default_temperature}",
        f"最大 tokens: {preset.max_tokens}",
        f"支持函数调用: {'是' if preset.supports_function_call else '否'}",
        "",
        f"描述: {preset.description}",
    ]
    
    return '\n'.join(lines)


def use_model(
    model_id: str,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
) -> 'Config':
    """
    快速切换到指定模型。
    
    这是最简单的方式来切换 LLM 模型。
    
    Args:
        model_id: 模型 ID（如 "gpt-4", "claude-3.5", "deepseek"）
        temperature: 可选的温度参数，会覆盖默认值
        api_key: 可选的 API Key，会覆盖环境变量
        
    Returns:
        配置好的 Config 实例
        
    Raises:
        ValueError: 模型 ID 不存在或缺少 API Key
        
    Example:
        >>> # 使用 GPT-4
        >>> config = use_model("gpt-4")
        
        >>> # 使用 Claude 3.5
        >>> config = use_model("claude-3.5")
        
        >>> # 使用自定义温度
        >>> config = use_model("gpt-4", temperature=0.5)
        
        >>> # 同时指定 API Key
        >>> config = use_model("deepseek", api_key="sk-xxx")
    """
    if model_id not in MODEL_REGISTRY:
        available = ", ".join(MODEL_REGISTRY.keys())
        raise ValueError(
            f"未知模型: {model_id}\n"
            f"可用模型: {available}\n\n"
            f"查看所有模型: python -c \"from config import list_models; print(list_models())\""
        )
    
    preset = MODEL_REGISTRY[model_id]
    
    # 检查 API Key
    if preset.api_key_env:
        key = api_key or os.environ.get(preset.api_key_env)
        if not key:
            raise ValueError(
                f"模型 {preset.name} 需要 API Key。\n"
                f"请设置环境变量: export {preset.api_key_env}='your-api-key'\n"
                f"或传入参数: use_model('{model_id}', api_key='your-api-key')"
            )
        os.environ[preset.api_key_env] = key
    
    # 创建配置
    config = Config()
    
    # 应用模型预设
    config.llm.provider = preset.provider
    config.llm.model_name = preset.model_name
    config.llm.api_base = preset.api_base
    config.llm.temperature = temperature if temperature is not None else preset.default_temperature
    config.llm.max_tokens = preset.max_tokens
    
    return config


# ============================================================================
# 配置数据类
# ============================================================================

@dataclass
class LLMConfig:
    """大语言模型配置"""
    provider: str = "aliyun"                    # 提供商
    model_name: str = "qwen-plus"             # 模型名称（阿里云百炼默认 qwen-plus）
    api_key: str = ""                          # API Key（直接写在配置中）
    api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"  # API 端点
    temperature: float = 0.7                   # 温度参数 (0.0-2.0)
    max_tokens: int = 4096                     # 最大输出 tokens
    api_timeout: int = 60                     # API 超时时间（秒）


@dataclass
class AgentConfig:
    """Agent 行为配置"""
    name: str = "SelfEvolvingAgent"
    awake_interval: int = 60
    max_iterations: int = 10
    max_runtime: int = 0
    auto_backup: bool = True
    backup_interval: int = 300
    auto_restart_threshold: int = 0


@dataclass
class ToolConfig:
    """工具配置"""
    web_search_enabled: bool = True
    file_edit_enabled: bool = True
    syntax_check_enabled: bool = True
    restart_enabled: bool = True
    allowed_directories: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=lambda: [
        '.env', '.password', '.secret', '.key', 'id_rsa', 'credentials.json'
    ])


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file_enabled: bool = False
    file_path: str = "logs/agent.log"


@dataclass
class NetworkConfig:
    """网络配置"""
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (compatible; SelfEvolvingAgent/1.0)"
    max_retries: int = 3


# ============================================================================
# 主配置类
# ============================================================================

class Config:
    """
    统一配置管理类。
    
    支持从 TOML 文件、环境变量、字典加载配置。
    配置优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
    
    Example:
        # 使用预定义模型（推荐）
        from config import use_model
        config = use_model("gpt-4")
        
        # 从默认配置文件加载
        config = Config()
        
        # 从指定文件加载
        config = Config(config_path="custom.toml")
        
        # 从字典创建
        config = Config.from_dict({
            'llm.model_name': 'gpt-4',
            'agent.awake_interval': 120,
        })
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_prefix: str = "AGENT_",
        **kwargs
    ) -> None:
        self.env_prefix = env_prefix
        
        # 初始化各模块配置
        self.llm = LLMConfig()
        self.agent = AgentConfig()
        self.tools = ToolConfig()
        self.log = LogConfig()
        self.network = NetworkConfig()
        
        # 设置允许目录
        project_root = Path(__file__).parent.resolve()
        self.tools.allowed_directories = [
            str(project_root),
            str(project_root / "tools"),
            str(Path.cwd()),
            str(Path.home()),
        ]
        
        # 加载配置
        self._load_from_config_file(config_path)
        self._load_from_env()
        self._load_from_kwargs(**kwargs)
        
        # 验证
        self._validate()
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """从字典创建配置"""
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
    
    def _load_from_config_file(self, config_path: Optional[str]) -> None:
        """从 TOML 文件加载配置"""
        if config_path is None:
            default_path = Path(__file__).parent / DEFAULT_CONFIG_PATH
            if default_path.exists():
                config_path = str(default_path)
            else:
                return
        
        config_file = Path(config_path)
        if not config_file.exists():
            return
        
        try:
            import tomllib
            with open(config_file, 'rb') as f:
                data = tomllib.load(f)
            self._apply_dict(data)
        except ImportError:
            try:
                import toml
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = toml.load(f)
                self._apply_dict(data)
            except ImportError:
                print("警告: 需要安装 toml 库来读取配置文件")
    
    def _apply_dict(self, data: Dict[str, Any]) -> None:
        """将字典应用到配置对象"""
        for section, settings in data.items():
            if hasattr(self, section):
                section_obj = getattr(self, section)
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        if hasattr(section_obj, key):
                            setattr(section_obj, key, value)
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # API Keys
        for key_name in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'DEEPSEEK_API_KEY',
                         'DASHSCOPE_API_KEY', 'ZHIPU_API_KEY', 'GOOGLE_API_KEY',
                         'SILICONFLOW_API_KEY', 'GROQ_API_KEY']:
            if os.environ.get(key_name):
                break  # 至少有一个 API Key
        
        # LLM 配置
        model_name = os.environ.get(f'{self.env_prefix}LLM_MODEL_NAME', '')
        if model_name:
            self.llm.model_name = model_name
        
        temperature = os.environ.get(f'{self.env_prefix}LLM_TEMPERATURE', '')
        if temperature:
            try:
                self.llm.temperature = float(temperature)
            except ValueError:
                pass
        
        # Agent 配置
        awake_interval = os.environ.get(f'{self.env_prefix}AWARE_INTERVAL', '')
        if awake_interval:
            try:
                self.agent.awake_interval = int(awake_interval)
            except ValueError:
                pass
        
        agent_name = os.environ.get(f'{self.env_prefix}NAME', '')
        if agent_name:
            self.agent.name = agent_name
        
        log_level = os.environ.get(f'{self.env_prefix}LOG_LEVEL', '')
        if log_level:
            self.log.level = log_level.upper()
    
    def _load_from_kwargs(self, **kwargs) -> None:
        """从关键字参数加载"""
        for key, value in kwargs.items():
            if '.' in key:
                section, setting = key.split('.', 1)
                if hasattr(self, section):
                    section_obj = getattr(self, section)
                    if hasattr(section_obj, setting):
                        setattr(section_obj, setting, value)
            elif hasattr(self, key):
                setattr(self, key, value)
    
    def _validate(self) -> None:
        """验证配置"""
        if self.llm.temperature < 0 or self.llm.temperature > 2:
            raise ValueError(f"LLM temperature 必须在 0-2 之间: {self.llm.temperature}")
        
        if self.agent.awake_interval < 1:
            raise ValueError(f"Agent awake_interval 必须大于 0: {self.agent.awake_interval}")
        
        if self.agent.max_iterations < 1:
            raise ValueError(f"Agent max_iterations 必须大于 0: {self.agent.max_iterations}")
    
    def get_api_key(self) -> Optional[str]:
        """获取 API Key（优先从配置读取，其次环境变量）"""
        # 1. 优先从配置文件读取
        if self.llm.api_key:
            return self.llm.api_key
        
        # 2. 其次从环境变量读取
        env_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'DEEPSEEK_API_KEY',
            'DASHSCOPE_API_KEY',
            'ZHIPU_API_KEY',
            'GOOGLE_API_KEY',
            'SILICONFLOW_API_KEY',
            'GROQ_API_KEY',
            f'{self.env_prefix}OPENAI_API_KEY',
        ]
        
        for var in env_vars:
            key = os.environ.get(var)
            if key:
                return key
        
        return None
    
    def set_api_key(self, api_key: str) -> None:
        """设置 API Key"""
        os.environ['OPENAI_API_KEY'] = api_key
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'llm': {
                'provider': self.llm.provider,
                'model_name': self.llm.model_name,
                'temperature': self.llm.temperature,
                'max_tokens': self.llm.max_tokens,
                'api_base': self.llm.api_base,
                'api_timeout': self.llm.api_timeout,
            },
            'agent': {
                'name': self.agent.name,
                'awake_interval': self.agent.awake_interval,
                'max_iterations': self.agent.max_iterations,
                'auto_backup': self.agent.auto_backup,
            },
            'log': {
                'level': self.log.level,
            },
        }
    
    def __repr__(self) -> str:
        return f"Config(model={self.llm.model_name}, provider={self.llm.provider})"


# ============================================================================
# 全局配置
# ============================================================================

_default_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局默认配置"""
    global _default_config
    if _default_config is None or config_path is not None:
        _default_config = Config(config_path=config_path)
    return _default_config


# ============================================================================
# 便捷函数
# ============================================================================

def switch_model(model_id: str, **kwargs) -> Config:
    """
    切换模型（use_model 的别名）
    """
    return use_model(model_id, **kwargs)


# ============================================================================
# 入口
# ============================================================================

if __name__ == "__main__":
    import json
    
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
    print("from config import use_model")
    print()
    print("# 切换到 GPT-4")
    print("config = use_model('gpt-4')")
    print()
    print("# 切换到 Claude 3.5")
    print("config = use_model('claude-3.5')")
    print()
    print("# 切换到 DeepSeek（性价比高）")
    print("config = use_model('deepseek')")
    print()
    print("# 查看模型详情")
    print("from config import show_model_info")
    print("print(show_model_info('gpt-4'))")
