from __future__ import annotations

from typing import Any

import pytest

from app.engine.provider import AIProvider
from app.engine.schemas import ChatResponse, Message


class _MockProvider(AIProvider):
    """Minimal concrete provider for testing the ABC."""

    def __init__(self, model: str = "mock-model", max_tokens: int = 4096) -> None:
        self._model = model
        self._max_tokens = max_tokens

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        return ChatResponse(
            content="mock response",
            model=self._model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

    def get_model_name(self) -> str:
        return self._model

    def get_max_tokens(self) -> int:
        return self._max_tokens


class TestAIProvider:
    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            AIProvider()  # type: ignore[abstract]

    def test_concrete_provider_instantiation(self) -> None:
        p = _MockProvider()
        assert isinstance(p, AIProvider)

    def test_get_model_name(self) -> None:
        p = _MockProvider(model="gpt-4")
        assert p.get_model_name() == "gpt-4"

    def test_get_max_tokens(self) -> None:
        p = _MockProvider(max_tokens=8192)
        assert p.get_max_tokens() == 8192

    def test_chat_returns_chat_response(self) -> None:
        p = _MockProvider()
        resp = p.chat([Message(role="user", content="hello")])
        assert isinstance(resp, ChatResponse)
        assert resp.content == "mock response"
        assert resp.model == "mock-model"

    def test_chat_with_multiple_messages(self) -> None:
        p = _MockProvider()
        messages = [
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hi"),
        ]
        resp = p.chat(messages)
        assert resp.content == "mock response"

    def test_chat_passes_kwargs(self) -> None:
        p = _MockProvider()
        resp = p.chat(
            [Message(role="user", content="test")],
            temperature=0.7,
            max_tokens=500,
        )
        assert isinstance(resp, ChatResponse)
