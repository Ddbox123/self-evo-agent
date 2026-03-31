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


# 初始化默认日志配置
setup_logging()
