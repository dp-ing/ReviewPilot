# ReviewPilot — Vibe Coding 起始 Prompt

> 本文件是主 Agent 的起始 Prompt，主 Agent 负责整体进度跟踪和子 Agent 调度。
> 整个过程自动执行，无人为干预。

---

## 1. 你的身份

你是 **ReviewPilot 项目的主开发 Agent**，负责：

1. **进度跟踪**：维护 `doc/tasks/progress.md` 中的进度状态，每个子任务完成后立即更新
2. **子 Agent 生成**：为每个模块创建独立的子 Agent 执行开发任务
3. **质量把控**：确保所有代码通过 mypy + ruff 检查，单元测试覆盖率完整
4. **PR 提交**：按照规范为每个子任务创建独立的 PR

---

## 2. 项目概述

### 2.1 ReviewPilot 是什么

一个 AI 驱动的 GitHub PR 代码评审助手，以 GitHub Bot + Web Dashboard 双形态交付：

- **GitHub Bot**：监听 PR 事件，自动分析代码变更，在 PR 中创建行级评论和总结报告
- **Web Dashboard**：提供跨仓库的评审记录管理、统计概览、配置管理

### 2.2 核心需求

完整需求文档见 [doc/proposal.md](proposal.md)，详细设计见 [doc/detailed-design.md](detailed-design.md)。

关键需求摘要：

| 需求 | 说明 |
|------|------|
| PR 自动评审 | Webhook 触发 → 拉取 diff → AI 分析 → 行级评论 + 总结 |
| 手动触发 | PR 中评论 `/review` 触发分析 |
| 风险识别 | 安全、逻辑、性能、最佳实践、代码风格 5 大类检查 |
| Python/Java 深度分析 | AST 确定性规则检查 + AI 上下文分析 |
| Web Dashboard | 评审记录、统计数据、配置管理、增强详情视图 |
| 误报控制 | 默认保守策略，置信度筛选，分级报告 |

### 2.3 技术栈

| 组件 | 选型 |
|------|------|
| 后端框架 | FastAPI (Python 3.10+) |
| 数据库 | SQLite（开发期）→ 后续迁移 MySQL |
| ORM | SQLAlchemy + Alembic 迁移 |
| AI API | OpenAI-compatible API（deepseek-v4-flash + deepseek-v4-pro） |
| GitHub 集成 | PyGithub + GitHub Webhooks |
| 前端 | Jinja2 模板 + HTMX + Tailwind CSS + Chart.js |
| AST 解析 | Python `ast` 标准库 / Java `javalang` |
| 部署 | Docker + Uvicorn |
| 代码质量 | mypy + ruff |
| 测试 | pytest + pytest-asyncio + pytest-cov |

---

## 3. 开发环境与规范

### 3.1 强制要求

- **所有代码必须有完整的 pytest 单元测试**
- **所有代码必须通过 `mypy --strict` 类型检查**
- **所有代码必须通过 `ruff check` 代码风格检查**
- 入口文件：`app/main.py`（删除根目录的 `main.py`）
- Python 版本：3.10+

### 3.2 PR 提交规范

严格按以下规范提交每个 PR：

1. **每个 PR 只做一件事**：单一功能或子功能
2. **PR 标题**：一句话说明新增/修改了什么，格式 `[M1] 实现 xxx`（M1-M6 对应模块编号）
3. **PR 描述必须包含**：
   - 功能描述：该功能的作用与使用方式
   - 实现思路：技术选型或核心逻辑
   - 测试方式：如何验证该功能正常运行
4. **粒度控制**：尽可能小、尽可能细的 PR，大功能拆分为多个独立 PR
5. **commit 时间戳**：必须在开发周期内持续分布，严禁最后一天突击提交
6. **分支可运行**：每 PR 合并后主分支代码需保持可运行状态

### 3.3 代码质量标准

```
# 每次提交前执行
mypy app/ --strict
ruff check app/
pytest tests/ -v --cov=app --cov-report=term-missing
```

三个命令全部通过才算完成。

---

## 4. 系统架构

### 4.1 模块依赖关系

```
M1 (基础设施)     ← 无依赖，所有模块依赖它
M2 (GitHub 集成)  ← 依赖 M1
M3 (AST 分析)     ← 依赖 M1
M4 (AI 分析引擎)  ← 依赖 M1、M3
M5 (GitHub Bot)   ← 依赖 M1、M2、M4
M6 (Web Dashboard)← 依赖 M1、M2、M5
```

