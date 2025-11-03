"""微信公众号文章爬虫

⚠️ 重要法律声明:
此模块仅供个人学习研究使用。
商业使用可能违反:
1. 微信公众平台服务协议
2. 中华人民共和国反不正当竞争法
3. 其他相关法律法规

使用前请确保:
- 已获得内容所有者的明确授权
- 仅用于个人学习研究目的
- 不进行商业化利用
- 遵守爬取频率限制

开发者不承担任何由此产生的法律责任。
"""

import asyncio
import sys
from datetime import datetime
from patchright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import re
import hashlib
import os
import json

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils import timezone as tz


class WechatArticleCrawler:
    """
    微信公众号文章爬虫

    功能:
    - 爬取微信公众号文章完整内容
    - 解析文章元数据（标题、作者、发布时间等）
    - 处理文章中的图片
    - 实现反爬策略（延迟、重试等）
    - 支持缓存机制
    """

    def __init__(self, headless: bool = True, rate_limit_delay: int = 10):
        """初始化微信爬虫"""
        self.headless = headless
        self.rate_limit_delay = rate_limit_delay

        # 浏览器状态持久化文件（保存验证后的Cookie）
        from pathlib import Path
        self.state_file = Path(__file__).parent.parent / 'cache' / 'wechat_browser_state.json'

        # User-Agent列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]

    async def crawl_article(self, url: str, use_cache: bool = True) -> Optional[Dict]:
        """
        爬取单篇微信公众号文章

        Args:
            url: 微信文章URL (https://mp.weixin.qq.com/s/...)
            use_cache: 是否使用缓存 (默认True)

        Returns:
            文章数据字典，包含:
            - title: 标题
            - author: 作者/公众号名称
            - published_at: 发布时间
            - summary: 摘要
            - content_html: 完整HTML内容
            - content_text: 完整纯文本
            - tags: 标签列表
            - url: 原文链接

        Returns None if:
            - URL无效
            - 爬取失败
            - 解析错误
        """
        # 验证URL格式
        if not self._is_valid_wechat_url(url):
            print(f"⚠️  无效的微信文章URL: {url}")
            return None

        # 检查缓存
        if use_cache:
            cached = self._load_from_cache(url)
            if cached:
                print(f"📦 从缓存加载: {cached.get('title', 'Unknown')}")
                return cached

        # 执行爬取
        import random
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)

            # 尝试加载已保存的浏览器状态（复用验证后的Cookie）
            if self.state_file.exists():
                print("📦 加载已保存的浏览器状态...")
                context = await browser.new_context(storage_state=str(self.state_file))
            else:
                context = await browser.new_context()

            page = await context.new_page()

            try:
                print(f"📄 正在爬取: {url[:50]}...")

                # 设置随机User-Agent
                await page.set_extra_http_headers({
                    'User-Agent': random.choice(self.user_agents),
                })

                # 访问页面
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # 模拟人类阅读行为（降低检测风险）
                await self._simulate_human_behavior(page)

                # 等待文章内容区域加载
                await page.wait_for_selector('#js_content', timeout=20000)

                # 获取并解析HTML
                html = await page.content()
                soup = BeautifulSoup(html, 'lxml')

                # 解析文章信息
                article = self._parse_article_page(soup, url)

                if article:
                    print(f"✅ 成功爬取: {article['title']}")

                    # 保存浏览器状态（下次复用）
                    await context.storage_state(path=str(self.state_file))

                    # 保存到缓存
                    if use_cache:
                        self._save_to_cache(url, article)

                    # 随机延迟（避免规律性检测）
                    delay = random.uniform(12, 18)
                    print(f"⏱️  等待 {delay:.1f} 秒...")
                    await asyncio.sleep(delay)

                return article

            except TimeoutError:
                print(f"❌ 页面加载超时: {url}")
                return None
            except Exception as e:
                print(f"❌ 爬取失败: {e}")
                return None
            finally:
                await context.close()
                await browser.close()

    def _is_valid_wechat_url(self, url: str) -> bool:
        """验证是否为有效的微信公众号文章URL"""
        if not url:
            return False
        return url.startswith('https://mp.weixin.qq.com/s')

    async def _simulate_human_behavior(self, page):
        """模拟人类阅读行为"""
        import random

        # 随机滚动2-4次
        for _ in range(random.randint(2, 4)):
            scroll_px = random.randint(200, 500)
            await page.evaluate(f'window.scrollBy(0, {scroll_px})')
            await asyncio.sleep(random.uniform(0.8, 2.0))

        # 停留3-5秒
        await asyncio.sleep(random.uniform(3, 5))

    def _parse_article_page(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """
        解析微信文章页面HTML

        Args:
            soup: BeautifulSoup对象
            url: 文章URL

        Returns:
            文章数据字典或None
        """
        try:
            # 提取标题
            title = self._extract_title(soup)
            if not title:
                print("⚠️  未能提取文章标题")
                return None

            # 提取作者/公众号名称
            author = self._extract_author(soup)

            # 提取发布时间
            published_at = self._extract_publish_time(soup)

            # 提取摘要
            summary = self._extract_summary(soup)

            # 提取文章主体内容
            content_elem = soup.select_one('#js_content')
            if not content_elem:
                print("⚠️  未找到文章内容区域 (#js_content)")
                return None

            # 处理图片URL（微信图片使用data-src）
            self._process_images(content_elem)

            # 获取HTML和纯文本内容
            content_html = str(content_elem)
            content_text = content_elem.get_text(separator="\n").strip()

            # 提取标签/关键词
            tags = self._extract_tags(soup)

            return {
                "title": title,
                "url": url,
                "author": author,
                "published_at": published_at,
                "summary": summary,
                "content_html": content_html,
                "content_text": content_text,
                "tags": tags,
                "source": "微信公众号",
                "crawled_at": tz.now()
            }

        except Exception as e:
            print(f"⚠️  解析文章页面失败: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取文章标题"""
        # 方法1: 查找 #activity-name
        title_elem = soup.select_one('#activity-name')
        if title_elem:
            return title_elem.get_text().strip()

        # 方法2: 查找 h1 标签
        h1_elem = soup.select_one('h1')
        if h1_elem:
            return h1_elem.get_text().strip()

        # 方法3: 从meta标签提取
        meta_title = soup.select_one('meta[property="og:title"]')
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()

        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者/公众号名称"""
        # 查找公众号名称
        author_elem = soup.select_one('#js_name')
        if author_elem:
            return author_elem.get_text().strip()

        # 备用：从meta标签提取
        meta_author = soup.select_one('meta[name="author"]')
        if meta_author and meta_author.get('content'):
            return meta_author.get('content').strip()

        return "未知作者"

    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime:
        """提取发布时间"""
        # 查找发布时间元素
        time_elem = soup.select_one('#publish_time')
        if time_elem:
            time_str = time_elem.get_text().strip()
            return self._parse_time_string(time_str)

        # 备用：查找meta标签
        meta_time = soup.select_one('meta[property="og:article:published_time"]')
        if meta_time and meta_time.get('content'):
            time_str = meta_time.get('content')
            return self._parse_time_string(time_str)

        # 解析失败返回当前时间
        return tz.now()

    def _parse_time_string(self, time_str: str) -> datetime:
        """解析时间字符串为datetime对象"""
        try:
            # 清理时间字符串
            time_str = time_str.strip()

            # 尝试不同的时间格式
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y年%m月%d日",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue

            # 使用正则提取日期
            match = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', time_str)
            if match:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day))

        except Exception as e:
            print(f"⚠️  时间解析失败: {e}")

        # 解析失败返回当前时间
        return tz.now()

    def _extract_summary(self, soup: BeautifulSoup) -> str:
        """提取文章摘要"""
        # 从meta description提取
        desc_elem = soup.select_one('meta[name="description"]')
        if desc_elem and desc_elem.get('content'):
            return desc_elem.get('content').strip()

        # 从og:description提取
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()

        return ""

    def _process_images(self, content_elem: BeautifulSoup):
        """
        处理文章中的图片
        微信图片通常使用data-src属性存储真实URL
        """
        images = content_elem.select('img')
        for img in images:
            # 微信图片的真实URL在data-src中
            data_src = img.get('data-src', '')
            if data_src:
                img['src'] = data_src

            # 处理其他可能的属性
            data_url = img.get('data-url', '')
            if data_url and not data_src:
                img['src'] = data_url

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取文章标签/关键词"""
        tags = []

        # 从meta keywords提取
        keywords_elem = soup.select_one('meta[name="keywords"]')
        if keywords_elem and keywords_elem.get('content'):
            keywords = keywords_elem.get('content', '')
            tags = [k.strip() for k in keywords.split(',') if k.strip()]

        return tags

    async def crawl_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        带重试机制的爬取

        Args:
            url: 文章URL
            max_retries: 最大重试次数

        Returns:
            文章数据或None
        """
        for attempt in range(max_retries):
            try:
                article = await self.crawl_article(url, use_cache=True)
                if article:
                    return article

                print(f"⚠️  第 {attempt + 1}/{max_retries} 次尝试失败，等待重试...")

                # 递增延迟（避免快速重试被封）
                retry_delay = 5 * (attempt + 1)
                await asyncio.sleep(retry_delay)

            except Exception as e:
                print(f"❌ 爬取出错 (尝试 {attempt + 1}/{max_retries}): {e}")

        # 所有重试失败
        print(f"❌ 爬取失败，已重试 {max_retries} 次")
        return None

    def _get_cache_path(self, url: str) -> str:
        """获取缓存文件路径"""
        # 创建缓存目录
        cache_dir = Path(__file__).parent.parent / 'cache' / 'wechat_articles'
        cache_dir.mkdir(parents=True, exist_ok=True)

        # 使用URL的MD5作为文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return str(cache_dir / f"{url_hash}.json")

    def _save_to_cache(self, url: str, article: Dict):
        """保存文章到缓存"""
        try:
            cache_path = self._get_cache_path(url)
            with open(cache_path, 'w', encoding='utf-8') as f:
                # 转换datetime为字符串以便JSON序列化
                article_copy = article.copy()
                for key in ['published_at', 'crawled_at']:
                    if key in article_copy and isinstance(article_copy[key], datetime):
                        article_copy[key] = article_copy[key].isoformat()

                json.dump(article_copy, f, ensure_ascii=False, indent=2)

            print(f"💾 已缓存到: {cache_path}")
        except Exception as e:
            print(f"⚠️  保存缓存失败: {e}")

    def _load_from_cache(self, url: str) -> Optional[Dict]:
        """从缓存加载文章"""
        try:
            cache_path = self._get_cache_path(url)
            if not os.path.exists(cache_path):
                return None

            with open(cache_path, 'r', encoding='utf-8') as f:
                article = json.load(f)

            # 转换时间字符串回datetime对象
            for key in ['published_at', 'crawled_at']:
                if key in article and isinstance(article[key], str):
                    article[key] = datetime.fromisoformat(article[key])

            return article
        except Exception as e:
            print(f"⚠️  读取缓存失败: {e}")
            return None


# 为了避免未导入Path错误
from pathlib import Path
