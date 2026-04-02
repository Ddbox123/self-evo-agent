from tools.token_manager import create_compressor
from tools.token_manager import estimate_messages_tokens
import json

# 创建压缩器
compressor = create_compressor()

# 构造测试消息
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 构造测试消息
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 构造测试消息（更长的内容来触发压缩）
messages = [
    SystemMessage(content='你是自我进化 AI Agent，一个能够自我进化的高级AI系统，具备代码编辑、网络搜索、自我重启等能力。你的核心任务是完成用户的指令，并不断提升自己的能力。'), 
    HumanMessage(content='请帮我分析一下当前的 compress_context_tool 工具是否正常工作，它应该返回包含 saved_tokens 和 compression_ratio 的结构化 JSON 输出。'),
    AIMessage(content='我已经检查了 compress_context_tool 的实现，它确实会返回包含 saved_tokens 和 compression_ratio 的 JSON 结构。让我创建一个测试来验证这个功能。'),
    HumanMessage(content='很好，请继续执行测试并报告结果。'),
    AIMessage(content='正在执行测试...')
]

print('原始消息:', messages)

# 执行压缩
try:
    compressed_messages, summary = compressor.compress(messages)
    
    # 计算 token 数
    before_tokens = estimate_messages_tokens(messages)
    after_tokens = estimate_messages_tokens(compressed_messages)
    
    saved_tokens = before_tokens - after_tokens if before_tokens > after_tokens else 0
    compression_ratio = (before_tokens - after_tokens) / before_tokens if before_tokens > 0 else 0
    
    result = {
        'saved_tokens': saved_tokens,
        'compression_ratio': round(compression_ratio, 4),
        'before_tokens': before_tokens,
        'after_tokens': after_tokens,
        'summary': summary,
        'status': 'success'
    }
    
    print('压缩结果:', json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    print('压缩失败:', str(e))
