import os

from celery import Celery

# 设置 Django 默认配置模块
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("snowmanblog")

# 从 Django settings 读取 Celery 配置(namespace='CELERY' 使 CELERY_* 生效)
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现各 app 中的 tasks.py
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
