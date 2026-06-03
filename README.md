# ReviewPilot

> **演示视频**：通过百度网盘分享的文件：七牛云代码评审演讲视频1-1.mp4
> 链接：https://pan.baidu.com/s/1ahKqazmmqxmFiujhVCAdMA
> 提取码：0000
>
> **备用链接**（简单云链）：https://easylink.cc/ajrdfo

AI 驱动的 GitHub PR 代码评审助手。自动分析 Pull Request 变更，通过 GitHub Bot 创建行级评论和总结报告，并提供 Web Dashboard 进行跨仓库管理。

## 功能特性

| 特性 | 说明 |
|------|------|
| PR 自动评审 | Webhook 触发 → 拉取 diff → AI 分析 → 行级评论 + 总结报告 |
| 手动触发 | PR 中评论 `/review` 即可触发分析，支持 `focus:security` 分类筛选 |
| 5 类分析 | 安全、逻辑、性能、最佳实践、代码风格，全维度检查 |
| Python/Java 深度 | AST 确定性规则检测（18 条规则）+ AI 上下文理解 |
| Web Dashboard | 评审记录、统计图表、仓库配置、增强详情视图 |
| 误报控制 | 可配置置信度阈值、忽略规则、分类开关，每仓库独立设置 |
| OAuth 登录 | GitHub OAuth 2.0 认证，CSRF 保护 |

## 架构概览

```
POST /webhook/github
  → EventRouter（签名验证 → 事件解析 → 路由分发）
    → AutoReviewHandler（PR 打开/同步/重新打开）
    → CommandHandler（issue_comment 中的 /review 命令）
      → AnalysisOrchestrator（两阶段 AI 分析）
        → 阶段一: deepseek-v4-flash（变更总结 + 风险标记）
        → 阶段二: deepseek-v4-pro（4 类并行深度分析）
      → PostProcessor（合并 → 去重 → 过滤 → 排序）
      → CommentCreator（格式化 → 行级评论 + 总结报告）
```

```
Web Dashboard（服务端渲染）
  GET /              → index.html（仪表盘 + 图表）
  GET /dashboard     → overview.html（Chart.js 统计图表）
  GET /reviews       → 分页列表 + 状态筛选
  GET /reviews/:id   → 详情 + 问题列表
  GET /reviews/:id/enhanced → 文件分组增强视图（Alpine.js）
  GET /repositories  → 仓库列表 + 配置状态
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI（Python 3.9+） |
| 数据库 | SQLite → MySQL（SQLAlchemy 2.0 + Alembic 迁移） |
| AI 引擎 | OpenAI 兼容 API（DeepSeek） |
| GitHub 集成 | PyGithub + httpx 直调 API |
| 前端渲染 | Jinja2 SSR + HTMX + Tailwind CSS CDN |
| 图表 | Chart.js CDN |
| 交互增强 | Alpine.js |
| AST 解析 | Python `ast` 标准库 / Java `javalang` |
| 认证 | GitHub OAuth 2.0 + Starlette SessionMiddleware |
| 代码质量 | mypy --strict + ruff check + pytest |

## 项目结构

```
ReviewPilot/
├── app/
│   ├── main.py                     # FastAPI 入口 + webhook 路由
│   ├── core/                       # M1: 配置、数据库、日志、异常
│   │   ├── config.py               # Pydantic BaseSettings（自动加载 .env + PEM）
│   │   ├── database.py             # SQLAlchemy 引擎 + session 工厂
│   │   ├── logging.py              # structlog JSON 格式日志
│   │   └── exceptions.py           # 9 级异常体系
│   ├── models/                     # M1: 6 个 SQLAlchemy ORM 模型
│   ├── github/                     # M2: Webhook 处理器 + API 客户端
│   ├── analyzer/                   # M3: Python/Java AST 分析器（18 条规则）
│   ├── engine/                     # M4: AI Provider、Diff 解析、编排器
│   │   └── prompts/                # Jinja2 Prompt 模板（系统 + 两阶段）
│   ├── bot/                        # M5: 事件路由、自动评审、命令处理、评论创建
│   └── web/                        # M6: OAuth、路由、统计服务、增强视图
├── templates/                      # Jinja2 模板（SSR）
│   ├── base.html                   # 主布局（导航 + 侧栏 + 内容区）
│   ├── index.html                  # 首页仪表盘
│   ├── auth/                       # 登录提示页
│   ├── dashboard/                  # 统计卡片 + 图表模板
│   ├── reviews/                    # 列表、详情、问题行、增强视图
│   ├── repos/                      # 列表、配置、配置表单
│   └── shared/                     # 严重级别徽章、分页、筛选栏
├── static/css/app.css              # 自定义样式
├── demo/test_repo/                 # 演示用测试仓库（含漏洞代码）
├── tests/                          # 439 个测试，91% 覆盖率
│   ├── test_core/                  # M1 测试（6 文件）
│   ├── test_github/                # M2 测试（3 文件）
│   ├── test_analyzer/              # M3 测试（5 文件 + fixtures）
│   ├── test_engine/                # M4 测试（7 文件）
│   ├── test_bot/                   # M5 测试（4 文件）
│   └── test_web/                   # M6 测试（5 文件）
├── doc/                            # 设计文档 + 任务清单
├── alembic/                        # 数据库迁移
├── Dockerfile + docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

