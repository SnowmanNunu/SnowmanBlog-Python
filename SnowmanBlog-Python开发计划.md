# SnowmanBlog Python 版 —— 需求与开发计划

> 原项目:[SnowmanNunu/SnowmanBlog](https://github.com/SnowmanNunu/SnowmanBlog)(Laravel 12 + Filament v3)
> 目标:用 Python 复刻同等功能,并借此学习 Python 生态,技术选型为 **Django**。

---

## 一、技术选型

| 层级 | 原项目(PHP) | Python 版 | 说明 |
|---|---|---|---|
| 后端框架 | Laravel 12 | **Django 5.x** | ORM/Migration 心智模型与 Eloquent 接近 |
| 后台面板 | Filament v3 | **Django Admin** + `django-unfold`(可选美化) | 模型注册即得 CRUD 界面,复刻 Filament 效率 |
| 数据库 | MySQL 5.7+ / SQLite | MySQL / SQLite | 不变 |
| 前端模板 | Blade | Django Template | 语法不同但心智模型一致(模板继承、组件) |
| CSS 框架 | Tailwind CSS 4.x | Tailwind CSS | 不变 |
| JS 交互 | Alpine.js | Alpine.js | 不变,轻量交互无需引入前端框架 |
| 构建工具 | Vite | Vite | 不变 |
| Markdown 渲染 | league/commonmark | `mistune` 或 `django-markdownx` | |
| 定时任务 | Laravel Schedule + Cron | **Celery Beat** | 对应文章定时发布 |
| 异步邮件/队列 | Laravel Queue | **Celery** + Redis broker | 对应评论邮件通知 |
| 多云存储抽象 | Laravel Filesystem | **django-storages** | S3/OSS/COS 均有现成 backend |
| 软删除 | Laravel SoftDeletes | `django-safedelete` 或自定义 Manager | 对应文章回收站 |
| 代码规范 | PHPStan + Laravel Pint | Ruff + Black | CI 中跑 |
| 部署 | Docker Compose(PHP-FPM+Nginx+MySQL+Redis+Scheduler) | Docker Compose(Gunicorn+Nginx+MySQL+Redis+Celery beat/worker) | 容器划分基本对齐 |

**备选方案**(暂不采用,记录供参考):
- **FastAPI**:适合前后端分离(前台用 Vue/Next.js,后台自建管理前端),异步性能更好,但没有内置 admin,工作量比 Django 方案大。
- **Flask**:过于轻量,`Flask-Admin` 界面老旧,不适合复刻 Filament 体验。

---

## 二、功能需求清单

### 前台展示
- [x] 文章列表与分页浏览
- [x] 文章详情页(封面图、分类、标签、SEO Meta 自定义)
- [x] 文章上一篇 / 下一篇导航
- [x] 相关文章推荐
- [x] 文章分类与标签筛选
- [x] 专栏系统(按内容系列聚合文章,专栏列表页 + 专栏内文章浏览)
- [x] 全站搜索标题/内容/摘要(LIKE 匹配;快捷键唤起与关键词高亮待增强)
- [x] 留言板(访客发表留言,博主后台回复)
- [x] 文章评论系统(嵌套回复;邮件通知待接 Celery)
- [x] 文章点赞功能(Redis 就绪,计数 + 防刷)
- [ ] Sitemap 站点地图(`/sitemap.xml`)
- [ ] RSS 订阅(`/rss.xml`)
- [x] 响应式设计(桌面端 + 移动端)
- [ ] 暗黑模式支持
- [ ] 站点 Logo 自定义

### 后台管理
- [x] 文章管理:发布、编辑、草稿、封面图上传、SEO 设置、定时发布、软删除与回收站
- [x] 专栏管理:增删改查、封面图、排序、文章归属
- [x] 分类管理:增删改查
- [x] 标签管理:增删改查
- [x] 留言管理:审核留言、博主回复、博主标识
- [x] 评论管理:审核评论、回复评论、邮件通知开关、博主标识
- [x] 友链管理:增删改查与排序
- [x] 站点设置:博客标题、描述、备案号、管理员邮箱、站点 Logo 等基础配置(key-value 可录入,前台应用在阶段四)
- [ ] 存储设置:可视化切换本地磁盘 / 阿里云 OSS / 腾讯云 COS / 七牛云 / AWS S3,无需改配置文件(依赖已装,页面待做)
- [x] 缓存管理:一键清除应用缓存、视图缓存、配置缓存(admin action)
- [x] 备份管理:数据库备份与下载(admin action 导出 JSON)

### 数据模型(初步设计)
- `Article`(文章)
- `Category`(分类)
- `Tag`(标签)
- `Column`(专栏)
- `Comment`(评论,自关联支持嵌套)
- `GuestBook`(留言)
- `FriendLink`(友链)
- `Setting`(站点设置,key-value 结构)
- `User`(用户/管理员)

---

## 三、开发计划

### 阶段一:项目初始化(1-2 天) ✅ 已完成
- `django-admin startproject` 搭建骨架
- 拆分 apps:`blog`(文章/分类/标签/专栏)、`interaction`(评论/留言/点赞)、`site_config`(设置/友链/存储配置)
- 配置 MySQL/SQLite、Redis(cache + Celery broker)
- 编写 Docker Compose:app / nginx / db / redis / celery-worker / celery-beat 六容器

### 阶段二:数据模型与迁移(2-3 天) ✅ 已完成
- 按上述模型清单定义 Model 并生成 Migration
- 评论表自关联实现嵌套回复
- 软删除:`django-safedelete` 或自定义 `deleted_at` 字段 + Manager,支撑文章回收站(采用自定义 Manager 方案)

### 阶段三:后台管理开发(核心,5-7 天) ✅ 已完成(存储设置页待补)
- Django Admin 注册全部模型,自定义 `list_display` / `search_fields` / Inline(专栏内文章、评论嵌套)
- 定时发布:Celery Beat 任务扫描到期草稿并发布
- 存储设置页:自定义 Admin 页面,动态切换 `django-storages` backend 配置并持久化到 `Setting` 表(依赖已装,页面待做)
- 缓存管理、数据库备份:自定义 admin action 或独立管理页面(已用 admin action 实现)

### 阶段四:前台功能开发(4-6 天) ✅ 已完成(搜索增强/邮件通知待补)
- 文章列表分页、详情页(封面/分类/标签/SEO meta)、上一篇下一篇、相关文章推荐
- 分类/标签筛选、专栏列表与专栏内文章浏览
- 全站搜索(数据量不大时用数据库 LIKE + Redis 缓存热词即可,不必上 Elasticsearch)
- 留言板、嵌套评论(Celery 异步发送邮件通知 — 邮件待接)、点赞(Redis 计数 + 简单防刷)

### 阶段五:辅助功能(2-3 天)
- Sitemap:`django.contrib.sitemaps`
- RSS:`django.contrib.syndication`
- 暗黑模式、响应式布局(Tailwind + Alpine.js)

### 阶段六:测试与部署(3-4 天)
- Pytest / Django TestCase 覆盖核心模型与视图
- Gunicorn + Nginx,Docker Compose 编排上线
- CI:GitHub Actions 跑测试 + Ruff/Black 代码风格检查

---

## 四、时间预估

- 全职节奏:约 **3-4 周**
- 业余节奏:约 **6-8 周**

建议开发顺序严格按阶段一 → 六推进,优先跑通后台管理,再做前台——大量前台展示逻辑依赖后台先录入测试数据。

---

## 五、阶段零:脚手架最小验证(已完成 ✅)

> 2026-08-21 执行。目的:在正式铺开阶段一之前,确认「Django 5 在本机可运行 + 首页渲染 + Admin 登录」方案可行。

### 环境结论
- 系统自带 Python 为 **3.9.6**,不满足 Django 5.x 的 `>=3.10` 要求。
- 已用 **`uv`** 安装并创建独立虚拟环境 **Python 3.12.14**(`.venv/`),安装 **Django 5.2.17**。
- `uv venv` 默认不带 pip 可执行命令,包管理一律走 `uv pip ...` 或 `.venv/bin/python -m ...`。

### 已完成的最小骨架
- 项目名 `config`,入口 `manage.py`。
- 最小 app:`core`(首页视图 `/`、健康检查 `/health/`、模板 + 静态 css)。
- 根路由:`/` → core 首页;`/admin/` → Django Admin。
- SQLite 迁移已跑通(admin/auth/contenttypes/sessions 表全部生成)。

### 实测验证结果(Localhost 8000)
| 端点 | 结果 |
|---|---|
| `GET /` | **200**,首页 HTML 正常渲染 |
| `GET /health/` | **200**,返回 `ok` |
| `GET /admin/login/` | **200**,登录页可访问 |
| `POST /admin/login/`(带 CSRF) | **302**,登录成功跳转 |
| `GET /admin/`(已登录) | **200**,后台 dashboard 正常(`Site administration`) |
| 静态 CSS `/static/css/style.css` | **200** |

> 补充:未带 CSRF token 时的 POST 会返回 403——符合 Django CSRF 防护预期,验证了安全中间件生效。

### 验收结论
**技术方案可行,可按开发计划进入阶段一。** 关键风险点(系统 Python 版本不足)已通过 `uv` 建立 Python 3.12 venv 解决。
后续阶段需注意:Django 5 模板/Tailwind/Alpine.js 使用方式、Celery + Redis、django-storages 等均在正式阶段引入。

### 当前项目结构
```
SnowmanBlog-Python/
├── .venv/                  # Python 3.12 虚拟环境
├── config/                 # 项目配置(settings/urls/wsgi/asgi)
├── core/                   # 最小 app(首页 + health)
│   ├── static/css/style.css
│   ├── templates/core/index.html
│   ├── urls.py / views.py / ...
├── manage.py
├── requirements.txt        # Django 5.2.17 + 依赖
├── .gitignore
└── SnowmanBlog-Python开发计划.md
```


---

## 六、开发进度总览(实时更新)

> 最近更新:2026-08-21(阶段一 ~ 阶段四完成,阶段五进行中)

| 阶段 | 内容 | 状态 | 备注 |
|---|---|---|---|
| 阶段零 | Django 脚手架最小验证 | ✅ 完成 | 首页 + Admin 跑通,Py3.12 venv |
| 阶段一 | 项目初始化 | ✅ 完成 | apps 拆分 + Redis + Celery + Docker Compose |
| 阶段二 | 数据模型与迁移 | ✅ 完成 | 9 模型 + 软删除 + 迁移 + 8 测试 |
| 阶段三 | 后台管理 | ✅ 完成 | Admin CRUD + 定时发布 + 缓存/备份(存储设置页待补) |
| 阶段四 | 前台功能开发 | ✅ 完成 | 列表/详情/搜索/专栏/留言/评论/点赞 + 中文 slug + Markdown |
| 阶段五 | 辅助功能 | 🔄 进行中 | Sitemap / RSS / 暗黑模式(当前所处阶段) |
| 阶段六 | 测试与部署 | ⏳ 待开始 | Gunicorn + Nginx + CI |

### 各项功能完成情况
- **后台管理**:文章(含定时发布/回收站)、专栏、分类、标签、留言、评论(嵌套/审核)、友链、站点设置、缓存管理、备份管理 —— ✅
- **前台展示**:列表/详情/上一篇下一个/相关推荐/分类标签筛选/专栏/搜索/留言板/嵌套评论/点赞/响应式 —— ✅
- **存储设置页**(OSS/COS/S3 可视化切换)— ⏳ 依赖已装,页面待做
- **异步**邮箱通知(评论)、搜索快捷键+关键词高亮 — ⏳ 待增强
- **GitHub 提交**:功能提交已推送(`24b13d9` / `bfd0e56` / `b23b145` / `17046c8` / `c87c956`)

### 技术要点备注
- 软删除采用自定义 `core/soft_delete.py`(Manager + 抽象基类),等效 Laravel SoftDeletes
- Celery 定时发布已验证端到端(worker 真实消费 Redis 任务并发布文章)
- 开发默认 SQLite,生产 `DB_ENGINE=mysql` 经环境变量切换

