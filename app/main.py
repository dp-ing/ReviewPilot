from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.bot.event_router import EventRouter
from app.core.config import get_config
from app.core.database import init_db
from app.core.logging import get_logger
from app.github.webhook import verify_signature
from app.web.auth import router as auth_router
from app.web.routes import router as web_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("app_starting", host=config.APP_HOST, port=config.APP_PORT)
    await init_db()
    logger.info("database_initialized")
    yield
    logger.info("app_stopping")


app = FastAPI(
    title="ReviewPilot",
    description="AI-driven GitHub PR code review assistant",
    version="0.1.0",
    lifespan=lifespan,
)

config = get_config()

event_router = EventRouter()

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY or "reviewpilot-dev-secret",
)

app.include_router(auth_router)
app.include_router(web_router)

@app.get("/health", response_class=JSONResponse)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/github")
async def webhook_github(request: Request) -> JSONResponse:
    """Handle incoming GitHub webhook events."""
    signature = request.headers.get("X-Hub-Signature-256", "")
    body_bytes = await request.body()

    if not verify_signature(body_bytes, signature):
        return JSONResponse(
            status_code=401, content={"error": "Invalid signature"}
        )

    payload: dict[str, object] = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "")

    response = event_router.handle_webhook(event_type, payload, signature)
    return JSONResponse(
        status_code=response.status_code, content=response.body
    )
