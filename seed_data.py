import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from blog.models import Article, Category, Column, Tag
from interaction.models import GuestBook

u = get_user_model().objects.get(username="admin")
cat = Category.objects.get_or_create(name="技术")[0]
col = Column.objects.get_or_create(name="Python 系列")[0]
t1 = Tag.objects.get_or_create(name="Django")[0]
t2 = Tag.objects.get_or_create(name="教程")[0]

titles = [
    "Django 入门指南",
    "Celery 异步任务实战",
    "Redis 缓存最佳实践",
    "软删除实现详解",
    "Markdown 渲染技巧",
]
for i, t in enumerate(titles):
    a, created = Article.objects.get_or_create(
        title=t,
        defaults=dict(
            author=u,
            category=cat,
            column=col,
            summary="这是 " + t + " 的摘要",
            content="# " + t + "\n\n这是一篇关于 **" + t + "** 的文章。\n\n- 要点一\n- 要点二",
            status=Article.Status.PUBLISHED,
            published_at=timezone.now() - timezone.timedelta(days=i),
            is_top=(i == 0),
        ),
    )
    a.tags.add(t1, t2)

print("seeded articles:", Article.objects.count())
GuestBook.objects.get_or_create(
    nickname="访客小王",
    defaults=dict(email="w@x.com", content="欢迎来访!", is_verified=True),
)
print("guestbook:", GuestBook.objects.count())
