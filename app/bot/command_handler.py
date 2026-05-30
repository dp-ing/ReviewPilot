from __future__ import annotations

import re
from typing import Callable, Optional

from app.core.logging import get_logger
from app.github.schemas import IssueCommentEvent

logger = get_logger(__name__)

_COMMAND_RE = re.compile(r"^/review(?:\s+focus:(?P<focus>[a-z_,]+))?\s*$", re.IGNORECASE)

_ALL_CATEGORIES = {"security", "logic", "performance", "style"}


class CommandHandler:
    """Handle the /review slash command in PR issue comments.

    Supported formats:
    - /review → full analysis (all categories)
    - /review focus:security → security only
    - /review focus:security,logic → security + logic
    """

    def __init__(
        self,
        collaborator_checker: Optional[Callable[[str, str, str], bool]] = None,
        on_review_command: Optional[Callable[[str, str, int, Optional[list[str]]], None]] = None,
        on_permission_denied: Optional[Callable[[str, str, int], None]] = None,
    ) -> None:
        self._collaborator_checker = collaborator_checker
        self._on_review_command = on_review_command
        self._on_permission_denied = on_permission_denied

    def handle(self, event: IssueCommentEvent) -> bool:
        """Process an issue_comment event. Returns True if command was handled."""
        if not isinstance(event, IssueCommentEvent):
            return False

        body = event.comment_body.strip() if event.comment_body else ""

        m = _COMMAND_RE.match(body)
        if not m:
            return False

        logger.info(
            "review_command_received",
            owner=event.owner,
            repo=event.repo,
            pr=event.pr_number,
            sender=event.sender,
        )

        # Parse focus categories
        focus_str = m.group("focus")
        categories: Optional[list[str]] = None
        if focus_str:
            categories = [
                c.strip() for c in focus_str.split(",") if c.strip() in _ALL_CATEGORIES
            ]
            if not categories:
                categories = None

        # Permission check
        if self._collaborator_checker is not None:
            if not self._collaborator_checker(
                event.owner, event.repo, event.sender
            ):
                logger.warning(
                    "permission_denied",
                    sender=event.sender,
                    owner=event.owner,
                    repo=event.repo,
                )
                if self._on_permission_denied is not None:
                    self._on_permission_denied(event.owner, event.repo, event.pr_number)
                return True  # Command matched, but denied

        # Execute review
        if self._on_review_command is not None:
            self._on_review_command(
                event.owner, event.repo, event.pr_number, categories
            )

        return True
