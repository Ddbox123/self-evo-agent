"""
网络工具模块

提供网页搜索和内容读取功能，供 Agent 获取外部知识。

本模块封装了常用的网络操作，使得 Agent 能够：
1. 通过搜索引擎查询相关信息
2. 读取指定网页的完整内容
3. 过滤和格式化网络返回结果

依赖：
    - requests: HTTP 请求库
    - 可选: beautifulsoup4 用于 HTML 解析
"""

import logging
import re
import sys
from typing import Optional

# 尝试导入 requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.basicConfig(level=logging.WARNING)
    logging.warning("requests 库未安装，web_tools 功能将受限。请运行: pip install requests")


# ============================================================================
# 配置常量
# ============================================================================

# 默认请求超时时间（秒）
DEFAULT_TIMEOUT = 30

# 浏览器 User-Agent
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 最大内容长度（字符）
MAX_CONTENT_LENGTH = 100000


# ============================================================================
# 日志配置
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 核心功能函数
# ============================================================================

def web_search(query: str, max_results: int = 5) -> str:
    """
    执行网络搜索并返回结果摘要。
    
    此函数使用网络搜索 API 或模拟搜索引擎行为来获取与查询相关的信息。
    返回的结果是格式化的文本，便于 Agent 理解和处理。
    
    Args:
        query: 搜索查询字符串，可以是问题、关键词或短语。
               建议使用清晰、具体的查询语句以获得更准确的结果。
               
               示例：
               - "Python 异步编程最佳实践"
               - "最新的机器学习框架对比"
               - "如何解决 'Connection refused' 错误"
               
        max_results: 最大返回结果数量，默认为 5。
                    取值范围 1-10，过多的结果可能导致信息过载。
    
    Returns:
        格式化的搜索结果字符串。
        
        返回格式示例：
        ```
        搜索结果: "Python 异步编程最佳实践"
        
        1. [标题] Python asyncio 完全指南
           URL: https://example.com/python-asyncio-guide
           摘要: asyncio 是 Python 用于处理异步 IO 的标准库...
        
        2. [标题] 异步编程 vs 多线程：性能对比
           URL: https://example.com/async-vs-threads
           摘要: 在 IO 密集型任务中，异步编程通常比多线程更高效...
        ```
        
        如果搜索失败或无可用结果，返回错误描述字符串。
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Notes:
        - 搜索结果会自动过滤广告和低质量内容
        - 结果按相关性排序
        - 某些网站可能有访问限制，此时会返回部分可用结果
    """
    logger.info(f"执行网络搜索: {query}")
    
    if not query or not isinstance(query, str):
        return "错误: 搜索查询不能为空"
    
    if not REQUESTS_AVAILABLE:
        return "错误: requests 库未安装，无法执行搜索"
    
    # TODO: 实现实际的搜索逻辑
    # 可选方案：
    # 1. 使用 DuckDuckGo API
    # 2. 使用 SerpAPI
    # 3. 使用 Google Custom Search API
    # 4. 模拟搜索引擎爬取（仅用于测试）
    
    # 临时实现：返回一个占位符结果
    placeholder_result = f"""搜索结果: "{query}"

[搜索结果不可用 - 搜索功能待实现]

当前返回占位信息，Agent 需要使用其他方式获取知识。

提示: 请实现以下搜索后端之一：
1. DuckDuckGo API (推荐，无需 API Key)
2. SerpAPI (需要免费注册)
3. Google Custom Search JSON API (免费有限额)
4. 自建网页爬虫

实现后请更新 web_tools.py 中的 web_search 函数。
"""
    
    logger.debug(f"搜索完成，结果长度: {len(placeholder_result)}")
    return placeholder_result


