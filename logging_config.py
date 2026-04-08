"""
日志配置模块

配置项目的日志记录格式和级别。
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """
    配置日志系统。

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 降低第三方库的日志级别，避免刷屏
    # httpx 只打印 WARNING 及以上（隐藏每个 HTTP 请求的 INFO 日志）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # langchain 只打印 WARNING 及以上
    logging.getLogger("langchain").setLevel(logging.WARNING)
    # openai 只打印 WARNING 及以上
    logging.getLogger("openai").setLevel(logging.WARNING)
    # httpcore 只打印 WARNING 及以上
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# 初始化默认日志配置
setup_logging()
