from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Article


@shared_task(name="blog.publish_scheduled_articles")
def publish_scheduled_articles():
    """扫描到期定时文章并发布。

    将 status=scheduled 且 published_at 已到点的文章置为 published。
    由 Celery Beat 定期(如每分钟)触发。
    """
    now = timezone.now()
    due = Article.objects.filter(status=Article.Status.SCHEDULED, published_at__lte=now)
    count = due.count()
    if count:
        due.update(status=Article.Status.PUBLISHED)
    return {"published": count}


@shared_task(name="interaction.send_comment_notification")
def send_comment_notification(comment_id):
    """评论被回复或新评论时,通知父评论者(若父评论开启 notify)。"""
    from interaction.models import Comment

    try:
        comment = Comment.objects.select_related("parent", "parent__user", "article").get(
            pk=comment_id
        )
    except Comment.DoesNotExist:
        return {"sent": 0}

    parent = comment.parent
    # 仅当父评论存在且开启了邮件通知时才发送
    if not parent or not parent.notify:
        return {"sent": 0}

    # 收件人:父评论的邮箱(优先)或父评论用户的账号邮箱
    recipient = parent.email or (parent.user.email if parent.user else None)
    if not recipient:
        return {"sent": 0}

    subject = f"你收到了新的回复 · {comment.article.title}"
    message = (
        f"{comment.nickname} 回复了你的评论:\n\n"
        f"{comment.content}\n\n"
        f"文章: {comment.article.title}\n"
        f"链接: http://pyblog.snowmannunu.top{comment.article.get_absolute_url()}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    return {"sent": 1}
