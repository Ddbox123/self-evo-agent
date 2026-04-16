# -*- coding: utf-8 -*-
"""
龙虾 ASCII 艺术库

提供可爱的龙虾宝宝 ASCII Art，用于 CLI 界面装饰。
所有 ASCII Art 使用统一宽度，确保对齐。
"""

from __future__ import annotations


# 龙虾宝宝 ASCII Art 集合
class LobsterASCII:
    """龙虾 ASCII Art 艺术库"""

    # 开心状态 - 紧凑版（适合状态面板）
    HAPPY = r"""
  (\ /)
  ( ^.^)
   >^<
  /| |\
  (_|_)
"""

    # 思考状态
    THINKING = r"""
  (\ /)
  ( ???)
   >?<
  /| |\
  (_|_)
"""

    # 工作状态
    WORKING = r"""
  (\ /)
  ( *.*)
   >~<
  /| |\
  (_|_)
"""

    # 睡觉状态
    SLEEPING = r"""
  (\ /)
  ( ---)
   >z<
  /| |\
  (_|_)
"""

    # 惊讶状态
    SURPRISED = r"""
  (\ /)
  ( O.O)
   >!<
  /| |\
  (_|_)
"""

    # 成功状态
    SUCCESS = r"""
  (\ /)
  ( ^o^)
   >v<
  /| |\
  (_|_)
"""

    # 错误状态
    SAD = r"""
  (\ /)
  ( T.T)
   >.<
  /| |\
  (_|_)
"""

    # 爱心龙虾
    LOVE = r"""
  (\ /)
  (<3<3)
   >^<
  /| |\
  (_|_)
"""

    # 龙虾 Banner - 左右分栏布局（龙虾在左，标题在右）
    BANNER = r"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                       ║
║   (\ /)                                                                                              ║
║   ( ^.^)    Self-Evolving Agent                                                                      ║
║    >^<      Terminal Edition v3.0                                                                    ║
║   /| |\                                                                                              ║
║   (_|_)                                                                                              ║
║                                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

    # 简洁 Banner（无龙虾，用于需要简单展示的场景）
    BANNER_SIMPLE = r"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                       ║
║                              Self-Evolving Agent                                                      ║
║                              Terminal Edition v3.0                                                     ║
║                                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

    # 龙虾装饰线
    DIVIDER = "─" * 80

    # 左右分栏布局
    @classmethod
    def get_two_column(cls, left: str, right: str, width: int = 70) -> str:
        """
        生成左右分栏内容

        Args:
            left: 左侧内容
            right: 右侧内容
            width: 总宽度

        Returns:
            格式化后的字符串
        """
        lines_left = left.strip().split('\n')
        lines_right = right.strip().split('\n')
        max_left = max(len(line) for line in lines_left) if lines_left else 0
        max_lines = max(len(lines_left), len(lines_right))

        result = []
        for i in range(max_lines):
            left_line = lines_left[i] if i < len(lines_left) else ""
            right_line = lines_right[i] if i < len(lines_right) else ""
            # 左对齐左侧，右对齐右侧
            result.append(left_line.ljust(max_left + 2) + right_line)

        return '\n'.join(result)

    @classmethod
    def get_status_art(cls, status: str) -> str:
        """
        根据状态获取对应的 ASCII Art

        Args:
            status: 状态名称

        Returns:
            对应的 ASCII Art
        """
        status_map = {
            "happy": cls.HAPPY,
            "thinking": cls.THINKING,
            "working": cls.WORKING,
            "sleeping": cls.SLEEPING,
            "surprised": cls.SURPRISED,
            "success": cls.SUCCESS,
            "sad": cls.SAD,
            "error": cls.SAD,
            "love": cls.LOVE,
        }
        return status_map.get(status.lower(), cls.HAPPY)

    @classmethod
    def get_banner(cls, name: str = "虾宝", version: str = "v3.0") -> str:
        """
        生成 Banner

        Args:
            name: 名称
            version: 版本

        Returns:
            格式化的 Banner 字符串
        """
        return cls.BANNER

    @classmethod
    def get_welcome_art(cls) -> str:
        """获取欢迎 ASCII Art"""
        return cls.HAPPY


# 全局常量 - 方便直接引用
LOBSTER_HAPPY = LobsterASCII.HAPPY
LOBSTER_THINKING = LobsterASCII.THINKING
LOBSTER_WORKING = LobsterASCII.WORKING
LOBSTER_SLEEPING = LobsterASCII.SLEEPING
LOBSTER_SURPRISED = LobsterASCII.SURPRISED
LOBSTER_SUCCESS = LobsterASCII.SUCCESS
LOBSTER_SAD = LobsterASCII.SAD
LOBSTER_LOVE = LobsterASCII.LOVE


def get_lobster_banner(name: str = "虾宝", version: str = "v3.0") -> str:
    """生成 Banner"""
    return LobsterASCII.get_banner(name, version)


def get_status_lobster(status: str) -> str:
    """根据状态获取龙虾"""
    return LobsterASCII.get_status_art(status)
