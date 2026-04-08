"""
Pydantic 数据模型定义

使用 Pydantic v2 定义所有配置项的数据模型，提供严格的类型校验和验证逻辑。
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    computed_field,
)


# ============================================================================
# LLM 配置
# ============================================================================

class LLMConfig(BaseModel):
    """
    大语言模型 (LLM) 配置

    Attributes:
        provider: 模型提供商 (openai, anthropic, deepseek, aliyun 等)
        model_name: 具体模型名称
        api_key: API 密钥（可从环境变量或配置文件读取）
        api_base: API 端点 URL
        temperature: 采样温度，控制输出的随机性 (0.0-2.0)
        max_tokens: 最大输出 token 数
        api_timeout: API 请求超时时间（秒）
    """
    provider: str = Field(
        default="aliyun",
        description="LLM 提供商: openai, anthropic, deepseek, aliyun, google, ollama 等"
    )
    model_name: str = Field(
        default="qwen-plus",
        description="具体模型名称，如 gpt-4, claude-3-5-sonnet-20241022, deepseek-chat"
    )
    api_key: str = Field(
        default="",
        description="API 密钥，可从环境变量获取"
    )
    api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="API 端点 URL"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度 (0.0-2.0)，越低越确定性，越高越随机"
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="最大输出 token 数"
    )
    api_timeout: int = Field(
        default=60,
        gt=0,
        description="API 请求超时时间（秒）"
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """验证提供商名称"""
        valid_providers = [
            "openai", "anthropic", "deepseek", "aliyun",
            "google", "zhipu", "ollama", "siliconflow", "groq"
        ]
        if v.lower() not in valid_providers:
            # 允许自定义提供商但发出警告
            pass
        return v.lower()

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """确保温度在有效范围内"""
        if not 0.0 <= v <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {v}")
        return round(v, 2)


# ============================================================================
# Agent 行为配置
# ============================================================================

class AgentConfig(BaseModel):
    """
    Agent 行为配置

    Attributes:
        name: Agent 实例名称
        workspace: 工作区目录路径
        awake_interval: 苏醒间隔（秒），Agent 定期检查是否有任务
        max_iterations: 单次苏醒的最大工具调用次数
        max_runtime: 最大运行时间（秒），0 表示无限制
        auto_backup: 是否启用自动备份
        backup_interval: 自动备份间隔（秒）
        auto_restart_threshold: 自动重启阈值（错误次数），0 表示禁用
    """
    name: str = Field(
        default="SelfEvolvingAgent",
        description="Agent 名称"
    )
    workspace: str = Field(
        default="workspace",
        description="工作区目录（相对于项目根目录）"
    )
    awake_interval: int = Field(
        default=60,
        gt=0,
        description="苏醒间隔（秒）"
    )
    max_iterations: int = Field(
        default=10,
        gt=0,
        description="单次苏醒的最大工具调用次数"
    )
    max_runtime: int = Field(
        default=0,
        ge=0,
        description="最大运行时间（秒），0 表示无限制"
    )
    auto_backup: bool = Field(
        default=True,
        description="是否启用自动备份"
    )
    backup_interval: int = Field(
        default=300,
        gt=0,
        description="自动备份间隔（秒）"
    )
    auto_restart_threshold: int = Field(
        default=0,
        ge=0,
        description="自动重启阈值，0 表示禁用"
    )

    @field_validator("awake_interval", "max_iterations", "backup_interval")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """验证正整数"""
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v


# ============================================================================
# 上下文压缩配置
# ============================================================================

class ContextCompressionConfig(BaseModel):
    """
    运行时上下文压缩配置

    Attributes:
        enabled: 是否启用压缩
        max_token_limit: Token 阈值，超过此值触发压缩
        keep_recent_steps: 保留最近的工具调用次数
        summary_max_chars: 压缩摘要的最大字符数
        compression_model: 用于压缩的模型名称
    """
    enabled: bool = Field(
        default=True,
        description="是否启用上下文压缩"
    )
    max_token_limit: int = Field(
        default=16000,
        gt=0,
        description="Token 阈值，超过此值触发压缩"
    )
    keep_recent_steps: int = Field(
        default=2,
        ge=0,
        description="保留最近的工具调用次数"
    )
    summary_max_chars: int = Field(
        default=200,
        gt=0,
        description="压缩摘要的最大字符数"
    )
    compression_model: str = Field(
        default="qwen-turbo",
        description="用于压缩的轻量模型"
    )

    @model_validator(mode="after")
    def validate_limits(self) -> "ContextCompressionConfig":
        """验证限制参数"""
        if self.keep_recent_steps > 10:
            raise ValueError("keep_recent_steps should not exceed 10")
        if self.summary_max_chars > 1000:
            raise ValueError("summary_max_chars should not exceed 1000")
        return self


# ============================================================================
# 工具配置
# ============================================================================

class ToolConfig(BaseModel):
    """
    工具模块配置

    Attributes:
        web_search_enabled: 是否启用网络搜索
        file_edit_enabled: 是否启用文件编辑
        syntax_check_enabled: 是否启用语法检查
        restart_enabled: 是否允许 Agent 自我重启
        allowed_directories: 允许访问的目录列表
        forbidden_patterns: 禁止访问的文件模式
    """
    web_search_enabled: bool = Field(
        default=True,
        description="是否启用网络搜索"
    )
    file_edit_enabled: bool = Field(
        default=True,
        description="是否启用文件编辑"
    )
    syntax_check_enabled: bool = Field(
        default=True,
        description="是否启用语法检查"
    )
    restart_enabled: bool = Field(
        default=True,
        description="是否允许 Agent 自我重启"
    )
    allowed_directories: List[str] = Field(
        default_factory=list,
        description="允许访问的目录列表"
    )
    forbidden_patterns: List[str] = Field(
        default_factory=lambda: [
            ".env", ".password", ".secret", ".key",
            "id_rsa", "credentials.json"
        ],
        description="禁止访问的文件模式"
    )

    @model_validator(mode="after")
    def setup_directories(self) -> "ToolConfig":
        """自动设置默认允许目录"""
        if not self.allowed_directories:
            project_root = Path(__file__).parent.parent.resolve()
            self.allowed_directories = [
                str(project_root),
                str(project_root / "tools"),
                str(Path.cwd()),
                str(Path.home()),
            ]
        return self


# ============================================================================
# 日志配置
# ============================================================================

class LogConfig(BaseModel):
    """
    日志系统配置

    Attributes:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: 日志格式字符串
        date_format: 日期时间格式
        file_enabled: 是否写入文件
        file_path: 日志文件路径
    """
    level: str = Field(
        default="INFO",
        description="日志级别"
    )
    format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(message)s",
        description="日志格式"
    )
    date_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="日期时间格式"
    )
    file_enabled: bool = Field(
        default=False,
        description="是否写入文件"
    )
    file_path: str = Field(
        default="logs/agent.log",
        description="日志文件路径"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper


# ============================================================================
# 网络配置
# ============================================================================

class NetworkConfig(BaseModel):
    """
    网络请求配置

    Attributes:
        timeout: 请求超时时间（秒）
        user_agent: HTTP User-Agent 头
        max_retries: 最大重试次数
    """
    timeout: int = Field(
        default=30,
        gt=0,
        description="请求超时时间（秒）"
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; SelfEvolvingAgent/1.0)",
        description="HTTP User-Agent"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="最大重试次数"
    )


# ============================================================================
# 主配置类
# ============================================================================

class AppConfig(BaseModel):
    """
    应用主配置类

    整合所有子配置模块，提供统一的配置管理接口。

    Example:
        # 创建默认配置
        config = AppConfig()

        # 从 TOML 加载
        config = AppConfig.from_toml("config.toml")

        # 访问配置
        config.llm.model_name = "gpt-4"
        print(config.llm.temperature)
    """
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    context_compression: ContextCompressionConfig = Field(
        default_factory=ContextCompressionConfig
    )
    tools: ToolConfig = Field(default_factory=ToolConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)

    @computed_field
    @property
    def workspace_path(self) -> Path:
        """获取工作区的绝对路径"""
        project_root = Path(__file__).parent.parent
        return project_root / self.agent.workspace

    def model_dump_simple(self) -> dict:
        """
        简化的字典导出（用于日志和调试）

        Returns:
            包含主要配置的字典
        """
        return {
            "llm": {
                "provider": self.llm.provider,
                "model_name": self.llm.model_name,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
            "agent": {
                "name": self.agent.name,
                "awake_interval": self.agent.awake_interval,
                "max_iterations": self.agent.max_iterations,
            },
            "compression": {
                "enabled": self.context_compression.enabled,
                "max_token_limit": self.context_compression.max_token_limit,
            },
            "log_level": self.log.level,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（向后兼容）

        Returns:
            配置字典
        """
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

    def get_api_key(self) -> Optional[str]:
        """
        获取 API Key（优先从配置读取，其次环境变量）

        Returns:
            API Key，未设置返回 None
        """
        import os

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
        self.llm.api_key = api_key

    def __repr__(self) -> str:
        return (
            f"AppConfig(model={self.llm.model_name}, "
            f"provider={self.llm.provider}, "
            f"temperature={self.llm.temperature})"
        )


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "LLMConfig",
    "AgentConfig",
    "ContextCompressionConfig",
    "ToolConfig",
    "LogConfig",
    "NetworkConfig",
    "AppConfig",
]
