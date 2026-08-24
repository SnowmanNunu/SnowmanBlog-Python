from django.contrib.syndication.views import Feed

from .models import Article


class LatestArticleFeed(Feed):
    """最新文章 RSS Feed。"""

    title = "SnowmanBlog 最新文章"
    link = "/"
    description = "SnowmanBlog 最新发布的文章"

    def items(self):
        return Article.published.order_by("-published_at")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary or item.content[:200]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at
