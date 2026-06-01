import threading
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.bot.auto_review import AutoReviewHandler
from app.bot.command_handler import CommandHandler
from app.bot.comment_creator import CommentCreator
from app.bot.event_router import EventRouter
from app.core.config import get_config
from app.core.database import SessionLocal, init_db
from app.core.logging import get_logger
from app.engine.orchestrator import AnalysisOrchestrator
from app.engine.openai_provider import OpenAIProvider
from app.github.client import GitHubClient
from app.github.schemas import IssueCommentEvent
from app.github.webhook import verify_signature
from app.web.auth import router as auth_router
from app.web.routes import router as web_router

logger = get_logger(__name__)


def _build_review_wiring() -> tuple[AutoReviewHandler, CommandHandler]:
    """Wire up all dependencies for the review pipeline."""
    cfg = get_config()

    # AI Providers
    provider_fast = OpenAIProvider(
        api_key=cfg.AI_API_KEY,
        api_base=cfg.AI_API_BASE,
        model=cfg.AI_DEFAULT_MODEL,
    )
    provider_strong = OpenAIProvider(
        api_key=cfg.AI_API_KEY,
        api_base=cfg.AI_API_BASE,
        model=cfg.AI_STRONG_MODEL,
    )

    # Orchestrator
    orchestrator = AnalysisOrchestrator(
        provider_fast=provider_fast,
        provider_strong=provider_strong,
    )

    def _client_factory(installation_id: int) -> GitHubClient:
        return GitHubClient(installation_id)

    def _build_summary(result: Any, pr_detail: Any) -> str:
        """Build review summary comment from analysis result."""
        pr_url = f"https://github.com/{pr_detail.base_branch}/pull/{pr_detail.number}"
        return CommentCreator().build_summary_comment(result, pr_url)

    def _review_trigger(owner: str, repo: str, pr_number: int, focus: Optional[list[str]] = None, installation_id: int = 0) -> None:
        """Trigger a review for a PR in background (used by /review command)."""
        logger.info("review_command_triggered", owner=owner, repo=repo, pr=pr_number, installation_id=installation_id)

        def _run_review() -> None:
            handler = AutoReviewHandler(
                github_client_factory=_client_factory,
                orchestrator=orchestrator,
                comment_creator=_build_summary,
                db_session_factory=SessionLocal,
            )
            from app.github.schemas import PROpenEvent
            fake_event = PROpenEvent(
                event_type="pull_request",
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                sender="review-command",
                raw_payload={"installation": {"id": installation_id}},
            )
            handler.handle(fake_event)

        threading.Thread(target=_run_review, daemon=True).start()

    auto_review = AutoReviewHandler(
        github_client_factory=_client_factory,
        orchestrator=orchestrator,
        comment_creator=_build_summary,
        db_session_factory=SessionLocal,
    )

    command = CommandHandler(
        collaborator_checker=None,  # Skip permission check for now
        on_review_command=_review_trigger,
        on_permission_denied=None,
    )

    return auto_review, command


def _router_handler(event: object) -> None:
    """Adapter: AutoReviewHandler.handle for EventRouter."""
    auto_review.handle(event)


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

auto_review, command_handler = _build_review_wiring()

event_router = EventRouter(
    auto_review_handler=lambda e: auto_review.handle(e),
    command_handler=lambda e: command_handler.handle(e),
)

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
