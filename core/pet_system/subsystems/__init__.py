# -*- coding: utf-8 -*-
"""
宠物子系统模块

包含所有宠物子系统：
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

from .base import PetSubsystem
from .gene_system import GeneSystem
from .heart_system import HeartSystem
from .dream_system import DreamSystem
from .personality_system import PersonalitySystem
from .hunger_system import HungerSystem
from .diary_system import DiarySystem
from .social_system import SocialSystem
from .health_system import HealthSystem
from .skin_system import SkinSystem
from .sound_system import SoundSystem

__all__ = [
    "PetSubsystem",
    "GeneSystem",
    "HeartSystem",
    "DreamSystem",
    "PersonalitySystem",
    "HungerSystem",
    "DiarySystem",
    "SocialSystem",
    "HealthSystem",
    "SkinSystem",
    "SoundSystem",
]
