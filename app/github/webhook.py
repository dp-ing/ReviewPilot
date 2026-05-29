from __future__ import annotations

import hmac
import hashlib
from typing import Any

from app.core.config import get_config
from app.core.exceptions import WebhookVerifyError
from app.github.schemas import (
    PROpenEvent,
    PRSyncEvent,
    IssueCommentEvent,
    InstallationEvent,
    UnknownEvent,
    BaseWebhookEvent,
)


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    secret = get_config().GITHUB_WEBHOOK_SECRET
    if not secret:
        raise WebhookVerifyError("GITHUB_WEBHOOK_SECRET is not configured")

    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def _extract_pr_from_payload(payload: dict[str, Any]) -> tuple[str, str, int]:
    repo_info: dict[str, Any] = payload.get("repository", {})
    owner: str = repo_info.get("owner", {}).get("login", "")
    repo: str = repo_info.get("name", "")
    pr_info: dict[str, Any] = payload.get("pull_request", {})
    pr_number: int = pr_info.get("number", 0) or payload.get("number", 0)
    return owner, repo, pr_number


def _extract_pr_from_issue_comment(payload: dict[str, Any]) -> tuple[str, str, int]:
    repo_info: dict[str, Any] = payload.get("repository", {})
    owner: str = repo_info.get("owner", {}).get("login", "")
    repo: str = repo_info.get("name", "")
    issue: dict[str, Any] = payload.get("issue", {}) or {}
    pr_url: str = issue.get("pull_request", {}).get("url", "") if issue else ""
    pr_number_str = pr_url.rstrip("/").rsplit("/", 1)[-1] if pr_url else "0"
    try:
        pr_number = int(pr_number_str)
    except (ValueError, TypeError):
        pr_number = 0
    return owner, repo, pr_number


def parse_event(event_type: str, payload: dict[str, Any]) -> BaseWebhookEvent:
    action: str = payload.get("action", "")

    if event_type == "ping":
        return UnknownEvent(event_type=event_type, raw_payload=payload)

    if event_type == "pull_request":
        owner, repo, pr_number = _extract_pr_from_payload(payload)
        sender: str = payload.get("sender", {}).get("login", "")

        if action in ("opened", "reopened"):
            return PROpenEvent(
                event_type=event_type,
                raw_payload=payload,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                action=action,
                sender=sender,
            )
        elif action == "synchronize":
            return PRSyncEvent(
                event_type=event_type,
                raw_payload=payload,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                action=action,
                sender=sender,
            )

    if event_type == "issue_comment":
        owner, repo, pr_number = _extract_pr_from_issue_comment(payload)
        comment: dict[str, Any] = payload.get("comment", {}) or {}
        return IssueCommentEvent(
            event_type=event_type,
            raw_payload=payload,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            comment_body=comment.get("body", ""),
            comment_id=comment.get("id", 0),
            sender=payload.get("sender", {}).get("login", ""),
        )

    if event_type in ("installation", "installation_repositories"):
        installations: dict[str, Any] = payload.get("installation", {}) or {}
        return InstallationEvent(
            event_type=event_type,
            raw_payload=payload,
            action=action,
            installation_id=installations.get("id", 0),
            sender=payload.get("sender", {}).get("login", ""),
        )

    return UnknownEvent(event_type=event_type, raw_payload=payload)


def extract_pr_identifiers(event: BaseWebhookEvent) -> tuple[str, str, int]:
    return (event.owner, event.repo, event.pr_number)
