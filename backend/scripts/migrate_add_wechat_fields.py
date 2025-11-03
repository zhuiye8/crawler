"""
⚠️ DEPRECATED - 此迁移脚本已过时
==========================================
此脚本添加的 wechat_content_html 和 wechat_content_text 字段已被删除。
新的数据库结构使用通用的 content_html 字段和 content_source 标记。

请勿运行此脚本！如需了解当前字段结构，请查看 app/models.py 中的 Article 模型。
==========================================
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到路径以便导入
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine


async def migrate_database():
    """执行数据库迁移：添加微信相关字段到articles表"""
    print("🚀 开始数据库迁移...")

    async with engine.begin() as conn:
        print("📋 添加微信相关字段到 articles 表...")

        # SQL迁移语句列表
        migration_sqls = [
            # 添加内容来源字段
            """
            ALTER TABLE articles
            ADD COLUMN IF NOT EXISTS content_source VARCHAR(50) DEFAULT 'pharnexcloud';
            """,
            # 添加微信原文链接字段
            """
            ALTER TABLE articles
            ADD COLUMN IF NOT EXISTS original_source_url TEXT;
            """,
            # 添加微信文章HTML内容字段
            """
            ALTER TABLE articles
            ADD COLUMN IF NOT EXISTS wechat_content_html TEXT;
            """,
            # 添加微信文章纯文本字段
            """
            ALTER TABLE articles
            ADD COLUMN IF NOT EXISTS wechat_content_text TEXT;
            """,
        ]

        # 逐条执行迁移SQL
        for sql in migration_sqls:
            try:
                await conn.execute(text(sql))
                print(f"  ✅ 成功执行: {sql.strip()[:50]}...")
            except Exception as e:
                print(f"  ⚠️  执行失败 (可能字段已存在): {e}")

    print("✅ 数据库迁移完成！")
    print("\n新增字段说明:")
    print("  - content_source: 内容来源标记 (pharnexcloud/wechat)")
    print("  - original_source_url: 微信公众号原文链接")
    print("  - wechat_content_html: 微信文章完整HTML内容")
    print("  - wechat_content_text: 微信文章完整纯文本")


async def rollback_migration():
    """回滚迁移：删除添加的字段"""
    confirm = input("⚠️  确定要回滚迁移吗？这将删除所有微信相关字段和数据。输入 'yes' 确认: ")
    if confirm.lower() != 'yes':
        print("❌ 已取消回滚")
        return

    print("🔄 开始回滚迁移...")

    async with engine.begin() as conn:
        rollback_sqls = [
            "ALTER TABLE articles DROP COLUMN IF EXISTS content_source;",
            "ALTER TABLE articles DROP COLUMN IF EXISTS original_source_url;",
            "ALTER TABLE articles DROP COLUMN IF EXISTS wechat_content_html;",
            "ALTER TABLE articles DROP COLUMN IF EXISTS wechat_content_text;",
        ]

        for sql in rollback_sqls:
            try:
                await conn.execute(text(sql))
                print(f"  ✅ 已删除字段")
            except Exception as e:
                print(f"  ❌ 删除失败: {e}")

    print("✅ 回滚完成！")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        asyncio.run(rollback_migration())
    else:
        asyncio.run(migrate_database())
