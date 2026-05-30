from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.pull_request import PullRequest
from app.models.review_issue import ReviewIssue
from app.models.review_record import ReviewRecord, ReviewStatus
from app.models.repository import Repository

logger = get_logger(__name__)


@dataclass
class OverviewStats:
    total_reviews: int = 0
    total_issues: int = 0
    critical_count: int = 0
    warning_count: int = 0
    suggestion_count: int = 0
    active_repos: int = 0
    avg_issues_per_review: float = 0.0


@dataclass
class IssueDistribution:
    by_severity: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)


@dataclass
class TrendPoint:
    date: str
    count: int


@dataclass
class RepoComparison:
    repo_name: str
    total_reviews: int
    total_issues: int
    critical_count: int


class StatsService:
    """Query dashboard statistics from the database."""

    def __init__(
        self,
        db_session_factory: Callable[[], Session],
    ) -> None:
        self._db_factory = db_session_factory

    def get_overview_stats(self) -> OverviewStats:
        """Aggregate high-level review statistics."""
        db = self._db_factory()
        try:
            total_reviews = db.query(ReviewRecord).count()

            total_issues = db.query(ReviewIssue).count()
            critical_count = (
                db.query(ReviewIssue)
                .filter(ReviewIssue.severity == "critical")
                .count()
            )
            warning_count = (
                db.query(ReviewIssue)
                .filter(ReviewIssue.severity == "warning")
                .count()
            )
            suggestion_count = (
                db.query(ReviewIssue)
                .filter(ReviewIssue.severity == "suggestion")
                .count()
            )

            active_repos = (
                db.query(Repository)
                .join(PullRequest, PullRequest.repository_id == Repository.id)
                .join(ReviewRecord, ReviewRecord.pull_request_id == PullRequest.id)
                .distinct()
                .count()
            )

            avg_issues = 0.0
            if total_reviews > 0:
                avg_issues = total_issues / total_reviews

            return OverviewStats(
                total_reviews=total_reviews,
                total_issues=total_issues,
                critical_count=critical_count,
                warning_count=warning_count,
                suggestion_count=suggestion_count,
                active_repos=active_repos,
                avg_issues_per_review=round(avg_issues, 1),
            )
        finally:
            db.close()

    def get_issue_distribution(self) -> IssueDistribution:
        """Breakdown of issues by severity and category."""
        db = self._db_factory()
        try:
            by_severity: dict[str, int] = {}
            for severity in ("critical", "warning", "suggestion"):
                count = (
                    db.query(ReviewIssue)
                    .filter(ReviewIssue.severity == severity)
                    .count()
                )
                by_severity[severity] = count

            by_category: dict[str, int] = {}
            rows = (
                db.query(ReviewIssue.category, func.count(ReviewIssue.id))
                .group_by(ReviewIssue.category)
                .all()
            )
            for category, count in rows:
                by_category[category] = count

            return IssueDistribution(
                by_severity=by_severity,
                by_category=by_category,
            )
        finally:
            db.close()

    def get_trend(self, days: int = 30) -> list[TrendPoint]:
        """Daily issue counts for the past N days."""
        db = self._db_factory()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            rows = (
                db.query(
                    func.date(ReviewIssue.created_at).label("day"),
                    func.count(ReviewIssue.id).label("cnt"),
                )
                .filter(ReviewIssue.created_at >= cutoff)
                .group_by("day")
                .order_by("day")
                .all()
            )

            date_map: dict[str, int] = {row[0]: row[1] for row in rows}

            points: list[TrendPoint] = []
            for i in range(days):
                d = cutoff + timedelta(days=i)
                ds = d.strftime("%Y-%m-%d")
                points.append(TrendPoint(date=ds, count=date_map.get(ds, 0)))
            return points
        finally:
            db.close()

    def get_repo_comparison(self) -> list[RepoComparison]:
        """Per-repository comparison of review activity."""
        db = self._db_factory()
        try:
            repos = db.query(Repository).all()
            comparisons: list[RepoComparison] = []
            for repo in repos:
                pr_ids = select(PullRequest.id).where(
                    PullRequest.repository_id == repo.id
                ).scalar_subquery()

                review_count = (
                    db.query(ReviewRecord)
                    .filter(ReviewRecord.pull_request_id.in_(pr_ids))
                    .filter(ReviewRecord.status == ReviewStatus.COMPLETED)
                    .count()
                )
                if review_count == 0:
                    continue

                issue_count = (
                    db.query(ReviewIssue)
                    .join(ReviewRecord)
                    .filter(ReviewRecord.pull_request_id.in_(pr_ids))
                    .count()
                )
                critical_count = (
                    db.query(ReviewIssue)
                    .join(ReviewRecord)
                    .filter(ReviewRecord.pull_request_id.in_(pr_ids))
                    .filter(ReviewIssue.severity == "critical")
                    .count()
                )

                comparisons.append(RepoComparison(
                    repo_name=repo.full_name,
                    total_reviews=review_count,
                    total_issues=issue_count,
                    critical_count=critical_count,
                ))
            return comparisons
        finally:
            db.close()
