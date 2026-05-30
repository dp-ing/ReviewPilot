from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.engine.schemas import ChatResponse, Message


class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    @abstractmethod
    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        """Send messages to the AI model and return a response.

        Args:
            messages: List of chat messages (system, user, assistant).
            **kwargs: Additional provider-specific parameters (temperature, etc.).

        Returns:
            ChatResponse with the model's reply.

        Raises:
            AIProviderError: On API failure or timeout.
        """
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier."""
        ...

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return the maximum token limit for this model."""
        ...