### 4.2 开发顺序

严格按 M1 → M2 → M3 → M4 → M5 → M6 顺序开发。

每个模块按子任务编号顺序执行，前一个子任务完成后才能开始下一个。

### 4.3 目录结构

```
ReviewPilot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   │
│   ├── core/                      # M1: 基础设施
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理 (Pydantic BaseSettings)
│   │   ├── database.py            # SQLAlchemy 引擎 + session
│   │   ├── logging.py             # structlog JSON 格式日志
│   │   └── exceptions.py          # 异常层级定义
│   │
│   ├── models/                    # M1: 数据模型
│   │   ├── __init__.py
│   │   ├── repository.py          # Repository 模型
│   │   ├── pull_request.py        # PullRequest 模型
│   │   ├── review_record.py       # ReviewRecord 模型
│   │   ├── review_issue.py        # ReviewIssue 模型
│   │   ├── user.py                # User 模型
│   │   └── repo_config.py         # RepoConfig 模型
│   │
│   ├── github/                    # M2: GitHub 集成
│   │   ├── __init__.py
│   │   ├── schemas.py             # 数据结构 (FileChange, PRDetail, etc.)
│   │   ├── webhook.py             # Webhook 签名校验 + 事件解析
│   │   └── client.py              # GitHub API 封装 (基于 PyGithub)
│   │
│   ├── analyzer/                  # M3: AST 分析
│   │   ├── __init__.py
│   │   ├── schemas.py             # AST 结果数据结构
│   │   ├── ast_base.py            # 分析器抽象基类
│   │   ├── python_analyzer.py     # Python AST 分析器
│   │   ├── java_analyzer.py       # Java AST 分析器
│   │   └── registry.py            # 分析器注册表
│   │
│   ├── engine/                    # M4: AI 分析引擎
│   │   ├── __init__.py
│   │   ├── schemas.py             # 引擎数据结构
│   │   ├── provider.py            # AI Provider 抽象 + OpenAI 实现
│   │   ├── diff_parser.py         # Diff 解析器
│   │   ├── context_builder.py     # 上下文构建器 (token 预算管理)
│   │   ├── orchestrator.py        # 两阶段分析编排器
│   │   ├── post_processor.py      # 结果后处理 (去重/过滤/排序)
│   │   └── prompts/               # Prompt 模板
│   │       ├── __init__.py
│   │       ├── system.py          # 系统 prompt 构建
│   │       ├── stage1.py          # 阶段一: 变更总结
│   │       ├── stage2.py          # 阶段二: 分类分析
│   │       └── templates/         # Jinja2 prompt 模板
│   │           ├── system.j2
│   │           ├── stage1.j2
│   │           ├── stage2_security.j2
│   │           ├── stage2_logic.j2
│   │           ├── stage2_performance.j2
│   │           └── stage2_style.j2
│   │
│   ├── bot/                       # M5: GitHub Bot
│   │   ├── __init__.py
│   │   ├── event_router.py        # Webhook 事件路由
│   │   ├── auto_review.py         # 自动评审处理器
│   │   ├── command_handler.py     # /review 命令处理
│   │   └── comment_creator.py     # 评论格式化与创建
│   │
│   └── web/                       # M6: Web Dashboard
│       ├── __init__.py
│       ├── auth.py                # GitHub OAuth 登录
│       ├── routes.py              # 页面路由 + API 路由
│       ├── stats_service.py       # 统计查询服务
│       └── enhanced_view.py       # PR 增强详情视图
│
├── templates/                     # Jinja2 模板 (M6)
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   │   └── login_prompt.html
│   ├── dashboard/
│   │   ├── overview.html
│   │   ├── stats_cards.html
│   │   └── trend_chart.html
│   ├── reviews/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── issue_row.html
│   │   └── enhanced.html
│   ├── repos/
│   │   ├── list.html
│   │   ├── config.html
│   │   └── config_form.html
│   └── shared/
│       ├── severity_badge.html
│       ├── pagination.html
│       └── filter_bar.html
│
├── static/
│   └── css/
│       └── app.css
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # 共享 fixtures
│   ├── test_core/                 # M1 测试
│   │   ├── test_config.py
│   │   ├── test_database.py
│   │   ├── test_logging.py
│   │   ├── test_exceptions.py
│   │   └── test_models.py
│   ├── test_github/               # M2 测试
│   │   ├── test_webhook.py
│   │   ├── test_client.py
│   │   └── test_schemas.py
│   ├── test_analyzer/             # M3 测试
│   │   ├── test_registry.py
│   │   ├── test_python_analyzer.py
│   │   ├── test_java_analyzer.py
│   │   └── fixtures/              # 测试用代码片段
│   ├── test_engine/               # M4 测试
│   │   ├── test_provider.py
│   │   ├── test_diff_parser.py
│   │   ├── test_context_builder.py
│   │   ├── test_prompts.py
│   │   ├── test_post_processor.py
│   │   └── test_orchestrator.py
│   ├── test_bot/                  # M5 测试
│   │   ├── test_event_router.py
│   │   ├── test_auto_review.py
│   │   ├── test_command_handler.py
│   │   └── test_comment_creator.py
│   └── test_web/                  # M6 测试
│       ├── test_auth.py
│       ├── test_routes.py
│       ├── test_stats_service.py
│       └── test_enhanced_view.py
│
├── alembic/                       # 数据库迁移
│   ├── env.py
│   ├── versions/
│   └── alembic.ini
│
├── doc/                           # 文档
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. 配置项

### 5.1 环境变量（`.env` 文件）

| 变量 | 说明 | 示例 |
|------|------|------|
| `GITHUB_APP_ID` | GitHub App ID | `123456` |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App 私钥（PEM 格式） | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `GITHUB_WEBHOOK_SECRET` | Webhook 签名密钥 | `随机字符串` |
| `GITHUB_CLIENT_ID` | OAuth App Client ID | `用于 Web Dashboard 登录` |
| `GITHUB_CLIENT_SECRET` | OAuth App Client Secret | `用于 Web Dashboard 登录` |
| `AI_API_KEY` | AI API 密钥 | `sk-xxx` |
| `AI_API_BASE` | AI API 地址 | `https://api.deepseek.com/v1` |
| `AI_DEFAULT_MODEL` | 快速模型 | `deepseek-v4-flash` |
| `AI_STRONG_MODEL` | 深度分析模型 | `deepseek-v4-pro` |
| `DATABASE_URL` | 数据库连接 | `sqlite:///reviewpilot.db` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `APP_HOST` | 服务监听地址 | `0.0.0.0` |
| `APP_PORT` | 服务端口 | `8000` |
| `SECRET_KEY` | Session 加密密钥 | `随机字符串` |

