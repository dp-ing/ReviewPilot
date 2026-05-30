from __future__ import annotations

from dataclasses import dataclass, field

from app.models.review_issue import ReviewIssue
from app.models.review_record import ReviewRecord


@dataclass
class FileIssueGroup:
    """Issues grouped by file path for enhanced view."""

    file_path: str
    issues: list[ReviewIssue] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0
    suggestion_count: int = 0


@dataclass
class EnhancedViewData:
    """Data for the enhanced review detail view."""

    record: ReviewRecord
    file_groups: list[FileIssueGroup] = field(default_factory=list)
    total_critical: int = 0
    total_warning: int = 0
    total_suggestion: int = 0


class EnhancedViewBuilder:
    """Build data for enhanced PR review detail page."""

    def build(
        self,
        record: ReviewRecord,
        issues: list[ReviewIssue],
    ) -> EnhancedViewData:
        """Group issues by file and compute per-file stats."""
        groups: dict[str, FileIssueGroup] = {}
        data = EnhancedViewData(record=record)

        for issue in issues:
            if issue.file_path not in groups:
                groups[issue.file_path] = FileIssueGroup(
                    file_path=issue.file_path
                )
            groups[issue.file_path].issues.append(issue)

            if issue.severity == "critical":
                groups[issue.file_path].critical_count += 1
                data.total_critical += 1
            elif issue.severity == "warning":
                groups[issue.file_path].warning_count += 1
                data.total_warning += 1
            else:
                groups[issue.file_path].suggestion_count += 1
                data.total_suggestion += 1

        # Sort: most critical issues first
        data.file_groups = sorted(
            groups.values(),
            key=lambda g: (-g.critical_count, -g.warning_count),
        )
        return data
