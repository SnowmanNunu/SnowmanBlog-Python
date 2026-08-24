"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, register_converter

from blog.converters import UnicodeSlugConverter
from blog.feeds import LatestArticleFeed
from blog.sitemaps import ArticleSitemap, StaticViewSitemap

# 全局注册 Unicode slug converter(支持中文 slug),供各 app 使用
register_converter(UnicodeSlugConverter, "uslug")

sitemaps = {
    "articles": ArticleSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("rss/", LatestArticleFeed(), name="rss_feed"),
    path("rss.xml", LatestArticleFeed(), name="rss_feed_xml"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # 具体前缀优先:留言板 / 健康检查
    path("", include("interaction.urls")),
    path("", include("core.urls")),
    # 前台整体挂在根路径(不再使用 /blog/ 前缀):
    #  / → 文章列表, /<slug> → 文章详情, /columns → 专栏, /search → 搜索
    path("", include("blog.urls")),
]
