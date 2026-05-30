from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from os import environ
from typing import Any

from app.core.exceptions import AIProviderError
from app.engine.provider import AIProvider
from app.engine.schemas import ChatResponse, Message


class OpenAIProvider(AIProvider):
    """OpenAI-compatible API provider with retry and timeout."""

    _DEFAULT_TIMEOUT = 60
    _MAX_RETRIES = 3
    _RETRY_DELAY = 1.0  # seconds, doubles each retry

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: int = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self.api_key = api_key or environ.get("OPENAI_API_KEY", "")
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def get_model_name(self) -> str:
        return self.model

    def get_max_tokens(self) -> int:
        limits: dict[str, int] = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4-turbo": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 16385,
        }
        return limits.get(self.model, 4096)

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        url = f"{self.api_base}/chat/completions"
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        body.update(kwargs)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._do_request(url, body)
            except urllib.error.HTTPError as exc:
                raise AIProviderError(
                    f"OpenAI API returned HTTP {exc.code}",
                    detail=self._read_error_body(exc),
                )
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    delay = self._RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)

        raise AIProviderError(
            f"OpenAI API request failed after {self.max_retries + 1} attempts",
            detail=str(last_error),
        )

    def _do_request(self, url: str, body: dict[str, Any]) -> ChatResponse:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        resp = urllib.request.urlopen(req, timeout=self.timeout)
        raw = json.loads(resp.read().decode("utf-8"))
        choice = raw["choices"][0]
        return ChatResponse(
            content=choice["message"]["content"],
            model=raw.get("model", self.model),
            usage=raw.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    @staticmethod
    def _read_error_body(exc: urllib.error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8")
        except Exception:
            return str(exc)
