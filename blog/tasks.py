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
    """评论相关的中后台邮件通知。

    场景:
    - 新增评论(回复)时,若目标评论开了邮件通知(notify=True),提醒被回复者;
    - 没有收件人地址时静默返回。
    """
    from interaction.models import Comment

    try:
        comment = Comment.objects.select_related("parent", "article").get(pk=comment_id)
    except Comment.DoesNotExist:
        return {"sent": 0}

    # 收件人:父评论用户有邮箱则发;否则发博主默认邮箱
    recipient = None
    if comment.parent and comment.parent.user and comment.parent.user.email:
        recipient = comment.parent.user.email
    elif settings.DEFAULT_FROM_EMAIL and settings.DEFAULT_FROM_EMAIL != "webmaster@localhost":
        recipient = settings.DEFAULT_FROM_EMAIL

    if not recipient:
        return {"sent": 0}

    subject = f"你收到了新的回复 · {comment.article.title}"
    message = (
        f"{comment.nickname} 回复了你的评论:\n\n"
        f"{comment.content}\n\n"
        f"文章: {comment.article.title}\n"
        f"链接: {comment.article.get_absolute_url()}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
    return {"sent": 1}
