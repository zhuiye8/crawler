"""
基础爬虫类 - 定义通用接口，支持多数据源扩展
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """爬虫基类 - 所有爬虫必须继承此类"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.source_name = self.get_source_name()

    @abstractmethod
    def get_source_name(self) -> str:
        """获取数据源名称"""
        pass

    @abstractmethod
    async def crawl_list_page(self, page_num: int) -> List[Dict]:
        """
        爬取列表页

        返回格式:
        [
            {
                "title": str,
                "url": str,
                "published_at": datetime,
                "author": str,
                "category": str,
                "summary": str,
                "tags": List[str]
            }
        ]
        """
        pass

    @abstractmethod
    async def crawl_detail_page(self, url: str) -> tuple[str, str, Optional[str]]:
        """
        爬取详情页

        返回: (content_html, content_text, original_source_url)
        """
        pass

    async def crawl_multiple_pages(
        self,
        num_pages: int = 10,
        max_articles: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        爬取多页数据（通用实现）

        参数:
            num_pages: 爬取页数
            max_articles: 最大文章数
            from_date: 起始日期
            to_date: 结束日期
        """
        all_articles = []
        empty_pages = 0

        for page_num in range(1, num_pages + 1):
            logger.info(f"[Crawler] 正在爬取第 {page_num} 页...")

            articles = await self.crawl_list_page(page_num)

            # 时间筛选
            filtered = []
            for article in articles:
                pub_date = article.get('published_at')
                if not pub_date:
                    continue

                if from_date and pub_date < from_date:
                    continue
                if to_date and pub_date > to_date:
                    continue

                filtered.append(article)

            # 早停判断
            if not filtered:
                empty_pages += 1
                logger.warning(f"[Crawler] 第 {page_num} 页无符合条件的文章")
                if empty_pages >= 3:
                    logger.info(f"[Crawler] 连续 {empty_pages} 页无数据，停止爬取")
                    break
            else:
                empty_pages = 0
                all_articles.extend(filtered)
                logger.info(f"[Crawler] 第 {page_num} 页找到 {len(filtered)} 篇文章")

            # 数量限制
            if max_articles and len(all_articles) >= max_articles:
                all_articles = all_articles[:max_articles]
                logger.info(f"[Crawler] 已达到最大文章数 {max_articles}，停止爬取")
                break

        logger.info(f"\n[Crawler] 爬取完成，共 {len(all_articles)} 篇文章")
        return all_articles

    def supports_wechat_extraction(self) -> bool:
        """是否支持提取微信原文链接"""
        return False
