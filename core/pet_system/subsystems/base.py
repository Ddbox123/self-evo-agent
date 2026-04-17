# -*- coding: utf-8 -*-
"""
子系统基类

所有宠物子系统的基类，提供通用接口
"""

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ..pet_system import PetSystem


class PetSubsystem:
    """宠物子系统基类"""

    def __init__(self, pet_system: 'PetSystem'):
        """
        初始化子系统

        Args:
            pet_system: 宠物系统实例
        """
        self.pet = pet_system
        self.config = pet_system.config
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """设置启用状态"""
        self._enabled = value

    def update(self, delta_time: float = 0):
        """
        每帧/定时更新

        Args:
            delta_time: 距离上次更新的时间（秒）
        """
        pass

    def get_status_text(self) -> str:
        """获取状态文本"""
        return ""

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        return {}

    def reset(self):
        """重置子系统"""
        pass
