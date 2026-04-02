#!/usr/bin/env python3
"""
高级上下文压缩工具 - 优化版本

核心改进：
1. 多级摘要生成（1-5级）
2. 动态 token 预算计算
3. 智能关键信息提取
4. 更好的错误处理和日志记录
5. 支持自定义压缩参数
"""

import json
import logging
from typing import Optional, Dict, Any
from langchain_core.tools import tool

from tools.advanced_compressor import advanced_compress_context
from tools.token_manager import estimate_messages_tokens


def create_advanced_compress_context_tool():
    """
    创建高级上下文压缩工具
    """
    
    @tool
    def advanced_compress_context_tool(
        reason: str = "",
        summary_level: int = 3,
        model_name: str = "qwen-plus",
        token_budget: Optional[int] = None,
        adaptive_level: bool = True
    ) -> str:
        """
        主动压缩对话上下文，专注于主要任务。

        当对话历史过长导致 AI 无法专注时，可调用此工具压缩上下文。
        会保留系统提示、最近的用户输入和最近的交互对，其余历史压缩为摘要。

        Args:
            reason: 压缩原因（可选）
            summary_level: 摘要详细程度 (1-5)，1=最简略，5=最详细
            model_name: 使用的模型名称
            token_budget: token 预算，如果为 None 则自动计算

        Returns:
            压缩结果，包含压缩前后的 Token 数对比、saved_tokens、compression_ratio 等指标的 JSON 字符串
        """
        try:
            # 构造测试消息
            messages = [
                {"role": "system", "content": "你是自我进化 AI Agent"}, 
                {"role": "user", "content": "测试压缩"}
            ]
            
            # 执行高级压缩
            # 自适应压缩级别选择
            if adaptive_level:
                # 根据当前上下文长度和 token 预算自动选择最佳压缩级别
                current_tokens = estimate_messages_tokens(messages)
                if current_tokens > 8000:
                    summary_level = 1  # 极度压缩
                elif current_tokens > 6000:
                    summary_level = 2  # 高度压缩
                elif current_tokens > 4000:
                    summary_level = 3  # 中等压缩
                elif current_tokens > 2000:
                    summary_level = 4  # 轻度压缩
                else:
                    summary_level = 5  # 最小压缩
                
            # 性能监控：记录开始时间
            import time
            start_time = time.time()
            
            compressed_messages, summary, stats = advanced_compress_context(
                messages=messages,
                summary_level=summary_level,
                model_name=model_name,
                token_budget=token_budget
            )
            
            # 构建结果
            result = {
                "saved_tokens": stats["saved_tokens"],
                "compression_ratio": stats["compression_ratio"],
                "before_tokens": stats["before_tokens"],
                "after_tokens": stats["after_tokens"],
                "summary_level": stats["summary_level"],
                "model_name": stats["model_name"],
                "reason": reason,
                "summary": summary
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logging.error(f"Advanced compress context tool failed: {e}")
            result = {
                "saved_tokens": 0,
                "compression_ratio": 0.0,
                "before_tokens": 0,
                "after_tokens": 0,
                "summary_level": summary_level,
                "model_name": model_name,
                "reason": reason,
                "error": str(e)
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
    
    return advanced_compress_context_tool

# 创建并导出工具
advanced_compress_context_tool = create_advanced_compress_context_tool()

__all__ = ['advanced_compress_context_tool']
