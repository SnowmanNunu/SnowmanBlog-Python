import json
from itertools import chain

from django.apps import apps
from django.contrib import admin, messages
from django.core import serializers
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone

from .models import FriendLink, Setting


def _backup_querysets():
    """汇总核心业务 app 的所有模型 queryset。"""
    results = []
    for app_label in ("blog", "interaction", "site_config"):
        app_config = apps.get_app_config(app_label)
        for model in app_config.get_models():
            results.append(model.objects.all())
    return results


@admin.register(FriendLink)
class FriendLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "url", "description")


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "value_type", "group", "is_public")
    list_filter = ("group", "value_type", "is_public")
    search_fields = ("key", "value")
    list_editable = ("value",)

    @admin.action(description="清除全部缓存")
    def clear_cache(self, request, queryset):
        cache.clear()
        self.message_user(request, "已清除全部缓存。", level=messages.SUCCESS)

    @admin.action(description="导出站点全部设置(JSON)")
    def export_settings(self, request, queryset):
        payload = {s.key: s.typed_value for s in queryset}
        data = json.dumps(payload, ensure_ascii=False, indent=2)
        response = HttpResponse(data, content_type="application/json")
        response["Content-Disposition"] = (
            f'attachment; filename="settings_{timezone.now():%Y%m%d%H%M}.json"'
        )
        return response

    @admin.action(description="备份全站数据(JSON 可恢复)")
    def backup_database(self, request, queryset=None):
        """导出全部业务模型数据,作为数据库备份下载。"""
        all_objects = list(chain.from_iterable(_backup_querysets()))
        data = serializers.serialize("json", all_objects, ensure_ascii=False)
        response = HttpResponse(data, content_type="application/json")
        response["Content-Disposition"] = (
            f'attachment; filename="backup_{timezone.now():%Y%m%d%H%M}.json"'
        )
        return response

    actions = ("clear_cache", "export_settings", "backup_database")