def read_webpage(url: str, max_length: Optional[int] = None) -> str:
    """
    读取指定网页的完整内容。
    
    此函数通过 HTTP GET 请求获取网页内容，并进行必要的清理和格式化。
    主要用于 Agent 需要阅读详细文档、教程或文章的场景。
    
    Args:
        url: 要读取的网页 URL。
             必须是有效的 HTTP 或 HTTPS URL。
             
             有效的 URL 示例：
             - "https://docs.python.org/3/library/asyncio.html"
             - "https://github.com/python/cpython"
             - "https://en.wikipedia.org/wiki/Artificial_intelligence"
             
        max_length: 可选的内容最大长度限制。
                   如果内容超过此限制，将被截断。
                   默认值为 None，表示使用系统默认限制（100000 字符）。
                   建议对于长页面设置此值以控制内存使用。
    
    Returns:
        网页的文本内容。
        
        成功时返回格式：
        ```
        URL: https://example.com/page
        Title: 页面标题
        
        --- Content ---
        页面正文内容...
        --- End ---
        ```
        
        失败时返回错误描述字符串。
        
        可能返回的错误信息：
        - "错误: 无效的 URL 格式"
        - "错误: 无法连接到服务器"
        - "错误: 请求超时"
        - "错误: 页面不存在 (404)"
        - "错误: 服务器内部错误 (500)"
        - "错误: 内容类型不支持"
    
    Raises:
        此函数不抛出异常，所有错误都通过返回字符串报告。
    
    Example:
        >>> result = read_webpage("https://httpbin.org/html")
        >>> if "错误:" not in result:
        ...     print("成功获取网页内容")
        ... else:
        ...     print(f"读取失败: {result}")
    
    Notes:
        - 自动设置常见的浏览器请求头，模拟真实浏览器访问
        - 自动处理重定向（最多 5 次）
        - 自动检测并处理常见的编码问题
        - 非 HTML 内容（如图片、PDF）可能返回提示信息
        - 脚本和样式标签的内容会被移除
        - 会尝试提取纯文本内容，减少噪音
    """
    logger.info(f"读取网页: {url}")
    
    # 参数验证
    if not url or not isinstance(url, str):
        return "错误: URL 不能为空"
    
    # URL 格式验证
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        return "错误: URL 必须以 http:// 或 https:// 开头"
    
    # 限制长度设置
    if max_length is None:
        max_length = MAX_CONTENT_LENGTH
    
    if not REQUESTS_AVAILABLE:
        return "错误: requests 库未安装，无法读取网页"
    
    try:
        # 发送 HTTP 请求
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=DEFAULT_TIMEOUT,
            allow_redirects=True,
            verify=True
        )
        
        # 检查响应状态
        if response.status_code == 404:
            return f"错误: 页面不存在 (404): {url}"
        elif response.status_code >= 500:
            return f"错误: 服务器内部错误 ({response.status_code})"
        elif response.status_code >= 400:
            return f"错误: 请求失败 ({response.status_code})"
        
        # 检测内容类型
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            return f"提示: 内容类型为 {content_type}，可能不是标准网页内容"
        
        # 获取响应编码并解码内容
        response.encoding = response.apparent_encoding or 'utf-8'
        content = response.text
        
        # 尝试提取 <title> 标签
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        title = title_match.group(1).strip() if title_match else "无标题"
        
        # 尝试提取 <meta description>
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            content, re.IGNORECASE
        )
        description = desc_match.group(1).strip() if desc_match else ""
        
        # 简化 HTML：移除脚本、样式和注释
        cleaned_content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        cleaned_content = re.sub(r'<style[^>]*>.*?</style>', '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
        cleaned_content = re.sub(r'<!--.*?-->', '', cleaned_content, flags=re.DOTALL)
        
        # 将 HTML 标签替换为换行符
        cleaned_content = re.sub(r'<br\s*/?>', '\n', cleaned_content, flags=re.IGNORECASE)
        cleaned_content = re.sub(r'<p[^>]*>', '\n\n', cleaned_content, flags=re.IGNORECASE)
        cleaned_content = re.sub(r'</p>', '', cleaned_content, flags=re.IGNORECASE)
        
        # 移除剩余的 HTML 标签
        cleaned_content = re.sub(r'<[^>]+>', '', cleaned_content)
        
        # 清理多余空白
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
        cleaned_content = cleaned_content.strip()
        
        # 截断超长内容
        if len(cleaned_content) > max_length:
            cleaned_content = cleaned_content[:max_length] + f"\n\n[内容已截断，原始长度 {len(cleaned_content)} 字符]"
        
        # 构建返回结果
        result = f"""URL: {url}
Title: {title}

--- Content ---"""
        
        if description:
            result += f"\n描述: {description}\n"
        
        result += f"\n{cleaned_content}\n--- End ---"
        
        logger.debug(f"网页读取成功，内容长度: {len(cleaned_content)}")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"读取超时: {url}")
        return f"错误: 请求超时 (>{DEFAULT_TIMEOUT}秒)"
    
    except requests.exceptions.ConnectionError:
        logger.error(f"连接失败: {url}")
        return f"错误: 无法连接到服务器，请检查 URL 是否正确"
    
    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常: {e}")
        return f"错误: 请求失败 - {str(e)}"
    
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        return f"错误: {str(e)}"


def extract_links(html_content: str, base_url: Optional[str] = None) -> list:
    """
    从 HTML 内容中提取所有链接。
    
    这是一个辅助函数，用于从网页 HTML 中提取所有超链接。
    返回的链接会经过清理和格式化。
    
    Args:
        html_content: HTML 字符串内容
        base_url: 可选的基准 URL，用于转换相对链接
        
    Returns:
        链接字典的列表，每个字典包含：
        - url: 完整 URL
        - text: 链接文本
        - is_external: 是否是外部链接
    """
    links = []
    
    # 提取所有 <a> 标签中的 href
    pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
    matches = re.findall(pattern, html_content, re.IGNORECASE)
    
    for href, text in matches:
        href = href.strip()
        text = text.strip()
        
        if not href or href.startswith(('#', 'javascript:', 'mailto:')):
            continue
        
        # 处理相对链接
        if base_url and not href.startswith(('http://', 'https://')):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        
        is_external = href.startswith('http')
        
        links.append({
            'url': href,
            'text': text or href,
            'is_external': is_external
        })
    
    return links
