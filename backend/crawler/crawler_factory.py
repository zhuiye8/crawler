"""
爬虫工厂 - 统一管理多个数据源爬虫
"""

from typing import Dict, Type, List
from .base_crawler import BaseCrawler
from .pharnex_crawler import PharnexCrawler


class CrawlerFactory:
    """爬虫工厂 - 根据数据源名称创建相应的爬虫实例"""

    # 注册所有可用的爬虫
    _crawlers: Dict[str, Type[BaseCrawler]] = {
        "pharnexcloud": PharnexCrawler,
        # 未来可以添加更多爬虫：
        # "yaozhi": YaozhiCrawler,
        # "dingxiang": DingxiangCrawler,
    }

    @classmethod
    def create_crawler(cls, source: str, headless: bool = True) -> BaseCrawler:
        """
        创建爬虫实例

        参数:
            source: 数据源名称（pharnexcloud, yaozhi, 等）
            headless: 是否无头模式

        返回:
            爬虫实例

        抛出:
            ValueError: 不支持的数据源
        """
        crawler_class = cls._crawlers.get(source.lower())

        if not crawler_class:
            available_sources = list(cls._crawlers.keys())
            raise ValueError(
                f"不支持的数据源: {source}. "
                f"可用的数据源: {', '.join(available_sources)}"
            )

        return crawler_class(headless=headless)

    @classmethod
    def get_available_sources(cls) -> List[Dict[str, str]]:
        """
        获取所有可用的数据源列表

        返回:
            [
                {"key": "pharnexcloud", "name": "药渡云"},
                ...
            ]
        """
        sources = []
        for key, crawler_class in cls._crawlers.items():
            # 临时创建实例获取名称
            temp_instance = crawler_class(headless=True)
            sources.append({
                "key": key,
                "name": temp_instance.source_name,
                "supports_wechat": temp_instance.supports_wechat_extraction()
            })

        return sources

    @classmethod
    def register_crawler(cls, source_key: str, crawler_class: Type[BaseCrawler]):
        """
        注册新的爬虫（动态扩展用）

        参数:
            source_key: 数据源标识符
            crawler_class: 爬虫类
        """
        cls._crawlers[source_key.lower()] = crawler_class
        print(f"✅ 已注册爬虫: {source_key}")
