"""数据库迁移脚本 - 添加翻译字段并迁移现有数据"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import engine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_database():
    """执行数据库迁移"""

    try:
        async with engine.begin() as conn:
            logger.info("开始数据库迁移...")

            # 步骤1: 添加新字段
            logger.info("步骤1: 添加新字段...")

            # 添加 content_html 字段
            try:
                await conn.execute(text("ALTER TABLE articles ADD COLUMN content_html TEXT"))
                logger.info("✅ 添加 content_html 字段")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ content_html 字段已存在，跳过")
                else:
                    raise

            # 添加 translated_content_text 字段
            try:
                await conn.execute(text("ALTER TABLE articles ADD COLUMN translated_content_text TEXT"))
                logger.info("✅ 添加 translated_content_text 字段")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ translated_content_text 字段已存在，跳过")
                else:
                    raise

            # 添加 translated_content_html 字段
            try:
                await conn.execute(text("ALTER TABLE articles ADD COLUMN translated_content_html TEXT"))
                logger.info("✅ 添加 translated_content_html 字段")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ translated_content_html 字段已存在，跳过")
                else:
                    raise

            # 步骤2: 迁移现有数据
            logger.info("步骤2: 迁移现有数据...")

            # 检查是否存在 wechat_content_html 字段
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'articles' AND column_name = 'wechat_content_html'
            """))
            wechat_html_exists = result.fetchone() is not None

            if wechat_html_exists:
                # 将 wechat_content_html 迁移到 content_html（优先保留微信HTML）
                result = await conn.execute(text("""
                    UPDATE articles
                    SET content_html = wechat_content_html
                    WHERE wechat_content_html IS NOT NULL
                    AND wechat_content_html != ''
                    AND (content_html IS NULL OR content_html = '')
                """))
                logger.info(f"✅ 迁移了 {result.rowcount} 条微信HTML记录到 content_html")

                # 步骤3: 删除旧字段
                logger.info("步骤3: 删除旧字段...")

                try:
                    await conn.execute(text("ALTER TABLE articles DROP COLUMN wechat_content_html"))
                    logger.info("✅ 删除 wechat_content_html 字段")
                except Exception as e:
                    logger.warning(f"⚠️ 删除 wechat_content_html 字段失败: {e}")

                try:
                    await conn.execute(text("ALTER TABLE articles DROP COLUMN wechat_content_text"))
                    logger.info("✅ 删除 wechat_content_text 字段")
                except Exception as e:
                    logger.warning(f"⚠️ 删除 wechat_content_text 字段失败: {e}")
            else:
                logger.info("⚠️ wechat_content_html 字段不存在，跳过数据迁移")

            # 步骤4: 验证迁移结果
            logger.info("步骤4: 验证迁移结果...")

            result = await conn.execute(text("""
                SELECT
                    COUNT(*) as total_articles,
                    COUNT(content_html) as articles_with_html,
                    COUNT(translated_content_text) as articles_with_translated_text,
                    COUNT(translated_content_html) as articles_with_translated_html
                FROM articles
                WHERE is_deleted = false
            """))

            stats = result.fetchone()
            logger.info(f"📊 迁移统计:")
            logger.info(f"   总文章数: {stats.total_articles}")
            logger.info(f"   包含HTML的文章: {stats.articles_with_html}")
            logger.info(f"   包含翻译文本的文章: {stats.articles_with_translated_text}")
            logger.info(f"   包含翻译HTML的文章: {stats.articles_with_translated_html}")

            logger.info("🎉 数据库迁移完成!")

    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_database())