from __future__ import annotations

from app.models.review_issue import ReviewIssue
from app.models.review_record import ReviewRecord, ReviewStatus
from app.web.enhanced_view import EnhancedViewBuilder, EnhancedViewData


def _make_issue(
    file_path: str = "test.py",
    severity: str = "warning",
) -> ReviewIssue:
    return ReviewIssue(
        id=1,
        review_record_id=1,
        file_path=file_path,
        line_start=1,
        line_end=1,
        severity=severity,
        category="security",
        title="Test issue",
        description="Description",
    )


def _make_record() -> ReviewRecord:
    return ReviewRecord(
        id=1,
        pull_request_id=1,
        status=ReviewStatus.COMPLETED,
        total_issues=0,
    )


class TestEnhancedViewBuilder:
    def test_empty_issues(self) -> None:
        builder = EnhancedViewBuilder()
        record = _make_record()
        result = builder.build(record, [])
        assert isinstance(result, EnhancedViewData)
        assert result.file_groups == []
        assert result.total_critical == 0

    def test_groups_by_file(self) -> None:
        builder = EnhancedViewBuilder()
        record = _make_record()
        issues = [
            _make_issue(file_path="a.py", severity="critical"),
            _make_issue(file_path="a.py", severity="warning"),
            _make_issue(file_path="b.py", severity="suggestion"),
        ]
        result = builder.build(record, issues)
        assert len(result.file_groups) == 2
        assert result.total_critical == 1
        assert result.total_warning == 1
        assert result.total_suggestion == 1

    def test_groups_sorted_by_critical_first(self) -> None:
        builder = EnhancedViewBuilder()
        record = _make_record()
        issues = [
            _make_issue(file_path="low.py", severity="suggestion"),
            _make_issue(file_path="high.py", severity="critical"),
        ]
        result = builder.build(record, issues)
        assert result.file_groups[0].file_path == "high.py"
        assert result.file_groups[1].file_path == "low.py"
