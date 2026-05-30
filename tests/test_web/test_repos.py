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


class TestReposList:
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

        resp = client.get("/repositories")
        assert resp.status_code == 200
        assert "仓库管理" in resp.text


class TestRepoConfig:
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
        mock_query.first.return_value = None
        mock_session.query.return_value = mock_query
        mock_session_cls.return_value = mock_session

        resp = client.get("/repositories/999/config")
        assert resp.status_code == 404
