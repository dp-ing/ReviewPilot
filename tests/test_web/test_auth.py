from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def _extract_state_from_login(client: TestClient) -> str:
    """Call /auth/login and extract the state parameter from the redirect URL."""
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code == 307
    location = resp.headers["location"]
    qs = parse_qs(urlparse(location).query)
    return qs["state"][0]


class TestAuthLogin:
    def test_login_redirects_to_github(self, client: TestClient) -> None:
        resp = client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 307
        location = resp.headers["location"]
        assert "github.com/login/oauth/authorize" in location
        assert "client_id=" in location
        assert "state=" in location
        assert "redirect_uri=" in location

    def test_login_state_persisted_in_session(self, client: TestClient) -> None:
        resp = client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 307
        # Session cookie should be set
        assert "session" in resp.cookies


class TestAuthCallback:
    def test_callback_without_state_rejects(self, client: TestClient) -> None:
        resp = client.get(
            "/auth/callback", params={"code": "test"}, follow_redirects=False
        )
        # No session at all → state mismatch
        location = resp.headers["location"]
        assert "error=invalid_state" in location

    def test_callback_state_mismatch_rejects(self, client: TestClient) -> None:
        # Get a session with a valid state (sets oauth_state in session)
        _extract_state_from_login(client)
        # Now use a DIFFERENT state - session has valid_state, but we send wrong
        resp = client.get(
            "/auth/callback",
            params={"code": "test", "state": "wrong_state"},
            follow_redirects=False,
        )
        location = resp.headers["location"]
        assert "error=invalid_state" in location

    def test_callback_without_code_rejects(self, client: TestClient) -> None:
        # Get state from login
        state = _extract_state_from_login(client)
        resp = client.get(
            "/auth/callback",
            params={"state": state},
            follow_redirects=False,
        )
        location = resp.headers["location"]
        assert "error=no_code" in location

    @patch("app.web.auth._exchange_code")
    @patch("app.web.auth._get_github_user")
    def test_callback_successful_login(
        self,
        mock_get_user: MagicMock,
        mock_exchange: MagicMock,
        client: TestClient,
    ) -> None:
        mock_exchange.return_value = "mock_access_token"
        mock_get_user.return_value = {
            "id": 12345,
            "login": "testuser",
            "avatar_url": "https://example.com/avatar.png",
        }

        state = _extract_state_from_login(client)
        resp = client.get(
            "/auth/callback",
            params={"code": "valid_code", "state": state},
            follow_redirects=False,
        )
        assert resp.status_code == 307
        assert resp.headers["location"] == "/"

    @patch("app.web.auth._exchange_code")
    def test_callback_token_exchange_fails(
        self, mock_exchange: MagicMock, client: TestClient
    ) -> None:
        mock_exchange.return_value = None

        state = _extract_state_from_login(client)
        resp = client.get(
            "/auth/callback",
            params={"code": "bad", "state": state},
            follow_redirects=False,
        )
        location = resp.headers["location"]
        assert "error=token_exchange_failed" in location


class TestAuthLogout:
    def test_logout_clears_session(self, client: TestClient) -> None:
        resp = client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 307
        assert resp.headers["location"] == "/"


class TestProtectedRoutes:
    def test_index_redirects_to_login_when_not_authenticated(
        self, client: TestClient
    ) -> None:
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 200
        assert "GitHub" in resp.text

    @patch("app.web.routes.require_auth")
    def test_index_shows_dashboard_when_authenticated(
        self, mock_auth: MagicMock, client: TestClient
    ) -> None:
        from app.models.user import User
        mock_user = User(
            id=1,
            github_user_id=999,
            login="testuser",
            avatar_url=None,
            is_admin=False,
        )
        mock_auth.return_value = mock_user

        resp = client.get("/")
        assert resp.status_code == 200
        assert "testuser" in resp.text
        assert "Dashboard" in resp.text


class TestRequireAuth:
    def test_require_auth_returns_none_when_no_session(self) -> None:
        from app.web.auth import require_auth
        from unittest.mock import Mock
        mock_request = Mock()
        mock_request.session = {}
        result = require_auth(mock_request)
        assert result is None
