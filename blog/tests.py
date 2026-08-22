from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
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


class ScheduledPublishTaskTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pubuser", password="test12345"
        )

    def test_publish_due_scheduled(self):
        """到期的定时文章被发布,未到期的不受影响。"""
        from .tasks import publish_scheduled_articles

        due = Article.objects.create(
            title="到期", status=Article.Status.SCHEDULED,
            published_at=timezone.now() - timezone.timedelta(minutes=1),
            author=self.user,
        )
        Article.objects.create(
            title="未来", status=Article.Status.SCHEDULED,
            published_at=timezone.now() + timezone.timedelta(days=1),
            author=self.user,
        )
        result = publish_scheduled_articles()
        self.assertEqual(result["published"], 1)
        # 到期篇已发布
        self.assertEqual(Article.objects.get(pk=due.pk).status, Article.Status.PUBLISHED)
        # 未来篇仍定时
        future = Article.objects.get(title="未来")
        self.assertEqual(future.status, Article.Status.SCHEDULED)


class AdminSmokeTest(TestCase):
    """验证后台各 changelist 可访问(登录后 200)。"""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="super", password="test12345", email="s@example.com"
        )
        self.client.login(username="super", password="test12345")

    def test_admin_changelists_accessible(self):
        from django.urls import reverse

        urls = [
            "admin:blog_article_changelist",
            "admin:blog_category_changelist",
            "admin:blog_tag_changelist",
            "admin:blog_column_changelist",
            "admin:interaction_comment_changelist",
            "admin:interaction_guestbook_changelist",
            "admin:interaction_articlelike_changelist",
            "admin:site_config_setting_changelist",
            "admin:site_config_friendlink_changelist",
        ]
        for name in urls:
            with self.subTest(name=name):
                resp = self.client.get(reverse(name))
                self.assertEqual(resp.status_code, 200, msg=name)

    def test_article_add_form_accessible(self):
        from django.urls import reverse

        resp = self.client.get(reverse("admin:blog_article_add"))
        self.assertEqual(resp.status_code, 200)


class FrontendViewTest(TestCase):
    """前台视图集成测试(文章列表/详情/搜索/分类/专栏/留言/评论/点赞)。"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer", password="test12345"
        )
        self.category = Category.objects.create(name="前端")
        self.tag = Tag.objects.create(name="测试")
        self.column = Column.objects.create(name="专栏A")
        self.article = Article.objects.create(
            title="前台测试文章",
            author=self.user,
            category=self.category,
            column=self.column,
            content="# 标题\n\n正文内容",
            summary="摘要",
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.article.tags.add(self.tag)

    def test_article_list_200(self):
        resp = self.client.get("/blog/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "前台测试文章")

    def test_article_detail_renders_markdown(self):
        resp = self.client.get(self.article.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<h1>标题</h1>", html=True)
        self.assertContains(resp, "前台测试文章")

    def test_category_and_tag_filter(self):
        cat_resp = self.client.get(reverse("blog:category_detail", args=[self.category.slug]))
        self.assertEqual(cat_resp.status_code, 200)
        tag_resp = self.client.get(reverse("blog:tag_detail", args=[self.tag.slug]))
        self.assertEqual(tag_resp.status_code, 200)

    def test_column_list_and_detail(self):
        resp = self.client.get("/blog/columns/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "专栏A")
        col_resp = self.client.get(reverse("blog:column_detail", args=[self.column.slug]))
        self.assertEqual(col_resp.status_code, 200)

    def test_search_finds_article(self):
        resp = self.client.get("/blog/search/", {"q": "前台"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "前台测试文章")

    def test_guestbook_page_and_submit(self):
        resp = self.client.get("/guestbook/")
        self.assertEqual(resp.status_code, 200)
        post = self.client.post(
            "/guestbook/",
            {"nickname": "访客", "content": "你好"},
            follow=True,
        )
        self.assertEqual(post.status_code, 200)
        from interaction.models import GuestBook

        self.assertTrue(GuestBook.objects.filter(nickname="访客").exists())

    def test_comment_submit(self):
        from interaction.models import Comment

        resp = self.client.post(
            reverse("interaction:submit_comment", args=[self.article.slug]),
            {"content": "一条评论", "nickname": "评论者"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Comment.objects.filter(article=self.article).count(), 1)

    def test_article_like_increments(self):
        resp = self.client.post(
            reverse("interaction:toggle_like", args=[self.article.slug]), follow=True
        )
        self.assertEqual(resp.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.like_count, 1)

    def test_draft_not_visible_in_list(self):
        Article.objects.create(
            title="草稿不显示", author=self.user, content="x", status=Article.Status.DRAFT
        )
        resp = self.client.get("/blog/")
        self.assertNotContains(resp, "草稿不显示")


        self.assertTrue(issubclass(Article, SoftDeletableModel))
