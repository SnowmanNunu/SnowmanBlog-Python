from celery import shared_task
from django.utils import timezone

from .models import Article


@shared_task(name="blog.publish_scheduled_articles")
def publish_scheduled_articles():
    """扫描到期定时文章并发布。

    将 status=scheduled 且 published_at 已到点的文章置为 published。
    由 Celery Beat 定期(如每分钟)触发。
    """
    now = timezone.now()
    due = Article.objects.filter(
        status=Article.Status.SCHEDULED, published_at__lte=now
    )
    count = due.count()
    if count:
        due.update(status=Article.Status.PUBLISHED)
    return {"published": count}