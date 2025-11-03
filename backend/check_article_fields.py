#!/usr/bin/env python3
"""检查articles表的实际字段"""

import asyncio
import asyncpg
from app.config import settings

async def check_article_fields():
    """检查articles表的实际字段"""

    try:
        # 转换DATABASE_URL格式
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(database_url)

        print("=== 检查articles表的所有字段 ===")
        columns_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'articles'
        ORDER BY ordinal_position;
        """

        columns = await conn.fetch(columns_query)

        if columns:
            print("articles表的所有字段：")
            for i, col in enumerate(columns, 1):
                print(f"  {i:2d}. {col['column_name']:<30} {col['data_type']:<20} (nullable: {col['is_nullable']})")
        else:
            print("未找到articles表")

        # 检查是否存在旧字段
        old_fields = ['wechat_content_html', 'wechat_content_text', 'translated_content_text']
        existing_old_fields = []

        for field in old_fields:
            exists = any(col['column_name'] == field for col in columns)
            if exists:
                existing_old_fields.append(field)

        if existing_old_fields:
            print(f"\n发现需要删除的旧字段：{existing_old_fields}")
        else:
            print(f"\n所有旧字段都已删除")

        await conn.close()

    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_article_fields())