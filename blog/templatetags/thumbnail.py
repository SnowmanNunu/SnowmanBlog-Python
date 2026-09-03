"""封面缩略图过滤器:动态生成并缓存等比缩放图,供列表页快速加载。"""

import os

from django import template
from django.conf import settings
from PIL import Image

register = template.Library()


def _thumbnail(src_field, width, height):
    """根据 ImageFieldFile 生成缩略图,返回其 URL;失败则返回原图 URL。"""
    if not src_field or not src_field.name:
        return ""
    try:
        base, _ext = os.path.splitext(src_field.name)
        thumb_rel = f"thumbnails/{os.path.basename(base)}_{width}x{height}.jpg"
        thumb_abs = os.path.join(settings.MEDIA_ROOT, thumb_rel)
        if not os.path.exists(thumb_abs):
            img = Image.open(src_field)
            img = img.convert("RGB")
            img.thumbnail((width, height), Image.LANCZOS)
            os.makedirs(os.path.dirname(thumb_abs), exist_ok=True)
            img.save(thumb_abs, "JPEG", quality=82)
        return f"{settings.MEDIA_URL}{thumb_rel}"
    except Exception:
        # 任何失败回退到原始文件 URL
        return src_field.url


@register.filter(name="thumbnail")
def thumbnail(value, size="400x300"):
    """用法: {{ article.cover_image|thumbnail:"400x300" }}"""
    try:
        w, h = size.lower().split("x")
        width, height = int(w), int(h)
    except (ValueError, AttributeError):
        return value.url if hasattr(value, "url") else value
    return _thumbnail(value, width, height)
