from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Article


class ArticleSitemap(Sitemap):
    """文章站点地图(仅已发布文章)。"""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.published.all()

    def lastmod(self, obj):
        return obj.published_at


class StaticViewSitemap(Sitemap):
    """主要静态页面地图。"""

    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return [
            "blog:article_list",
            "blog:column_list",
            "interaction:guestbook",
        ]

    def location(self, item):
        return reverse(item)
