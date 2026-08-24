from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Article

from .models import ArticleLike, Comment, GuestBook


class InteractionTestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="inter", password="test12345")
        self.article = Article.objects.create(
            title="互动测试文章",
            author=self.user,
            content="内容",
            status=Article.Status.PUBLISHED,
            published_at=timezone.now(),
        )


class GuestBookTests(TestCase):
    def test_submit_and_hidden_until_verified(self):
        """留言提交后默认隐藏,审核通过后才展示。"""
        resp = self.client.post("/guestbook/", {"nickname": "小明", "content": "你好"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        entry = GuestBook.objects.get(nickname="小明")
        self.assertFalse(entry.is_verified)
        # 未审核 → 页面不显示
        page = self.client.get("/guestbook/")
        self.assertNotContains(page, "你好")
        # 审核后 → 展示
        entry.is_verified = True
        entry.save()
        self.assertContains(self.client.get("/guestbook/"), "你好")

    def test_empty_nickname_rejected(self):
        count_before = GuestBook.objects.count()
        self.client.post("/guestbook/", {"nickname": "", "content": "x"})
        self.assertEqual(GuestBook.objects.count(), count_before)


class CommentTests(InteractionTestBase):
    def test_nested_reply_flow(self):
        """顶层评论 + 嵌套回复,均需审核;计数随提交更新。"""
        url = reverse("interaction:submit_comment", args=[self.article.slug])
        self.client.post(url, {"content": "顶层评论", "nickname": "访客A"})
        root = Comment.objects.get(content="顶层评论")
        self.assertEqual(root.status, Comment.Status.PENDING)

        self.client.post(url, {"content": "回复A", "nickname": "访客B", "parent_id": root.id})
        reply = Comment.objects.get(content="回复A")
        self.assertEqual(reply.parent, root)
        self.assertEqual(reply.reply_to_nick, "访客A")
        # 评论数随提交更新(与视图逻辑一致)
        self.article.refresh_from_db()
        self.assertEqual(self.article.comment_count, 2)

    def test_empty_content_rejected(self):
        url = reverse("interaction:submit_comment", args=[self.article.slug])
        self.client.post(url, {"content": "", "nickname": "x"})
        self.assertEqual(Comment.objects.count(), 0)


class LikeTests(InteractionTestBase):
    def test_like_then_unlike(self):
        """点赞 +1,重复点赞取消归零(AJAX 返回 JSON)。"""
        url = reverse("interaction:toggle_like", args=[self.article.slug])
        self.client.post(url)  # 点赞
        self.assertEqual(ArticleLike.objects.count(), 1)
        self.article.refresh_from_db()
        self.assertEqual(self.article.like_count, 1)

        # AJAX 再次点赞 → 取消
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        data = resp.json()
        self.assertFalse(data["liked"])
        self.assertEqual(data["count"], 0)
        self.article.refresh_from_db()
        self.assertEqual(self.article.like_count, 0)

    def test_anonymous_like_recorded_with_visitor_key(self):
        self.client.post(
            reverse("interaction:toggle_like", args=[self.article.slug]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        like = ArticleLike.objects.get()
        self.assertIsNone(like.user)
        self.assertTrue(like.visitor_key)


class GuestBookModelTest(TestCase):
    def test_ordering_newest_first(self):
        GuestBook.objects.create(nickname="早的", content="a", is_verified=True)
        later = GuestBook.objects.create(nickname="晚的", content="b", is_verified=True)
        self.assertEqual(GuestBook.objects.first(), later)
