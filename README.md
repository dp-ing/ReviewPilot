# ReviewPilot

AI-driven GitHub PR code review assistant. Automatically analyzes pull request changes and provides line-level comments and summary reports via GitHub Bot + Web Dashboard.

## Features

| Feature | Description |
|---------|-------------|
| PR Auto Review | Webhook-triggered → fetch diff → AI analysis → line-level comments + summary |
| Manual Trigger | `/review` command in PR comments, supports `focus:security,logic` filter |
| 5 Analysis Categories | security, logic, performance, best_practice, code style |
| Python/Java AST | Deterministic rule checking (18 rules total) + AI contextual analysis |
| Web Dashboard | Review records, statistics charts, repo configuration, enhanced detail view |
| False Positive Control | Configurable confidence thresholds, ignore patterns, per-repo settings |
| OAuth Login | GitHub OAuth for Dashboard access control |

## Architecture

```
POST /webhook/github
  → EventRouter (signature verify → parse event → route)
    → AutoReviewHandler (PR open/sync)
    → CommandHandler (issue_comment /review)
      → AnalysisOrchestrator (two-phase AI analysis)
        → Stage 1: deepseek-v4-flash (change summary + risk flags)
        → Stage 2: deepseek-v4-pro (4-category parallel deep analysis)
      → PostProcessor (merge, dedup, filter, sort)
      → CommentCreator (format → line comments + summary)
```

```
Web Dashboard (SSR)
  GET /              → index.html (dashboard with stats)
  GET /dashboard     → dashboard/overview.html (Chart.js charts)
  GET /reviews       → list with pagination + filter
  GET /reviews/:id   → detail with issue list
  GET /reviews/:id/enhanced → file-grouped view with Alpine.js
  GET /repositories  → repo list with config status
  GET /repositories/:id/config → HTMX config form
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.9+) |
| Database | SQLite → MySQL (SQLAlchemy 2.0 + Alembic migrations) |
| AI | OpenAI-compatible API (DeepSeek) |
| GitHub Integration | PyGithub + raw API via httpx |
| Frontend | Jinja2 SSR + HTMX + Tailwind CSS + Chart.js + Alpine.js |
| AST Analysis | Python `ast` stdlib / Java `javalang` |
| Auth | GitHub OAuth 2.0 + Starlette SessionMiddleware |
| Code Quality | mypy --strict + ruff + pytest |

## Project Structure

```
ReviewPilot/
├── app/
│   ├── main.py                     # FastAPI entry point + webhook route
│   ├── core/                       # M1: Config, database, logging, exceptions
│   │   ├── config.py               # Pydantic BaseSettings (auto-loads .env)
│   │   ├── database.py             # SQLAlchemy engine + session factory
│   │   ├── logging.py              # structlog JSON logger
│   │   └── exceptions.py           # 9-exception hierarchy
│   ├── models/                     # M1: SQLAlchemy ORM models (6 models)
│   ├── github/                     # M2: Webhook handler + API client
│   ├── analyzer/                   # M3: Python/Java AST analyzer (18 rules)
│   ├── engine/                     # M4: AI provider, diff parser, orchestrator
│   │   └── prompts/                # Jinja2 prompt templates (system + 2 stages)
│   ├── bot/                        # M5: Event router, auto review, commands, comments
│   └── web/                        # M6: OAuth, routes, stats service, enhanced view
├── templates/                      # Jinja2 templates (SSR)
│   ├── base.html                   # Main layout (nav + sidebar + content)
│   ├── index.html                  # Home dashboard
│   ├── auth/                       # Login prompt
│   ├── dashboard/                  # Stats cards + chart templates
│   ├── reviews/                    # List, detail, issue row, enhanced view
│   ├── repos/                      # List, config, config form
│   └── shared/                     # Severity badge, pagination, filter bar
├── static/css/app.css              # Custom styles
├── tests/                          # 439 tests, 90% coverage
│   ├── test_core/                  # M1 tests (6 files)
│   ├── test_github/                # M2 tests (3 files)
│   ├── test_analyzer/              # M3 tests (5 files + fixtures)
│   ├── test_engine/                # M4 tests (7 files)
│   ├── test_bot/                   # M5 tests (4 files)
│   └── test_web/                   # M6 tests (5 files)
├── alembic/                        # Database migrations
├── doc/                            # Design docs + task lists
├── Dockerfile + docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

## API Routes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Home dashboard |
| `GET` | `/dashboard` | Full dashboard with charts |
| `GET` | `/dashboard/stats` | JSON stats (HTMX) |
| `GET` | `/health` | Health check |
| `POST` | `/webhook/github` | GitHub webhook receiver |
| `GET` | `/auth/login` | GitHub OAuth redirect |
| `GET` | `/auth/callback` | OAuth callback handler |
| `GET` | `/auth/logout` | Clear session |
| `GET` | `/reviews` | Review list (paginated, filterable) |
| `GET` | `/reviews/{id}` | Review detail |
| `GET` | `/reviews/{id}/enhanced` | Enhanced view (issues grouped by file) |
| `PATCH` | `/api/reviews/{id}/issues/{issue_id}` | Update issue status |
| `GET` | `/repositories` | Repository list |
| `GET` | `/repositories/{id}/config` | Repository config page |
| `PUT` | `/api/repositories/{id}/config` | Save repository config |

## Analysis Rules

### Python (10 rules)
| Rule ID | Severity | Category |
|---------|----------|----------|
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

### Java (8 rules)
| Rule ID | Severity | Category |
|---------|----------|----------|
| java-command-injection | critical | security |
| java-unsafe-deserial | critical | security |
| java-sql-concat | warning | security |
| java-resource-leak | warning | best_practice |
| java-hardcoded-secret | warning | security |
| java-complexity | warning | style |
| java-method-length | suggestion | style |
| java-unhandled-exception | suggestion | style |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Fill in GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY (or .pem path),
# GITHUB_WEBHOOK_SECRET, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
# AI_API_KEY, SECRET_KEY

# 3. Initialize database
alembic upgrade head

# 4. Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note**: `GITHUB_APP_PRIVATE_KEY` accepts either the PEM content directly or a path to a `.pem`/`.key` file. The config auto-detects and loads from file when needed.

## Development

```bash
# Type check
mypy app/ --strict

# Lint
ruff check app/

# Tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# All three must pass before commit
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_APP_ID` | GitHub App ID | — |
| `GITHUB_APP_PRIVATE_KEY` | PEM private key (content or file path) | — |
| `GITHUB_WEBHOOK_SECRET` | Webhook HMAC-SHA256 secret | — |
| `GITHUB_CLIENT_ID` | OAuth App client ID | — |
| `GITHUB_CLIENT_SECRET` | OAuth App client secret | — |
| `AI_API_KEY` | AI API key | — |
| `AI_API_BASE` | AI API endpoint | `https://api.deepseek.com/v1` |
| `AI_DEFAULT_MODEL` | Fast model for Stage 1 | `deepseek-v4-flash` |
| `AI_STRONG_MODEL` | Deep analysis model | `deepseek-v4-pro` |
| `DATABASE_URL` | Database connection | `sqlite:///reviewpilot.db` |
| `APP_HOST` | Server bind address | `0.0.0.0` |
| `APP_PORT` | Server port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `SECRET_KEY` | Session encryption key | — |

## Quality Metrics

| Metric | Value |
|--------|-------|
| mypy --strict | 0 issues (46 source files) |
| ruff check | 0 issues |
| Tests | 439 passed |
| Coverage | 90% |

## License

MIT
