# -*- coding: utf-8 -*-
"""
心跳系统

用 API 调用模拟心跳，可视化活跃状态
"""

from typing import Dict, Any
from datetime import datetime
from .base import PetSubsystem


class HeartSystem(PetSubsystem):
    """心跳系统 - 可视化活跃状态"""

    def __init__(self, pet_system):
        super().__init__(pet_system)
        self._last_active_check = datetime.now()

    def beat(self) -> Dict[str, Any]:
        """
        执行一次心跳

        Returns:
            心跳状态信息
        """
        heart = self.pet.data.heart
        heart.beat_count += 1
        heart.last_beat = datetime.now().isoformat()

        # 判断活跃状态
        if not heart.is_active:
            heart.is_active = True
            heart.active_since = datetime.now().isoformat()

        return {
            "rate": self.get_current_rate(),
            "is_active": heart.is_active,
            "beat_count": heart.beat_count,
        }

    def get_current_rate(self) -> float:
        """
        获取当前心跳频率

        Returns:
            心跳频率 (Hz)
        """
        heart = self.pet.data.heart
        if heart.is_active:
            return self.config.heart.active_rate
        return self.config.heart.idle_rate

    def check_idle(self) -> bool:
        """
        检查是否应该进入空闲状态

        Returns:
            是否应该进入空闲
        """
        if not self.pet.data.heart.is_active:
            return False

        if self.pet.data.heart.active_since:
            active_time = datetime.now() - datetime.fromisoformat(self.pet.data.heart.active_since)
            return active_time.total_seconds() > self.config.heart.cooldown_time * 10
        return False

    def start_idle(self):
        """进入空闲状态"""
        heart = self.pet.data.heart
        heart.is_active = False
        heart.active_since = None

    def get_heartbeat_animation(self) -> str:
        """
        获取心跳动画符号

        Returns:
            心跳符号
        """
        rate = self.get_current_rate()
        if rate > 1.5:
            return "<3"  # 快速跳动
        elif rate > 0.5:
            return "♥"  # 正常跳动
        return "♡"  # 缓慢跳动

    def get_active_duration(self) -> float:
        """
        获取活跃持续时间

        Returns:
            活跃时间（秒）
        """
        heart = self.pet.data.heart
        if not heart.active_since:
            return 0.0

        active_time = datetime.now() - datetime.fromisoformat(heart.active_since)
        return active_time.total_seconds()

    def get_status_text(self) -> str:
        """获取状态文本"""
        heart = self.pet.data.heart
        animation = self.get_heartbeat_animation()

        if heart.is_active:
            duration = self.get_active_duration()
            return f"{animation} 活跃中 ({int(duration)}s) | 累计心跳 {heart.beat_count}"
        return f"{animation} 休眠中 | 累计心跳 {heart.beat_count}"

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        heart = self.pet.data.heart
        return {
            "is_alive": heart.is_alive,
            "is_active": heart.is_active,
            "beat_count": heart.beat_count,
            "current_rate": self.get_current_rate(),
            "active_duration": self.get_active_duration(),
        }
