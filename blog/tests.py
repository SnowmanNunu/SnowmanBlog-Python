from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.soft_delete import SoftDeletableModel
from .models import Article, Category, Column, Tag
from interaction.models import ArticleLike, Comment, GuestBook


class ArticleModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester", password="test12345"
        )
        self.category = Category.objects.create(name="技术")
        self.column = Column.objects.create(name="Python 系列")

    def test_article_creation_and_slug(self):
        """文章创建时自动生成 slug,并绑定分类/专栏/标签。"""
        tag = Tag.objects.create(name="Django")
        article = Article.objects.create(
            title="你好世界",
            author=self.user,
            category=self.category,
            column=self.column,
            content="# 标题",
            summary="摘要",
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        article.tags.add(tag)
        self.assertEqual(article.slug, "你好世界")
        self.assertEqual(article.category, self.category)
        self.assertEqual(article.tags.count(), 1)

    def test_soft_delete_and_restore(self):
        """软删除后默认不可见,恢复后重新可见;真删除从库中移除。"""
        article = Article.objects.create(
            title="回收站测试", author=self.user, content="content"
        )
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())

        article.delete()
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())
        self.assertTrue(Article.objects.deleted_only().filter(pk=article.pk).exists())

        article.restore()
        self.assertTrue(Article.objects.filter(pk=article.pk).exists())

        article.hard_delete()
        self.assertFalse(Article.all_objects.filter(pk=article.pk).exists())

    def test_published_manager_only_returns_published(self):
        Article.objects.create(
            title="已发布", status=Article.Status.PUBLISHED,
            published_at=timezone.now(), author=self.user,
        )
        Article.objects.create(title="草稿", status=Article.Status.DRAFT, author=self.user)
        self.assertEqual(Article.published.count(), 1)

    def test_scheduled_not_yet_visible(self):
        """未到发布时间的定时文章不属于已发布集合。"""
        Article.objects.create(
            title="未来发布", status=Article.Status.SCHEDULED,
            published_at=timezone.now() + timezone.timedelta(days=1),
            author=self.user,
        )
        self.assertEqual(Article.published.count(), 0)

    def test_comment_nesting(self):
        """评论自关联嵌套回复。"""
        article = Article.objects.create(title="评论测试", author=self.user, content="x")
        root = Comment.objects.create(
            article=article, nickname="访客A", content="顶层评论"
        )
        reply = Comment.objects.create(
            article=article, parent=root, nickname="访客B",
            content="回复A", reply_to_nick="访客A",
        )
        self.assertEqual(root.replies.count(), 1)
        self.assertEqual(reply.parent, root)
        self.assertEqual(Comment.objects.filter(parent__isnull=True).count(), 1)

    def test_article_like_unique_constraint(self):
        """同一访客对同一文章不能重复点赞。"""
        article = Article.objects.create(title="点赞测试", author=self.user, content="x")
        ArticleLike.objects.create(article=article, visitor_key="visitor-1")
        with self.assertRaises(Exception):
            ArticleLike.objects.create(article=article, visitor_key="visitor-1")

    def test_guestbook_creation(self):
        book = GuestBook.objects.create(nickname="访客", content="留言内容")
        self.assertEqual(GuestBook.objects.get(pk=book.pk).nickname, "访客")

    def test_abstract_soft_delete(self):
        """确认抽象基类被覆盖(防御性检查)。"""
        self.assertTrue(issubclass(Article, SoftDeletableModel))
