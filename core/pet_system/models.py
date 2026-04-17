# -*- coding: utf-8 -*-
"""
Pydantic 数据模型

定义宠物系统的所有数据结构和配置模型
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime


# ============================================================================
# 配置模型
# ============================================================================

class PetConfig(BaseModel):
    """宠物系统主配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="是否启用宠物系统")
    name: str = Field(default="虾宝", description="宠物名称")
    auto_save: bool = Field(default=True, description="自动保存")
    save_interval: int = Field(default=60, description="自动保存间隔(秒)")


class GeneConfig(BaseModel):
    """基因系统配置"""
    model_config = ConfigDict(extra="ignore")

    inherit_from_model: bool = Field(default=True, description="从模型继承基因特征")
    context_window_factor: float = Field(default=0.001, description="上下文窗口→寿命因子")


class HeartConfig(BaseModel):
    """心跳系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用心跳可视化")
    active_rate: float = Field(default=2.0, description="活跃时心跳频率(Hz)")
    idle_rate: float = Field(default=0.5, description="空闲时心跳频率(Hz)")
    cooldown_time: int = Field(default=5, description="心跳冷却时间(秒)")


class DreamConfig(BaseModel):
    """梦境系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用梦境系统")
    compression_triggers_dream: bool = Field(default=True, description="压缩时触发梦境")
    dream_duration: int = Field(default=3, description="梦境持续时间(秒)")
    keep_key_memory_ratio: float = Field(default=0.7, description="梦境中保留关键记忆比例")


class PersonalityConfig(BaseModel):
    """性格系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用性格养成")
    learning_window: int = Field(default=100, description="学习窗口(操作次数)")
    trait_change_rate: float = Field(default=0.05, description="性格变化率")


class HungerConfig(BaseModel):
    """饥饿系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用饥饿系统")
    food_per_meal: float = Field(default=0.1, description="每次饭量占上下文比例")
    hunger_decay_rate: float = Field(default=1.0, description="饱食度衰减率")
    mood_decay_rate: float = Field(default=0.5, description="心情衰减率")
    auto_feed_threshold: int = Field(default=1000, description="自动投喂阈值(tokens)")


class DiaryConfig(BaseModel):
    """日记系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用成长日记")
    max_entries: int = Field(default=365, description="最大日记条目数")
    auto_summarize: bool = Field(default=True, description="自动生成摘要")
    sentiment_analysis: bool = Field(default=True, description="情感分析")


class SocialConfig(BaseModel):
    """社交系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用同伴社交")
    track_other_models: bool = Field(default=True, description="跟踪其他模型")
    friendship_gain_rate: float = Field(default=1.0, description="友谊增长速度")
    max_friends: int = Field(default=10, description="最大好友数")


class HealthConfig(BaseModel):
    """健康系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用健康体检")
    check_interval: int = Field(default=30, description="健康检查间隔(秒)")
    response_time_weight: float = Field(default=0.3, description="响应时间权重")
    error_rate_weight: float = Field(default=0.4, description="错误率权重")
    efficiency_weight: float = Field(default=0.3, description="效率权重")


class SkinConfig(BaseModel):
    """装扮系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用装扮系统")
    unlock_by_achievement: bool = Field(default=True, description="通过成就解锁皮肤")
    rarity_weights: Dict[str, float] = Field(
        default_factory=lambda: {"common": 0.7, "rare": 0.2, "epic": 0.08, "legendary": 0.02}
    )


class SoundConfig(BaseModel):
    """声音系统配置"""
    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=True, description="启用情绪声音")
    volume: float = Field(default=0.5, description="音量(0-1)")
    mood_sounds: bool = Field(default=True, description="心情声音")
    action_sounds: bool = Field(default=True, description="动作声音")


# ============================================================================
# 数据模型
# ============================================================================

class PetAttributes(BaseModel):
    """宠物基础属性"""
    name: str = "虾宝"
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100
    mood: int = 100
    hunger: int = 100
    energy: int = 100
    health: int = 100
    love: int = 50
    total_tasks: int = 0
    total_uptime: int = 0
    birth_time: str = ""
    skills: Dict[str, int] = Field(default_factory=lambda: {
        "代码分析": 1,
        "自我进化": 1,
        "问题解决": 1,
        "学习能力": 1,
        "工具使用": 1,
        "沟通表达": 1,
    })
    achievements: List[str] = Field(default_factory=list)


