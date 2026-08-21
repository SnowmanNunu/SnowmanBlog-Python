from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def index(request):
    """首页最小验证视图。"""
    message = "Django 脚手架最小验证成功 ✅"
    return render(request, "core/index.html", {"title": "SnowmanBlog", "message": message})


@require_GET
def health(request):
    """健康检查端点,验证 Django 能正常响应。"""
    return HttpResponse("ok", content_type="text/plain")
