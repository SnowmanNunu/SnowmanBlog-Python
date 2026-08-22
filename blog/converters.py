"""自定义 SlugConverter(支持中文等 Unicode 字符)。

默认 Django 的 ``<slug:...>`` 仅匹配 ASCII,而我们的 slug 可能含中文
(slugify 使用 allow_unicode=True),因此需要放宽正则。
"""


class UnicodeSlugConverter:
    regex = r"[-\w]+"
    # \w 在 Python 3 默认含 unicode 字母数字,加上连字符与下划线

    def to_python(self, value):
        return value

    def to_url(self, value):
        return str(value)
