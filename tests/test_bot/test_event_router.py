from __future__ import annotations

from typing import Any

from app.bot.event_router import EventRouter
from app.github.schemas import (
    BaseWebhookEvent,
    IssueCommentEvent,
    PROpenEvent,
    PRSyncEvent,
)


def _make_pr_open_payload() -> dict[str, Any]:
    return {
        "action": "opened",
        "pull_request": {"number": 1},
        "repository": {"owner": {"login": "test"}, "name": "repo"},
        "sender": {"login": "user"},
    }


def _make_pr_sync_payload() -> dict[str, Any]:
    return {
        "action": "synchronize",
        "pull_request": {"number": 2},
        "repository": {"owner": {"login": "test"}, "name": "repo"},
        "sender": {"login": "user"},
    }


def _make_issue_comment_payload(body: str = "/review") -> dict[str, Any]:
    return {
        "action": "created",
        "issue": {"number": 3, "pull_request": {"url": "https://api.github.com/repos/t/r/pulls/3"}},
        "comment": {"body": body, "id": 100},
        "repository": {"owner": {"login": "test"}, "name": "repo"},
        "sender": {"login": "user"},
    }


class TestEventRouter:
    def test_missing_signature_returns_401(self) -> None:
        router = EventRouter()
        resp = router.handle_webhook("pull_request", _make_pr_open_payload(), "")
        assert resp.status_code == 401

    def test_pr_open_routes_to_auto_review(self) -> None:
        events: list[BaseWebhookEvent] = []

        def handler(event: BaseWebhookEvent) -> None:
            events.append(event)

        router = EventRouter(auto_review_handler=handler)
        resp = router.handle_webhook(
            "pull_request", _make_pr_open_payload(), "sha256=abc"
        )
        assert resp.status_code == 200
        assert len(events) == 1
        assert isinstance(events[0], PROpenEvent)

    def test_pr_sync_routes_to_auto_review(self) -> None:
        events: list[BaseWebhookEvent] = []

        def handler(event: BaseWebhookEvent) -> None:
            events.append(event)

        router = EventRouter(auto_review_handler=handler)
        resp = router.handle_webhook(
            "pull_request", _make_pr_sync_payload(), "sha256=abc"
        )
        assert resp.status_code == 200
        assert len(events) == 1
        assert isinstance(events[0], PRSyncEvent)

    def test_issue_comment_routes_to_command_handler(self) -> None:
        events: list[IssueCommentEvent] = []

        def handler(event: IssueCommentEvent) -> None:
            events.append(event)

        router = EventRouter(command_handler=handler)
        resp = router.handle_webhook(
            "issue_comment", _make_issue_comment_payload(), "sha256=abc"
        )
        assert resp.status_code == 200
        assert len(events) == 1
        assert isinstance(events[0], IssueCommentEvent)
        assert events[0].comment_body == "/review"

    def test_unknown_event_returns_200(self) -> None:
        router = EventRouter()
        resp = router.handle_webhook(
            "ping", {"action": "ping"}, "sha256=abc"
        )
        assert resp.status_code == 200
        assert "ignored" in resp.body.get("message", "").lower()

    def test_auto_review_not_called_when_no_handler(self) -> None:
        router = EventRouter()
        resp = router.handle_webhook(
            "pull_request", _make_pr_open_payload(), "sha256=abc"
        )
        assert resp.status_code == 200

    def test_command_not_called_when_no_handler(self) -> None:
        router = EventRouter()
        resp = router.handle_webhook(
            "issue_comment", _make_issue_comment_payload(), "sha256=abc"
        )
        assert resp.status_code == 200
