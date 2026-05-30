from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from app.core.exceptions import (
    AIProviderError,
    GitHubAPIError,
    PRTooLargeError,
)
from app.core.logging import get_logger
from app.github.schemas import (
    BaseWebhookEvent,
    PRDetail,
    PROpenEvent,
    PRSyncEvent,
)
from app.engine.schemas import AnalysisResult
from app.models.repo_config import RepoConfig
from app.models.review_record import ReviewRecord, ReviewStatus

logger = get_logger(__name__)

# Maximum diff size before PR is considered too large (bytes)
_MAX_DIFF_BYTES = 500_000


class AutoReviewHandler:
    """Handle automatic PR review triggered by webhook events.

    Flow:
    1. Check repo auto_review config
    2. Create ReviewRecord (pending)
    3. Fetch PR detail + diff via GitHubClient
    4. Run AnalysisOrchestrator
    5. Format comments via CommentCreator
    6. Submit review via GitHubClient
    7. Update ReviewRecord (completed)
    """

    def __init__(
        self,
        github_client_factory: Callable[[int], Any],
        orchestrator: Any,  # Duck-typed: must have .analyze(pr_data) -> AnalysisResult
        comment_creator: Optional[Callable[[AnalysisResult, PRDetail], str]] = None,
        db_session_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._client_factory = github_client_factory
        self._orchestrator = orchestrator
        self._comment_creator = comment_creator
        self._db_factory = db_session_factory

    def handle(self, event: BaseWebhookEvent) -> Optional[AnalysisResult]:
        """Run the full auto-review pipeline. Returns None on early exit."""
        if not isinstance(event, (PROpenEvent, PRSyncEvent)):
            return None

        owner = event.owner
        repo = event.repo
        pr_number = event.pr_number

        try:
            return self._execute_review(owner, repo, pr_number, event)
        except PRTooLargeError as exc:
            logger.warning("pr_too_large", owner=owner, repo=repo, pr=pr_number)
            self._notify_pr_too_large(owner, repo, pr_number, str(exc))
            return None
        except AIProviderError as exc:
            logger.error("ai_provider_error", error=str(exc))
            self._notify_ai_error(owner, repo, pr_number)
            return None
        except GitHubAPIError as exc:
            logger.error("github_api_error", error=str(exc))
            return None
        except Exception as exc:
            logger.error("auto_review_unexpected_error", error=str(exc))
            return None

    def _execute_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        event: BaseWebhookEvent,
    ) -> Optional[AnalysisResult]:
        """Core review execution with happy-path logic."""
        installation_id = self._extract_installation_id(event)

        # Check auto_review config
        if not self._is_auto_review_enabled(owner, repo):
            logger.info("auto_review_disabled", owner=owner, repo=repo)
            return None

        # Create pending review record
        review_record = self._create_review_record(
            pr_number=pr_number,
            status=ReviewStatus.PENDING,
            triggered_by=getattr(event, "sender", "webhook"),
        )

        # Fetch PR data
        client = self._client_factory(installation_id)
        pr_detail: PRDetail = client.get_pr(owner, repo, pr_number)
        pr_files = client.get_pr_files(owner, repo, pr_number)

        # Build diff text from file patches
        diff_text = self._build_diff_text(pr_files)

        # Check PR size
        if len(diff_text.encode("utf-8")) > _MAX_DIFF_BYTES:
            raise PRTooLargeError(
                f"PR diff exceeds {_MAX_DIFF_BYTES} bytes"
            )

        # Build pr_detail dict for orchestrator
        pr_data: dict[str, Any] = {
            "pr_title": pr_detail.title,
            "pr_description": pr_detail.body or "",
            "pr_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
            "diff_text": diff_text,
            "changed_files": [f.filename for f in pr_files],
        }

        # Run analysis
        result: AnalysisResult = self._orchestrator.analyze(pr_data)

        # Submit review
        if self._comment_creator is not None:
            summary = self._comment_creator(result, pr_detail)
            client.create_review(
                owner=owner,
                repo=repo,
                pr_number=pr_number,
                commit_id=pr_detail.head_sha,
                body=summary,
                comments=[],  # Line comments built separately
            )

        # Update review record
        self._update_review_record(
            review_record,
            status=ReviewStatus.COMPLETED,
            result=result,
        )

        return result

    def _extract_installation_id(self, event: BaseWebhookEvent) -> int:
        payload: dict[str, Any] = getattr(event, "raw_payload", {})
        installation: dict[str, Any] = payload.get("installation", {}) or {}
        install_id: int = installation.get("id", 0)
        return install_id

    def _is_auto_review_enabled(self, owner: str, repo: str) -> bool:
        """Check if auto_review is enabled for the repository."""
        if self._db_factory is None:
            return True  # Default when no DB configured
        try:
            db = self._db_factory()
            try:
                repo_config = (
                    db.query(RepoConfig).join(RepoConfig.repository).filter(
                        RepoConfig.repository.has(full_name=f"{owner}/{repo}")
                    ).first()
                )
                if repo_config is None:
                    return True  # Default enabled
                val: bool = repo_config.auto_review
                return val
            finally:
                db.close()
        except Exception:
            return True  # Default to enabled on DB error

    def _create_review_record(
        self,
        pr_number: int,
        status: ReviewStatus,
        triggered_by: str = "webhook",
    ) -> Optional[ReviewRecord]:
        if self._db_factory is None:
            return None
        try:
            db = self._db_factory()
            try:
                record = ReviewRecord(
                    status=status,
                    triggered_by=triggered_by,
                    started_at=datetime.utcnow(),
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                return record
            finally:
                db.close()
        except Exception:
            return None

    def _update_review_record(
        self,
        record: Optional[ReviewRecord],
        status: ReviewStatus,
        result: Optional[AnalysisResult] = None,
    ) -> None:
        if record is None or self._db_factory is None:
            return
        try:
            db = self._db_factory()
            try:
                record = db.merge(record)
                record.status = status
                record.completed_at = datetime.utcnow()
                if result is not None:
                    record.summary = result.phase1.summary if result.phase1 else ""
                    record.total_issues = result.stats.total_findings
                    record.critical_count = result.stats.by_severity.get("critical", 0)
                    record.warning_count = result.stats.by_severity.get("warning", 0)
                    record.suggestion_count = result.stats.by_severity.get("suggestion", 0)
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

    @staticmethod
    def _build_diff_text(pr_files: list[Any]) -> str:
        """Build unified diff text from file change list."""
        parts: list[str] = []
        for f in pr_files:
            if f.patch:
                parts.append(f"diff --git a/{f.filename} b/{f.filename}")
                parts.append(f"--- a/{f.filename}")
                parts.append(f"+++ b/{f.filename}")
                parts.append(f.patch)
        return "\n".join(parts)

    def _notify_pr_too_large(
        self, owner: str, repo: str, pr_number: int, message: str
    ) -> None:
        """Post a comment about PR being too large."""
        try:
            client = self._client_factory(0)
            client.create_issue_comment(
                owner, repo, pr_number,
                f":warning: **PR too large for automatic review**\n\n{message}",
            )
        except Exception:
            pass

    def _notify_ai_error(
        self, owner: str, repo: str, pr_number: int
    ) -> None:
        """Post a comment about AI service degradation."""
        try:
            client = self._client_factory(0)
            client.create_issue_comment(
                owner, repo, pr_number,
                ":warning: **AI analysis service is currently degraded.** "
                "Your PR will be reviewed when the service recovers.",
            )
        except Exception:
            pass
