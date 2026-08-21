"""共享软删除基类与 Manager(对应原项目 Laravel SoftDeletes)。

用法: 让模型继承 ``SoftDeletableModel``,即自动具备:
- ``deleted_at`` 时间戳字段(软删除标记)
- 默认 ``objects`` 管理器仅返回未删除记录
- ``all_objects`` 返回全部(含已删除)
- ``.delete()`` 默认软删除,``.hard_delete()`` 真删除,``.restore()`` 恢复
- ``deleted_only``、``all_with_deleted`` 便捷查询
"""

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        """对 QuerySet 内所有记录执行软删除。"""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """真删除。"""
        return super().delete()


class SoftDeleteManager(models.Manager):
    """默认管理器:仅返回未删除记录。"""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).exclude(
            deleted_at__isnull=False
        )

    def all_with_deleted(self):
        """包含已删除记录(实际已删除形态)。"""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        """仅已删除(回收站)记录。"""
        return self.all_with_deleted().filter(deleted_at__isnull=False)


class SoftDeletableModel(models.Model):
    deleted_at = models.DateTimeField("删除时间", null=True, blank=True, editable=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft=True):
        if soft:
            self.deleted_at = timezone.now()
            self.save(using=using)
        else:
            return super().delete(using=using, keep_parents=keep_parents)

    def hard_delete(self, using=None, keep_parents=False):
        """真删除(从数据库移除)。"""
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self, using=None):
        """从回收站恢复。"""
        self.deleted_at = None
        self.save(using=using)