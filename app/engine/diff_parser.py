from __future__ import annotations

import re
from typing import Optional

from app.engine.schemas import DiffHunk, DiffLine, ParsedDiff

_HUNK_HEADER_RE = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$"
)


class DiffParser:
    """Parse a unified diff into a structured ParsedDiff."""

    def parse(self, diff_text: str) -> ParsedDiff:
        if not diff_text.strip():
            return ParsedDiff()

        files: dict[str, list[DiffHunk]] = {}
        stats: dict[str, tuple[int, int]] = {}
        current_file: Optional[str] = None
        current_hunk: Optional[DiffHunk] = None
        added_count = 0
        removed_count = 0

        for line in diff_text.splitlines():
            # File header: diff --git a/... b/...
            if line.startswith("diff --git "):
                if current_file is not None and current_hunk is not None:
                    self._finish_hunk(files, current_file, current_hunk)
                current_file = self._extract_filename(line)
                current_hunk = None
                added_count = 0
                removed_count = 0
                continue

            # Skip --- and +++ lines, but track file
            if line.startswith("--- ") or line.startswith("+++ "):
                continue

            # Hunk header: @@ -old_start,old_count +new_start,new_count @@
            m = _HUNK_HEADER_RE.match(line)
            if m:
                if current_file is not None and current_hunk is not None:
                    self._finish_hunk(files, current_file, current_hunk)
                old_start = int(m.group(1))
                old_count = int(m.group(2)) if m.group(2) else 1
                new_start = int(m.group(3))
                new_count = int(m.group(4)) if m.group(4) else 1
                current_hunk = DiffHunk(
                    header=line,
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                )
                continue

            # Content lines within a hunk
            if current_hunk is not None and current_file is not None and line:
                kind = line[0]
                if kind in (" ", "+", "-"):
                    dl = DiffLine(kind=kind, content=line[1:])
                    if kind == " ":
                        current_hunk.old_count = max(
                            current_hunk.old_count,
                            (current_hunk.old_start + len([dl for dl in current_hunk.lines if dl.kind != "+"])),
                        )
                    elif kind == "+":
                        added_count += 1
                        dl.new_line = current_hunk.new_start + added_count - 1
                    elif kind == "-":
                        removed_count += 1
                        dl.old_line = current_hunk.old_start + removed_count - 1
                    current_hunk.lines.append(dl)

        # Finish last hunk
        if current_file is not None and current_hunk is not None:
            self._finish_hunk(files, current_file, current_hunk)

        # Compute stats
        for fname, hunks in files.items():
            added = sum(1 for h in hunks for dl in h.lines if dl.kind == "+")
            removed = sum(1 for h in hunks for dl in h.lines if dl.kind == "-")
            stats[fname] = (added, removed)

        return ParsedDiff(files=files, stats=stats)

    @staticmethod
    def _extract_filename(diff_git_line: str) -> str:
        # "diff --git a/path/to/file.py b/path/to/file.py"
        parts = diff_git_line.split()
        if len(parts) >= 4:
            b_path = parts[3]
            if b_path.startswith("b/"):
                return b_path[2:]
            return b_path
        return ""

    @staticmethod
    def _finish_hunk(
        files: dict[str, list[DiffHunk]],
        filename: str,
        hunk: DiffHunk,
    ) -> None:
        if filename not in files:
            files[filename] = []
        files[filename].append(hunk)

    @staticmethod
    def group_by_file(parsed: ParsedDiff) -> dict[str, list[DiffHunk]]:
        """Return a copy of the file-to-hunks mapping."""
        return dict(parsed.files)

    @staticmethod
    def extract_changed_lines(hunk: DiffHunk) -> list[tuple[int, str]]:
        """Extract added/removed lines with their new line numbers."""
        result: list[tuple[int, str]] = []
        for dl in hunk.lines:
            if dl.kind == "+" and dl.new_line is not None:
                result.append((dl.new_line, dl.content))
        return result