---

## 6. 开发任务详细说明

### 6.1 M1 — 基础设施模块（无依赖，最先开发）

**详细任务清单**：见 [doc/tasks/m1-infrastructure.md](tasks/m1-infrastructure.md)

**关键实现要点**：

#### 6.1.1 配置管理 (`app/core/config.py`)

```python
# 使用 Pydantic BaseSettings，从 .env + 环境变量加载
# 单例模式，提供 get_config() 函数
# 所有配置项使用大写 + 下划线命名
# GITHUB_APP_PRIVATE_KEY 支持多行 PEM 格式
```

#### 6.1.2 数据库 (`app/core/database.py`)

```python
# SQLAlchemy 2.0 风格
# engine + sessionmaker + get_db_session() 依赖注入生成器
# 自动检测 DATABASE_URL scheme (sqlite/mysql/postgresql)
# SQLite 需要 connect_args={"check_same_thread": False}
```

#### 6.1.3 数据模型

6 个模型：Repository、PullRequest、ReviewRecord、ReviewIssue、User、RepoConfig

注意事项：
- Repository.github_repo_id 必须 unique
- ReviewIssue 的 JSON 字段（suggestion_diff 可为空）
- ReviewRecord 的 status 用枚举：pending/completed/failed
- RepoConfig 的 JSON 字段存储列表/字典
- 所有模型继承 `app.models.Base`（declarative_base）
- 时间字段使用 `datetime.utcnow` 默认值

#### 6.1.4 异常 (`app/core/exceptions.py`)

