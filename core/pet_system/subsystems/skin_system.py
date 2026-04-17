# -*- coding: utf-8 -*-
"""
装扮系统

成就解锁外观，皮肤系统
"""

from typing import Dict, Any, List
from .base import PetSubsystem


class SkinSystem(PetSubsystem):
    """装扮系统 - 成就解锁外观"""

    # 成就 → 皮肤映射
    ACHIEVEMENT_SKINS = {
        "first_task": {"skin": "starter", "rarity": "common", "name": "初学者"},
        "code_master": {"skin": "coder", "rarity": "rare", "name": "代码大师"},
        "helper": {"skin": "helper", "rarity": "rare", "name": "小助手"},
        "explorer": {"skin": "explorer", "rarity": "epic", "name": "探索者"},
        "legendary": {"skin": "legendary", "rarity": "legendary", "name": "传奇"},
        "daily_100": {"skin": "daily_100", "rarity": "common", "name": "百日打卡"},
        "level_10": {"skin": "level_10", "rarity": "rare", "name": "十级进阶"},
        "social_butterfly": {"skin": "social", "rarity": "epic", "name": "社交达人"},
        "night_owl": {"skin": "night_owl", "rarity": "rare", "name": "夜猫子"},
        "workaholic": {"skin": "workaholic", "rarity": "epic", "name": "工作狂人"},
    }

    # 稀有度配置
    RARITY_CONFIGS = {
        "common": {"color": "⚪", "glow": False, "name": "普通"},
        "rare": {"color": "🔵", "glow": False, "name": "稀有"},
        "epic": {"color": "🟣", "glow": True, "name": "史诗"},
        "legendary": {"color": "🟡", "glow": True, "name": "传说"},
    }

    def check_achievement(self, achievement_id: str) -> bool:
        """
        检查成就并解锁皮肤

        Args:
            achievement_id: 成就 ID

        Returns:
            是否解锁了新成就
        """
        # 检查是否已获得
        if achievement_id in self.pet.data.attributes.achievements:
            return False

        # 记录成就
        self.pet.data.attributes.achievements.append(achievement_id)

        # 解锁皮肤
        if achievement_id in self.ACHIEVEMENT_SKINS:
            skin_info = self.ACHIEVEMENT_SKINS[achievement_id]
            self.unlock_skin(skin_info["skin"], skin_info["rarity"])

        # 播放声音
        self.pet.sound_system.play_sound("achieve")

        return True

    def unlock_skin(self, skin_id: str, rarity: str):
        """
        解锁皮肤

        Args:
            skin_id: 皮肤 ID
            rarity: 稀有度
        """
        skin = self.pet.data.skin
        if skin_id not in skin.unlocked_skins:
            skin.unlocked_skins.append(skin_id)

        # 如果是新解锁的稀有皮肤，设置为当前
        if rarity in ["epic", "legendary"]:
            skin.current_skin = skin_id
            skin.skin_rarity = rarity

    def equip_skin(self, skin_id: str) -> bool:
        """
        装备皮肤

        Args:
            skin_id: 皮肤 ID

        Returns:
            是否成功装备
        """
        skin = self.pet.data.skin
        if skin_id in skin.unlocked_skins:
            skin.current_skin = skin_id

            # 更新稀有度
            for ach_id, info in self.ACHIEVEMENT_SKINS.items():
                if info["skin"] == skin_id:
                    skin.skin_rarity = info["rarity"]
                    break

            return True
        return False

    def get_skin_info(self, skin_id: str) -> Dict[str, Any]:
        """
        获取皮肤信息

        Args:
            skin_id: 皮肤 ID

        Returns:
            皮肤信息
        """
        for ach_id, info in self.ACHIEVEMENT_SKINS.items():
            if info["skin"] == skin_id:
                return {
                    "id": skin_id,
                    "name": info["name"],
                    "rarity": info["rarity"],
                    "rarity_info": self.RARITY_CONFIGS.get(info["rarity"], {}),
                }
        return {"id": skin_id, "name": skin_id, "rarity": "common", "rarity_info": self.RARITY_CONFIGS["common"]}

    def get_rarity_emoji(self, rarity: str) -> str:
        """
        获取稀有度表情

        Args:
            rarity: 稀有度

        Returns:
            稀有度表情
        """
        return self.RARITY_CONFIGS.get(rarity, {}).get("color", "⚪")

    def get_status_text(self) -> str:
        """获取状态文本"""
        skin = self.pet.data.skin
        current_info = self.get_skin_info(skin.current_skin)
        rarity_emoji = self.get_rarity_emoji(skin.skin_rarity)

        unlocked_count = len(skin.unlocked_skins)
        total_skins = len(self.ACHIEVEMENT_SKINS)

        return f"""
👗 装扮: {rarity_emoji} {current_info['name']}
   已解锁: {unlocked_count}/{total_skins} 款皮肤
   稀有度: {self.RARITY_CONFIGS.get(skin.skin_rarity, {}).get('name', '普通')}
"""

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        skin = self.pet.data.skin
        return {
            "current_skin": skin.current_skin,
            "skin_rarity": skin.skin_rarity,
            "unlocked_skins": skin.unlocked_skins,
            "unlocked_count": len(skin.unlocked_skins),
        }
