'''
网络工具模块

提供网页搜索和内容读取功能。
'''

import time
import json
from typing import List, Dict, Optional

# 尝试导入 requests，如果失败则使用内置 urllib
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    import urllib.request
    import urllib.parse


def web_search(query: str, max_results: int = 5) -> str:
    '''
    使用 DuckDuckGo 搜索引擎进行网络搜索
    
    Args:
        query: 搜索关键词
        max_results: 最大返回结果数
    
    Returns:
        搜索结果摘要
    '''
    if not REQUESTS_AVAILABLE:
        return "错误: requests 库未安装，请运行 'pip install requests'"
    
    try:
        # 使用 DuckDuckGo API
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取搜索结果
        results = []
        if 'RelatedTopics' in data and data['RelatedTopics']:
            for topic in data['RelatedTopics'][:max_results]:
                if 'Text' in topic:
                    results.append(topic['Text'])
        
        if not results and 'AbstractText' in data and data['AbstractText']:
            results.append(f"摘要: {data['AbstractText']}")
        
        if not results:
            results.append("未找到相关搜索结果")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"搜索失败: {str(e)}"


def read_webpage(url: str) -> str:
    '''
    读取指定网页的完整内容
    
    Args:
        url: 网页 URL
    
    Returns:
        网页正文内容
    '''
    if not REQUESTS_AVAILABLE:
        return "错误: requests 库未安装，请运行 'pip install requests'"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 简单的 HTML 清理
        content = response.text
        # 移除 script 和 style 标签
        import re
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # 提取 body 内容
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
        if body_match:
            content = body_match.group(1)
        # 移除其他 HTML 标签
        content = re.sub(r'<[^>]+>', '', content)
        # 清理空白字符
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content[:2000] + "..." if len(content) > 2000 else content
        
    except Exception as e:
        return f"读取网页失败: {str(e)}"

# 其他工具函数...
def extract_links(url: str) -> List[str]:
    '''提取网页中的链接'''
    return []