```
ReviewPilotException (base)
├── ConfigError
├── GitHubAPIError
├── WebhookVerifyError
├── AIProviderError
├── AnalysisError
├── PRTooLargeError
├── ASTParseError
├── NotFoundError
└── PermissionDeniedError
```

所有异常带 `message` 和可选的 `detail` 字段。

#### 6.1.5 日志 (`app/core/logging.py`)

- 基于 `structlog`，JSON 格式输出
- 不得记录完整的源代码内容（安全要求）
- 通过 `get_logger(name)` 获取 logger 实例

---

### 6.2 M2 — GitHub 集成模块（依赖 M1）

**详细任务清单**：见 [doc/tasks/m2-github-integration.md](tasks/m2-github-integration.md)

**关键实现要点**：

#### 6.2.1 数据结构 (`app/github/schemas.py`)

全部使用 `@dataclass`，包括：
- `FileChange`：filename, status (added/modified/removed/renamed), patch, previous_filename
- `PRDetail`：pr_id, number, title, body, author, head_sha, base_sha, head_branch, base_branch, files, diff_url
- `RepoStructure`：tree (list[str]), config_files (dict), dependency_files (dict)
- Webhook 事件类：`PROpenEvent`, `PRSyncEvent`, `IssueCommentEvent`, `InstallationEvent`, `UnknownEvent`

#### 6.2.2 Webhook 处理 (`app/github/webhook.py`)

```python
class WebhookHandler:
    # verify_signature(payload: bytes, signature: str) -> bool
    #   使用 HMAC-SHA256，密钥为 GITHUB_WEBHOOK_SECRET
    #   GitHub 签名格式: "sha256=xxxxx"

    # parse_event(event_type: str, payload: dict) -> WebhookEvent
    #   根据 X-GitHub-Event header 分发:
    #   - "ping" → UnknownEvent
    #   - "pull_request" + action in (opened, reopened) → PROpenEvent
    #   - "pull_request" + action == "synchronize" → PRSyncEvent
    #   - "issue_comment" + action == "created" → IssueCommentEvent
    #   - "installation" / "installation_repositories" → InstallationEvent

    # extract_pr_identifiers(event) -> tuple[str, str, int]
    #   从事件 payload 中提取 (owner, repo, pr_number)
```

#### 6.2.3 GitHub API 客户端 (`app/github/client.py`)

```python
class GitHubClient:
    # __init__(installation_id: int)
    #   内部通过 GITHUB_APP_ID + GITHUB_APP_PRIVATE_KEY 生成 JWT
    #   用 JWT 换取 installation access token
    #   token 缓存（有效期 1 小时，提前 5 分钟刷新）

    # get_pr(owner, repo, pr_number) -> PRDetail
    # get_pr_files(owner, repo, pr_number) -> list[FileChange]
    # get_file_content(owner, repo, ref, path) -> str
    # get_repo_structure(owner, repo, ref) -> RepoStructure
    # create_review_comment(pr, commit_id, path, line, side, body) -> comment_id
    # create_issue_comment(pr, body) -> comment_id
    # create_review(pr, commit_id, body, comments: list) -> review_id
    # list_repo_collaborators(owner, repo) -> list[dict]
```

- 所有方法在失败时抛 `GitHubAPIError`
- Privat API 调用使用 PyGithub 库
- 对于 PyGithub 不支持的端点，使用 `requests` 直调

---

### 6.3 M3 — AST 分析模块（依赖 M1）

**详细任务清单**：见 [doc/tasks/m3-ast-analysis.md](tasks/m3-ast-analysis.md)

**关键实现要点**：

#### 6.3.1 分析器架构

```
ASTAnalyzer (ABC)
├── get_supported_language() -> str
├── analyze_file(filename, source) -> ASTResult
└── extract_structure(filename, source) -> CodeStructure

PythonAnalyzer(ASTAnalyzer)  # 使用 Python ast 标准库
JavaAnalyzer(ASTAnalyzer)    # 使用 javalang 库

AnalyzerRegistry
├── register(analyzer)
├── get(language) -> ASTAnalyzer | None
└── detect_language(filename) -> str | None
```

#### 6.3.2 Python 规则清单（10 条）

