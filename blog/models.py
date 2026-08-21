from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from core.soft_delete import SoftDeleteManager, SoftDeletableModel


class PublishedArticleManager(SoftDeleteManager):
    """便捷管理器:仅返回已发布文章(status=published 且已到发布时间)。"""

    def get_queryset(self):
        from .models import Article

        return (
            super()
            .get_queryset()
            .filter(status=Article.Status.PUBLISHED, published_at__isnull=False)
        )


class Category(SoftDeletableModel):
    """文章分类。"""

    name = models.CharField("分类名称", max_length=50)
    slug = models.SlugField("别名", max_length=60, unique=True, blank=True)
    description = models.CharField("描述", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Tag(SoftDeletableModel):
    """文章标签。"""

    name = models.CharField("标签名称", max_length=30)
    slug = models.SlugField("别名", max_length=40, unique=True, blank=True)

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ["id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Column(SoftDeletableModel):
    """专栏:按内容系列聚合文章。"""

    name = models.CharField("专栏名称", max_length=60)
    slug = models.SlugField("别名", max_length=70, unique=True, blank=True)
    description = models.TextField("简介", blank=True)
    cover = models.ImageField("封面图", upload_to="columns/", blank=True, null=True)
    sort_order = models.PositiveIntegerField("排序", default=0)

    class Meta:
        verbose_name = "专栏"
        verbose_name_plural = "专栏"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Article(SoftDeletableModel):
    """文章。

    - ``status`` 控制发布状态(草稿 / 已发布 / 定时发布)
    - 软删除(``deleted_at``)支撑回收站;真删除用 ``hard_delete``
    - ``published_at`` 为实际发布时间,定时发布由 Celery Beat 扫描到期草稿置为已发布
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        PUBLISHED = "published", "已发布"
        SCHEDULED = "scheduled", "定时发布"
        TRASHED = "trashed", "回收站"

    title = models.CharField("标题", max_length=200)
    slug = models.SlugField("别名", max_length=220, unique=True, blank=True)
    summary = models.TextField("摘要", blank=True)
    content = models.TextField("正文(Markdown)")
    cover_image = models.ImageField("封面图", upload_to="articles/", blank=True, null=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="作者",
        related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name="分类",
        related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    column = models.ForeignKey(
        Column,
        verbose_name="专栏",
        related_name="articles",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="标签", blank=True, related_name="articles"
    )

    status = models.CharField(
        "状态", max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    is_top = models.BooleanField("置顶", default=False)
    published_at = models.DateTimeField("发布时间", null=True, blank=True, db_index=True)

    view_count = models.PositiveIntegerField("浏览量", default=0)
    like_count = models.PositiveIntegerField("点赞数", default=0, editable=False)
    comment_count = models.PositiveIntegerField("评论数", default=0, editable=False)

    # SEO(Meta)
    seo_title = models.CharField("SEO 标题", max_length=200, blank=True)
    seo_keywords = models.CharField("SEO 关键词", max_length=200, blank=True)
    seo_description = models.CharField("SEO 描述", max_length=255, blank=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = SoftDeleteManager()
    published = PublishedArticleManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = "文章"
        verbose_name_plural = "文章"
        ordering = ["-is_top", "-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:article_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
