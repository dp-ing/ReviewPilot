from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.core.database import SessionLocal
from app.models.review_issue import ReviewIssue
from app.models.review_record import ReviewRecord
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


@router.get("/reviews", response_class=HTMLResponse)
async def reviews_list(
    request: Request,
    page: int = 1,
    status: str = "",
) -> HTMLResponse:
    """List all review records with filtering and pagination."""
    user = require_auth(request)
    if user is None:
        return templates.TemplateResponse(
            request=request, name="auth/login_prompt.html"
        )

    db = SessionLocal()
    try:
        query: Any = db.query(ReviewRecord).order_by(ReviewRecord.created_at.desc())
        if status:
            query = query.filter(ReviewRecord.status == status)

        total: int = query.count()
        per_page = 20
        total_pages = max(1, (total + per_page - 1) // per_page)
        offset_val = (page - 1) * per_page
        records = query.offset(offset_val).limit(per_page).all()

        page_range: list[object] = []
        for p in range(1, total_pages + 1):
            if p == 1 or p == total_pages or abs(p - page) <= 2:
                page_range.append(p)
            elif page_range and page_range[-1] != "...":
                page_range.append("...")

        return templates.TemplateResponse(
            request=request,
            name="reviews/list.html",
            context={
                "user": user,
                "records": records,
                "page": page,
                "total_pages": total_pages,
                "total": total,
                "current_status": status,
                "query_string": f"status={status}" if status else "",
                "page_range": page_range,
            },
        )
    finally:
        db.close()


@router.get("/reviews/{review_id}", response_class=HTMLResponse)
async def review_detail(request: Request, review_id: int) -> HTMLResponse:
    """Show details of a specific review record."""
    user = require_auth(request)
    if user is None:
        return templates.TemplateResponse(
            request=request, name="auth/login_prompt.html"
        )

    db = SessionLocal()
    try:
        record = db.query(ReviewRecord).filter(ReviewRecord.id == review_id).first()
        if record is None:
            return HTMLResponse("Not Found", status_code=404)

        issues = (
            db.query(ReviewIssue)
            .filter(ReviewIssue.review_record_id == review_id)
            .all()
        )

        return templates.TemplateResponse(
            request=request,
            name="reviews/detail.html",
            context={
                "user": user,
                "record": record,
                "issues": issues,
            },
        )
    finally:
        db.close()


@router.patch("/api/reviews/{review_id}/issues/{issue_id}")
async def update_issue_status(
    request: Request,
    review_id: int,
    issue_id: int,
) -> JSONResponse:
    """HTMX endpoint: toggle issue status."""
    db = SessionLocal()
    try:
        issue = (
            db.query(ReviewIssue)
            .filter(ReviewIssue.id == issue_id)
            .filter(ReviewIssue.review_record_id == review_id)
            .first()
        )
        if issue is None:
            return JSONResponse({"error": "Not Found"}, status_code=404)

        return JSONResponse({"id": issue.id, "status": "ok"})
    finally:
        db.close()
