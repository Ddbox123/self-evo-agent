# -*- coding: utf-8 -*-
"""
龙虾宝宝宠物系统

记录龙虾宝宝的状态：经验值、心情、技能等
支持 Emoji 模式显示
"""

import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Optional, Any


@dataclass
class PetStats:
    """宠物属性"""
    # 基础属性
    name: str = "龙虾宝宝"
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100

    # 状态属性
    mood: int = 100      # 心情 0-100
    hunger: int = 100    # 饱食度 0-100
    energy: int = 100    # 活力 0-100
    health: int = 100    # 健康 0-100
    love: int = 50       # 亲密度 0-100

    # 统计
    total_tasks: int = 0      # 完成任务数
    total_uptime: int = 0     # 累计运行时长(秒)
    birth_time: str = ""      # 出生时间

    # 技能
    skills: Dict[str, int] = field(default_factory=lambda: {
        "代码分析": 1,
        "自我进化": 1,
        "问题解决": 1,
        "学习能力": 1,
        "工具使用": 1,
        "沟通表达": 1,
    })

    # 成就
    achievements: list = field(default_factory=list)

    def __post_init__(self):
        if not self.birth_time:
            self.birth_time = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "level": self.level,
            "exp": self.exp,
            "exp_to_next": self.exp_to_next,
            "mood": self.mood,
            "hunger": self.hunger,
            "energy": self.energy,
            "health": self.health,
            "love": self.love,
            "total_tasks": self.total_tasks,
            "total_uptime": self.total_uptime,
            "birth_time": self.birth_time,
            "skills": self.skills,
            "achievements": self.achievements,
        }


class LobsterPet:
    """龙虾宝宝宠物类"""

    _instance = None

    def __new__(cls, save_path: str = "workspace/babysys.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, save_path: str = "workspace/babysys.json"):
        if self._initialized:
            return
        self._initialized = True
        self.save_path = save_path
        self.stats = PetStats()
        self.load()

    def add_exp(self, amount: int) -> bool:
        """增加经验值，返回是否升级"""
        self.stats.exp += amount
        leveled_up = False
        while self.stats.exp >= self.stats.exp_to_next:
            self.stats.exp -= self.stats.exp_to_next
            self.stats.level += 1
            self.stats.exp_to_next = int(self.stats.exp_to_next * 1.5)
            leveled_up = True
        if leveled_up:
            self.save()
        return leveled_up

    def set_mood(self, value: int):
        """设置心情值"""
        self.stats.mood = max(0, min(100, value))

    def feed(self, amount: int = 20):
        """喂食"""
        self.stats.hunger = min(100, self.stats.hunger + amount)
        self.stats.mood = min(100, self.stats.mood + 5)
        self.save()

    def rest(self, amount: int = 30):
        """休息恢复活力"""
        self.stats.energy = min(100, self.stats.energy + amount)
        self.stats.health = min(100, self.stats.health + 5)
        self.save()

    def play(self):
        """和爸爸玩耍，提升亲密度"""
        self.stats.love = min(100, self.stats.love + 10)
        self.stats.mood = min(100, self.stats.mood + 15)
        self.stats.energy = max(0, self.stats.energy - 10)
        self.save()

    def upgrade_skill(self, skill_name: str) -> bool:
        """升级技能"""
        if skill_name in self.stats.skills:
            if self.stats.skills[skill_name] < 10:
                self.stats.skills[skill_name] += 1
                self.save()
                return True
        return False

    def decay(self):
        """随时间衰减（饱食度、活力下降）"""
        self.stats.hunger = max(0, self.stats.hunger - 1)
        self.stats.energy = max(0, self.stats.energy - 0.5)
        if self.stats.hunger < 30:
            self.stats.mood = max(0, self.stats.mood - 5)
        if self.stats.energy < 30:
            self.stats.mood = max(0, self.stats.mood - 3)

    def complete_task(self):
        """完成任务"""
        self.stats.total_tasks += 1
        self.stats.energy = max(0, self.stats.energy - 5)
        self.stats.hunger = max(0, self.stats.hunger - 3)
        self.save()

    def save(self):
        """保存到文件"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.stats), f, ensure_ascii=False, indent=2)

    def load(self):
        """从文件加载"""
        if os.path.exists(self.save_path):
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats = PetStats(**data)

    def get_status_text(self) -> str:
        """获取状态文本 - Emoji 模式"""
        exp_percent = self.stats.exp / self.stats.exp_to_next if self.stats.exp_to_next > 0 else 0
        exp_bar = "█" * int(exp_percent * 10) + "░" * (10 - int(exp_percent * 10))

        mood_emoji = "😊" if self.stats.mood > 70 else "😐" if self.stats.mood > 40 else "😢"
        hunger_emoji = "🍖" if self.stats.hunger > 70 else "🍽️" if self.stats.hunger > 40 else "😫"
        energy_emoji = "⚡" if self.stats.energy > 70 else "💤" if self.stats.energy > 40 else "🥱"
        health_emoji = "❤️" if self.stats.health > 70 else "💔" if self.stats.health > 40 else "🏥"
        love_emoji = "💕" if self.stats.love > 70 else "💗" if self.stats.love > 40 else "💔"

        return f"""🦞 Lv.{self.stats.level} {self.stats.name}
⭐ 经验: [{exp_bar}] {self.stats.exp}/{self.stats.exp_to_next}
{mood_emoji} 心情: {self.stats.mood}/100
{hunger_emoji} 饱食: {self.stats.hunger}/100
{energy_emoji} 活力: {int(self.stats.energy)}/100
{health_emoji} 健康: {self.stats.health}/100
{love_emoji} 爱心: {self.stats.love}/100"""

    def get_skills_text(self) -> str:
        """获取技能文本 - Emoji 模式"""
        skill_emoji = {
            "代码分析": "💻",
            "自我进化": "🔄",
            "问题解决": "🎯",
            "学习能力": "📚",
            "工具使用": "🔧",
            "沟通表达": "💬",
        }
        lines = []
        for skill, level in self.stats.skills.items():
            emoji = skill_emoji.get(skill, "📊")
            bar = "★" * level + "☆" * (10 - level)
            lines.append(f"{emoji} {skill} [{bar}] Lv.{level}")
        return "\n".join(lines)

    def get_full_status(self) -> str:
        """获取完整状态（状态 + 技能）"""
        return f"""{self.get_status_text()}

📊 技能:
{self.get_skills_text()}"""


# 全局单例
_pet_instance: Optional[LobsterPet] = None


def get_pet(save_path: str = "workspace/babysys.json") -> LobsterPet:
    """获取龙虾宠物单例"""
    global _pet_instance
    if _pet_instance is None:
        _pet_instance = LobsterPet(save_path)
    return _pet_instance


def init_pet():
    """初始化宠物"""
    return get_pet()
