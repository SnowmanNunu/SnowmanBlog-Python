from django.contrib import admin, messages

from .models import Article, Category, Column, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "article_count", "deleted_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order",)

    @admin.display(description="文章数")
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "deleted_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class ArticleInline(admin.TabularInline):
    """专栏下的文章列表(只读)。"""

    model = Article
    extra = 0
    fields = ("title", "status", "published_at")
    readonly_fields = ("title", "status", "published_at")
    can_delete = False


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "article_count", "deleted_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ArticleInline,)

    @admin.display(description="文章数")
    def article_count(self, obj):
        return obj.articles.count()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """文章后台。

    - 默认仅展示未删除文章;回收站通过 ``show_trash`` action 查看并恢复。
    - 提供「恢复」「软删除到回收站」「硬删除」三种 action。
    """

    list_display = (
        "title", "status", "category", "column", "is_top",
        "published_at", "view_count", "like_count", "comment_count", "deleted_at",
    )
    list_filter = ("status", "category", "column", "is_top")
    search_fields = ("title", "summary", "content", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = (
        "author", "view_count", "like_count", "comment_count",
        "created_at", "updated_at", "deleted_at",
    )
    date_hierarchy = "published_at"
    autocomplete_fields = ("category", "column")
    filter_horizontal = ("tags",)

    fieldsets = (
        ("基本信息", {"fields": ("title", "slug", "summary", "content", "cover_image")}),
        (
            "归属",
            {"fields": ("author", "category", "column", "tags", "is_top")},
        ),
        (
            "发布",
            {
                "fields": ("status", "published_at"),
                "description": "将状态设为「定时发布」并填入发布时间,Celery Beat 到点会自动发布。",
            },
        ),
        ("统计", {"fields": ("view_count", "like_count", "comment_count")}),
        ("SEO", {"fields": ("seo_title", "seo_keywords", "seo_description")}),
        ("系统", {"fields": ("created_at", "updated_at", "deleted_at")}),
    )

    def get_queryset(self, request):
        """后台列表默认用软删除管理器(只显示未删);回收站视图用全部。"""
        qs = self.model.objects.all()  # 未删除
        if request.GET.get("trash") == "1":
            qs = self.model.all_objects.all()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    @admin.action(description="恢复选中文章")
    def restore_articles(self, request, queryset):
        """从回收站恢复。"""
        restored = 0
        for article in queryset:
            article.restore()
            restored += 1
        self.message_user(request, f"已恢复 {restored} 篇文章。", level=messages.SUCCESS)

    @admin.action(description="移入回收站(软删除)")
    def soft_delete_articles(self, request, queryset):
        n = queryset.count()
        queryset.delete()
        self.message_user(request, f"已将 {n} 篇文章移入回收站。")

    @admin.action(description="彻底删除(不可恢复)")
    def hard_delete_articles(self, request, queryset):
        n = queryset.count()
        queryset.hard_delete()
        self.message_user(request, f"已彻底删除 {n} 篇文章。", level=messages.WARNING)

    def save_model(self, request, obj, form, change):
        """保存时自动记录作者。"""
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    actions = ("restore_articles", "soft_delete_articles", "hard_delete_articles")
