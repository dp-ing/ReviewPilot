from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base
from app.models.pull_request import PullRequest
from app.models.review_issue import ReviewIssue
from app.models.review_record import ReviewRecord, ReviewStatus
from app.models.repository import Repository
from app.web.stats_service import StatsService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create an in-memory SQLite session with schema initialized."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_repo(
    db: Session,
    repo_id: int = 1,
    full_name: str = "test/repo",
) -> Repository:
    repo = Repository(
        github_repo_id=repo_id * 100,
        name="repo",
        full_name=full_name,
        owner=full_name.split("/")[0],
        html_url=f"https://github.com/{full_name}",
    )
    db.add(repo)
    db.flush()
    return repo


def _create_pr(
    db: Session,
    repo: Repository,
    pr_number: int = 1,
) -> PullRequest:
    pr = PullRequest(
        repository_id=repo.id,
        pr_number=pr_number,
        title="Test PR",
        author="testuser",
        head_sha="abc123",
        base_sha="def456",
        head_branch="feature",
        base_branch="main",
    )
    db.add(pr)
    db.flush()
    return pr


def _create_review(
    db: Session,
    pr: PullRequest,
    status: ReviewStatus = ReviewStatus.COMPLETED,
) -> ReviewRecord:
    record = ReviewRecord(
        pull_request_id=pr.id,
        status=status,
    )
    db.add(record)
    db.flush()
    return record


def _create_issue(
    db: Session,
    record: ReviewRecord,
    severity: str = "warning",
    category: str = "security",
    title: str = "Test issue",
    description: str = "Description",
) -> ReviewIssue:
    issue = ReviewIssue(
        review_record_id=record.id,
        file_path="src/test.py",
        line_start=1,
        line_end=1,
        severity=severity,
        category=category,
        title=title,
        description=description,
    )
    db.add(issue)
    db.flush()
    return issue


class TestOverviewStats:
    def test_empty_database(self, db_session: Session) -> None:
        service = StatsService(db_session_factory=lambda: db_session)
        stats = service.get_overview_stats()
        assert stats.total_reviews == 0
        assert stats.total_issues == 0
        assert stats.critical_count == 0
        assert stats.active_repos == 0

    def test_with_reviews_and_issues(self, db_session: Session) -> None:
        repo = _create_repo(db_session)
        pr = _create_pr(db_session, repo)
        for _ in range(5):
            review = _create_review(db_session, pr)
            _create_issue(db_session, review, severity="critical")
        for _ in range(3):
            review = _create_review(db_session, pr)
            _create_issue(db_session, review, severity="warning")
        for _ in range(2):
            review = _create_review(db_session, pr)
        db_session.commit()

        service = StatsService(db_session_factory=lambda: db_session)
        stats = service.get_overview_stats()
        assert stats.total_reviews == 10
        assert stats.total_issues == 8
        assert stats.critical_count == 5
        assert stats.warning_count == 3
        assert stats.suggestion_count == 0
        assert stats.active_repos == 1
        assert stats.avg_issues_per_review == 0.8


class TestIssueDistribution:
    def test_distribution_counts(self, db_session: Session) -> None:
        repo = _create_repo(db_session)
        pr = _create_pr(db_session, repo)
        r1 = _create_review(db_session, pr)
        _create_issue(db_session, r1, severity="critical", category="security")
        _create_issue(db_session, r1, severity="critical", category="security")
        _create_issue(db_session, r1, severity="warning", category="logic")
        db_session.commit()

        service = StatsService(db_session_factory=lambda: db_session)
        dist = service.get_issue_distribution()
        assert dist.by_severity["critical"] == 2
        assert dist.by_severity["warning"] == 1
        assert dist.by_severity["suggestion"] == 0
        assert dist.by_category["security"] == 2
        assert dist.by_category["logic"] == 1


class TestTrend:
    def test_trend_returns_daily_points(self, db_session: Session) -> None:
        repo = _create_repo(db_session)
        pr = _create_pr(db_session, repo)
        r1 = _create_review(db_session, pr)
        issue = _create_issue(db_session, r1)
        issue.created_at = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        service = StatsService(db_session_factory=lambda: db_session)
        trend = service.get_trend(days=7)
        assert len(trend) == 7
        assert sum(p.count for p in trend) == 1


class TestRepoComparison:
    def test_empty_database(self, db_session: Session) -> None:
        service = StatsService(db_session_factory=lambda: db_session)
        repos = service.get_repo_comparison()
        assert repos == []

    def test_repo_with_reviews(self, db_session: Session) -> None:
        repo = _create_repo(db_session)
        pr = _create_pr(db_session, repo)
        for _ in range(3):
            review = _create_review(db_session, pr)
            _create_issue(db_session, review, severity="critical")
        db_session.commit()

        service = StatsService(db_session_factory=lambda: db_session)
        repos = service.get_repo_comparison()
        assert len(repos) == 1
        assert repos[0].repo_name == "test/repo"
        assert repos[0].total_reviews == 3
        assert repos[0].total_issues == 3
        assert repos[0].critical_count == 3
