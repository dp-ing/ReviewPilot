from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any
from unittest.mock import patch

import pytest

from app.core.exceptions import AIProviderError
from app.engine.openai_provider import OpenAIProvider
from app.engine.provider import AIProvider
from app.engine.schemas import ChatResponse, Message


def _build_response(content: str, model: str = "gpt-4o-mini") -> Any:
    resp_data = {
        "choices": [{
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "model": model,
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    }

    class _FakeResponse:
        @staticmethod
        def read() -> bytes:
            return json.dumps(resp_data).encode("utf-8")

    return _FakeResponse()


def _http_error() -> Any:
    raise urllib.error.HTTPError(
        "http://test", 500, "Internal Server Error", {}, None  # type: ignore[arg-type]
    )


class TestOpenAIProvider:
    def test_is_ai_provider(self) -> None:
        p = OpenAIProvider(api_key="sk-test")
        assert isinstance(p, AIProvider)

    def test_get_model_name(self) -> None:
        p = OpenAIProvider(model="gpt-4o", api_key="sk-test")
        assert p.get_model_name() == "gpt-4o"

    def test_get_max_tokens(self) -> None:
        p = OpenAIProvider(model="gpt-4o", api_key="sk-test")
        assert p.get_max_tokens() == 128000

    def test_get_max_tokens_unknown_model(self) -> None:
        p = OpenAIProvider(model="unknown-model", api_key="sk-test")
        assert p.get_max_tokens() == 4096

    def test_chat_success(self) -> None:
        p = OpenAIProvider(api_key="sk-test")
        with patch.object(urllib.request, "urlopen", return_value=_build_response("hello")):
            resp = p.chat([Message(role="user", content="hi")])
        assert isinstance(resp, ChatResponse)
        assert resp.content == "hello"

    def test_chat_http_error(self) -> None:
        p = OpenAIProvider(api_key="sk-test", max_retries=0)
        with patch.object(urllib.request, "urlopen", side_effect=_http_error):
            with pytest.raises(AIProviderError):
                p.chat([Message(role="user", content="hi")])

    def test_chat_connection_error_with_retry(self) -> None:
        """First attempt fails, second succeeds."""
        p = OpenAIProvider(api_key="sk-test", max_retries=1)

        call_count = [0]

        def side_effect(*args: Any, **kwargs: Any) -> Any:
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("Connection refused")
            return _build_response("retry success")

        with patch.object(urllib.request, "urlopen", side_effect=side_effect):
            resp = p.chat([Message(role="user", content="hi")])
        assert resp.content == "retry success"
        assert call_count[0] == 2

    def test_chat_all_retries_fail(self) -> None:
        p = OpenAIProvider(api_key="sk-test", max_retries=2)
        with patch.object(urllib.request, "urlopen", side_effect=OSError("fail")):
            with pytest.raises(AIProviderError):
                p.chat([Message(role="user", content="hi")])

    def test_custom_api_base(self) -> None:
        p = OpenAIProvider(api_key="sk-test", api_base="https://custom.api.com/v1")
        with patch.object(urllib.request, "urlopen", return_value=_build_response("ok")):
            resp = p.chat([Message(role="user", content="hi")])
        assert resp.content == "ok"

    def test_chat_passes_kwargs_to_body(self) -> None:
        p = OpenAIProvider(api_key="sk-test")
        captured_body: dict[str, Any] = {}

        def capture_request(req: urllib.request.Request, **kw: Any) -> Any:
            captured_body.update(json.loads(req.data.decode("utf-8")))
            return _build_response("ok")

        with patch.object(urllib.request, "urlopen", side_effect=capture_request):
            p.chat(
                [Message(role="user", content="hi")],
                temperature=0.5,
                max_tokens=100,
            )
        assert captured_body.get("temperature") == 0.5
        assert captured_body.get("max_tokens") == 100

    def test_timeout_configuration(self) -> None:
        p = OpenAIProvider(api_key="sk-test", timeout=30)
        assert p.timeout == 30
