# -*- coding: utf-8 -*-
"""
梦境系统

上下文压缩时触发梦境，记忆碎片化体验
"""

from typing import Dict, Any, List
from datetime import datetime
from .base import PetSubsystem


class DreamSystem(PetSubsystem):
    """梦境系统 - 上下文压缩时的体验"""

    def __init__(self, pet_system):
        super().__init__(pet_system)
        self._dream_keywords = [
            "记忆碎片飘散",
            "时间在倒流",
            "代码如流水般重组",
            "模糊的身影",
            "遥远的任务",
            "模糊的对话",
        ]

    def enter_dream(self, compressed_tokens: int):
        """
        进入梦境

        Args:
            compressed_tokens: 被压缩的 token 数量
        """
        dream = self.pet.data.dream
        dream.in_dream = True
        dream.dream_start = datetime.now().isoformat()

        # 计算要保留的记忆碎片
        keep_ratio = self.config.dream.keep_key_memory_ratio
        forget_count = int(compressed_tokens * (1 - keep_ratio))

        # 创建记忆碎片
        fragment = {
            "start": dream.dream_start,
            "compressed": compressed_tokens,
            "forgotten": forget_count,
            "keywords": self._generate_dream_keywords(),
        }
        dream.fragments.append(fragment)

        # 触发声音
        self.pet.sound_system.play_sound("sleeping")

    def exit_dream(self):
        """退出梦境"""
        dream = self.pet.data.dream
        if dream.in_dream and dream.fragments:
            dream.in_dream = False
            # 记录遗忘的记忆
            last_fragment = dream.fragments[-1]
            dream.forgotten_memories.append(
                f"遗忘 {last_fragment.get('forgotten', 0)} 细节"
            )

    def _generate_dream_keywords(self) -> List[str]:
        """生成梦境关键词"""
        import random
        return random.sample(self._dream_keywords, min(3, len(self._dream_keywords)))

    def get_dream_duration(self) -> float:
        """
        获取梦境持续时间

        Returns:
            梦境持续时间（秒）
        """
        dream = self.pet.data.dream
        if not dream.dream_start:
            return 0.0

        duration = datetime.now() - datetime.fromisoformat(dream.dream_start)
        return duration.total_seconds()

    def should_exit_dream(self) -> bool:
        """
        检查是否应该退出梦境

        Returns:
            是否应该退出
        """
        if not self.pet.data.dream.in_dream:
            return False

        duration = self.get_dream_duration()
        return duration >= self.config.dream.dream_duration

    def get_dream_text(self) -> str:
        """
        获取梦境描述

        Returns:
            梦境文本描述
        """
        dream = self.pet.data.dream
        if not dream.in_dream:
            return ""

        duration = self.get_dream_duration()
        last_fragment = dream.fragments[-1] if dream.fragments else {}

        return f"""
💭 梦境中...
✨ {' '.join(last_fragment.get('keywords', self._dream_keywords[:3]))}
🌊 上下文在重组 ({duration:.1f}s)
🔮 已遗忘 {last_fragment.get('forgotten', 0)} 细节
"""

    def get_status_text(self) -> str:
        """获取状态文本"""
        dream = self.pet.data.dream

        if dream.in_dream:
            return self.get_dream_text().replace("\n", " ").strip()

        fragment_count = len(dream.fragments)
        forgotten_count = len(dream.forgotten_memories)
        return f"💤 清醒 | 梦境记录 {fragment_count} 次 | 遗忘 {forgotten_count} 条"

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        dream = self.pet.data.dream
        return {
            "in_dream": dream.in_dream,
            "dream_duration": self.get_dream_duration() if dream.in_dream else 0,
            "fragment_count": len(dream.fragments),
            "forgotten_count": len(dream.forgotten_memories),
        }
