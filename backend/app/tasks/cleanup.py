"""定时清理任务 - 物理删除已软删除的文章"""
import logging
from datetime import timedelta
from sqlalchemy import select, delete
from app.database import get_db_context
from app.models import Article
from app.utils import timezone as tz
from app.utils.s3_client import get_s3_client
from app.config import settings

logger = logging.getLogger(__name__)


async def cleanup_deleted_articles():
    """
    物理删除超过N天的已软删除文章

    从配置文件读取删除阈值（CLEANUP_DELETED_AFTER_DAYS）
    默认30天
    """
    days_threshold = getattr(settings, 'CLEANUP_DELETED_AFTER_DAYS', 30)
    cutoff_date = tz.now() - timedelta(days=days_threshold)

    logger.info(f"🗑️  开始清理任务：删除 {days_threshold} 天前的已删除文章（截止日期: {cutoff_date}）")

    async with get_db_context() as db:
        try:
            # 查询需要物理删除的文章
            result = await db.execute(
                select(Article).where(
                    Article.is_deleted == True,
                    Article.updated_at < cutoff_date
                )
            )
            articles_to_delete = result.scalars().all()

            if not articles_to_delete:
                logger.info("✅ 没有需要清理的文章")
                return

            logger.info(f"📋 找到 {len(articles_to_delete)} 篇需要清理的文章")

            # 获取S3客户端
            s3_client = get_s3_client()
            deleted_count = 0
            failed_count = 0

            for article in articles_to_delete:
                try:
                    # 删除S3文件
                    # 文章ID格式：article_{timestamp}
                    # S3键格式：{article_id}/original.html, {article_id}/cleaned.txt, {article_id}/wechat_original.html
                    article_prefix = f"article_{article.id}/"

                    # 删除原始HTML
                    try:
                        s3_client.delete_object(settings.S3_BUCKET_RAW, f"{article_prefix}original.html")
                    except Exception as e:
                        logger.warning(f"⚠️  删除S3文件失败 (original.html): {e}")

                    # 删除清理后文本
                    try:
                        s3_client.delete_object(settings.S3_BUCKET_CLEAN, f"{article_prefix}cleaned.txt")
                    except Exception as e:
                        logger.warning(f"⚠️  删除S3文件失败 (cleaned.txt): {e}")

                    # 删除微信原文（如果有）
                    if article.wechat_content_html:
                        try:
                            s3_client.delete_object(settings.S3_BUCKET_RAW, f"{article_prefix}wechat_original.html")
                        except Exception as e:
                            logger.warning(f"⚠️  删除S3文件失败 (wechat_original.html): {e}")

                    # 物理删除数据库记录
                    await db.delete(article)

                    deleted_count += 1
                    logger.info(f"  ✅ 已删除: {article.title} (ID: {article.id})")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"  ❌ 删除失败: {article.title} (ID: {article.id}), 错误: {e}")
                    continue

            # 提交所有删除操作
            await db.commit()

            logger.info(f"🎉 清理完成！成功删除 {deleted_count} 篇文章，失败 {failed_count} 篇")

        except Exception as e:
            logger.error(f"❌ 清理任务执行失败: {e}")
            await db.rollback()
            raise


def schedule_cleanup_task(scheduler):
    """
    配置清理任务到调度器

    Args:
        scheduler: APScheduler调度器实例
    """
    # 每天凌晨3点执行清理任务
    scheduler.add_job(
        cleanup_deleted_articles,
        trigger='cron',
        hour=3,
        minute=0,
        id='cleanup_deleted_articles',
        name='清理已删除文章',
        replace_existing=True
    )

    logger.info("✅ 已配置定时清理任务：每天凌晨3:00执行")
