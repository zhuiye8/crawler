"""Articles API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Article, ArticleAIOutput, Source
from app.schemas import ArticleListResponse, ArticleListItem, ArticleDetail
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    from_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List articles with pagination and filters

    - page: Page number (default 1)
    - page_size: Items per page (default 20, max 100)
    - category: Filter by category
    - from_date: Filter by date (YYYY-MM-DD)
    """
    # Build query
    query = select(Article).where(Article.is_deleted == False)

    if category:
        query = query.where(Article.category == category)

    if from_date:
        try:
            date_obj = datetime.strptime(from_date, "%Y-%m-%d")
            query = query.where(Article.published_at >= date_obj)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and sorting
    query = query.order_by(Article.published_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    articles = result.scalars().all()

    # Build response
    items = []
    for article in articles:
        items.append(ArticleListItem(
            id=article.id,
            title=article.title,
            summary=article.summary,
            author=article.author,
            source_name="药渡云",
            category=article.category,
            tags=article.tags,
            published_at=article.published_at
        ))

    return ArticleListResponse(
        data=items,
        pagination={"total": total, "page": page, "page_size": page_size}
    )


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get article detail by ID

    Returns full article with AI analysis
    """
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get AI analysis
    ai_result = await db.execute(
        select(ArticleAIOutput).where(ArticleAIOutput.article_id == article_id)
    )
    ai_output = ai_result.scalar_one_or_none()

    ai_analysis = None
    if ai_output:
        ai_analysis = {
            "summary": ai_output.summary,
            "key_points": ai_output.key_points,
            "entities": ai_output.entities
        }

    return ArticleDetail(
        id=article.id,
        title=article.title,
        summary=article.summary,
        author=article.author,
        source_name="药渡云",
        category=article.category,
        tags=article.tags,
        published_at=article.published_at,
        content_url=article.content_url,
        content_text_excerpt=article.content_text[:500] if article.content_text else None,
        ai_analysis=ai_analysis
    )
