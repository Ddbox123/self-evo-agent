# 简化日志配置
import logging

def setup_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(message)s'
    )
    return logging.getLogger()
