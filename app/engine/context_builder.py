from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.engine.diff_parser import DiffParser
from app.engine.schemas import AnalysisContext

# Token budget allocation ratios
_DIFF_RATIO = 0.4
_AST_RATIO = 0.2
_FILES_RATIO = 0.2
_PROJECT_RATIO = 0.1
# Remaining 0.1 is buffer — not pre-allocated

_CHARS_PER_TOKEN = 4


class ContextBuilder:
    """Assemble AnalysisContext from PR metadata with token budget control.

    Priority loading order:
    1. diff (40% budget)
    2. AST structure (20% budget)
    3. full file contents (20% budget)
    4. project deps/config (10% budget)
    """

    def __init__(
        self,
        diff_parser: Optional[DiffParser] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.diff_parser = diff_parser or DiffParser()
        self.project_root = project_root or Path(".")

    def build(self, pr_detail: dict[str, Any], token_budget: int = 4000) -> AnalysisContext:
        """Build an AnalysisContext from PR metadata, respecting token budget."""
        diff_text: str = pr_detail.get("diff_text", "")
        parsed_diff = self.diff_parser.parse(diff_text)

        ast_summary: dict[str, Any] = pr_detail.get("ast_summary", {})

        changed_files: list[str] = pr_detail.get("changed_files", [])
        if not changed_files:
            changed_files = list(parsed_diff.files.keys())

        project_info: dict[str, Any] = pr_detail.get("project_info", {})

        diff_budget = int(token_budget * _DIFF_RATIO)
        ast_budget = int(token_budget * _AST_RATIO)
        files_budget = int(token_budget * _FILES_RATIO)
        project_budget = int(token_budget * _PROJECT_RATIO)

        token_used = 0

        # 1. Diff (already parsed — estimate token cost of the diff text)
        diff_tokens = self._estimate_tokens(diff_text)
        token_used += min(diff_tokens, diff_budget)

        # 2. AST summary — truncate to budget
        ast_text = self._dict_to_text(ast_summary)
        ast_tokens = self._estimate_tokens(ast_text)
        if ast_tokens > ast_budget:
            ast_summary = self._truncate_ast_summary(ast_summary, ast_budget)
            ast_tokens = ast_budget
        token_used += ast_tokens

        # 3. File contents — load and truncate
        files_budget_remaining = files_budget
        file_contents: dict[str, str] = {}
        for fname in changed_files:
            if files_budget_remaining <= 0:
                break
            content = self._load_file(fname)
            if content is None:
                continue
            content_tokens = self._estimate_tokens(content)
            if content_tokens > files_budget_remaining:
                content = self._truncate_text(content, files_budget_remaining)
                content_tokens = files_budget_remaining
            file_contents[fname] = content
            files_budget_remaining -= content_tokens
        token_used += files_budget - files_budget_remaining

        # 4. Project info — truncate to budget
        proj_text = self._dict_to_text(project_info)
        proj_tokens = self._estimate_tokens(proj_text)
        if proj_tokens > project_budget:
            project_info = self._truncate_project_info(project_info, project_budget)
            proj_tokens = project_budget
        token_used += proj_tokens

        return AnalysisContext(
            pr_title=pr_detail.get("pr_title", ""),
            pr_description=pr_detail.get("pr_description", ""),
            parsed_diff=parsed_diff,
            ast_summary=ast_summary,
            file_contents=file_contents,
            project_info=project_info,
            token_budget=token_budget,
            token_used=token_used,
        )

    def _load_file(self, filename: str) -> Optional[str]:
        """Load file content from project_root, if it exists."""
        filepath = self.project_root / filename
        try:
            return filepath.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough estimate: 1 token ≈ 4 characters."""
        return max(1, len(text) // _CHARS_PER_TOKEN)

    @staticmethod
    def _truncate_text(text: str, max_tokens: int) -> str:
        """Truncate text to fit within max_tokens."""
        max_chars = max_tokens * _CHARS_PER_TOKEN
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n... [truncated]"

    @staticmethod
    def _dict_to_text(d: dict[str, Any]) -> str:
        """Convert a dict to a rough text representation for token estimation."""
        parts: list[str] = []
        for key, value in d.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def _truncate_ast_summary(
        self, ast: dict[str, Any], max_tokens: int
    ) -> dict[str, Any]:
        """Truncate AST summary to token budget."""
        text = self._dict_to_text(ast)
        truncated = self._truncate_text(text, max_tokens)
        return {"summary": truncated}

    def _truncate_project_info(
        self, info: dict[str, Any], max_tokens: int
    ) -> dict[str, Any]:
        """Truncate project info to token budget."""
        text = self._dict_to_text(info)
        truncated = self._truncate_text(text, max_tokens)
        return {"summary": truncated}
