"""数据库迁移：添加爬虫任务表"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
from app.models import Base


async def migrate():
    """添加 crawler_tasks 表"""
    print("🚀 开始数据库迁移...")

    async with engine.begin() as conn:
        # 创建表
        print("📋 创建 crawler_tasks 表...")
        await conn.run_sync(Base.metadata.create_all)

        print("✅ 迁移完成！")


async def rollback():
    """回滚：删除 crawler_tasks 表"""
    print("⚠️  开始回滚...")

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS crawler_tasks CASCADE"))

        print("✅ 回滚完成！")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()

    if args.rollback:
        asyncio.run(rollback())
    else:
        asyncio.run(migrate())
