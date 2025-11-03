"""AI分析服务 - 使用DeepSeek API"""

import json
import re
from openai import AsyncOpenAI
from app.config import settings
from app.models import Article


# 初始化AI客户端（OpenAI SDK兼容DeepSeek）
ai_client = AsyncOpenAI(
    api_key=settings.AI_API_KEY,
    base_url=settings.AI_API_BASE
)


async def analyze_article(article: Article) -> dict:
    """
    使用AI分析文章内容

    Args:
        article: 文章对象

    Returns:
        包含analysis的字典（一段分析文字）
    """
    # 构建提示词 - 只要求生成一段分析文字
    prompt = f"""你是一名熟悉医药行业的资深分析师。请用一段话（150-250字）分析以下医药新闻的核心内容和意义。

【要求】
1. 用简体中文
2. 一段话概括，不要分点列举
3. 突出关键信息：涉及的药物/技术、临床意义、商业影响等
4. 语言专业但易懂
5. 字数控制在150-250字

【文章内容】
标题：{article.title}
作者：{article.author or '未知'}
正文：{article.content_text[:3000] if article.content_text else article.summary}

请直接输出分析文字，不要使用JSON格式或其他格式标记。
"""

    try:
        # 调用AI API
        response = await ai_client.chat.completions.create(
            model=settings.AI_MODEL_CHAT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        analysis_text = response.choices[0].message.content.strip()

        # 返回简单格式
        return {
            "analysis": analysis_text
        }

    except Exception as e:
        print(f"AI分析失败: {str(e)}")
        raise Exception(f"AI分析失败: {str(e)}")


def _parse_ai_response(content: str) -> dict:
    """
    解析AI响应，支持多种格式

    Args:
        content: AI返回的内容

    Returns:
        解析后的字典
    """
    try:
        # 尝试直接解析JSON
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试从markdown代码块中提取JSON
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试从```包裹的内容中提取
    code_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    # 如果都失败，返回默认结构
    return {
        "summary": content[:200] if len(content) > 200 else content,
        "key_points": [],
        "entities": {
            "drugs": [],
            "diseases": [],
            "companies": []
        }
    }
