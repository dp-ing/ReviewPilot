from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.engine.schemas import AnalysisResult, DiffHunk, EngineFinding

_SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning": "🟠",
    "suggestion": "⚪",
}

_SEVERITY_LABEL = {
    "critical": "Critical",
    "warning": "Warning",
    "suggestion": "Suggestion",
}


@dataclass
class ReviewCommentData:
    """Data for a GitHub Pull Request review comment attached to a diff line."""

    path: str
    position: int  # 1-indexed line position in the file's unified diff
    body: str


class CommentCreator:
    """Create formatted PR review comments from analysis results."""

    def build_line_comment(
        self, issue: EngineFinding, diff_hunks: list[DiffHunk]
    ) -> Optional[ReviewCommentData]:
        """Convert an EngineFinding to a line comment anchored to a diff position.

        Returns None if the issue's line cannot be located in any diff hunk,
        signalling the caller to fall back to a PR conversation comment.
        """
        position = self._find_diff_position(
            issue.line_start, issue.line_end, diff_hunks
        )
        if position is None:
            return None

        emoji = _SEVERITY_EMOJI.get(issue.severity, "")
        label = _SEVERITY_LABEL.get(issue.severity, issue.severity.capitalize())

        parts: list[str] = [
            f"{emoji} **{label}**: {issue.title}",
            "",
            issue.description,
        ]
        if issue.suggestion:
            parts.extend([
                "",
                "**建议修复**:",
                "```suggestion",
                issue.suggestion,
                "```",
            ])

        return ReviewCommentData(
            path=issue.file_path,
            position=position,
            body="\n".join(parts),
        )

    def build_summary_comment(self, result: AnalysisResult, pr_url: str) -> str:
        """Build a markdown summary comment for the PR review."""
        lines: list[str] = [
            "## 🤖 AI Review 总结",
            "",
        ]

        if result.phase1 and result.phase1.summary:
            lines.append(result.phase1.summary)
            lines.append("")

        lines.append("### 问题统计")
        lines.append("| 级别 | 数量 |")
        lines.append("|------|------|")
        for severity in ("critical", "warning", "suggestion"):
            count = result.stats.by_severity.get(severity, 0)
            emoji = _SEVERITY_EMOJI.get(severity, "")
            label = _SEVERITY_LABEL.get(severity, severity.capitalize())
            lines.append(f"| {emoji} {label} | {count} |")

        file_counts: dict[str, int] = {}
        for f in result.findings:
            file_counts[f.file_path] = file_counts.get(f.file_path, 0) + 1

        if file_counts:
            lines.append("")
            lines.append("### 高风险文件")
            for file_path, count in sorted(
                file_counts.items(), key=lambda x: -x[1]
            ):
                lines.append(f"- `{file_path}` ({count} 个问题)")

        lines.append("")
        lines.append("---")
        lines.append(f"> 查看完整分析报告: [Dashboard]({pr_url})")

        return "\n".join(lines)

    @staticmethod
    def _find_diff_position(
        line_start: int, line_end: int, diff_hunks: list[DiffHunk]
    ) -> Optional[int]:
        """Find the 1-indexed diff position for a range of new file lines.

        Walks through hunks accumulating line counts. Returns None when
        the target lines fall outside every hunk (e.g. unchanged code).
        """
        position = 0
        for hunk in diff_hunks:
            # Count the @@ header line
            position += 1

            hunk_new_end = hunk.new_start + hunk.new_count - 1
            if line_end < hunk.new_start or line_start > hunk_new_end:
                position += len(hunk.lines)
                continue

            current_new_line = hunk.new_start
            for i, dl in enumerate(hunk.lines):
                if dl.kind != "-":
                    if line_start <= current_new_line <= line_end:
                        return position + i + 1
                    current_new_line += 1

            position += len(hunk.lines)

        return None
