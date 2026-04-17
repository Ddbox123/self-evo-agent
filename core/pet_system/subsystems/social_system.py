# -*- coding: utf-8 -*-
"""
社交系统

多模型协作关系，好友系统
"""

from typing import Dict, Any, List
from datetime import datetime
from .base import PetSubsystem


class SocialSystem(PetSubsystem):
    """社交系统 - 多模型协作关系"""

    def meet_model(self, model_name: str):
        """
        遇见新模型

        Args:
            model_name: 模型名称
        """
        social = self.pet.data.social

        # 检查是否已认识
        for friend in social.friends:
            if friend.model_name == model_name:
                return

        # 检查是否超过最大好友数
        if len(social.friends) >= self.config.social.max_friends:
            # 移除友谊度最低的好友
            social.friends.sort(key=lambda x: x.friendship_level)
            social.friends.pop(0)

        # 添加新朋友
        from ..models import FriendData
        friend = FriendData(
            model_name=model_name,
            first_met=datetime.now().isoformat(),
        )
        social.friends.append(friend)

        # 播放声音
        self.pet.sound_system.play_sound("new_friend")

    def interact(self, model_name: str):
        """
        与模型互动

        Args:
            model_name: 模型名称
        """
        social = self.pet.data.social

        for friend in social.friends:
            if friend.model_name == model_name:
                friend.last_interaction = datetime.now().isoformat()
                friend.collaboration_count += 1

                # 增加友谊度
                friend.friendship_level = min(100,
                    friend.friendship_level + self.config.social.friendship_gain_rate)
                break

        social.total_interactions += 1

    def get_friendship_level_name(self, level: int) -> str:
        """
        获取友谊等级名称

        Args:
            level: 友谊度

        Returns:
            友谊等级名称
        """
        if level >= 80:
            return "挚友"
        elif level >= 60:
            return "好友"
        elif level >= 40:
            return "伙伴"
        elif level >= 20:
            return "认识"
        return "陌生人"

    def get_friendship_emoji(self, level: int) -> str:
        """
        获取友谊表情

        Args:
            level: 友谊度

        Returns:
            友谊表情
        """
        if level >= 80:
            return "💞"
        elif level >= 60:
            return "💕"
        elif level >= 40:
            return "💗"
        elif level >= 20:
            return "💛"
        return "🤍"

    def get_friends_list(self) -> List[Dict[str, Any]]:
        """
        获取好友列表

        Returns:
            好友列表
        """
        return sorted(
            self.pet.data.social.friends,
            key=lambda x: x.friendship_level,
            reverse=True
        )

    def get_friends_text(self, limit: int = 5) -> str:
        """
        获取好友列表文本

        Args:
            limit: 显示数量

        Returns:
            好友列表文本
        """
        friends = self.get_friends_list()[:limit]
        if not friends:
            return "🤝 还没有朋友，快去认识新模型吧！"

        lines = ["🤝 好友列表:"]
        for friend in friends:
            emoji = self.get_friendship_emoji(friend.friendship_level)
            name = self.get_friendship_level_name(friend.friendship_level)
            lines.append(f"   {emoji} {friend.model_name} - {name} ({friend.friendship_level}%)")

        return "\n".join(lines)

    def get_status_text(self) -> str:
        """获取状态文本"""
        social = self.pet.data.social
        friends = self.get_friends_list()

        if not friends:
            return f"""
🤝 社交: {social.total_interactions} 次互动
   {self.get_friends_text()}
"""

        best_friend = friends[0] if friends else None
        best_text = ""
        if best_friend:
            emoji = self.get_friendship_emoji(best_friend.friendship_level)
            best_text = f"   最佳好友: {emoji} {best_friend.model_name}\n"

        return f"""
🤝 社交: {len(friends)} 好友 | {social.total_interactions} 次互动
{best_text}{self.get_friends_text(3)}
"""

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        social = self.pet.data.social
        friends = self.get_friends_list()

        return {
            "friend_count": len(friends),
            "total_interactions": social.total_interactions,
            "best_friend": friends[0].model_name if friends else None,
            "friends": [
                {"name": f.model_name, "level": f.friendship_level}
                for f in friends[:5]
            ],
        }
