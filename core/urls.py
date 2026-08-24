from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # 根路径 "/" 已由 blog 前台接管(文章列表)。core 仅保留健康检查。
    path("health/", views.health, name="health"),
]
