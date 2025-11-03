"""Admin API - Analytics and Statistics"""

from datetime import timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Article
from app.schemas import (
    OverviewStats,
    ArticleTrendItem,
    SourceDistributionItem,
    CategoryDistributionItem
)
from app.utils import timezone as tz

router = APIRouter(prefix="/analytics", tags=["Admin-Analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    """Get overview statistics"""

    today_start = tz.today_start()
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    total_result = await db.execute(
        select(func.count(Article.id)).where(Article.is_deleted == False)
    )
    total_articles = total_result.scalar()

    today_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.published_at >= today_start
        )
    )
    today_articles = today_result.scalar()

    week_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.published_at >= week_start
        )
    )
    week_articles = week_result.scalar()

    month_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.published_at >= month_start
        )
    )
    month_articles = month_result.scalar()

    wechat_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.content_source == "wechat"
        )
    )
    wechat_articles = wechat_result.scalar()

    pharnex_result = await db.execute(
        select(func.count(Article.id)).where(
            Article.is_deleted == False,
            Article.content_source == "pharnexcloud"
        )
    )
    pharnex_articles = pharnex_result.scalar()

    return OverviewStats(
        total_articles=total_articles,
        today_articles=today_articles,
        week_articles=week_articles,
        month_articles=month_articles,
        wechat_articles=wechat_articles,
        pharnex_articles=pharnex_articles
    )


@router.get("/trends", response_model=list[ArticleTrendItem])
async def get_article_trends(
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """Get article publication trends by date"""

    end_date = tz.today_start()
    start_date = end_date - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Article.published_at).label("date"),
            func.count(Article.id).label("count")
        )
        .where(
            Article.is_deleted == False,
            Article.published_at >= start_date
        )
        .group_by(func.date(Article.published_at))
        .order_by(func.date(Article.published_at))
    )

    trends = []
    for row in result.all():
        trends.append(ArticleTrendItem(
            date=row.date.strftime("%Y-%m-%d"),
            count=row.count
        ))

    return trends


@router.get("/sources", response_model=list[SourceDistributionItem])
async def get_source_distribution(db: AsyncSession = Depends(get_db)):
    """Get content source distribution"""

    total_result = await db.execute(
        select(func.count(Article.id)).where(Article.is_deleted == False)
    )
    total = total_result.scalar() or 1

    result = await db.execute(
        select(
            Article.content_source,
            func.count(Article.id).label("count")
        )
        .where(Article.is_deleted == False)
        .group_by(Article.content_source)
    )

    distribution = []
    for row in result.all():
        source_name = "WeChat" if row.content_source == "wechat" else "PharnexCloud"
        distribution.append(SourceDistributionItem(
            source=source_name,
            count=row.count,
            percentage=round(row.count / total * 100, 2)
        ))

    return distribution


@router.get("/categories", response_model=list[CategoryDistributionItem])
async def get_category_distribution(db: AsyncSession = Depends(get_db)):
    """Get category distribution"""

    result = await db.execute(
        select(
            Article.category,
            func.count(Article.id).label("count")
        )
        .where(Article.is_deleted == False)
        .group_by(Article.category)
        .order_by(func.count(Article.id).desc())
    )

    distribution = []
    for row in result.all():
        if row.category:
            distribution.append(CategoryDistributionItem(
                category=row.category,
                count=row.count
            ))

    return distribution
