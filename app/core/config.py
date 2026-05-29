from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # GitHub App
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # AI API
    AI_API_KEY: str = ""
    AI_API_BASE: str = "https://api.deepseek.com/v1"
    AI_DEFAULT_MODEL: str = "deepseek-v4-flash"
    AI_STRONG_MODEL: str = "deepseek-v4-pro"

    # Database
    DATABASE_URL: str = "sqlite:///reviewpilot.db"

    # Server
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_config() -> Settings:
    return Settings()
