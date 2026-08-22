from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.article_list, name="article_list"),
    path("search/", views.search_articles, name="search"),
    path("columns/", views.column_list, name="column_list"),
    path("columns/<uslug:slug>/", views.column_detail, name="column_detail"),
    path("category/<uslug:slug>/", views.category_detail, name="category_detail"),
    path("tag/<uslug:slug>/", views.tag_detail, name="tag_detail"),
    path("<uslug:slug>/", views.article_detail, name="article_detail"),
]
