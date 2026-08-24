import hashlib

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from blog.models import Article

from .models import ArticleLike, Comment, GuestBook


@require_http_methods(["GET", "POST"])
def guestbook(request):
    """留言板:展示 + 提交留言。"""
    if request.method == "POST":
        nickname = request.POST.get("nickname", "").strip()
        email = request.POST.get("email", "").strip()
        content = request.POST.get("content", "").strip()
        if nickname and content:
            GuestBook.objects.create(
                nickname=nickname,
                email=email,
                content=content,
                is_verified=False,  # 默认待审核
            )
            messages.success(request, "留言已提交,感谢你的留言!")
            return redirect(reverse("interaction:guestbook"))
        messages.error(request, "昵称和内容不能为空。")
        return redirect(reverse("interaction:guestbook"))

    # 仅展示已审核的留言
    entries = GuestBook.objects.filter(is_verified=True)
    return render(request, "interaction/guestbook.html", {"entries": entries})


@require_POST
def submit_comment(request, slug):
    """提交评论(嵌套回复)。"""
    article = get_object_or_404(Article.published, slug=slug)
    content = request.POST.get("content", "").strip()
    parent_id = request.POST.get("parent_id") or None
    nickname = request.POST.get("nickname", "").strip() or (
        request.user.username if request.user.is_authenticated else "匿名"
    )

    parent = None
    reply_to = ""
    if parent_id:
        parent = Comment.objects.filter(pk=parent_id).first()
        if parent:
            reply_to = parent.nickname

    if content:
        Comment.objects.create(
            article=article,
            parent=parent,
            user=request.user if request.user.is_authenticated else None,
            nickname=nickname,
            content=content,
            reply_to_nick=reply_to,
            status=Comment.Status.PENDING,  # 默认待审核
        )
        # 更新文章评论计数
        total = Comment.objects.filter(article=article).count()
        Article.objects.filter(pk=article.pk).update(comment_count=total)
        messages.success(request, "评论已提交,审核通过后将显示。")
    else:
        messages.error(request, "评论内容不能为空。")

    return redirect(reverse("blog:article_detail", kwargs={"slug": article.slug}))


@require_POST
def toggle_like(request, slug):
    """点赞/取消点赞(Redis 计数 + 唯一约束防刷)。"""
    article = get_object_or_404(Article.published, slug=slug)
    # 访客标识:IP + UA 哈希(简单防刷)
    ua = request.META.get("HTTP_USER_AGENT", "")
    visitor_key = hashlib.sha256(f"{request.META.get('REMOTE_ADDR')}|{ua}".encode()).hexdigest()
    user = request.user if request.user.is_authenticated else None

    try:
        with transaction.atomic():
            ArticleLike.objects.create(article=article, user=user, visitor_key=visitor_key)
        liked = True
    except IntegrityError:
        # 已点赞 → 取消:删除用户点赞或访客点赞
        queryset = ArticleLike.objects.filter(article=article)
        if user:
            queryset = queryset.filter(user=user)
        else:
            queryset = queryset.filter(visitor_key=visitor_key)
        queryset.delete()
        liked = False

    new_count = ArticleLike.objects.filter(article=article).count()
    Article.objects.filter(pk=article.pk).update(like_count=new_count)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "count": new_count})
    return redirect(reverse("blog:article_detail", kwargs={"slug": article.slug}))
