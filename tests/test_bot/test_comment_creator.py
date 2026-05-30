from __future__ import annotations

from typing import Optional

from app.bot.comment_creator import CommentCreator
from app.engine.schemas import (
    AnalysisResult,
    AnalysisStats,
    DiffHunk,
    DiffLine,
    EngineFinding,
    Phase1Result,
)


def _make_finding(
    severity: str = "warning",
    file_path: str = "src/main.py",
    line_start: int = 10,
    line_end: int = 10,
    title: str = "Test issue",
    description: str = "Test description",
    suggestion: str = "",
) -> EngineFinding:
    return EngineFinding(
        rule_id="TEST-001",
        severity=severity,
        category="security",
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        title=title,
        description=description,
        suggestion=suggestion,
        confidence=0.8,
    )


def _make_hunk(
    new_start: int = 1,
    new_count: int = 20,
    old_start: int = 1,
    old_count: int = 20,
    lines: Optional[list[DiffLine]] = None,
) -> DiffHunk:
    if lines is None:
        lines = [
            DiffLine(kind=" ", content=f"line {i}", old_line=i, new_line=i)
            for i in range(new_start, new_start + new_count)
        ]
    return DiffHunk(
        header=f"@@ -{old_start},{old_count} +{new_start},{new_count} @@",
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        lines=lines,
    )


def _make_result(
    findings: Optional[list[EngineFinding]] = None,
    summary: str = "Test summary",
) -> AnalysisResult:
    if findings is None:
        findings = []
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1
    return AnalysisResult(
        pr_url="https://github.com/test/repo/pull/1",
        findings=findings,
        phase1=Phase1Result(
            summary=summary,
            risk_level="medium",
            key_changes=["Change 1"],
            analysis_directions=["security"],
        ),
        stats=AnalysisStats(
            total_findings=len(findings),
            by_severity=by_severity,
            by_category=by_category,
        ),
    )


