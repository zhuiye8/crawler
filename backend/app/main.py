"""FastAPI main application"""

import sys
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.api import auth, articles, chat
from app.api.admin import articles as admin_articles, crawler as admin_crawler, analytics as admin_analytics
from app.config import settings
from app.tasks.cleanup import schedule_cleanup_task

# Windows 平台配置
if sys.platform == 'win32':
    # 设置标准输出使用 UTF-8 编码
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    # 设置 Windows 事件循环策略以支持子进程（patchright 需要）
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 配置日志使用 UTF-8 编码
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 创建全局调度器实例
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动定时任务调度器...")

    # 配置清理任务
    schedule_cleanup_task(scheduler)

    # 启动调度器
    scheduler.start()
    logger.info("✅ 定时任务调度器已启动")

    yield

    # 关闭时执行
    logger.info("🛑 关闭定时任务调度器...")
    scheduler.shutdown()
    logger.info("✅ 定时任务调度器已关闭")


# Create FastAPI app
app = FastAPI(
    title="Medical News RAG API",
    description="Medical news aggregation with AI-powered Q&A",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(articles.router, prefix="/v1/articles", tags=["Articles"])
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])

# Include admin routers
app.include_router(admin_articles.router, prefix="/v1/admin")
app.include_router(admin_crawler.router, prefix="/v1/admin")
app.include_router(admin_analytics.router, prefix="/v1/admin")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Medical News RAG API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.ENVIRONMENT == "development"
    )
