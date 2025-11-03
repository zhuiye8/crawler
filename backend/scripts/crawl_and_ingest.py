"""从药渡云爬取文章并存入数据库（集成微信公众号爬取）"""

import asyncio
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import get_db_context
from app.models import Article, Source
from app.utils.html_cleaner import clean_html
from app.utils.s3_client import get_s3_client
from app.utils import timezone as tz
from app.config import settings
from crawler.pharnex_crawler import PharnexCrawler
from crawler.wechat_crawler import WechatArticleCrawler

# 配置选项
ENABLE_WECHAT_CRAWL = True  # 是否启用微信公众号爬取
WECHAT_CRAWL_DELAY = 10  # 微信爬取间隔（秒）


async def ingest_articles(articles: list):
    """将爬取的文章存入数据库（包含微信公众号内容）"""
    s3_client = get_s3_client()
    pharnex_crawler = PharnexCrawler()
    wechat_crawler = WechatArticleCrawler(
        headless=True,
        rate_limit_delay=WECHAT_CRAWL_DELAY
    ) if ENABLE_WECHAT_CRAWL else None

    async with get_db_context() as db:
        # 获取数据源
        result = await db.execute(select(Source).where(Source.name == "药渡云"))
        source = result.scalar_one_or_none()
        if not source:
            print("❌ 未找到数据源 '药渡云'，请先运行 init_db.py")
            return

        for article_data in articles:
            try:
                print(f"\n📝 处理文章: {article_data['title']}")

                # 爬取药渡云详情页（包含微信原文链接提取）
                content_html, content_text, original_source_url = await pharnex_crawler.crawl_detail_page(
                    article_data["url"]
                )

                if not content_text:
                    print(f"⚠️  未找到内容，跳过")
                    continue

                # 清理内容
                content_text = clean_html(content_html) if content_html else content_text

                # 初始化微信内容字段
                wechat_content_html = None
                wechat_content_text = None
                content_source = "pharnexcloud"

                # 如果找到微信原文链接且启用了微信爬取
                if original_source_url and wechat_crawler:
                    print(f"  🔗 发现微信原文链接，尝试爬取...")
                    try:
                        wechat_article = await wechat_crawler.crawl_with_retry(
                            original_source_url,
                            max_retries=2  # 最多重试2次
                        )

                        if wechat_article:
                            wechat_content_html = wechat_article.get('content_html')
                            wechat_content_text = wechat_article.get('content_text')
                            content_source = "wechat"
                            print(f"  ✅ 成功爬取微信内容 ({len(wechat_content_text)} 字符)")

                            # 使用微信内容作为主内容（如果更完整）
                            if wechat_content_text and len(wechat_content_text) > len(content_text):
                                content_text = wechat_content_text
                                content_html = wechat_content_html
                                print(f"  ℹ️  使用微信内容作为主内容")
                        else:
                            print(f"  ⚠️  微信爬取失败，降级使用药渡云内容")

                    except Exception as e:
                        print(f"  ⚠️  微信爬取出错: {e}，降级使用药渡云内容")

                # 计算去重哈希
                canonical_hash = hashlib.sha256(content_text.encode()).hexdigest()

                # 检查未删除的文章是否已存在
                active_result = await db.execute(
                    select(Article).where(
                        Article.canonical_hash == canonical_hash,
                        Article.is_deleted == False
                    )
                )
                active_article = active_result.scalar_one_or_none()

                if active_article:
                    print(f"  ⏭️  文章已存在: {active_article.title}")
                    continue

                # 检查已删除的文章
                deleted_result = await db.execute(
                    select(Article).where(
                        Article.canonical_hash == canonical_hash,
                        Article.is_deleted == True
                    )
                )
                deleted_article = deleted_result.scalar_one_or_none()

                # 生成文章ID用于S3存储
                article_id = f"article_{int(tz.now().timestamp() * 1000)}"

                # 上传到S3
                s3_key_raw = f"{article_id}/original.html"
                s3_key_clean = f"{article_id}/cleaned.txt"

                s3_client.upload_text(content_html or "", settings.S3_BUCKET_RAW, s3_key_raw)
                s3_client.upload_text(content_text, settings.S3_BUCKET_CLEAN, s3_key_clean)

                # 如果有微信内容，也保存微信版本
                if wechat_content_html:
                    s3_key_wechat = f"{article_id}/wechat_original.html"
                    s3_client.upload_text(wechat_content_html, settings.S3_BUCKET_RAW, s3_key_wechat)

                if deleted_article:
                    # 更新已删除文章的数据并恢复
                    deleted_article.title = article_data["title"]
                    deleted_article.summary = article_data.get("summary", "")
                    deleted_article.author = article_data.get("author", "药渡云")
                    deleted_article.category = article_data.get("category", "前沿研究")
                    deleted_article.tags = article_data.get("tags", [])
                    deleted_article.published_at = article_data["published_at"]
                    deleted_article.content_url = article_data["url"]
                    deleted_article.content_text = content_text
                    deleted_article.content_source = content_source
                    deleted_article.original_source_url = original_source_url or None
                    deleted_article.wechat_content_html = wechat_content_html
                    deleted_article.wechat_content_text = wechat_content_text
                    deleted_article.crawled_at = tz.now()
                    deleted_article.is_deleted = False  # 恢复文章

                    await db.commit()
                    await db.refresh(deleted_article)

                    print(f"  ♻️  恢复并更新已删除文章: {deleted_article.title} (ID: {deleted_article.id})")
                else:
                    # 创建新文章记录
                    article = Article(
                        title=article_data["title"],
                        summary=article_data.get("summary", ""),
                        author=article_data.get("author", "药渡云"),
                        source_id=source.id,
                        category=article_data.get("category", "前沿研究"),
                        tags=article_data.get("tags", []),
                        published_at=article_data["published_at"],
                        content_url=article_data["url"],
                        content_text=content_text,
                        content_source=content_source,
                        original_source_url=original_source_url or None,
                        wechat_content_html=wechat_content_html,
                        wechat_content_text=wechat_content_text,
                        canonical_hash=canonical_hash,
                    )

                    db.add(article)
                    await db.commit()
                    await db.refresh(article)

                    print(f"  ✅ 已入库: {article.title} (ID: {article.id}, 来源: {content_source})")
                await asyncio.sleep(1)  # 请求限流

            except Exception as e:
                print(f"  ❌ 处理文章出错: {e}")
                await db.rollback()
                continue