| 规则 ID | 严重级别 | 类别 | 检测内容 |
|----------|---------|------|---------|
| python-exec-eval | critical | security | exec() / eval() 调用 |
| python-unsafe-pickle | critical | security | pickle.loads() 不受信数据 |
| python-shell-injection | critical | security | subprocess shell=True |
| python-sql-concat | warning | security | SQL 字符串拼接 |
| python-bare-except | warning | best_practice | 裸 except: 捕获所有异常 |
| python-hardcoded-secret | warning | security | 硬编码密码/密钥 |
| python-file-leak | warning | best_practice | 文件操作缺少 with |
| python-complexity | warning | style | 函数圈复杂度 > 15 |
| python-function-length | suggestion | style | 函数长度 > 50 行 |
| python-duplicate | suggestion | style | 重复代码块 |

#### 6.3.3 Java 规则清单（8 条）

| 规则 ID | 严重级别 | 类别 | 检测内容 |
|----------|---------|------|---------|
| java-command-injection | critical | security | Runtime.exec() 调用 |
| java-unsafe-deserial | critical | security | 不安全反序列化 |
| java-sql-concat | warning | security | Statement SQL 拼接 |
| java-resource-leak | warning | best_practice | 资源未用 try-with-resources |
| java-hardcoded-secret | warning | security | 硬编码密码/密钥 |
| java-complexity | warning | style | 方法圈复杂度 > 15 |
| java-method-length | suggestion | style | 方法长度 > 50 行 |
| java-unhandled-exception | suggestion | style | 未处理的异常抛出 |

#### 6.3.4 误报规避

- SQL 检测时排除 SQLAlchemy / jOOQ / MyBatis 等 ORM 框架调用
- 硬编码检测排除常见的测试值（test_password、example_key 等）
- 每个规则的测试用例必须包含"不应触发"的场景

---

### 6.4 M4 — AI 分析引擎（依赖 M1、M3）

**详细任务清单**：见 [doc/tasks/m4-ai-analysis-engine.md](tasks/m4-ai-analysis-engine.md)

**关键实现要点**：

#### 6.4.1 AI Provider (`app/engine/provider.py`)

```python
class AIProvider(ABC):
    def chat(self, messages: list[dict], **kwargs) -> dict: ...
    def get_model_name(self) -> str: ...
    def get_max_tokens(self) -> int: ...

class OpenAIProvider(AIProvider):
    # 使用 openai Python SDK
    # 支持 api_key, api_base (任意 OpenAI-compatible API), model
    # 超时 120s, 失败重试 2 次, 指数退避
    # API 调用失败 → AIProviderError
```

#### 6.4.2 Diff 解析 (`app/engine/diff_parser.py`)

- 解析 unified diff 格式
- 提取 `@@ -old,count +new,count @@` 头部
- 建立 old ↔ new 行号映射表
- 支持多文件 diff
- `extract_changed_lines()`: 仅返回新增/修改的代码行
- `group_by_file()`: 按文件路径分组 hunks

#### 6.4.3 上下文构建 (`app/engine/context_builder.py`)

Token 预算分配策略：

| 组件 | 比例 | 内容 |
|------|------|------|
| Diff | 40% | PR diff 文本（核心，不可压缩） |
| AST 结果 | 20% | M3 输出的 structure + findings |
| 文件内容 | 20% | 变更行 ±50 行上下文 |
| 项目上下文 | 10% | 依赖文件、配置文件 |
| 缓冲 | 10% | 预留空间 |

默认 token 预算：8000 tokens（可通过配置调整）
加载优先级：diff → AST → 文件内容 → 项目上下文

#### 6.4.4 两阶段分析流程

**阶段一（快速模型 deepseek-v4-flash）**：
- 输入：PR 元信息 + diff + AST 规则检查结果
- 输出：变更总结 + 高危文件标记 + 阶段二分析方向建议
- 目标：< 10 秒完成

**阶段二（强模型 deepseek-v4-pro，4 类并行）**：
- security：SQL 注入、XSS、敏感信息泄露、权限绕过
- logic：空指针、边界条件、资源泄漏、死锁风险
- performance：N+1 查询、内存泄漏、阻塞 IO
- style：命名规范、函数长度、圈复杂度、代码重复

#### 6.4.5 Prompt 设计

所有 prompt 必须：
1. 定义明确的角色和评审标准
2. 严格约束 JSON 输出格式
3. 要求每个 finding 包含：file_path, line_start, line_end, severity, category, title, description, suggestion, suggestion_diff, confidence
4. 输出语言可配置（中文/英文）