class TestBuildLineComment:
    def test_line_comment_with_suggestion(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(
            severity="warning",
            file_path="src/main.py",
            line_start=5,
            suggestion="use const",
        )
        hunk = _make_hunk(new_start=1, new_count=10)
        result = cc.build_line_comment(finding, [hunk])
        assert result is not None
        assert result.path == "src/main.py"
        assert result.position > 0
        assert "🟠" in result.body
        assert "**Warning**" in result.body
        assert "Test issue" in result.body
        assert "Test description" in result.body
        assert "```suggestion" in result.body
        assert "use const" in result.body

    def test_line_comment_without_suggestion(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(suggestion="")
        hunk = _make_hunk(new_start=1, new_count=10)
        result = cc.build_line_comment(finding, [hunk])
        assert result is not None
        assert "```suggestion" not in result.body

    def test_critical_emoji(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(severity="critical")
        hunk = _make_hunk(new_start=1, new_count=10)
        result = cc.build_line_comment(finding, [hunk])
        assert result is not None
        assert "🔴" in result.body
        assert "**Critical**" in result.body

    def test_warning_emoji(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(severity="warning")
        hunk = _make_hunk(new_start=1, new_count=10)
        result = cc.build_line_comment(finding, [hunk])
        assert result is not None
        assert "🟠" in result.body
        assert "**Warning**" in result.body

    def test_suggestion_emoji(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(severity="suggestion")
        hunk = _make_hunk(new_start=1, new_count=10)
        result = cc.build_line_comment(finding, [hunk])
        assert result is not None
        assert "⚪" in result.body
        assert "**Suggestion**" in result.body

    def test_line_not_in_hunk_returns_none(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(line_start=100, line_end=100)
        hunk = _make_hunk(new_start=1, new_count=20)
        result = cc.build_line_comment(finding, [hunk])
        assert result is None

    def test_empty_hunks_returns_none(self) -> None:
        cc = CommentCreator()
        finding = _make_finding()
        result = cc.build_line_comment(finding, [])
        assert result is None

    def test_line_in_middle_hunk(self) -> None:
        cc = CommentCreator()
        finding = _make_finding(file_path="a.py", line_start=35, line_end=35)
        hunk1 = _make_hunk(new_start=1, new_count=20)
        hunk2 = _make_hunk(new_start=30, new_count=20)
        hunks = [hunk1, hunk2]
        result = cc.build_line_comment(finding, hunks)
        assert result is not None
        assert result.path == "a.py"


class TestBuildSummaryComment:
    def test_summary_with_findings(self) -> None:
        cc = CommentCreator()
        findings = [
            _make_finding(severity="critical", file_path="a.py"),
            _make_finding(severity="warning", file_path="a.py"),
            _make_finding(severity="suggestion", file_path="b.py"),
        ]
        result = _make_result(findings)
        summary = cc.build_summary_comment(result, "https://github.com/test/repo/pull/1")
        assert "🤖 AI Review 总结" in summary
        assert "Test summary" in summary
        assert "### 问题统计" in summary
        assert "🔴" in summary
        assert "🟠" in summary
        assert "⚪" in summary
        assert "Critical" in summary
        assert "| 1 |" in summary
        assert "高风险文件" in summary
        assert "a.py" in summary
        assert "b.py" in summary
        assert "Dashboard" in summary

    def test_summary_empty_findings(self) -> None:
        cc = CommentCreator()
        result = _make_result([], summary="No issues found")
        summary = cc.build_summary_comment(result, "https://example.com/pr/1")
        assert "No issues found" in summary
        assert "| 0 |" in summary
        assert "高风险文件" not in summary

    def test_summary_no_phase1(self) -> None:
        cc = CommentCreator()
        result = AnalysisResult(
            pr_url="https://example.com/pr/1",
            findings=[],
            phase1=None,
            stats=AnalysisStats(),
        )
        summary = cc.build_summary_comment(result, "https://example.com/pr/1")
        assert "🤖 AI Review 总结" in summary
        assert "### 问题统计" in summary

    def test_summary_file_sorting(self) -> None:
        """High-risk files should be sorted by issue count descending."""
        cc = CommentCreator()
        findings = [
            _make_finding(file_path="low.py"),
            _make_finding(file_path="high.py"),
            _make_finding(file_path="high.py"),
            _make_finding(file_path="high.py"),
        ]
        result = _make_result(findings)
        summary = cc.build_summary_comment(result, "https://x.com/pr/1")
        high_pos = summary.index("high.py")
        low_pos = summary.index("low.py")
        assert high_pos < low_pos


class TestDiffPosition:
    def test_simple_line_mapping(self) -> None:
        """Line 5 in a hunk starting at new_start=1 should map correctly."""
        hunk = _make_hunk(new_start=1, new_count=10)
        pos = CommentCreator._find_diff_position(5, 5, [hunk])
        assert pos is not None
        # position = 1 (header) + line_index_in_hunk (4) + 1
        assert pos == 6

    def test_added_lines_accounted(self) -> None:
        """Lines with kind '+' count as new lines, '-' do not."""
        hunk = DiffHunk(
            header="@@ -1,3 +1,5 @@",
            old_start=1,
            old_count=3,
            new_start=1,
            new_count=5,
            lines=[
                DiffLine(kind=" ", content="keep", old_line=1, new_line=1),
                DiffLine(kind="-", content="removed", old_line=2, new_line=None),
                DiffLine(kind="+", content="added1", old_line=None, new_line=2),
                DiffLine(kind="+", content="added2", old_line=None, new_line=3),
                DiffLine(kind=" ", content="keep", old_line=3, new_line=4),
                DiffLine(kind="+", content="added3", old_line=None, new_line=5),
            ],
        )
        # new line 3: header(1) + skip lines[0..2] + 1 = 5
        # lines[0]=" " new=1, lines[1]="-" skip, lines[2]="+" new=2, lines[3]="+" new=3
        pos = CommentCreator._find_diff_position(3, 3, [hunk])
        assert pos is not None
        assert pos == 5

    def test_multi_hunk_position(self) -> None:
        hunk1 = _make_hunk(new_start=1, new_count=5)
        hunk2 = _make_hunk(new_start=10, new_count=5)
        pos = CommentCreator._find_diff_position(12, 12, [hunk1, hunk2])
        assert pos is not None
        # hunk1: header(1) + 5 lines = 6
        # hunk2: header(1) + skip to new line 12 (3rd new line, 0-indexed 2)
        # position = 6 + 1 + 2 + 1 = 10
        assert pos == 10

    def test_line_range_matches(self) -> None:
        """A multi-line issue (line_start != line_end) should find its start line."""
        hunk = _make_hunk(new_start=1, new_count=20)
        pos = CommentCreator._find_diff_position(8, 12, [hunk])
        assert pos is not None
        # first new line >= 8 is at index 7 (new line 8)
        assert pos == 1 + 7 + 1

    def test_line_outside_all_hunks(self) -> None:
        hunk1 = _make_hunk(new_start=1, new_count=10)
        hunk2 = _make_hunk(new_start=50, new_count=10)
        pos = CommentCreator._find_diff_position(30, 30, [hunk1, hunk2])
        assert pos is None
