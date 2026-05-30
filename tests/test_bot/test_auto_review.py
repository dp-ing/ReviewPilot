from __future__ import annotations

from typing import Any, Optional
from unittest.mock import patch

from app.bot.auto_review import AutoReviewHandler
from app.core.exceptions import PRTooLargeError
from app.core.exceptions import AIProviderError
from app.engine.schemas import AnalysisResult, AnalysisStats, Phase1Result
from app.github.schemas import PRDetail, PROpenEvent, PRSyncEvent


class _MockGitHubClient:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.reviews: list[dict[str, Any]] = []
        self.comments: list[dict[str, Any]] = []
        self.last_pr_detail: Optional[PRDetail] = None

    def get_pr(self, owner: str, repo: str, pr_number: int) -> PRDetail:
        if self.should_fail:
            raise AIProviderError("mock failure")
        detail = PRDetail(
            pr_id=1,
            number=pr_number,
            title="Test PR",
            body="Test body",
            author="user",
            head_sha="abc123",
            base_sha="def456",
            head_branch="feat",
            base_branch="main",
        )
        self.last_pr_detail = detail
        return detail

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[Any]:
        return [
            _MockFileChange("main.py", "modified", "patch data"),
            _MockFileChange("lib.py", "modified", "lib patch"),
        ]

    def create_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_id: str,
        body: str,
        comments: list[dict[str, Any]],
    ) -> int:
        self.reviews.append({"body": body, "comments": comments})
        return 1

    def create_issue_comment(
        self, owner: str, repo: str, pr_number: int, body: str
    ) -> int:
        self.comments.append({"body": body})
        return 1


class _MockFileChange:
    def __init__(self, filename: str, status: str, patch: str) -> None:
        self.filename = filename
        self.status = status
        self.patch = patch
        self.additions = 1
        self.deletions = 1
        self.changes = 2


def _make_mock_result() -> AnalysisResult:
    return AnalysisResult(
        pr_url="https://github.com/test/repo/pull/1",
        phase1=Phase1Result(
            summary="Test summary",
            risk_level="low",
            key_changes=["Change 1"],
            analysis_directions=["security", "style"],
        ),
        stats=AnalysisStats(
            total_findings=3,
            by_severity={"critical": 1, "warning": 1, "suggestion": 1},
            by_category={"security": 1, "style": 2},
            token_usage={"phase1": 100, "security": 200},
            duration_ms=500,
        ),
    )


class _MockOrchestrator:
    def analyze(self, *args: Any, **kwargs: Any) -> AnalysisResult:
        return _make_mock_result()

    def _mock_init(self, *args: Any, **kwargs: Any) -> None:
        pass


class _MockSession:
    def __init__(self) -> None:
        self._objects: list[Any] = []
        self.committed = False
        self.closed = False

    def add(self, obj: Any) -> None:
        self._objects.append(obj)

    def commit(self) -> None:
        self.committed = True

    def close(self) -> None:
        self.closed = True

    def merge(self, obj: Any) -> Any:
        return obj

    def query(self, *args: Any, **kwargs: Any) -> "_MockQuery":
        return _MockQuery()

    def refresh(self, obj: Any) -> None:
        pass


class _MockQuery:
    def join(self, *args: Any, **kwargs: Any) -> "_MockQuery":
        return self

    def filter(self, *args: Any, **kwargs: Any) -> "_MockQuery":
        return self

    def first(self) -> Any:
        return _MockRepoConfig()


class _MockRepoConfig:
    auto_review: bool = True


def _make_pr_open_event() -> PROpenEvent:
    return PROpenEvent(
        event_type="pull_request",
        raw_payload={
            "action": "opened",
            "installation": {"id": 42},
        },
        owner="test",
        repo="repo",
        pr_number=1,
        action="opened",
        sender="user",
    )


class TestAutoReviewHandler:
    def test_happy_path_completes_review(self) -> None:
        client = _MockGitHubClient()

        def client_factory(installation_id: int) -> _MockGitHubClient:
            return client

        def comment_creator(result: Any, pr_detail: Any) -> str:
            return "## Review Summary"

        orchestrator = _MockOrchestrator()
        def db_factory() -> _MockSession:
            return _MockSession()

        handler = AutoReviewHandler(
            github_client_factory=client_factory,
            orchestrator=orchestrator,
            comment_creator=comment_creator,
            db_session_factory=db_factory,
        )

        result = handler.handle(_make_pr_open_event())
        assert result is not None
        assert result.stats.total_findings == 3
        assert len(client.reviews) == 1
        assert "## Review Summary" in client.reviews[0]["body"]

    def test_pr_sync_triggers_review(self) -> None:
        client = _MockGitHubClient()
        orchestrator = _MockOrchestrator()

        handler = AutoReviewHandler(
            github_client_factory=lambda i: client,
            orchestrator=orchestrator,
        )
        event = PRSyncEvent(
            event_type="pull_request",
            raw_payload={"action": "synchronize", "installation": {"id": 42}},
            owner="test",
            repo="repo",
            pr_number=2,
            action="synchronize",
            sender="user",
        )
        result = handler.handle(event)
        assert result is not None

    def test_non_pr_event_skipped(self) -> None:
        from app.github.schemas import IssueCommentEvent

        client = _MockGitHubClient()
        orchestrator = _MockOrchestrator()

        handler = AutoReviewHandler(
            github_client_factory=lambda i: client,
            orchestrator=orchestrator,
        )
        event = IssueCommentEvent(
            event_type="issue_comment",
            raw_payload={},
            owner="test",
            repo="repo",
            pr_number=1,
        )
        result = handler.handle(event)
        assert result is None

    def test_pr_too_large_posts_comment(self) -> None:
        client = _MockGitHubClient()
        orchestrator = _MockOrchestrator()

        handler = AutoReviewHandler(
            github_client_factory=lambda i: client,
            orchestrator=orchestrator,
        )

        with patch.object(
            AutoReviewHandler, "_execute_review",
            side_effect=PRTooLargeError("too large"),
        ):
            result = handler.handle(_make_pr_open_event())

        assert result is None
        # Verify a comment was posted
        assert len(client.comments) == 1

    def test_ai_error_handled_gracefully(self) -> None:
        client = _MockGitHubClient(should_fail=True)
        orchestrator = _MockOrchestrator()

        handler = AutoReviewHandler(
            github_client_factory=lambda i: client,
            orchestrator=orchestrator,
        )
        result = handler.handle(_make_pr_open_event())
        assert result is None

    def test_build_diff_text(self) -> None:
        files = [
            _MockFileChange("a.py", "modified", "+new\n-old"),
            _MockFileChange("b.py", "added", "+hello"),
        ]
        diff = AutoReviewHandler._build_diff_text(files)
        assert "diff --git a/a.py b/a.py" in diff
        assert "diff --git a/b.py b/b.py" in diff
        assert "+new" in diff
        assert "+hello" in diff

    def test_no_comment_creator_still_runs_analysis(self) -> None:
        client = _MockGitHubClient()
        orchestrator = _MockOrchestrator()

        handler = AutoReviewHandler(
            github_client_factory=lambda i: client,
            orchestrator=orchestrator,
        )
        result = handler.handle(_make_pr_open_event())
        assert result is not None
        # No review created since no comment_creator
        assert len(client.reviews) == 0
