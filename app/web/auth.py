from __future__ import annotations

import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_config
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    """Redirect to GitHub OAuth authorization page."""
    config = get_config()
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    params = {
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": _redirect_uri(request),
        "state": state,
        "scope": "read:user",
    }
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    """Handle GitHub OAuth callback: exchange code → token → user info."""
    config = get_config()

    # Verify state
    saved_state: str = request.session.pop("oauth_state", "")
    if not saved_state or not secrets.compare_digest(saved_state, state):
        logger.warning("oauth_state_mismatch")
        return RedirectResponse("/?error=invalid_state")

    if not code:
        logger.warning("oauth_no_code")
        return RedirectResponse("/?error=no_code")

    # Exchange code for access token
    token = await _exchange_code(code, config, request)
    if not token:
        return RedirectResponse("/?error=token_exchange_failed")

    # Get GitHub user info
    github_user = await _get_github_user(token)
    if not github_user:
        return RedirectResponse("/?error=user_fetch_failed")

    # Create or update user
    gh_id = int(github_user["id"])  # type: ignore[call-overload]
    gh_login = str(github_user["login"])
    gh_avatar: Optional[str] = github_user.get("avatar_url")  # type: ignore[assignment]

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(
            User.github_user_id == gh_id
        ).first()
        if user is None:
            user = User(
                github_user_id=gh_id,
                login=gh_login,
                avatar_url=gh_avatar,
            )
            db.add(user)
        else:
            user.login = gh_login
            user.avatar_url = gh_avatar
        db.commit()
        db.refresh(user)
        request.session["user_id"] = user.id
        request.session["user_login"] = user.login
        logger.info("user_logged_in", login=user.login)
    finally:
        db.close()

    return RedirectResponse("/")


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Clear session and redirect to home."""
    request.session.clear()
    return RedirectResponse("/")


async def get_current_user(request: Request) -> Optional[User]:
    """Load the current user from session data."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    db: Session = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def require_auth(request: Request) -> Optional[User]:
    """Sync version for template rendering. Returns User or None."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    db: Session = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def _redirect_uri(request: Request) -> str:
    """Build the OAuth redirect URI from the request base URL."""
    base = str(request.base_url).rstrip("/")
    return f"{base}/auth/callback"


async def _exchange_code(
    code: str, config: Settings, request: Request
) -> Optional[str]:
    """Exchange OAuth authorization code for an access token."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": config.GITHUB_CLIENT_ID,
                    "client_secret": config.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": _redirect_uri(request),
                },
                headers={"Accept": "application/json"},
                timeout=15,
            )
            data: dict[str, object] = resp.json()
            raw: object = data.get("access_token")
            if isinstance(raw, str):
                return raw
            return None
        except Exception as exc:
            logger.error("token_exchange_error", error=str(exc))
            return None


async def _get_github_user(token: str) -> Optional[dict[str, object]]:
    """Fetch the authenticated GitHub user profile."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return None
            data: dict[str, object] = resp.json()
            return data
        except Exception as exc:
            logger.error("user_fetch_error", error=str(exc))
            return None