async def main(args):
    """主函数：爬取药渡云文章并存入数据库"""
    print("🚀 开始爬取...")
    print(f"📌 微信爬取: {'✅ 启用' if ENABLE_WECHAT_CRAWL else '❌ 禁用'}")

    # 计算时间范围（统一归零到0点，避免时分秒干扰）
    from_date = None
    to_date = None

    if args.days_back:
        # 获取今天0点
        from_date = tz.today_start() - timedelta(days=args.days_back)
        print(f"📅 时间范围: 最近 {args.days_back} 天 (从 {from_date.strftime('%Y-%m-%d')} 开始)")
    elif args.from_date:
        from_date = tz.naive_to_china(datetime.strptime(args.from_date, "%Y-%m-%d"))
        if args.to_date:
            to_date = tz.naive_to_china(datetime.strptime(args.to_date, "%Y-%m-%d"))
            # 结束日期设为当天23:59:59
            to_date = to_date.replace(hour=23, minute=59, second=59)
            print(f"📅 时间范围: {args.from_date} 至 {args.to_date}")
        else:
            print(f"📅 时间范围: {args.from_date} 至今")

    # 打印爬取配置
    print(f"📄 页数限制: {args.pages} 页")
    if args.max_articles:
        print(f"📊 文章数限制: {args.max_articles} 篇")

    # 爬取文章
    crawler = PharnexCrawler(headless=True)
    articles = await crawler.crawl_multiple_pages(
        num_pages=args.pages,
        max_articles=args.max_articles,
        from_date=from_date,
        to_date=to_date
    )

    print(f"\n📊 共爬取 {len(articles)} 篇文章")
    print("💾 开始存入数据库...")

    await ingest_articles(articles)

    print("\n🎉 爬取和入库完成！")
    print("\n💡 提示:")
    print("  - 如需禁用微信爬取，修改 ENABLE_WECHAT_CRAWL = False")
    print("  - 如需调整微信爬取间隔，修改 WECHAT_CRAWL_DELAY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="药渡云文章爬虫")

    # 数量控制
    parser.add_argument("--pages", type=int, default=10, help="爬取页数 (默认: 10)")
    parser.add_argument("--max-articles", type=int, default=None, help="最大文章数 (可选)")

    # 时间范围
    parser.add_argument("--days-back", type=int, default=None, help="最近N天 (例如: 7, 30)")
    parser.add_argument("--from-date", type=str, default=None, help="起始日期 (格式: YYYY-MM-DD)")
    parser.add_argument("--to-date", type=str, default=None, help="结束日期 (格式: YYYY-MM-DD)")

    args = parser.parse_args()

    asyncio.run(main(args))
