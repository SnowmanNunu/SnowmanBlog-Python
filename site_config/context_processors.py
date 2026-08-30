"""全站 context processor:把前台可见的站点设置注入每个模板。"""

from .models import Setting


def site_settings(request):
    """提供 site_title / site_description,供 base 模板使用。

    读取 Setting 表中 is_public=True 的记录;缺失时用默认值,保证任何页面都能渲染。
    """
    defaults = {
        "site_title": "SnowmanBlog",
        "site_description": "用 Django 构建的个人博客",
    }
    try:
        for s in Setting.objects.filter(is_public=True):
            defaults[s.key] = s.typed_value
    except Exception:
        pass
    return defaults
