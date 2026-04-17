# -*- coding: utf-8 -*-
"""
日记系统

记录成长历程，支持情感分析
"""

from typing import Dict, Any, List
from datetime import datetime
from .base import PetSubsystem


class DiarySystem(PetSubsystem):
    """日记系统 - 记录成长历程"""

    # 情感关键词
    POSITIVE_WORDS = ["成功", "完成", "好", "棒", "开心", "学到了", "进步", "完美", "优秀", "胜利"]
    NEGATIVE_WORDS = ["失败", "错误", "问题", "困难", "累", "挫折", "Bug", "崩溃", "错误", "失败"]

    def add_entry(self, content: str, title: str = ""):
        """
        添加日记条目

        Args:
            content: 内容
            title: 标题（可选）
        """
        diary = self.pet.data.diary

        entry = self.pet.data.__class__.__bases__[0].__dataclass_fields__

        entry_obj = self.pet.data.__class__.__dataclass_fields__ if hasattr(self, 'entry') else None

        from ..models import DiaryEntry
        entry = DiaryEntry(
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            title=title or self._generate_title(content),
            content=content,
            sentiment=self._analyze_sentiment(content),
            token_count=self.pet.data.hunger.daily_tokens,
        )

        diary.entries.append(entry)
        diary.total_entries += 1

        # 保持最大条目数
        max_entries = self.config.diary.max_entries
        if len(diary.entries) > max_entries:
            diary.entries = diary.entries[-max_entries:]

    def _generate_title(self, content: str) -> str:
        """
        生成标题

        Args:
            content: 内容

        Returns:
            标题
        """
        # 简单实现：取内容前20个字符
        if len(content) > 20:
            return content[:20] + "..."
        return content

    def _analyze_sentiment(self, content: str) -> float:
        """
        情感分析

        Args:
            content: 内容

        Returns:
            情感分数 (-1 到 1)
        """
        score = 0.0
        for word in self.POSITIVE_WORDS:
            if word in content:
                score += 0.2
        for word in self.NEGATIVE_WORDS:
            if word in content:
                score -= 0.2

        return max(-1.0, min(1.0, score))

    def get_sentiment_emoji(self, sentiment: float) -> str:
        """
        获取情感表情

        Args:
            sentiment: 情感分数

        Returns:
            情感表情
        """
        if sentiment > 0.5:
            return "😊"
        elif sentiment > 0.2:
            return "🙂"
        elif sentiment > -0.2:
            return "😐"
        elif sentiment > -0.5:
            return "😢"
        return "😭"

    def get_recent_entries(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近的日记条目

        Args:
            days: 天数

        Returns:
            日记条目列表
        """
        from datetime import timedelta
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        return [
            {
                "date": e.date,
                "title": e.title,
                "sentiment": e.sentiment,
                "emoji": self.get_sentiment_emoji(e.sentiment),
            }
            for e in self.pet.data.diary.entries
            if e.date >= cutoff
        ]

    def get_recent_diary_text(self, days: int = 7) -> str:
        """
        获取最近日记文本

        Args:
            days: 天数

        Returns:
            日记文本
        """
        entries = self.get_recent_entries(days)
        if not entries:
            return "📔 还没有日记记录"

        lines = ["📔 最近日记:"]
        for e in entries:
            lines.append(f"   {e['emoji']} {e['date']} - {e['title']}")

        return "\n".join(lines)

    def get_average_sentiment(self, days: int = 7) -> float:
        """
        获取平均情感

        Args:
            days: 天数

        Returns:
            平均情感分数
        """
        entries = self.get_recent_entries(days)
        if not entries:
            return 0.0

        return sum(e["sentiment"] for e in entries) / len(entries)

    def get_status_text(self) -> str:
        """获取状态文本"""
        diary = self.pet.data.diary
        avg_sentiment = self.get_average_sentiment()

        return f"""
📔 日记: {diary.total_entries} 条记录
   最近情感: {self.get_sentiment_emoji(avg_sentiment)} ({avg_sentiment:+.2f})
   {'最近有记录' if diary.entries else '还没有记录'}
"""

    def get_status_dict(self) -> Dict[str, Any]:
        """获取状态字典"""
        diary = self.pet.data.diary
        return {
            "total_entries": diary.total_entries,
            "average_sentiment": self.get_average_sentiment(),
            "recent_entries": self.get_recent_entries(3),
        }
