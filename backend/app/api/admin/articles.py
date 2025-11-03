"""Admin API - Article Management"""

from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from app.database import get_db
from app.models import Article, Source
from app.schemas import (
    ArticleResponse,
    ArticleDetailResponse,
    ArticleUpdateRequest,
    BatchDeleteRequest
)

router = APIRouter(prefix="/articles", tags=["Admin-Articles"])


@router.get("/", response_model=dict)
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    keyword: str = Query(None, description="Search keyword"),
    category: str = Query(None, description="Category filter"),
    content_source: str = Query(None, description="Content source"),
    from_date: str = Query(None, description="From date YYYY-MM-DD"),
    to_date: str = Query(None, description="To date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    """Get article list with pagination, search, and filters"""

    query = select(Article).where(Article.is_deleted == False)

    if keyword:
        search_filter = or_(
            Article.title.ilike(f"%{keyword}%"),
            Article.summary.ilike(f"%{keyword}%"),
            Article.author.ilike(f"%{keyword}%")
        )
        query = query.where(search_filter)

    if category:
        query = query.where(Article.category == category)

    if content_source:
        query = query.where(Article.content_source == content_source)

    if from_date:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        query = query.where(Article.published_at >= from_dt)
    if to_date:
        to_dt = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.where(Article.published_at <= to_dt)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Article.published_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    articles = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": [ArticleResponse.model_validate(article) for article in articles]
    }


@router.get("/{article_id}", response_model=ArticleDetailResponse)
async def get_article_detail(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get article detail"""

    result = await db.execute(
        select(Article).where(
            and_(Article.id == article_id, Article.is_deleted == False)
        )
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return ArticleDetailResponse.model_validate(article)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    request: ArticleUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update article"""

    result = await db.execute(
        select(Article).where(
            and_(Article.id == article_id, Article.is_deleted == False)
        )
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)

    await db.commit()
    await db.refresh(article)

    return ArticleResponse.model_validate(article)


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete article (soft delete)"""

    result = await db.execute(
        select(Article).where(
            and_(Article.id == article_id, Article.is_deleted == False)
        )
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article.is_deleted = True
    await db.commit()

    return {"message": "Deleted successfully", "article_id": article_id}


@router.delete("/batch/delete")
async def batch_delete_articles(
    request: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Batch delete articles (soft delete)"""

    result = await db.execute(
        select(Article).where(
            and_(Article.id.in_(request.article_ids), Article.is_deleted == False)
        )
    )
    articles = result.scalars().all()

    deleted_count = 0
    for article in articles:
        article.is_deleted = True
        deleted_count += 1

    await db.commit()

    return {
        "message": "Batch delete successful",
        "deleted_count": deleted_count,
        "total_requested": len(request.article_ids)
    }
