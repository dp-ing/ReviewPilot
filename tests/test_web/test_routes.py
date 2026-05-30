from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def _mock_auth(
    mock_auth: MagicMock,
    mock_session_cls: MagicMock,
) -> MagicMock:
    from app.models.user import User
    mock_user = User(
        id=1, github_user_id=999, login="test", avatar_url=None, is_admin=False
    )
    mock_auth.return_value = mock_user

    mock_session = MagicMock()
    mock_query = MagicMock()
    mock_query.all.return_value = []
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    mock_session.query.return_value = mock_query
    mock_session_cls.return_value = mock_session
    return mock_user


def _patch_stats_service() -> MagicMock:
    """Patch get_stats_service to return a mock with canned stats."""
    from app.web.stats_service import (
        IssueDistribution,
        OverviewStats,
        RepoComparison,
        TrendPoint,
    )

    mock_service = MagicMock()
    mock_service.get_overview_stats.return_value = OverviewStats(
        total_reviews=0,
        total_issues=0,
        critical_count=0,
        warning_count=0,
        suggestion_count=0,
        active_repos=0,
        avg_issues_per_review=0.0,
    )
    mock_service.get_issue_distribution.return_value = IssueDistribution(
        by_severity={},
        by_category={},
    )
    mock_service.get_trend.return_value = []
    mock_service.get_repo_comparison.return_value = []
    return mock_service


class TestDashboardRoute:
    def test_unauthenticated_shows_login(self, client: TestClient) -> None:
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 200
        assert "GitHub" in resp.text

    @patch("app.web.routes.get_stats_service")
    @patch("app.web.routes.require_auth")
    @patch("app.web.routes.SessionLocal")
    def test_authenticated_shows_dashboard(
        self,
        mock_session_cls: MagicMock,
        mock_auth: MagicMock,
        mock_stats_fn: MagicMock,
        client: TestClient,
    ) -> None:
        _mock_auth(mock_auth, mock_session_cls)
        mock_stats_fn.return_value = _patch_stats_service()
        resp = client.get("/dashboard")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text


class TestRepositoriesRoute:
    def test_unauthenticated_shows_login(self, client: TestClient) -> None:
        resp = client.get("/repositories", follow_redirects=False)
        assert resp.status_code == 200
        assert "GitHub" in resp.text

    @patch("app.web.routes.require_auth")
    @patch("app.web.routes.SessionLocal")
    def test_authenticated_shows_list(
        self,
        mock_session_cls: MagicMock,
        mock_auth: MagicMock,
        client: TestClient,
    ) -> None:
        _mock_auth(mock_auth, mock_session_cls)
        resp = client.get("/repositories")
        assert resp.status_code == 200
        assert "仓库管理" in resp.text


class TestRepoConfigRoute:
    @patch("app.web.routes.require_auth")
    @patch("app.web.routes.SessionLocal")
    def test_not_found_returns_404(
        self,
        mock_session_cls: MagicMock,
        mock_auth: MagicMock,
        client: TestClient,
    ) -> None:
        _mock_auth(mock_auth, mock_session_cls)
        resp = client.get("/repositories/999/config")
        assert resp.status_code == 404


class TestIndexRoute:
    def test_unauthenticated_shows_login(self, client: TestClient) -> None:
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 200
        assert "GitHub" in resp.text

    @patch("app.web.routes.get_stats_service")
    @patch("app.web.routes.require_auth")
    @patch("app.web.routes.SessionLocal")
    def test_authenticated_shows_index(
        self,
        mock_session_cls: MagicMock,
        mock_auth: MagicMock,
        mock_stats_fn: MagicMock,
        client: TestClient,
    ) -> None:
        _mock_auth(mock_auth, mock_session_cls)
        mock_stats_fn.return_value = _patch_stats_service()
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text


class TestDashboardStats:
    @patch("app.web.routes.get_stats_service")
    def test_returns_json(self, mock_stats_fn: MagicMock, client: TestClient) -> None:
        mock_stats_fn.return_value = _patch_stats_service()
        resp = client.get("/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "overview" in data
        assert "by_severity" in data
        assert "trend" in data
        assert "repo_comparison" in data


class TestHealthCheck:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
