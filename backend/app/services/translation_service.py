"""AI翻译服务 - 使用DeepSeek API进行智能翻译"""

import re
import logging
from typing import Optional
from openai import AsyncOpenAI
from bs4 import BeautifulSoup, NavigableString
from app.config import settings

logger = logging.getLogger(__name__)

# 初始化DeepSeek客户端（使用OpenAI兼容API）
client = AsyncOpenAI(
    api_key=settings.AI_API_KEY,
    base_url=f"{settings.AI_API_BASE}/v1"
)


def detect_chinese_content(text: str) -> bool:
    """
    检测文本是否主要为中文内容
    返回True如果中文字符占比超过30%，否则返回False
    """
    if not text or not text.strip():
        return True  # 空文本默认不需要翻译

    # 移除HTML标签进行检测
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = clean_text.strip()

    if not clean_text:
        return True

    # 计算中文字符数量
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
    total_chars = len(clean_text.replace(' ', '').replace('\n', '').replace('\t', ''))

    if total_chars == 0:
        return True

    chinese_ratio = chinese_chars / total_chars

    logger.info(f"文本语言检测: 中文字符比例 {chinese_ratio:.2%} ({chinese_chars}/{total_chars})")

    # 如果中文字符占比超过30%，认为是中文内容
    return chinese_ratio > 0.3


async def translate_text_to_chinese(text: str) -> str:
    """
    使用DeepSeek API将文本翻译为中文
    """
    if not text or not text.strip():
        return text

    try:
        # 构建翻译prompt
        prompt = f"""请将以下文本翻译成简体中文，要求：
1. 保持原文的语气和风格
2. 医药专业术语请不要翻译！
3. 如果原文已经是中文，请直接返回原文
4. 只返回翻译结果，不要添加任何解释

待翻译文本：
{text}"""

        response = await client.chat.completions.create(
            model=settings.AI_MODEL_CHAT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )

        translated_text = response.choices[0].message.content.strip()
        logger.info(f"文本翻译完成: {len(text)} -> {len(translated_text)} 字符")

        return translated_text

    except Exception as e:
        logger.error(f"文本翻译失败: {str(e)}")
        return text  # 翻译失败时返回原文


async def translate_html_content(html_content: str) -> str:
    """
    翻译HTML内容，保留HTML结构和格式
    只翻译文本节点，保留所有HTML标签和属性
    """
    if not html_content or not html_content.strip():
        return html_content

    # 检测是否需要翻译
    if detect_chinese_content(html_content):
        logger.info("检测到主要为中文内容，跳过翻译")
        return html_content

    logger.info("检测到非中文内容，开始翻译...")

    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # 收集所有需要翻译的文本节点
        text_nodes = []
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString):
                text = element.strip()
                if text and not re.match(r'^[\s\n\r\t]*$', str(element)):
                    text_nodes.append(element)

        logger.info(f"找到 {len(text_nodes)} 个文本节点需要翻译")

        # 批量翻译文本节点
        if text_nodes:
            # 将所有文本合并，用特殊分隔符分隔
            combined_text = "\n---TRANSLATE_SEPARATOR---\n".join([str(node).strip() for node in text_nodes])

            # 翻译合并后的文本
            translated_combined = await translate_text_to_chinese(combined_text)

            # 分割翻译结果
            translated_parts = translated_combined.split("\n---TRANSLATE_SEPARATOR---\n")

            # 确保翻译结果数量匹配
            if len(translated_parts) == len(text_nodes):
                # 替换原文本节点
                for i, node in enumerate(text_nodes):
                    node.replace_with(translated_parts[i].strip())

                logger.info("HTML翻译完成")
            else:
                logger.warning(f"翻译结果数量不匹配: {len(translated_parts)} vs {len(text_nodes)}")
                # 逐个翻译作为备选方案
                for node in text_nodes:
                    if str(node).strip():
                        translated = await translate_text_to_chinese(str(node))
                        node.replace_with(translated)

        return str(soup)

    except Exception as e:
        logger.error(f"HTML翻译失败: {str(e)}")
        return html_content  # 翻译失败时返回原内容


async def translate_article_html(content_html: Optional[str]) -> Optional[str]:
    """
    翻译文章的HTML内容，保持格式和样式
    返回翻译后的HTML内容
    """
    if not content_html:
        return content_html

    try:
        logger.info("开始翻译HTML内容...")
        translated_html = await translate_html_content(content_html)
        return translated_html

    except Exception as e:
        logger.error(f"HTML内容翻译失败: {str(e)}")
        return content_html  # 翻译失败时返回原内容


