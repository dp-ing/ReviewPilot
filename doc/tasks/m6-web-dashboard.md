# M6 — Web Dashboard 模块任务列表

> 模块职责：GitHub OAuth 认证、评审记录管理、统计概览、配置管理、增强详情视图
> 依赖：M1, M2, M5

---

## 子任务

### 6.1 认证模块

- [x] **PR-06-01** — 实现 `app/web/auth.py` — GitHub OAuth 登录
  - `GET /auth/login` → 重定向到 GitHub OAuth（含 state 参数防 CSRF）
  - `GET /auth/callback?code=&state=` → code 换 token → 获取用户信息 → 创建/匹配 User → 设置 session
- [x] **PR-06-02** — 实现 Auth middleware
  - 从 session cookie 读取 user_id → 注入 `request.state.user`
  - 未登录访问保护路由 → 重定向 `/auth/login`
- [x] **PR-06-03** — 创建 `templates/auth/login_prompt.html` 登录引导页
- [x] **PR-06-04** — 编写认证测试（未登录重定向 + OAuth 回调流程 + session 正确设置）

### 6.2 基础布局

- [x] **PR-06-05** — 创建 `templates/base.html` — 基础 HTML 布局（header + sidebar + content + Tailwind CDN）
- [x] **PR-06-06** — 创建 `templates/shared/` 共享组件
  - `severity_badge.html` — 严重级别标签
  - `pagination.html` — 分页组件
  - `filter_bar.html` — 筛选栏组件

### 6.3 首页与路由注册

- [x] **PR-06-07** — 实现 `app/web/routes.py` — 注册所有页面路由
- [x] **PR-06-08** — 创建 `templates/index.html` — 首页（已登录→Dashboard，未登录→登录引导）
- [x] **PR-06-09** — 在 `app/main.py` 注册 Web 路由模块 + 静态文件挂载

### 6.4 Dashboard 统计概览

- [x] **PR-06-10** — 实现 `app/web/stats_service.py` — `StatsService`
  - `get_overview_stats()` — 总 PR 数/评审数/问题数/平均问题数
  - `get_issue_distribution()` — 按严重级别 + 按类别
  - `get_trend()` — 每日问题发现趋势
  - `get_repo_comparison()` — 各仓库对比
- [x] **PR-06-11** — 创建 `templates/dashboard/overview.html` — Dashboard 主页（统计卡片 + 图表容器）
- [x] **PR-06-12** — 集成 Chart.js — 环形图（问题分布）+ 折线图（趋势）+ 柱状图（仓库对比）
- [x] **PR-06-13** — 实现 HTMX 局部刷新：`GET /dashboard/stats` → `stats_cards.html` + `trend_chart.html`
- [x] **PR-06-14** — 编写统计查询测试（Mock 数据库 → 验证统计数字）

### 6.5 评审记录管理

- [x] **PR-06-15** — 创建 `templates/reviews/list.html` — 评审记录列表页（时间/仓库/状态筛选）
- [x] **PR-06-16** — 创建 `templates/reviews/detail.html` — 评审详情页（问题列表 + 代码上下文）
- [x] **PR-06-17** — 创建 `templates/reviews/issue_row.html` — 单条 issue HTMX 行（状态切换）
- [x] **PR-06-18** — 实现 `PATCH /api/reviews/{id}/issues/{issue_id}` — HTMX 更新问题状态（open/confirmed/ignored）
- [x] **PR-06-19** — 编写评审页面测试（列表渲染 + 详情渲染 + HTMX 状态更新）

### 6.6 仓库配置管理

- [x] **PR-06-20** — 创建 `templates/repos/list.html` — 仓库列表页
- [x] **PR-06-21** — 创建 `templates/repos/config.html` + `config_form.html` — 仓库配置编辑页
- [x] **PR-06-22** — 实现 `PUT /api/repositories/{id}/config` — 保存配置（HTMX 表单提交）
  - auto_review 开关、sensitivity 选择、enabled_categories 勾选
  - ignore_patterns 编辑、language 选择
- [x] **PR-06-23** — 编写配置管理测试（配置读取 + 保存 + HTMX 响应）

### 6.7 PR 增强详情视图

- [x] **PR-06-24** — 实现 `app/web/enhanced_view.py` — `EnhancedViewBuilder`
  - `build(review_record, pr_detail, issues)` → `EnhancedViewData`
  - diff 行与 issue 的映射构建
- [x] **PR-06-25** — 创建 `templates/reviews/enhanced.html` — 增强详情页
  - 左侧：代码 diff（added 绿 / removed 红 高亮）
  - 右侧：问题列表（按 severity 颜色条标注）
  - 点击问题行 → 展开详情（title + description + suggestion）
- [x] **PR-06-26** — 编写增强视图测试（diff + issue 映射正确性）

### 6.8 样式与体验

- [x] **PR-06-27** — Tailwind CSS 样式完善（响应式布局、暗色模式支持）
- [x] **PR-06-28** — 加载状态 + 空数据状态 + 错误状态 UI

---

## 完成标准

- [x] GitHub OAuth 登录流程完整可用
- [x] Dashboard 页面正确展示统计数据 + 图表
- [x] 评审记录列表支持筛选，详情页展示完整问题列表
- [x] 问题状态可通过 HTMX 切换
- [x] 仓库配置表单可正常提交并生效
- [x] PR 增强详情页正确标注 diff 行 + 问题
- [x] 页面在移动端基本可用
