"""Crawler Service - Manage crawler task execution"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import CrawlerTask
from app.database import get_db_context
from app.utils import timezone as tz


class CrawlerService:
    """Crawler task management service (singleton)"""

    _instance = None
    _current_task_id: Optional[int] = None
    _is_running: bool = False
    _progress: Dict = {}
    _logs: list = []  # 存储最近的日志
    _max_logs: int = 100  # 最多保留100条日志

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def is_running(self) -> bool:
        """Check if a task is currently running"""
        return self._is_running

    def get_current_task_id(self) -> Optional[int]:
        """Get current running task ID"""
        return self._current_task_id

    def get_progress(self) -> Dict:
        """Get current progress"""
        return self._progress

    def add_log(self, message: str):
        """添加日志消息"""
        log_entry = {
            "timestamp": tz.now().isoformat(),
            "message": message
        }
        self._logs.append(log_entry)
        # 保持日志数量在限制内
        if len(self._logs) > self._max_logs:
            self._logs = self._logs[-self._max_logs:]

    def get_logs(self) -> list:
        """获取所有日志"""
        return self._logs

    def clear_logs(self):
        """清空日志"""
        self._logs = []

    async def create_and_run_task(self, config: dict) -> int:
        """Create and async run crawler task"""

        if self._is_running:
            raise RuntimeError("A task is already running")

        async with get_db_context() as db:
            task = CrawlerTask(
                config=config,
                status="pending",
                articles_count=0
            )
            db.add(task)
            await db.commit()
            await db.refresh(task)
            task_id = task.id

        asyncio.create_task(self._run_crawler_task(task_id, config))

        return task_id

    async def _run_crawler_task(self, task_id: int, config: dict):
        """Execute crawler task (background)"""

        # 确保 Windows 上的事件循环策略正确（支持子进程）
        import sys
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

        self._current_task_id = task_id
        self._is_running = True
        self._progress = {"status": "starting", "articles_crawled": 0}
        self.clear_logs()  # 清空之前的日志

        try:
            self.add_log(f"任务 #{task_id} 开始执行")

            async with get_db_context() as db:
                result = await db.execute(
                    select(CrawlerTask).where(CrawlerTask.id == task_id)
                )
                task = result.scalar_one()
                task.status = "running"
                task.started_at = tz.now()
                await db.commit()

            from crawler.crawler_factory import CrawlerFactory
            from scripts.crawl_and_ingest import ingest_articles

            # 获取数据源（默认药渡云）
            source = config.get("source", "pharnexcloud")
            self.add_log(f"正在初始化爬虫: {source}")
            crawler = CrawlerFactory.create_crawler(source, headless=True)
            self.add_log(f"使用爬虫: {crawler.source_name}")

            num_pages = config.get("pages", 10)
            max_articles = config.get("max_articles")
            days_back = config.get("days_back")
            from_date_str = config.get("from_date")
            to_date_str = config.get("to_date")

            from_date = None
            to_date = None
            if days_back:
                from_date = tz.today_start() - timedelta(days=days_back)
            elif from_date_str:
                from_date = tz.naive_to_china(datetime.strptime(from_date_str, "%Y-%m-%d"))
                if to_date_str:
                    to_date = tz.naive_to_china(
                        datetime.strptime(to_date_str, "%Y-%m-%d").replace(
                            hour=23, minute=59, second=59
                        )
                    )

            self._progress = {"status": "crawling", "articles_crawled": 0}
            self.add_log(f"开始爬取: {num_pages}页, 最大{max_articles}篇")

            articles = await crawler.crawl_multiple_pages(
                num_pages=num_pages,
                max_articles=max_articles,
                from_date=from_date,
                to_date=to_date
            )

            self.add_log(f"爬取完成，共获取 {len(articles)} 篇文章")
            self._progress = {"status": "ingesting", "articles_crawled": len(articles)}
            self.add_log("正在将文章保存到数据库...")

            await ingest_articles(articles)
            self.add_log("文章保存完成")

            async with get_db_context() as db:
                result = await db.execute(
                    select(CrawlerTask).where(CrawlerTask.id == task_id)
                )
                task = result.scalar_one()
                task.status = "completed"
                task.completed_at = tz.now()
                task.articles_count = len(articles)
                await db.commit()

            self._progress = {
                "status": "completed",
                "articles_crawled": len(articles)
            }
            self.add_log(f"任务完成！成功爬取 {len(articles)} 篇文章")

        except Exception as e:
            error_msg = str(e)
            self.add_log(f"错误: {error_msg}")
            async with get_db_context() as db:
                result = await db.execute(
                    select(CrawlerTask).where(CrawlerTask.id == task_id)
                )
                task = result.scalar_one()
                task.status = "failed"
                task.completed_at = tz.now()
                task.error_message = str(e)
                await db.commit()

            self._progress = {"status": "failed", "error": str(e)}

        finally:
            self._is_running = False
            self._current_task_id = None


crawler_service = CrawlerService()
