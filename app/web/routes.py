from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.database import SessionLocal
from app.web.auth import require_auth
from app.web.stats_service import StatsService

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="templates")

_stats_service: Optional[StatsService] = None


def get_stats_service() -> StatsService:
    global _stats_service
    if _stats_service is None:
        _stats_service = StatsService(db_session_factory=SessionLocal)
    return _stats_service


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Home page: shows dashboard when logged in, login prompt otherwise."""
    user = require_auth(request)
    if user is None:
        return templates.TemplateResponse(
            request=request, name="auth/login_prompt.html"
        )

    service = get_stats_service()
    overview = service.get_overview_stats()
    distribution = service.get_issue_distribution()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "stats": {
                "total_reviews": overview.total_reviews,
                "total_issues": overview.total_issues,
                "critical_count": overview.critical_count,
                "active_repos": overview.active_repos,
            },
            "by_severity": distribution.by_severity,
            "by_category": distribution.by_category,
        },
    )


@router.get("/dashboard/stats")
async def dashboard_stats(request: Request) -> JSONResponse:
    """HTMX endpoint: return stats as JSON for partial refresh."""
    service = get_stats_service()
    overview = service.get_overview_stats()
    distribution = service.get_issue_distribution()
    trend = service.get_trend()
    repos = service.get_repo_comparison()

    return JSONResponse({
        "overview": {
            "total_reviews": overview.total_reviews,
            "total_issues": overview.total_issues,
            "critical_count": overview.critical_count,
            "warning_count": overview.warning_count,
            "suggestion_count": overview.suggestion_count,
            "active_repos": overview.active_repos,
            "avg_issues_per_review": overview.avg_issues_per_review,
        },
        "by_severity": distribution.by_severity,
        "by_category": distribution.by_category,
        "trend": [{"date": p.date, "count": p.count} for p in trend],
        "repo_comparison": [
            {
                "repo_name": r.repo_name,
                "total_reviews": r.total_reviews,
                "total_issues": r.total_issues,
                "critical_count": r.critical_count,
            }
            for r in repos
        ],
    })
