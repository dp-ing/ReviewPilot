from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import get_config
from app.core.database import init_db
from app.core.logging import get_logger

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


@app.get("/health", response_class=JSONResponse)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
