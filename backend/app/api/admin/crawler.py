"""Admin API - Crawler Management - 支持多数据源"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import CrawlerTask
from app.schemas import (
    CrawlerConfigRequest,
    CrawlerTaskResponse,
    CrawlerStatusResponse
)
from app.services.crawler_service import crawler_service
from crawler.crawler_factory import CrawlerFactory

router = APIRouter(prefix="/crawler", tags=["Admin-Crawler"])


@router.get("/sources", response_model=list)
async def get_available_sources():
    """获取所有可用的数据源"""
    return CrawlerFactory.get_available_sources()


@router.post("/tasks", response_model=dict)
async def create_crawler_task(
    request: CrawlerConfigRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create crawler task"""

    if crawler_service.is_running():
        raise HTTPException(status_code=400, detail="A task is already running")

    config = request.model_dump(exclude_none=True)
    task_id = await crawler_service.create_and_run_task(config)

    return {
        "message": "Task created and started",
        "task_id": task_id,
        "config": config
    }


@router.get("/tasks", response_model=dict)
async def get_crawler_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Status filter"),
    db: AsyncSession = Depends(get_db)
):
    """Get crawler task list"""

    query = select(CrawlerTask)
    if status:
        query = query.where(CrawlerTask.status == status)

    query = query.order_by(CrawlerTask.created_at.desc())

    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [CrawlerTaskResponse.model_validate(task) for task in tasks]
    }


@router.get("/tasks/{task_id}", response_model=CrawlerTaskResponse)
async def get_crawler_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get crawler task detail"""

    result = await db.execute(
        select(CrawlerTask).where(CrawlerTask.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return CrawlerTaskResponse.model_validate(task)


@router.get("/status", response_model=CrawlerStatusResponse)
async def get_crawler_status(db: AsyncSession = Depends(get_db)):
    """Get crawler current status"""

    is_running = crawler_service.is_running()
    current_task = None
    progress = None

    if is_running:
        task_id = crawler_service.get_current_task_id()
        progress = crawler_service.get_progress()

        if task_id:
            result = await db.execute(
                select(CrawlerTask).where(CrawlerTask.id == task_id)
            )
            task = result.scalar_one_or_none()
            if task:
                current_task = CrawlerTaskResponse.model_validate(task)

    return CrawlerStatusResponse(
        is_running=is_running,
        current_task=current_task,
        progress=progress
    )


@router.get("/logs", response_model=list)
async def get_crawler_logs():
    """获取爬虫执行日志"""
    return crawler_service.get_logs()


@router.post("/cancel/{task_id}")
async def cancel_crawler_task(task_id: int):
    """Cancel crawler task (not implemented in current version)"""

    current_task_id = crawler_service.get_current_task_id()

    if current_task_id != task_id:
        raise HTTPException(status_code=400, detail="Task is not running")

    raise HTTPException(
        status_code=501,
        detail="Cancel not supported in current version"
    )
