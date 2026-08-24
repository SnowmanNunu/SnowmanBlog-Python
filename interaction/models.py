from django.conf import settings
from django.db import models


class Comment(models.Model):
    """文章评论,自关联支持嵌套回复。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    article = models.ForeignKey(
        "blog.Article",
        verbose_name="文章",
        related_name="comments",
        on_delete=models.CASCADE,
    )
    parent = models.ForeignKey(
        "self",
        verbose_name="父评论",
        related_name="replies",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        related_name="comments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    nickname = models.CharField("昵称", max_length=50, blank=True)
    avatar = models.CharField("头像", max_length=255, blank=True)

    content = models.TextField("内容")
    is_admin = models.BooleanField("是否博主", default=False)
    notify = models.BooleanField("收到回复邮件通知", default=False)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.PENDING)

    # 冗余:记录回复目标昵称,便于展示「回复 @xxx」
    reply_to_nick = models.CharField("回复对象昵称", max_length=50, blank=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.nickname or '匿名'}: {self.content[:20]}"


class GuestBook(models.Model):
    """访客留言板,博主后台回复。"""

    nickname = models.CharField("昵称", max_length=50)
    email = models.EmailField("邮箱", blank=True)
    content = models.TextField("留言内容")
    reply = models.TextField("博主回复", blank=True)
    is_admin = models.BooleanField("是否博主", default=False)
    is_verified = models.BooleanField("是否审核通过", default=False)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.nickname}: {self.content[:20]}"


class ArticleLike(models.Model):
    """文章点赞记录(用于计数与简单防刷)。"""

    article = models.ForeignKey(
        "blog.Article",
        verbose_name="文章",
        related_name="likes",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="用户",
        related_name="article_likes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # 匿名点赞用客户端标识(如 IP + UA 哈希)防刷
    visitor_key = models.CharField("访客标识", max_length=128, blank=True)
    created_at = models.DateTimeField("点赞时间", auto_now_add=True)

    class Meta:
        verbose_name = "点赞"
        verbose_name_plural = "点赞"
        ordering = ["-created_at"]
        constraints = [
            # 同一用户对同一文章只能点赞一次(user 为 NULL 时 SQLite/MySQL 均允许多个)
            models.UniqueConstraint(fields=["article", "user"], name="uniq_article_user_like"),
            # 同一访客标识对同一文章只能点赞一次
            models.UniqueConstraint(
                fields=["article", "visitor_key"], name="uniq_article_visitor_like"
            ),
        ]

    def __str__(self):
        return f"点赞#{self.article_id}"
