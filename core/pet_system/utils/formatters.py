# -*- coding: utf-8 -*-
"""
格式化工具

提供宠物状态的各种格式化输出
"""

from typing import Dict, Any


class StatusFormatter:
    """状态格式化工具"""

    @staticmethod
    def format_exp_bar(exp: int, exp_to_next: int, length: int = 10) -> str:
        """格式化经验条"""
        if exp_to_next <= 0:
            return "░" * length
        percent = exp / exp_to_next
        filled = int(percent * length)
        return "█" * filled + "░" * (length - filled)

    @staticmethod
    def get_mood_emoji(mood: int) -> str:
        """根据心情值获取表情"""
        if mood > 80:
            return "😊"
        elif mood > 60:
            return "🙂"
        elif mood > 40:
            return "😐"
        elif mood > 20:
            return "😢"
        return "😭"

    @staticmethod
    def get_hunger_emoji(hunger: int) -> str:
        """根据饱食度获取表情"""
        if hunger > 70:
            return "🍖"
        elif hunger > 40:
            return "🍽️"
        elif hunger > 20:
            return "🥺"
        return "😫"

    @staticmethod
    def get_energy_emoji(energy: int) -> str:
        """根据活力值获取表情"""
        if energy > 70:
            return "⚡"
        elif energy > 40:
            return "💤"
        return "🥱"

    @staticmethod
    def get_health_emoji(health: int) -> str:
        """根据健康值获取表情"""
        if health > 70:
            return "❤️"
        elif health > 40:
            return "💔"
        return "🏥"

    @staticmethod
    def get_love_emoji(love: int) -> str:
        """根据亲密度获取表情"""
        if love > 70:
            return "💕"
        elif love > 40:
            return "💗"
        return "💔"

    @staticmethod
    def get_heartbeat_emoji(is_active: bool, rate: float = 1.0) -> str:
        """根据心跳状态获取表情"""
        if is_active:
            if rate > 1.5:
                return "<3"
            return "♥"
        return "♡"

    @staticmethod
    def get_personality_desc(traits: Dict[str, float]) -> str:
        """获取性格描述"""
        if not traits:
            return "均衡发展"

        dominant = max(traits.items(), key=lambda x: x[1])
        descriptions = {
            "rational": "理性冷静",
            "creative": "创意无限",
            "cautious": "谨慎小心",
            "bold": "勇敢大胆",
            "social": "善于社交",
            "solitary": "独立自主",
        }
        return descriptions.get(dominant[0], "均衡发展")

    @staticmethod
    def get_food_level_emoji(hunger: int) -> str:
        """获取食物等级"""
        if hunger > 70:
            return "🍖 饱饱"
        elif hunger > 40:
            return "🍽️ 刚好"
        elif hunger > 20:
            return "🥺 饿了"
        return "😫 饥饿"

    @staticmethod
    def get_skin_rarity_emoji(rarity: str) -> str:
        """获取皮肤稀有度表情"""
        emojis = {
            "common": "⚪",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡",
        }
        return emojis.get(rarity, "⚪")


class Formatters:
    """格式化工具集合"""

    status = StatusFormatter()

    @classmethod
    def format_number(cls, num: int) -> str:
        """格式化数字（添加千位分隔符）"""
        return f"{num:,}"

    @classmethod
    def format_percentage(cls, value: int, total: int) -> str:
        """格式化百分比"""
        if total <= 0:
            return "0%"
        return f"{int(value / total * 100)}%"
