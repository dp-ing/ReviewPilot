from __future__ import annotations

from typing import Any, Optional

from app.bot.command_handler import CommandHandler
from app.github.schemas import IssueCommentEvent


def _make_comment_event(body: str, sender: str = "user") -> IssueCommentEvent:
    return IssueCommentEvent(
        event_type="issue_comment",
        raw_payload={},
        owner="test",
        repo="repo",
        pr_number=1,
        comment_body=body,
        comment_id=100,
        sender=sender,
    )


class TestCommandParsing:
    def test_review_alone_triggers_full_analysis(self) -> None:
        captured: list[Optional[list[str]]] = []

        def handler(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            captured.append(focus)

        ch = CommandHandler(on_review_command=handler)
        event = _make_comment_event("/review")
        result = ch.handle(event)
        assert result is True
        assert captured == [None]

    def test_review_with_focus_security(self) -> None:
        captured: list[Optional[list[str]]] = []

        def handler(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            captured.append(focus)

        ch = CommandHandler(on_review_command=handler)
        event = _make_comment_event("/review focus:security")
        result = ch.handle(event)
        assert result is True
        assert captured == [["security"]]

    def test_review_with_focus_multi(self) -> None:
        captured: list[Optional[list[str]]] = []

        def handler(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            captured.append(focus)

        ch = CommandHandler(on_review_command=handler)
        event = _make_comment_event("/review focus:security,logic")
        result = ch.handle(event)
        assert result is True
        assert captured == [["security", "logic"]]

    def test_review_case_insensitive(self) -> None:
        captured: list[Optional[list[str]]] = []

        def handler(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            captured.append(focus)

        ch = CommandHandler(on_review_command=handler)
        event = _make_comment_event("/REVIEW")
        result = ch.handle(event)
        assert result is True

    def test_plain_comment_is_ignored(self) -> None:
        ch = CommandHandler()
        event = _make_comment_event("looks good")
        result = ch.handle(event)
        assert result is False

    def test_partial_match_is_ignored(self) -> None:
        ch = CommandHandler()
        event = _make_comment_event("please /review this PR")
        result = ch.handle(event)
        assert result is False

    def test_focus_with_invalid_category_ignored(self) -> None:
        captured: list[Optional[list[str]]] = []

        def handler(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            captured.append(focus)

        ch = CommandHandler(on_review_command=handler)
        event = _make_comment_event("/review focus:unknown")
        result = ch.handle(event)
        assert result is True
        # Invalid category → focus is None (default to all)
        assert captured == [None]


class TestPermissionCheck:
    def test_collaborator_accepted(self) -> None:
        reviews: list[Any] = []

        def check_collab(owner: str, repo: str, user: str) -> bool:
            return True

        def on_review(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            reviews.append((owner, repo, pr))

        ch = CommandHandler(
            collaborator_checker=check_collab,
            on_review_command=on_review,
        )
        event = _make_comment_event("/review", sender="collaborator")
        result = ch.handle(event)
        assert result is True
        assert len(reviews) == 1

    def test_non_collaborator_rejected(self) -> None:
        reviews: list[Any] = []
        denied: list[Any] = []

        def check_collab(owner: str, repo: str, user: str) -> bool:
            return False

        def on_review(owner: str, repo: str, pr: int, focus: Optional[list[str]]) -> None:
            reviews.append((owner, repo, pr))

        def on_denied(owner: str, repo: str, pr: int) -> None:
            denied.append((owner, repo, pr))

        ch = CommandHandler(
            collaborator_checker=check_collab,
            on_review_command=on_review,
            on_permission_denied=on_denied,
        )
        event = _make_comment_event("/review", sender="outsider")
        result = ch.handle(event)
        assert result is True  # Command matched
        assert len(reviews) == 0  # But review NOT triggered
        assert len(denied) == 1  # Permission denied callback called
