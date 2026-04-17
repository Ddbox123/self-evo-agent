# -*- coding: utf-8 -*-
"""
性格系统

根据使用模式养成性格
"""

from typing import Dict, Any
from datetime import datetime
from .base import PetSubsystem


class PersonalitySystem(PetSubsystem):
    """性格系统 - 根据使用模式养成"""

    # 行为 → 性格映射
    BEHAVIOR_TRAIT_MAP = {
        "code_analysis": {"rational": 0.2},
        "code_generation": {"rational": 0.2, "creative": 0.1},
        "refactoring": {"rational": 0.3, "cautious": 0.2},
        "debugging": {"cautious": 0.3, "rational": 0.2},
        "creative_writing": {"creative": 0.3},
        "chat": {"social": 0.2},
        "problem_solving": {"bold": 0.2, "rational": 0.1},
        "data_analysis": {"rational": 0.3},
        "planning": {"cautious": 0.2, "rational": 0.2},
        "learning": {"rational": 0.2, "creative": 0.1},
    }

    # 性格描述
    TRAIT_DESCRIPTIONS = {
        "rational": "理性冷静",
        "creative": "创意无限",
        "cautious": "谨慎小心",
        "bold": "勇敢大胆",
        "social": "善于社交",
        "solitary": "独立自主",
    }

    def record_behavior(self, behavior_type: str):
        """
        记录行为，影响性格

        Args:
            behavior_type: 行为类型
        """
        personality = self.pet.data.personality

        # 添加历史
        personality.behavior_history.append({
            "type": behavior_type,
            "time": datetime.now().isoformat(),
        })

        # 保持窗口大小
        window = self.config.personality.learning_window
        if len(personality.behavior_history) > window:
            personality.behavior_history = personality.behavior_history[-window:]

        # 更新性格
        if behavior_type in self.BEHAVIOR_TRAIT_MAP:
            changes = self.BEHAVIOR_TRAIT_MAP[behavior_type]
            rate = self.config.personality.trait_change_rate

            for trait, delta in changes.items():
                if trait in personality.traits:
                    change = delta * rate * 100
                    personality.traits[trait] = max(0, min(100,
                        personality.traits[trait] + change
                    ))

            # 归一化性格值
            self._normalize_traits(personality.traits)

    def _normalize_traits(self, traits: Dict[str, float]):
        """归一化性格值"""
        total = sum(traits.values())
        if total > 0:
            for key in traits:
                traits[key] = (traits[key] / total) * 300  # 保持总和为300

    def get_dominant_trait(self) -> str:
        """
        获取主要性格

        Returns:
            主要性格名称
        """
        traits = self.pet.data.personality.traits
        if not traits:
            return "neutral"

        dominant = max(traits.items(), key=lambda x: x[1])
        return dominant[0]

    def get_personality_text(self) -> str:
        """
        获取性格描述

        Returns:
            性格描述文本
        """
        dominant = self.get_dominant_trait()
        return self.TRAIT_DESCRIPTIONS.get(dominant, "均衡发展")

    def get_trait_bar(self, trait_name: str) -> str:
        """
        获取性格条形图

        Args:
            trait_name: 性格名称

        Returns:
            条形图字符串
        """
        traits = self.pet.data.personality.traits
        value = traits.get(trait_name, 50)
        bar_length = int(value / 10)
        return "▓" * bar_length + "░" * (10 - bar_length)

    def get_status_text(self) -> str:
        """获取状态文本"""
        traits = self.pet.data.personality.traits
        dominant = self.get_dominant_trait()
        dominant_desc = self.TRAIT_DESCRIPTIONS.get(dominant, "均衡发展")

        lines = [f"🎭 性格: {dominant_desc}"]
        for trait, value in sorted(traits.items(), key=lambda x: -x[1])[:3]:
            bar = self.get_trait_bar(trait)
            desc = self.TRAIT_DESCRIPTIONS.get(trait, trait)
            lines.append(f"   {desc}: [{bar}] {int(value)}")

        return "\n".join(lines)

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        personality = self.pet.data.personality
        return {
            "traits": personality.traits,
            "dominant_trait": self.get_dominant_trait(),
            "behavior_count": len(personality.behavior_history),
        }
