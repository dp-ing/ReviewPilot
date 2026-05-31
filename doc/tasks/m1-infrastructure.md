# M1 — 基础设施模块任务列表

> 模块职责：项目配置、数据库模型、日志、异常定义
> 依赖：无（所有模块依赖 M1）

---

## 子任务

### 1.1 项目骨架初始化

- [x] **PR-01-01** — 创建项目目录结构（`app/`, `app/core/`, `app/models/`, `tests/` 等）
- [x] **PR-01-02** — 编写 `requirements.txt`（FastAPI, SQLAlchemy, PyGithub, Pydantic, structlog, uvicorn 等）
- [x] **PR-01-03** — 创建 `app/main.py` FastAPI 入口骨架（不含路由，仅启动 + 生命周期钩子）
- [x] **PR-01-04** — 创建 `.env.example` 示例配置文件
- [x] **PR-01-05** — 编写 `Dockerfile` 基础镜像
- [x] **PR-01-06** — 编写 `docker-compose.yml`（app + 可选 MySQL/Redis）

### 1.2 配置管理

- [x] **PR-01-07** — 实现 `app/core/config.py` — Pydantic BaseSettings 配置类
  - `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`
  - `AI_API_KEY`, `AI_API_BASE`, `AI_DEFAULT_MODEL`, `AI_STRONG_MODEL`
  - `DATABASE_URL`, `LOG_LEVEL`, `APP_HOST`, `APP_PORT`
  - 单例 `get_config()` 函数
- [x] **PR-01-08** — 编写配置加载测试（默认值 + 环境变量覆盖）

### 1.3 数据库

- [x] **PR-01-09** — 实现 `app/core/database.py` — SQLAlchemy engine + session factory + `get_db_session()` 依赖注入
- [x] **PR-01-10** — 创建 `app/models/__init__.py` + 声明式基类 `Base`

### 1.4 数据模型

- [x] **PR-01-11** — 实现 `app/models/repository.py` — Repository 模型
- [x] **PR-01-12** — 实现 `app/models/pull_request.py` — PullRequest 模型
- [x] **PR-01-13** — 实现 `app/models/review_record.py` — ReviewRecord 模型
- [x] **PR-01-14** — 实现 `app/models/review_issue.py` — ReviewIssue 模型
- [x] **PR-01-15** — 实现 `app/models/user.py` — User 模型
- [x] **PR-01-16** — 实现 `app/models/repo_config.py` — RepoConfig 模型
- [x] **PR-01-17** — 编写模型关系测试（FK 关联、JSON 字段序列化、CRUD 操作）

### 1.5 日志与异常

- [x] **PR-01-18** — 实现 `app/core/logging.py` — structlog JSON 格式日志（不含源码内容）
- [x] **PR-01-19** — 实现 `app/core/exceptions.py` — 异常类层级（9 个子异常）
- [x] **PR-01-20** — 编写异常与日志的单元测试

---

## 完成标准

- [x] FastAPI 应用可启动，无路由但健康检查通过
- [x] 数据库表可通过 Alembic 自动创建
- [x] 所有模型 CRUD 测试通过
- [x] 配置可从 `.env` 正确加载
- [x] 异常层级完整，日志输出为 JSON 格式
