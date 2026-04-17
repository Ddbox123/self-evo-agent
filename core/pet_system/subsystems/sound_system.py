# -*- coding: utf-8 -*-
"""
声音系统

情绪反馈，声音系统
"""

from typing import Dict, Any, Optional
from .base import PetSubsystem


class SoundSystem(PetSubsystem):
    """声音系统 - 情绪反馈"""

    # 心情 → 声音映射
    MOOD_SOUNDS = {
        "happy": "♪~ ♪~ ♪",
        "excited": "♪♪♪♪♪",
        "neutral": "♪",
        "sad": "♪...",
        "hungry": "肚肚~",
        "sleepy": "呼~ 呼~",
    }

    # 动作 → 声音映射
    ACTION_SOUNDS = {
        "eating": "好吃好吃！",
        "sleeping": "zzZ",
        "level_up": "升级啦！✨",
        "new_friend": "交到新朋友啦！",
        "achieve": "获得成就！🎉",
        "start": "启动啦~",
        "idle": "...",
    }

    # 声音描述
    SOUND_DESCRIPTIONS = {
        "eating": "进食",
        "sleeping": "睡眠",
        "level_up": "升级",
        "new_friend": "交友",
        "achieve": "成就",
        "start": "启动",
        "idle": "空闲",
    }

    def play_sound(self, sound_type: str) -> Optional[str]:
        """
        播放声音

        Args:
            sound_type: 声音类型

        Returns:
            播放的声音文本
        """
        sound = self.pet.data.sound
        if not sound.sound_enabled:
            return None

        if self.config.sound.action_sounds and sound_type in self.ACTION_SOUNDS:
            sound.last_sound = self.ACTION_SOUNDS[sound_type]
        elif self.config.sound.mood_sounds:
            mood = self._get_current_mood()
            sound.last_sound = self.MOOD_SOUNDS.get(mood, "♪")

        return sound.last_sound

    def _get_current_mood(self) -> str:
        """
        获取当前心情

        Returns:
            心情状态
        """
        if self.pet.data.dream.in_dream:
            return "sleepy"

        hunger = self.pet.data.attributes.hunger
        if hunger < 30:
            return "hungry"

        mood = self.pet.data.attributes.mood
        if mood > 80:
            return "happy"
        elif mood > 60:
            return "neutral"
        elif mood > 40:
            return "sad"
        else:
            return "excited"

    def get_mood_sound(self) -> str:
        """
        获取心情声音

        Returns:
            心情声音
        """
        mood = self._get_current_mood()
        return self.MOOD_SOUNDS.get(mood, "♪")

    def set_volume(self, volume: float):
        """
        设置音量

        Args:
            volume: 音量 (0-1)
        """
        self.config.sound.volume = max(0.0, min(1.0, volume))

    def toggle_sound(self, enabled: bool = None):
        """
        切换声音开关

        Args:
            enabled: 是否启用（None 表示切换）
        """
        if enabled is None:
            self.pet.data.sound.sound_enabled = not self.pet.data.sound.sound_enabled
        else:
            self.pet.data.sound.sound_enabled = enabled

    def get_status_text(self) -> str:
        """获取状态文本"""
        sound = self.pet.data.sound
        last_sound = sound.last_sound or "无"

        enabled_text = "开启" if sound.sound_enabled else "关闭"
        volume_text = f"{int(self.config.sound.volume * 100)}%"

        return f"""
🔊 声音: {enabled_text} | 音量: {volume_text}
   当前: {last_sound}
"""

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        sound = self.pet.data.sound
        return {
            "sound_enabled": sound.sound_enabled,
            "volume": self.config.sound.volume,
            "last_sound": sound.last_sound,
            "mood_sound": self.get_mood_sound(),
        }
