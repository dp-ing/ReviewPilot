from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.core.logging import get_logger
from app.github.schemas import (
    BaseWebhookEvent,
    IssueCommentEvent,
    PROpenEvent,
    PRSyncEvent,
)
from app.github.webhook import parse_event

logger = get_logger(__name__)


@dataclass
class WebhookResponse:
    """Response from the webhook event router."""

    status_code: int = 200
    body: dict[str, Any] = field(default_factory=dict)

    def to_json_response(self) -> tuple[dict[str, Any], int]:
        return self.body, self.status_code


class EventRouter:
    """Route GitHub webhook events to the appropriate handler.

    Routing rules:
    - PR opened / reopened / synchronize → auto_review_handler
    - issue_comment created → command_handler
    - Other events → 200 OK (ignored)
    """

    def __init__(
        self,
        auto_review_handler: Optional[Callable[[BaseWebhookEvent], None]] = None,
        command_handler: Optional[Callable[[IssueCommentEvent], None]] = None,
    ) -> None:
        self.auto_review_handler = auto_review_handler
        self.command_handler = command_handler

    def handle_webhook(
        self,
        event_type: str,
        payload: dict[str, Any],
        signature: str,
    ) -> WebhookResponse:
        """Handle an incoming GitHub webhook event.

        Steps:
        1. Verify HMAC signature
        2. Parse the event payload
        3. Route to the matching handler
        """
        # Verify signature — payload must be raw bytes but we accept dict here
        # The actual verification happens in the FastAPI route before calling this
        if not signature:
            return WebhookResponse(status_code=401, body={"error": "Missing signature"})

        # Parse event
        event = parse_event(event_type, payload)

        # Route
        if isinstance(event, (PROpenEvent, PRSyncEvent)):
            if self.auto_review_handler is not None:
                self.auto_review_handler(event)
            return WebhookResponse(
                status_code=200,
                body={"message": "Review triggered"},
            )

        if isinstance(event, IssueCommentEvent):
            if self.command_handler is not None:
                self.command_handler(event)
            return WebhookResponse(status_code=200, body={"message": "Command processed"})

        # Other events — acknowledged but not processed
        event_type_str = event.event_type if event else "unknown"
        logger.debug("unhandled_event_type", event_type=event_type_str)
        return WebhookResponse(status_code=200, body={"message": "Event ignored"})