## API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 首页仪表盘 |
| `GET` | `/dashboard` | 完整仪表盘（含图表） |
| `GET` | `/dashboard/stats` | JSON 统计数据（HTMX） |
| `GET` | `/health` | 健康检查 |
| `POST` | `/webhook/github` | GitHub Webhook 接收端点 |
| `GET` | `/auth/login` | GitHub OAuth 跳转 |
| `GET` | `/auth/callback` | OAuth 回调处理 |
| `GET` | `/auth/logout` | 清除会话 |
| `GET` | `/reviews` | 评审记录列表（分页 + 筛选） |
| `GET` | `/reviews/{id}` | 评审详情 |
| `GET` | `/reviews/{id}/enhanced` | 增强视图（按文件分组） |
| `PATCH` | `/api/reviews/{id}/issues/{issue_id}` | 更新问题状态 |
| `GET` | `/repositories` | 仓库列表 |
| `GET` | `/repositories/{id}/config` | 仓库配置页面 |
| `PUT` | `/api/repositories/{id}/config` | 保存仓库配置 |

## 分析规则

### Python（10 条）
| 规则 ID | 严重级别 | 类别 |
|---------|---------|------|
| python-exec-eval | critical | security |
| python-unsafe-pickle | critical | security |
| python-shell-injection | critical | security |
| python-sql-concat | warning | security |
| python-bare-except | warning | best_practice |
| python-hardcoded-secret | warning | security |
| python-file-leak | warning | best_practice |
| python-complexity | warning | style |
| python-function-length | suggestion | style |
| python-duplicate | suggestion | style |

### Java（8 条）
| 规则 ID | 严重级别 | 类别 |
|---------|---------|------|
| java-command-injection | critical | security |
| java-unsafe-deserial | critical | security |
| java-sql-concat | warning | security |
| java-resource-leak | warning | best_practice |
| java-hardcoded-secret | warning | security |
| java-complexity | warning | style |
| java-method-length | suggestion | style |
| java-unhandled-exception | suggestion | style |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 GITHUB_APP_ID、GITHUB_APP_PRIVATE_KEY、
# GITHUB_WEBHOOK_SECRET、GITHUB_CLIENT_ID、GITHUB_CLIENT_SECRET、
# AI_API_KEY、SECRET_KEY 等配置

# 3. 初始化数据库
alembic upgrade head

# 4. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **注意**：`GITHUB_APP_PRIVATE_KEY` 支持直接填写 PEM 内容，或填写 `.pem`/`.key` 文件路径，程序会自动识别并加载。

## 开发

```bash
# 类型检查
mypy app/ --strict

# 代码风格检查
ruff check app/

# 测试 + 覆盖率
pytest tests/ -v --cov=app --cov-report=term-missing

# 提交前三个命令必须全部通过
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `GITHUB_APP_ID` | GitHub App ID | — |
| `GITHUB_APP_PRIVATE_KEY` | PEM 私钥（内容或文件路径） | — |
| `GITHUB_WEBHOOK_SECRET` | Webhook HMAC-SHA256 密钥 | — |
| `GITHUB_CLIENT_ID` | OAuth App Client ID | — |
| `GITHUB_CLIENT_SECRET` | OAuth App Client Secret | — |
| `AI_API_KEY` | AI API 密钥 | — |
| `AI_API_BASE` | AI API 地址 | `https://api.deepseek.com/v1` |
| `AI_DEFAULT_MODEL` | 阶段一快速模型 | `deepseek-v4-flash` |
| `AI_STRONG_MODEL` | 阶段二深度分析模型 | `deepseek-v4-pro` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///reviewpilot.db` |
| `APP_HOST` | 服务监听地址 | `0.0.0.0` |
| `APP_PORT` | 服务端口 | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `SECRET_KEY` | Session 加密密钥 | — |

## 质量指标

| 指标 | 结果 |
|------|------|
| mypy --strict | 0 问题（46 个源文件） |
| ruff check | 0 问题 |
| 单元测试 | 439 通过 |
| E2E 测试 | 4 通过（需 AI_API_KEY） |
| 代码覆盖率 | 91% |

## 演示与文档

| 文档 | 说明 |
|------|------|
| [操作指南](doc/operation_guide.md) | 本机演示操作步骤（从零搭建） |
| [演讲稿](doc/demo_script.md) | 演示视频演讲稿（8-12 分钟） |
| [幻灯片](doc/demo_slides.html) | 浏览器演示幻灯片（← → 翻页） |
| [演示代码](demo/test_repo/) | 含漏洞的测试仓库代码 |

## 许可证

MIT
