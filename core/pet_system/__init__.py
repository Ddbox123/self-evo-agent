# -*- coding: utf-8 -*-
"""
宠物系统模块

提供完整的模型宠物生态系统，包含10大子系统：
- GeneSystem   - 基因系统
- HeartSystem  - 心跳系统
- DreamSystem  - 梦境系统
- PersonalitySystem - 性格养成
- HungerSystem - 饥饿系统
- DiarySystem  - 成长日记
- SocialSystem - 同伴社交
- HealthSystem - 健康体检
- SkinSystem   - 装扮系统
- SoundSystem  - 声音系统
"""

from .pet_system import PetSystem, get_pet_system
from .models import (
    PetData,
    PetAttributes,
    PetConfig,
    GeneData,
    HeartData,
    DreamData,
    PersonalityData,
    HungerData,
    DiaryData,
    SocialData,
    HealthData,
    SkinData,
    SoundData,
)

__all__ = [
    "PetSystem",
    "get_pet_system",
    "PetData",
    "PetAttributes",
    "PetConfig",
    "GeneData",
    "HeartData",
    "DreamData",
    "PersonalityData",
    "HungerData",
    "DiaryData",
    "SocialData",
    "HealthData",
    "SkinData",
    "SoundData",
]