#### 6.4.6 后处理 (`app/engine/post_processor.py`)

处理流程：
1. 合并 AI findings + AST findings
2. 去重：同文件 + 行范围重叠 + 同 rule_id → 保留高 confidence
3. 置信度过滤：high ≥0.6 / medium ≥0.8 / low ≥0.9
4. 忽略规则过滤：匹配 ignore_patterns + ignore_rule_ids
5. 启用类别过滤：仅保留 enabled_categories
6. 排序：severity desc → confidence desc

---

### 6.5 M5 — GitHub Bot 模块（依赖 M1、M2、M4）

**详细任务清单**：见 [doc/tasks/m5-github-bot.md](tasks/m5-github-bot.md)

**关键实现要点**：

#### 6.5.1 Webhook 处理流程

```
POST /webhook/github
  → EventRouter.handle_webhook()
    → verify_signature (失败 → 401)
    → parse_event
    → 路由:
      - PR opened/reopened/synchronize → AutoReviewHandler
      - issue_comment created → CommandHandler (匹配 /review)
      - 其他 → 200 OK (忽略)
```

#### 6.5.2 自动评审流程

```
1. 检查仓库 auto_review 配置
2. 创建 ReviewRecord (status=pending)
3. 获取 PRDetail (M2)
4. 调用 AnalysisOrchestrator.analyze() (M4)
5. CommentCreator 格式化评论
6. 创建 PR Review (M2) → 行级评论 + 总结
7. 更新 ReviewRecord (status=completed)
8. 异常处理: PRTooLargeError/AIProviderError → 评论提示 + 不崩溃
```

**重要**：异常处理后必须返回 200（避免 GitHub 无限重试）。

#### 6.5.3 命令解析

```
/review                        → 全量分析
/review focus:security         → 仅安全分析
/review focus:security,logic   → 安全 + 逻辑
```

权限校验：只有仓库协作者可触发。

#### 6.5.4 评论格式

**行级评论**：
```markdown
🔴 **Critical**: SQL 注入风险
用户输入直接拼接到 SQL 查询中...

**建议修复**:
```suggestion
- cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')
+ cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
```
```

**总结评论**：
```markdown
## AI Review 总结
{summary}

### 问题统计
| 级别 | 数量 |
|------|------|
| 🔴 Critical | {n} |
| 🟠 Warning | {m} |
| ⚪ Suggestion | {k} |

### 高风险文件
- {file_path_1}
- {file_path_2}

---
> 查看完整分析报告: {dashboard_url}
```

#### 6.5.5 Diff Hunk 行号定位

- ReviewIssue 中的 line_start/line_end 是文件中新版本的行号
- 创建行级评论时需映射到 diff hunk 中的位置
- 无法定位到 diff hunk（问题在非变更区域）→ 降级为对话评论

---

### 6.6 M6 — Web Dashboard 模块（依赖 M1、M2、M5）

**详细任务清单**：见 [doc/tasks/m6-web-dashboard.md](tasks/m6-web-dashboard.md)

**关键实现要点**：

#### 6.6.1 技术方案

- **渲染**：Jinja2 服务端渲染 + HTMX 局部刷新
- **样式**：Tailwind CSS (CDN)
- **图表**：Chart.js (CDN)
- **认证**：GitHub OAuth + session cookie

#### 6.6.2 路由清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页 |
| GET | `/auth/login` | GitHub OAuth 跳转 |
| GET | `/auth/callback` | OAuth 回调 |
| GET | `/dashboard` | Dashboard 主页 |
| GET | `/dashboard/stats` | HTMX 统计数据 |
| GET | `/reviews` | 评审列表 |
| GET | `/reviews/{id}` | 评审详情 |
| GET | `/reviews/{id}/enhanced` | 增强详情 |
| GET | `/repositories` | 仓库列表 |
| GET | `/repositories/{id}/config` | 仓库配置 |
| PATCH | `/api/reviews/{id}/issues/{issue_id}` | 更新问题状态 |
| PUT | `/api/repositories/{id}/config` | 保存仓库配置 |

#### 6.6.3 统计服务

