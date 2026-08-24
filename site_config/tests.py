import json

from django.test import TestCase

from .models import FriendLink, Setting


class SettingTest(TestCase):
    def test_typed_value_conversions(self):
        """value_type 各类型正确转换。"""
        cases = {
            "str": ("snowman", "snowman"),
            "int": ("42", 42),
            "bool": ("true", True),
            "json": ('{"a": 1}', {"a": 1}),
        }
        for i, (vtype, (raw, expected)) in enumerate(cases.items()):
            s = Setting.objects.create(key=f"k{i}", value=raw, value_type=vtype)
            self.assertEqual(s.typed_value, expected, msg=vtype)

    def test_bool_false_values(self):
        s = Setting.objects.create(key="b0", value="0", value_type="bool")
        self.assertFalse(s.typed_value)

    def test_invalid_json_falls_back_to_raw(self):
        s = Setting.objects.create(key="bad", value="{oops", value_type="json")
        self.assertEqual(s.typed_value, "{oops")


class SettingAdminActionTest(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        get_user_model().objects.create_superuser(
            username="cfgadmin", password="test12345", email="c@example.com"
        )
        self.client.login(username="cfgadmin", password="test12345")

    def test_export_settings_action(self):
        """导出 action 返回可下载 JSON。"""
        Setting.objects.create(key="site_title", value="雪人博客")
        resp = self.client.post(
            "/admin/site_config/setting/",
            {"action": "export_settings", "_selected_action": [Setting.objects.get().pk]},
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["site_title"], "雪人博客")


class FriendLinkTest(TestCase):
    def test_ordering_by_sort_order(self):
        low = FriendLink.objects.create(title="低优先", url="https://a.com", sort_order=9)
        high = FriendLink.objects.create(title="高优先", url="https://b.com", sort_order=1)
        self.assertEqual(list(FriendLink.objects.all()), [high, low])

    def test_inactive_filter(self):
        FriendLink.objects.create(title="启用", url="https://a.com", is_active=True)
        FriendLink.objects.create(title="停用", url="https://b.com", is_active=False)
        self.assertEqual(FriendLink.objects.filter(is_active=True).count(), 1)
