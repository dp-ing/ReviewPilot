from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.web.auth import require_auth

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Home page: shows dashboard when logged in, login prompt otherwise."""
    user = require_auth(request)
    if user is None:
        return templates.TemplateResponse(
            request=request, name="auth/login_prompt.html"
        )
    return templates.TemplateResponse(
        request=request, name="index.html", context={"user": user}
    )
