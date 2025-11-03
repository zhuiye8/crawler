#!/usr/bin/env python3
"""
数据库迁移脚本：移除translated_content_text字段，简化翻译功能
只保留translated_content_html字段用于HTML翻译
"""

import asyncio
import asyncpg
from app.config import settings
from datetime import datetime

async def migrate_remove_text_translation():
    """移除translated_content_text字段"""

    try:
        # 转换DATABASE_URL格式
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(database_url)

        print(f"开始迁移 - {datetime.now()}")
        print("=" * 50)

        # 1. 检查当前状态
        print("1. 检查迁移前状态...")

        # 检查表结构
        columns_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'articles'
        AND column_name LIKE '%translated%'
        ORDER BY column_name;
        """
        columns = await conn.fetch(columns_query)

        print("当前翻译字段：")
        text_field_exists = False
        html_field_exists = False

        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']}")
            if col['column_name'] == 'translated_content_text':
                text_field_exists = True
            elif col['column_name'] == 'translated_content_html':
                html_field_exists = True

        if not text_field_exists:
            print("translated_content_text 字段不存在，无需迁移")
            await conn.close()
            return

        if not html_field_exists:
            print("警告：translated_content_html 字段不存在！")
            await conn.close()
            return

        # 2. 检查数据情况
        print("\n2. 检查数据情况...")
        data_check_query = """
        SELECT
            COUNT(*) as total_articles,
            COUNT(translated_content_text) as articles_with_text,
            COUNT(translated_content_html) as articles_with_html,
            COUNT(CASE WHEN translated_content_text IS NOT NULL AND translated_content_text != '' THEN 1 END) as non_empty_text,
            COUNT(CASE WHEN translated_content_html IS NOT NULL AND translated_content_html != '' THEN 1 END) as non_empty_html
        FROM articles;
        """

        stats = await conn.fetchrow(data_check_query)
        print(f"数据统计：")
        print(f"  - 总文章数: {stats['total_articles']}")
        print(f"  - 有text翻译的文章: {stats['articles_with_text']}")
        print(f"  - 有html翻译的文章: {stats['articles_with_html']}")
        print(f"  - 非空text翻译: {stats['non_empty_text']}")
        print(f"  - 非空html翻译: {stats['non_empty_html']}")

        # 3. 数据备份（如果有数据的话）
        if stats['non_empty_text'] > 0:
            print(f"\n警告：发现 {stats['non_empty_text']} 篇文章有text翻译数据！")

            # 检查是否有text数据但没有html数据的情况
            orphan_data_query = """
            SELECT id, title,
                   CASE WHEN translated_content_text IS NOT NULL AND translated_content_text != '' THEN true ELSE false END as has_text,
                   CASE WHEN translated_content_html IS NOT NULL AND translated_content_html != '' THEN true ELSE false END as has_html
            FROM articles
            WHERE (translated_content_text IS NOT NULL AND translated_content_text != '')
            AND (translated_content_html IS NULL OR translated_content_html = '')
            LIMIT 5;
            """

            orphan_data = await conn.fetch(orphan_data_query)
            if orphan_data:
                print(f"发现 {len(orphan_data)} 篇文章只有text翻译没有html翻译：")
                for article in orphan_data:
                    print(f"  - ID {article['id']}: {article['title'][:50]}...")

                response = input("是否将text翻译复制到html字段? (y/N): ")
                if response.lower() == 'y':
                    print("正在复制text翻译到html字段...")
                    copy_query = """
                    UPDATE articles
                    SET translated_content_html = translated_content_text
                    WHERE (translated_content_text IS NOT NULL AND translated_content_text != '')
                    AND (translated_content_html IS NULL OR translated_content_html = '');
                    """
                    result = await conn.execute(copy_query)
                    print(f"已复制数据，影响行数: {result.split()[-1]}")
                else:
                    print("用户选择不复制数据，继续删除字段...")

        # 4. 执行字段删除
        print(f"\n3. 删除 translated_content_text 字段...")

        try:
            drop_column_query = "ALTER TABLE articles DROP COLUMN IF EXISTS translated_content_text;"
            await conn.execute(drop_column_query)
            print("成功删除 translated_content_text 字段")
        except Exception as e:
            print(f"删除字段失败: {str(e)}")
            await conn.close()
            return

        # 5. 验证结果
        print(f"\n4. 验证迁移结果...")

        # 再次检查表结构
        final_columns = await conn.fetch(columns_query)

        print("迁移后的翻译字段：")
        for col in final_columns:
            print(f"  - {col['column_name']}: {col['data_type']}")

        text_field_still_exists = any(col['column_name'] == 'translated_content_text' for col in final_columns)

        if text_field_still_exists:
            print("迁移失败：translated_content_text 字段仍然存在")
        else:
            print("迁移成功：translated_content_text 字段已删除")

        await conn.close()

        print("=" * 50)
        print(f"迁移完成 - {datetime.now()}")

    except Exception as e:
        print(f"迁移失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(migrate_remove_text_translation())