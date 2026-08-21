from django.db import models


class Setting(models.Model):
    """站点设置,key-value 结构。"""

    key = models.CharField("键", max_length=100, unique=True)
    value = models.TextField("值", blank=True)
    value_type = models.CharField(
        "值类型",
        max_length=20,
        choices=[
            ("str", "字符串"),
            ("int", "整数"),
            ("bool", "布尔"),
            ("json", "JSON"),
        ],
        default="str",
    )
    group = models.CharField("分组", max_length=50, blank=True, default="site")
    is_public = models.BooleanField("前台可见", default=False)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "站点设置"
        verbose_name_plural = "站点设置"
        ordering = ["group", "key"]

    def __str__(self):
        return self.key

    @property
    def typed_value(self):
        """按 value_type 转换为对应 Python 类型。"""
        if self.value_type == "int":
            return int(self.value) if self.value else 0
        if self.value_type == "bool":
            return self.value in ("1", "true", "True", "yes", "on")
        if self.value_type in ("choice", "json"):
            try:
                import json

                return json.loads(self.value) if self.value else None
            except (json.JSONDecodeError, ValueError):
                return self.value
        return self.value


class FriendLink(models.Model):
    """友情链接。"""

    title = models.CharField("名称", max_length=60)
    url = models.URLField("链接", max_length=255)
    logo = models.ImageField("Logo", upload_to="friends/", blank=True, null=True)
    description = models.CharField("描述", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_active = models.BooleanField("是否启用", default=True)

    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "友链"
        verbose_name_plural = "友链"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title
