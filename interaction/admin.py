from django.contrib import admin, messages

from .models import ArticleLike, Comment, GuestBook


class ReplyInline(admin.TabularInline):
    """评论嵌套回复 Inline。"""

    model = Comment
    fk_name = "parent"
    extra = 0
    fields = ("nickname", "content", "status", "created_at")
    readonly_fields = ("nickname", "content", "created_at")
    can_delete = False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("nickname", "short_content", "article", "parent", "status", "is_admin", "created_at")
    list_filter = ("status", "is_admin")
    search_fields = ("content", "nickname", "reply_to_nick", "user__username")
    inlines = (ReplyInline,)
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    fieldsets = (
        ("文章", {"fields": ("article", "parent", "reply_to_nick")}),
        ("访客", {"fields": ("nickname", "email", "avatar", "user")}),
        ("内容", {"fields": ("content",)}),
        ("审核", {"fields": ("status", "is_admin", "notify")}),
        ("时间", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="内容")
    def short_content(self, obj):
        return obj.content[:50]

    @admin.action(description="通过审核")
    def approve_comments(self, request, queryset):
        queryset.update(status=Comment.Status.APPROVED)
        self.message_user(request, f"已通过 {queryset.count()} 条评论审核。")

    @admin.action(description="拒绝评论")
    def reject_comments(self, request, queryset):
        queryset.update(status=Comment.Status.REJECTED)
        self.message_user(request, f"已拒绝 {queryset.count()} 条评论。")

    actions = ("approve_comments", "reject_comments")


@admin.register(GuestBook)
class GuestBookAdmin(admin.ModelAdmin):
    list_display = ("nickname", "short_content", "is_verified", "is_admin", "created_at")
    list_filter = ("is_verified", "is_admin")
    search_fields = ("nickname", "content", "reply")
    readonly_fields = ("created_at",)

    @admin.display(description="留言内容")
    def short_content(self, obj):
        return obj.content[:30]

    @admin.action(description="审核通过留言")
    def verify_guestbooks(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"已审核通过 {queryset.count()} 条留言。")


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "visitor_key", "created_at")
    search_fields = ("article__title", "user__username", "visitor_key")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