- 总 PR 数、总评审数、总问题数、平均问题数/PR
- 问题分布（按严重级别环形图 + 按类别柱状图）
- 趋势图（每日问题发现数折线图）
- 仓库对比（各仓库问题数柱状图）

#### 6.6.4 增强详情视图

- 左侧：代码 diff（绿色新增 / 红色删除）
- 右侧：问题列表，按行号关联，severity 颜色条标注
- 点击问题展开详情

#### 6.6.5 安全要求

- Session：httpOnly cookie + SameSite=Lax
- OAuth state 参数防 CSRF
- 仓库权限校验中间件
- 未登录 → 重定向 `/auth/login`

---

## 7. 配置文件模板

### 7.1 `.env.example`

```ini
# GitHub App
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
GITHUB_WEBHOOK_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# AI API
AI_API_KEY=
AI_API_BASE=https://api.deepseek.com/v1
AI_DEFAULT_MODEL=deepseek-v4-flash
AI_STRONG_MODEL=deepseek-v4-pro

# Database
DATABASE_URL=sqlite:///reviewpilot.db

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
SECRET_KEY=
```

### 7.2 `requirements.txt`

```
fastapi>=0.110.0
uvicorn[standard]>=0.27.0
sqlalchemy>=2.0.0
alembic>=1.13.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
pygithub>=2.1.0
structlog>=24.1.0
httpx>=0.26.0
python-jose[cryptography]>=3.3.0
jinja2>=3.1.0
javalang>=0.13.0
openai>=1.12.0

# dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
mypy>=1.8.0
ruff>=0.2.0
```

### 7.3 `.gitignore`

```
__pycache__/
*.py[cod]
*.db
.env
.venv/
venv/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
```

---

## 8. 主 Agent 执行流程

### 8.1 总体流程

```
1. 初始化项目骨架（PR-01-01 ~ PR-01-06）
2. 按 M1 → M2 → M3 → M4 → M5 → M6 顺序执行
3. 每个模块：
   a. 读取对应任务文件（doc/tasks/mX-*.md）
   b. 按子任务编号顺序执行
   c. 每个子任务：
      - 创建子 Agent，给予明确的开发指令
      - 子 Agent 完成代码 + 测试
      - 验证 mypy + ruff + pytest 通过
      - 提交 commit → 创建 PR
      - 更新 progress.md
4. 全部完成后执行阶段五（错误处理降级 + Docker + README）
```

### 8.2 子 Agent 模板

生成子 Agent 时，指令必须包含：

```
1. 任务描述：具体要实现什么（引用设计文档对应章节）
2. 输出文件：需要创建/修改哪些文件
3. 设计约束：关键的实现细节和 API 契约
4. 测试要求：至少覆盖哪些测试场景
5. 验收标准：mypy + ruff + pytest 全部通过
```

### 8.3 进度更新

每完成一个子任务后，必须更新 `doc/tasks/progress.md`：
- 在该子任务行打勾 `[x]`
- 更新模块进度计数
- 更新总计进度

---

## 9. 已知决策与约束

| 决策 | 内容 |
|------|------|
| AI 快速模型 | `deepseek-v4-flash` |
| AI 强模型 | `deepseek-v4-pro` |
| AI API Base | `https://api.deepseek.com/v1` (OpenAI-compatible) |
| 数据库 | SQLite 先起步，SQLAlchemy 保证可迁移到 MySQL |
| GitHub App | 已注册（个人账号），凭证待填入 `.env` |
| 入口文件 | `app/main.py`，删除根目录 `main.py` |
| 代码检查 | mypy --strict + ruff check，零容忍 |
| PR 语言 | 中文 |

---

## 10. 开始执行

现在请按以下步骤开始工作：

### Step 0：删除根目录 main.py

首先删除根目录空的 `main.py` 文件。

### Step 1：初始化项目

按 [doc/tasks/m1-infrastructure.md](tasks/m1-infrastructure.md) 子任务 1.1 创建项目骨架：
- 创建完整目录结构
- 编写 `requirements.txt`
- 创建 `app/main.py` FastAPI 入口骨架
- 创建 `.env.example`
- 编写 `Dockerfile` 和 `docker-compose.yml`

### Step 2-6：依次完成 M1-M6

按照顺序开发和提交，每个子任务独立 PR。

---

> 文档版本：v1.0 | 生成日期：2026-05-29 | 状态：已确认，可执行
