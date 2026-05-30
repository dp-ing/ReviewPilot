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


class TestReviewsList:
    def test_unauthenticated_shows_login(self, client: TestClient) -> None:
        resp = client.get("/reviews", follow_redirects=False)
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
        from app.models.user import User
        mock_user = User(
            id=1, github_user_id=999, login="test", avatar_url=None, is_admin=False
        )
        mock_auth.return_value = mock_user

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_session.query.return_value = mock_query
        mock_session_cls.return_value = mock_session

        resp = client.get("/reviews")
        assert resp.status_code == 200
        assert "评审记录" in resp.text


class TestReviewDetail:
    @patch("app.web.routes.require_auth")
    @patch("app.web.routes.SessionLocal")
    def test_not_found_returns_404(
        self,
        mock_session_cls: MagicMock,
        mock_auth: MagicMock,
        client: TestClient,
    ) -> None:
        from app.models.user import User
        mock_user = User(
            id=1, github_user_id=999, login="test", avatar_url=None, is_admin=False
        )
        mock_auth.return_value = mock_user

        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Not found
        mock_session.query.return_value = mock_query
        mock_session_cls.return_value = mock_session

        resp = client.get("/reviews/999")
        assert resp.status_code == 404
