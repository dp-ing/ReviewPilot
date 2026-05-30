# ReviewPilot

AI-driven GitHub PR code review assistant. Automatically analyzes pull request changes and provides line-level comments and summary reports.

## Features

- **PR Auto Review**: Webhook-triggered diff analysis with AI + AST rules
- **Manual Trigger**: `/review` command in PR comments
- **5 Analysis Categories**: Security, Logic, Performance, Best Practice, Code Style
- **Python/Java Deep Analysis**: AST deterministic rule checking + AI contextual analysis
- **Web Dashboard**: Review records, statistics, repo configuration, enhanced detail view
- **False Positive Control**: Configurable confidence thresholds and ignore rules

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.9+) |
| Database | SQLite (dev) → MySQL (prod) |
| ORM | SQLAlchemy 2.0 + Alembic |
| AI | OpenAI-compatible API |
| Frontend | Jinja2 + HTMX + Tailwind CSS + Chart.js |
| AST | Python `ast` stdlib / Java `javalang` |
| Code Quality | mypy --strict + ruff |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GitHub App credentials and AI API key

# Initialize database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Development

```bash
# Type check
mypy app/ --strict

# Lint
ruff check app/

# Run tests
pytest tests/ -v --cov=app --cov-report=term-missing
```

## Configuration

See `.env.example` for all environment variables. Key settings:

| Variable | Description |
|----------|-------------|
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App private key (PEM) |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature secret |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | OAuth App for Dashboard login |
| `AI_API_KEY` | AI API key |
| `AI_API_BASE` | AI API endpoint (default: `https://api.deepseek.com/v1`) |
| `DATABASE_URL` | Database connection string |

## License

MIT
