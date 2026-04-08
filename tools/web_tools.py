"""
网络工具模块

提供网页搜索和内容读取功能（基于 CLI curl）。
"""

import subprocess
import json
import urllib.parse
from typing import List, Dict, Optional


def web_search(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索引擎进行网络搜索

    通过 CLI (curl) 执行 HTTP 请求。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数

    Returns:
        搜索结果摘要
    """
    try:
        import subprocess
        import json
        import urllib.parse

        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"

        cmd = f'curl -s -A "Mozilla/5.0" "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            return f"搜索请求失败: {result.stderr or '未知错误'}"

        data = json.loads(result.stdout)

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

    except subprocess.TimeoutExpired:
        return "搜索超时，请稍后重试"
    except json.JSONDecodeError:
        return "搜索结果解析失败"
    except Exception as e:
        return f"搜索失败: {str(e)}"


def read_webpage(url: str) -> str:
    """
    读取指定网页的完整内容

    通过 CLI (curl) 获取网页。

    Args:
        url: 网页 URL

    Returns:
        网页正文内容
    """
    import re

    try:
        cmd = f'curl -s -L -A "Mozilla/5.0" "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            return f"读取网页失败: {result.stderr or '未知错误'}"

        content = result.stdout

        # 简单的 HTML 清理
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
        if body_match:
            content = body_match.group(1)
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()

        return content[:2000] + "..." if len(content) > 2000 else content

    except subprocess.TimeoutExpired:
        return "读取超时，请稍后重试"
    except Exception as e:
        return f"读取网页失败: {str(e)}"

# 其他工具函数...
def extract_links(url: str) -> List[str]:
    '''提取网页中的链接'''
    return []