class GeneData(BaseModel):
    """基因数据"""
    model_source: str = "unknown"
    model_family: str = "unknown"
    context_window: int = 32768
    lifespan_base: int = 1000
    traits: Dict[str, float] = Field(default_factory=dict)
    appearance_modifiers: Dict[str, str] = Field(default_factory=dict)


class HeartData(BaseModel):
    """心跳数据"""
    is_alive: bool = True
    is_active: bool = False
    last_beat: str = ""
    beat_count: int = 0
    active_since: Optional[str] = None


class DreamData(BaseModel):
    """梦境数据"""
    in_dream: bool = False
    dream_start: Optional[str] = None
    fragments: List[Dict[str, Any]] = Field(default_factory=list)
    forgotten_memories: List[str] = Field(default_factory=list)


class PersonalityData(BaseModel):
    """性格数据"""
    traits: Dict[str, float] = Field(default_factory=lambda: {
        "rational": 50,
        "creative": 50,
        "cautious": 50,
        "bold": 50,
        "social": 50,
        "solitary": 50,
    })
    behavior_history: List[Dict[str, Any]] = Field(default_factory=list)


class HungerData(BaseModel):
    """饥饿数据"""
    context_window: int = 32768
    meal_size: int = 3276
    daily_tokens: int = 0
    total_tokens: int = 0
    total_llm_calls: int = 0
    last_feed_date: str = ""
    food_level: str = "full"


class DiaryEntry(BaseModel):
    """日记条目"""
    date: str = ""
    title: str = ""
    content: str = ""
    sentiment: float = 0.0
    token_count: int = 0
    task_summary: str = ""


class DiaryData(BaseModel):
    """日记数据"""
    entries: List[DiaryEntry] = Field(default_factory=list)
    total_entries: int = 0


class FriendData(BaseModel):
    """好友数据"""
    model_name: str = ""
    friendship_level: int = 0
    first_met: str = ""
    last_interaction: str = ""
    collaboration_count: int = 0


class SocialData(BaseModel):
    """社交数据"""
    friends: List[FriendData] = Field(default_factory=list)
    total_interactions: int = 0


class HealthMetrics(BaseModel):
    """健康指标"""
    heart_rate: int = 60
    temperature: float = 36.5
    metabolism: float = 1.0
    activity: int = 0


class HealthData(BaseModel):
    """健康数据"""
    overall: int = 100
    metrics: HealthMetrics = Field(default_factory=HealthMetrics)
    last_check: str = ""
    issues: List[str] = Field(default_factory=list)


class SkinData(BaseModel):
    """装扮数据"""
    current_skin: str = "default"
    unlocked_skins: List[str] = Field(default_factory=lambda: ["default"])
    skin_rarity: str = "common"
    decorations: List[str] = Field(default_factory=list)


class SoundData(BaseModel):
    """声音数据"""
    mood_sound: str = "happy"
    last_sound: Optional[str] = None
    sound_enabled: bool = True


class DailyRecord(BaseModel):
    """每日记录"""
    date: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 0


class PetData(BaseModel):
    """完整宠物数据"""
    version: str = "3.0"
    attributes: PetAttributes = Field(default_factory=PetAttributes)
    gene: GeneData = Field(default_factory=GeneData)
    heart: HeartData = Field(default_factory=HeartData)
    dream: DreamData = Field(default_factory=DreamData)
    personality: PersonalityData = Field(default_factory=PersonalityData)
    hunger: HungerData = Field(default_factory=HungerData)
    diary: DiaryData = Field(default_factory=DiaryData)
    social: SocialData = Field(default_factory=SocialData)
    health: HealthData = Field(default_factory=HealthData)
    skin: SkinData = Field(default_factory=SkinData)
    sound: SoundData = Field(default_factory=SoundData)
    daily_records: List[DailyRecord] = Field(default_factory=list)
