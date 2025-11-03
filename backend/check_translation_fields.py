#!/usr/bin/env python3
"""检查数据库中翻译相关字段的情况"""

import asyncio
import asyncpg
from app.config import settings

async def check_translation_fields():
    """检查数据库中翻译字段的情况"""

    try:
        # 转换DATABASE_URL格式，从postgresql+asyncpg://为postgresql://
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(database_url)

        # 检查表结构中的翻译字段
        print("=== 检查articles表结构中的翻译字段 ===")
        columns_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'articles'
        AND column_name LIKE '%translated%'
        ORDER BY column_name;
        """

        columns = await conn.fetch(columns_query)

        if columns:
            print("发现的翻译字段：")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        else:
            print("未发现翻译相关字段")

        print("\n=== 检查翻译字段的数据情况 ===")

        # 检查是否存在translated_content_text字段
        text_field_exists = any(col['column_name'] == 'translated_content_text' for col in columns)
        html_field_exists = any(col['column_name'] == 'translated_content_html' for col in columns)

        if text_field_exists:
            # 统计translated_content_text字段的数据
            text_count_query = """
            SELECT
                COUNT(*) as total_articles,
                COUNT(translated_content_text) as articles_with_text_translation,
                COUNT(CASE WHEN translated_content_text IS NOT NULL AND translated_content_text != '' THEN 1 END) as articles_with_non_empty_text
            FROM articles;
            """
            text_stats = await conn.fetchrow(text_count_query)
            print(f"translated_content_text 统计:")
            print(f"  - 总文章数: {text_stats['total_articles']}")
            print(f"  - 有text翻译的文章: {text_stats['articles_with_text_translation']}")
            print(f"  - 有非空text翻译的文章: {text_stats['articles_with_non_empty_text']}")
        else:
            print("translated_content_text 字段不存在")

        if html_field_exists:
            # 统计translated_content_html字段的数据
            html_count_query = """
            SELECT
                COUNT(*) as total_articles,
                COUNT(translated_content_html) as articles_with_html_translation,
                COUNT(CASE WHEN translated_content_html IS NOT NULL AND translated_content_html != '' THEN 1 END) as articles_with_non_empty_html
            FROM articles;
            """
            html_stats = await conn.fetchrow(html_count_query)
            print(f"\ntranslated_content_html 统计:")
            print(f"  - 总文章数: {html_stats['total_articles']}")
            print(f"  - 有html翻译的文章: {html_stats['articles_with_html_translation']}")
            print(f"  - 有非空html翻译的文章: {html_stats['articles_with_non_empty_html']}")
        else:
            print("translated_content_html 字段不存在")

        # 如果两个字段都存在，检查数据一致性
        if text_field_exists and html_field_exists:
            print("\n=== 检查翻译字段数据一致性 ===")
            consistency_query = """
            SELECT
                COUNT(CASE WHEN translated_content_text IS NOT NULL AND translated_content_html IS NULL THEN 1 END) as text_only,
                COUNT(CASE WHEN translated_content_text IS NULL AND translated_content_html IS NOT NULL THEN 1 END) as html_only,
                COUNT(CASE WHEN translated_content_text IS NOT NULL AND translated_content_html IS NOT NULL THEN 1 END) as both_exist,
                COUNT(CASE WHEN translated_content_text IS NULL AND translated_content_html IS NULL THEN 1 END) as neither
            FROM articles;
            """
            consistency_stats = await conn.fetchrow(consistency_query)
            print(f"数据一致性统计:")
            print(f"  - 只有text翻译: {consistency_stats['text_only']}")
            print(f"  - 只有html翻译: {consistency_stats['html_only']}")
            print(f"  - 两者都有: {consistency_stats['both_exist']}")
            print(f"  - 两者都没有: {consistency_stats['neither']}")

        await conn.close()
        print("\n检查完成！")

    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_translation_fields())