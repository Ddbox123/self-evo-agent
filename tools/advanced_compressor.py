#!/usr/bin/env python3
"""
高级 Token 压缩器 - 优化版本

核心改进：
1. 动态 token 预算计算
2. 多级摘要生成（1-5级）
3. 智能关键信息提取
4. 更好的错误处理和日志记录
"""

import json
import logging
from typing import List, Tuple, Any, Optional
from tools.token_manager import EnhancedTokenCompressor, estimate_messages_tokens


def create_advanced_compressor(
    token_budget: int = None,
    summary_level: int = 3,
    model_name: str = "qwen-plus"
) -> EnhancedTokenCompressor:
    """
    创建高级压缩器实例
    
    Args:
        token_budget: token 预算，如果为 None 则根据模型自动计算
        summary_level: 摘要详细程度 (1-5)，1=最简略，5=最详细
        model_name: 模型名称，用于调整压缩策略
    
    Returns:
        EnhancedTokenCompressor 实例
    """
    # 根据模型自动计算 token 预算
    if token_budget is None:
        if "qwen" in model_name.lower():
            token_budget = 4096
        elif "gpt" in model_name.lower():
            token_budget = 8192
        else:
            token_budget = 4096
    
    # 根据摘要级别调整压缩参数
    compression_params = {
        1: {"max_chars": 200, "keep_recent": 1},
        2: {"max_chars": 400, "keep_recent": 2},
        3: {"max_chars": 800, "keep_recent": 3},
        4: {"max_chars": 1200, "keep_recent": 4},
        5: {"max_chars": 2000, "keep_recent": 5}
    }
    
    params = compression_params.get(summary_level, compression_params[3])
    
    return EnhancedTokenCompressor(
        token_budget=token_budget,
        max_summary_chars=params["max_chars"],
        keep_recent_messages=params["keep_recent"]
    )


def advanced_compress_context(
    messages: List[Any],
    summary_level: int = 3,
    model_name: str = "qwen-plus",
    token_budget: int = None
) -> Tuple[List[Any], str, dict]:
    """
    执行高级压缩
    
    Args:
        messages: 原始消息列表
        summary_level: 摘要级别 (1-5)
        model_name: 模型名称
        token_budget: token 预算
    
    Returns:
        (压缩后的消息, 摘要, 统计信息)
    """
    try:
        # 创建高级压缩器
        compressor = create_advanced_compressor(
            token_budget=token_budget,
            summary_level=summary_level,
            model_name=model_name
        )
        
        # 执行压缩
        compressed_messages, summary = compressor.compress(messages)
        
        # 计算统计信息
        before_tokens = estimate_messages_tokens(messages)
        after_tokens = estimate_messages_tokens(compressed_messages)
        
        saved_tokens = before_tokens - after_tokens
        compression_ratio = saved_tokens / before_tokens if before_tokens > 0 else 0
        
        stats = {
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "saved_tokens": saved_tokens,
            "compression_ratio": round(compression_ratio, 4),
            "summary_level": summary_level,
            "model_name": model_name
        }
        
        return compressed_messages, summary, stats
        
    except Exception as e:
        logging.error(f"Advanced compression failed: {e}")
        # 回退到基础压缩
        from tools.token_manager import create_compressor
        compressor = create_compressor(token_budget=4096)
        compressed_messages, summary = compressor.compress(messages)
        
        before_tokens = estimate_messages_tokens(messages)
        after_tokens = estimate_messages_tokens(compressed_messages)
        
        saved_tokens = before_tokens - after_tokens
        compression_ratio = saved_tokens / before_tokens if before_tokens > 0 else 0
        
        stats = {
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "saved_tokens": saved_tokens,
            "compression_ratio": round(compression_ratio, 4),
            "summary_level": summary_level,
            "model_name": model_name,
            "error": str(e)
        }
        
        return compressed_messages, summary, stats

# 导出函数
__all__ = ['create_advanced_compressor', 'advanced_compress_context']
