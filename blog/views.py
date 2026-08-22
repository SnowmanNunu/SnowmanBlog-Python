import mistune
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from interaction.models import Comment

from .models import Article, Category, Column, Tag

markdown = mistune.create_markdown(escape=False, plugins=["strikethrough", "table"])

PAGE_SIZE = 6


def _published_articles():
    """前台仅展示已发布文章。"""
    return Article.published.select_related("category", "column", "author")


def _paginate(request, queryset, per_page=PAGE_SIZE):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return page_obj


@require_GET
def article_list(request):
    """文章列表(分页)。"""
    queryset = _published_articles()
    # 可选分类/标签筛选参数
    category_slug = request.GET.get("category")
    tag_slug = request.GET.get("tag")
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)
    context = {
        "page_obj": _paginate(request, queryset),
        "articles": _paginate(request, queryset).object_list,
        "categories": Category.objects.all(),
        "columns": Column.objects.all(),
    }
    return render(request, "blog/article_list.html", context)


@require_GET
def article_detail(request, slug):
    """文章详情:正文渲染、上一篇/下一篇、相关推荐、评论。"""
    article = get_object_or_404(_published_articles(), slug=slug)

    # 上一篇 / 下一篇(按发布时间排序,UTF slug 直接对比)
    prev_article = (
        Article.published.filter(published_at__lt=article.published_at)
        .order_by("-published_at")
        .first()
    )
    next_article = (
        Article.published.filter(published_at__gt=article.published_at)
        .order_by("published_at")
        .first()
    )

    # 相关推荐:同分类或同标签,排除自身
    related = Article.published.exclude(pk=article.pk)
    tag_q = Q(tags__in=article.tags.all())
    cat_q = Q(category=article.category)
    related = related.filter(tag_q | cat_q).distinct()[:5]

    comments = Comment.objects.filter(
        article=article, status=Comment.Status.APPROVED, parent__isnull=True
    ).select_related("user")

    context = {
        "article": article,
        "content_html": markdown(article.content),
        "prev_article": prev_article,
        "next_article": next_article,
        "related_articles": related,
        "comments": comments,
    }
    return render(request, "blog/article_detail.html", context)


@require_GET
def column_list(request):
    """专栏列表。"""
    columns = Column.objects.filter(articles__isnull=False).distinct()
    return render(request, "blog/column_list.html", {"columns": columns})


@require_GET
def column_detail(request, slug):
    """专栏内文章浏览。"""
    column = get_object_or_404(Column.objects.all(), slug=slug)
    articles = _published_articles().filter(column=column)
    context = {
        "column": column,
        "page_obj": _paginate(request, articles),
    }
    return render(request, "blog/column_detail.html", context)


@require_GET
def category_detail(request, slug):
    category = get_object_or_404(Category.objects.all(), slug=slug)
    articles = _published_articles().filter(category=category)
    return render(
        request,
        "blog/article_list.html",
        {
            "page_obj": _paginate(request, articles),
            "category": category,
            "categories": Category.objects.all(),
        },
    )


@require_GET
def tag_detail(request, slug):
    tag = get_object_or_404(Tag.objects.all(), slug=slug)
    articles = _published_articles().filter(tags__slug=slug)
    return render(
        request,
        "blog/article_list.html",
        {"page_obj": _paginate(request, articles), "tag": tag},
    )


@require_GET
def search_articles(request):
    """全站搜索(LIKE 匹配标题/内容/摘要)。"""
    q = request.GET.get("q", "").strip()
    results = _published_articles().filter(Q(title__icontains=q)) if q else []
    return render(
        request,
        "blog/search.html",
        {"query": q, "page_obj": _paginate(request, results) if q else results},
    )

