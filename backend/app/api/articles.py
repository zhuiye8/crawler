"""Articles API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Article, ArticleAIOutput, Source
from app.schemas import ArticleListResponse, ArticleListItem, ArticleDetail
from app.services.ai_service import analyze_article
from app.services.translation_service import translate_article_html, detect_chinese_content
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
            "analysis": ai_output.summary  # 使用简化格式，与AI分析API保持一致
        }

    return ArticleDetail(
        id=article.id,
        title=article.title,
        summary=article.summary,
        author=article.author,
        source_name="???",
        category=article.category,
        tags=article.tags,
        published_at=article.published_at,
        content_url=article.content_url,
        content_text=article.content_text,
        content_html=article.content_html,
        content_source=article.content_source,
        translated_content_html=article.translated_content_html,
        ai_analysis=ai_analysis
    )



@router.post("/{article_id}/analyze")
async def generate_ai_analysis(
    article_id: int,
    force_regenerate: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    为指定文章生成AI分析

    参数：
    - force_regenerate: 是否强制重新生成（默认False，已有分析时直接返回）

    返回AI分析结果（摘要、关键点、实体）
    """
    # 获取文章
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 检查是否已有AI分析（获取最新的一条）
    ai_result = await db.execute(
        select(ArticleAIOutput)
        .where(ArticleAIOutput.article_id == article_id)
        .order_by(ArticleAIOutput.created_at.desc())
        .limit(1)
    )
    existing_ai = ai_result.scalar_one_or_none()

    # 如果已有分析且不是强制重新生成，直接返回现有的
    if existing_ai and not force_regenerate:
        return {
            "success": True,
            "message": "返回已有AI分析",
            "data": {
                "analysis": existing_ai.summary  # summary字段存储的就是分析文字
            }
        }

    try:
        # 调用AI分析
        ai_analysis_result = await analyze_article(article)
        analysis_text = ai_analysis_result.get("analysis", "")

        # 保存或更新AI分析结果（使用summary字段存储分析文字）
        if existing_ai:
            # 更新现有记录
            existing_ai.summary = analysis_text
            existing_ai.key_points = []
            existing_ai.entities = {}
            existing_ai.model_name = "deepseek-chat"
        else:
            # 创建新记录
            ai_output = ArticleAIOutput(
                article_id=article.id,
                version_no=article.version_no,
                summary=analysis_text,
                key_points=[],
                entities={},
                model_name="deepseek-chat"
            )
            db.add(ai_output)

        await db.commit()

        return {
            "success": True,
            "message": "AI分析完成",
            "data": {
                "analysis": analysis_text
            }
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"AI分析失败: {str(e)}")


@router.post("/{article_id}/translate")
async def generate_translation(
    article_id: int,
    force_regenerate: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    为指定文章生成AI翻译

    参数：
    - force_regenerate: 是否强制重新翻译（默认False，已有翻译时直接返回）

    返回翻译结果（只翻译HTML内容，保持格式和样式）
    """
    # 获取文章
    result = await db.execute(
        select(Article).where(Article.id == article_id, Article.is_deleted == False)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # 检查是否已有翻译（如果不是强制重新翻译）
    if not force_regenerate and article.translated_content_html:
        return {
            "success": True,
            "message": "返回已有翻译",
            "data": {
                "translated_content_html": article.translated_content_html,
                "is_chinese": detect_chinese_content(article.content_html or ""),
                "requires_translation": False
            }
        }

    try:
        # 检测文章语言（只检测HTML内容）
        content_to_check = article.content_html or ""
        is_chinese = detect_chinese_content(content_to_check)

        if is_chinese:
            # 中文文章不需要翻译，直接返回原HTML
            article.translated_content_html = article.content_html
            await db.commit()

            return {
                "success": True,
                "message": "检测到中文文章，无需翻译",
                "data": {
                    "translated_content_html": article.content_html,
                    "is_chinese": True,
                    "requires_translation": False
                }
            }

        # 非中文文章，执行HTML翻译
        translated_html = await translate_article_html(article.content_html)

        # 更新文章的翻译字段
        article.translated_content_html = translated_html
        await db.commit()

        return {
            "success": True,
            "message": "翻译完成",
            "data": {
                "translated_content_html": translated_html,
                "is_chinese": False,
                "requires_translation": True
            }
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
