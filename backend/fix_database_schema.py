#!/usr/bin/env python3
"""修复数据库schema问题"""

import asyncio
import asyncpg
from app.config import settings
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.pool import NullPool

async def fix_database_schema():
    """修复数据库schema问题"""

    try:
        print("正在修复数据库schema问题...")

        # 1. 使用asyncpg直接操作数据库
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(database_url)

        print("1. 检查并删除不存在的字段...")

        # 检查是否存在需要删除的字段
        old_fields = ['wechat_content_html', 'wechat_content_text', 'translated_content_text']

        for field in old_fields:
            try:
                # 尝试删除字段（如果存在）
                drop_query = f"ALTER TABLE articles DROP COLUMN IF EXISTS {field};"
                await conn.execute(drop_query)
                print(f"  - 尝试删除字段: {field}")
            except Exception as e:
                print(f"  - 删除字段 {field} 时出错: {str(e)}")

        await conn.close()

        print("2. 清理SQLAlchemy元数据缓存...")

        # 创建同步连接来清理元数据
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url, poolclass=NullPool)

        # 清理所有缓存的元数据
        metadata = MetaData()
        metadata.reflect(bind=engine)
        metadata.clear()

        # 重新加载表结构
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"  - 发现 {len(tables)} 个表")

        # 显式清理articles表的缓存
        if 'articles' in tables:
            columns = inspector.get_columns('articles')
            print(f"  - articles表有 {len(columns)} 个字段")

            for col in columns:
                if col['name'] in old_fields:
                    print(f"  - ⚠️  发现残留字段: {col['name']}")
                else:
                    print(f"  - ✓ {col['name']}")

        engine.dispose()

        print("3. 数据库schema修复完成!")

    except Exception as e:
        print(f"修复失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(fix_database_schema())