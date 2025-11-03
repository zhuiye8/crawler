#!/usr/bin/env python3
"""重建数据库表结构"""

import asyncio
import asyncpg
from app.config import settings
from app.models import Base
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

async def rebuild_database():
    """重建数据库表结构"""

    try:
        print("开始重建数据库...")

        # 1. 使用asyncpg删除所有表
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncpg.connect(database_url)

        print("1. 删除所有现有表...")

        # 获取所有表名
        tables_query = """
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public' AND tablename NOT LIKE 'pg_%' AND tablename != 'information_schema';
        """
        tables = await conn.fetch(tables_query)

        for table in tables:
            table_name = table['tablename']
            print(f"  - 删除表: {table_name}")
            await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        await conn.close()

        print("2. 重新创建表结构...")

        # 2. 使用SQLAlchemy重新创建表
        sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url, poolclass=NullPool)

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("  - 成功创建所有表")

        # 验证表结构
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"3. 验证表结构...")
        print(f"  - 共创建 {len(tables)} 个表: {', '.join(tables)}")

        if 'articles' in tables:
            columns = inspector.get_columns('articles')
            print(f"  - articles表有 {len(columns)} 个字段:")
            for col in columns:
                print(f"    * {col['name']}: {col['type']}")

        engine.dispose()

        print("✅ 数据库重建完成!")

    except Exception as e:
        print(f"重建失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(rebuild_database())