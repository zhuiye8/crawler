"""药渡云爬虫 - 前沿研究栏目（重构版，继承 BaseCrawler）"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from patchright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils import timezone as tz

from .base_crawler import BaseCrawler

logger = logging.getLogger(__name__)


class PharnexCrawler(BaseCrawler):
    """药渡云爬虫 - 支持微信原文提取"""

    BASE_URL = "https://www.pharnexcloud.com/zixun/shiye/qy"

    def get_source_name(self) -> str:
        """数据源名称"""
        return "药渡云"

    def supports_wechat_extraction(self) -> bool:
        """支持微信原文提取"""
        return True

    async def crawl_list_page(self, page_num: int = 1) -> List[Dict]:
        """爬取文章列表页"""
        url = f"{self.BASE_URL}?page={page_num}"
        articles = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')

                article_items = soup.select("li.report-item")

                for item in article_items:
                    try:
                        article = self._parse_article_item(item)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.error(f"[Crawler] 解析文章失败: {e}")

            except TimeoutError:
                logger.warning(f"[Crawler] 页面加载超时 {page_num}")
            except Exception as e:
                logger.error(f"[Crawler] 爬取页面出错 {page_num}: {e}")
            finally:
                await browser.close()

        return articles

    def _parse_article_item(self, item) -> Optional[Dict]:
        """解析单个文章项"""
        try:
            # 标题和链接 - 新结构：div.title > a.no-redirect
            title_elem = item.select_one("div.title a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href")
            if url and not url.startswith("http"):
                url = f"https://www.pharnexcloud.com{url}"

            # 摘要 - 新结构：div.desc
            summary_elem = item.select_one("div.desc")
            summary = summary_elem.get_text(strip=True) if summary_elem else ""

            # 信息项 - 新结构：div.info > div.info-item
            info_items = item.select("div.info-item")

            # 第一个info-item是作者，第二个是日期
            author = "药渡云"
            date_text = ""

            if len(info_items) >= 1:
                author = info_items[0].get_text(strip=True)
            if len(info_items) >= 2:
                date_text = info_items[1].get_text(strip=True)

            published_at = self._parse_date(date_text)

            return {
                "title": title,
                "url": url,
                "published_at": published_at,
                "author": author,
                "category": "前沿研究",
                "summary": summary,
                "tags": []
            }
        except Exception as e:
            logger.error(f"[Crawler] 解析文章项失败: {e}")
            return None

    def _parse_date(self, date_text: str) -> datetime:
        """解析日期"""
        try:
            date_text = date_text.strip()
            # 匹配格式：2025.10.27 或 2025-10-27
            match = re.search(r'(\d{4})[.\-年](\d{1,2})[.\-月](\d{1,2})', date_text)
            if match:
                year, month, day = match.groups()
                return tz.naive_to_china(datetime(int(year), int(month), int(day)))
        except Exception:
            pass
        return tz.now()

    async def crawl_detail_page(self, url: str) -> tuple[str, str, Optional[str]]:
        """
        爬取详情页

        返回: (content_html, content_text, wechat_url)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 提取正文内容
                content_div = soup.select_one("div.article-content, div.content, article")
                content_html = str(content_div) if content_div else ""
                content_text = content_div.get_text(separator="\n", strip=True) if content_div else ""

                # 提取微信原文链接
                wechat_url = None
                wechat_link = soup.select_one('a[href*="mp.weixin.qq.com"]')
                if wechat_link:
                    wechat_url = wechat_link.get('href')
                    logger.info(f"[Crawler] 发现微信原文: {wechat_url}")

                await browser.close()
                return content_html, content_text, wechat_url

            except Exception as e:
                logger.error(f"[Crawler] 爬取详情页出错: {e}")
                await browser.close()
                return "", "", None
