from django.test import TestCase

from blog.models import Article

from .soft_delete import SoftDeletableModel


class HealthEndpointTest(TestCase):
    def test_health_ok(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode(), "ok")


class SoftDeleteManagerTest(TestCase):
    def test_default_manager_excludes_deleted(self):
        """软删除后默认管理器不可见,all_objects/deleted_only 可见。"""
        article = Article.objects.create(title="待删除", content="x")
        article.delete()

        self.assertEqual(Article.objects.count(), 0)
        self.assertEqual(Article.objects.deleted_only().count(), 1)
        self.assertEqual(Article.all_objects.count(), 1)

        # restore 后重新可见
        article.restore()
        self.assertEqual(Article.objects.count(), 1)

    def test_queryset_delete_soft_deletes(self):
        """QuerySet.delete() 执行的是软删除。"""
        Article.objects.create(title="q1", content="x")
        Article.objects.create(title="q2", content="x")
        Article.objects.all().delete()
        self.assertEqual(Article.objects.count(), 0)
        self.assertEqual(Article.all_objects.count(), 2)

    def test_abstract_base_registered(self):
        self.assertTrue(issubclass(Article, SoftDeletableModel))
