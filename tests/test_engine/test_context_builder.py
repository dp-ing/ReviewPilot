from __future__ import annotations

from pathlib import Path

from app.engine.context_builder import ContextBuilder
from app.engine.schemas import AnalysisContext


_SAMPLE_DIFF = """\
diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    print("extra")
     return 0
"""

_PR_DETAIL = {
    "pr_title": "Test PR",
    "pr_description": "A test pull request",
    "diff_text": _SAMPLE_DIFF,
    "changed_files": ["main.py"],
    "ast_summary": {"main.py": {"classes": 0, "functions": 1}},
    "project_info": {"language": "python", "framework": "flask"},
}


class TestContextBuilder:
    def test_build_returns_analysis_context(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL)
        assert isinstance(ctx, AnalysisContext)

    def test_build_sets_pr_metadata(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL)
        assert ctx.pr_title == "Test PR"
        assert ctx.pr_description == "A test pull request"

    def test_build_parses_diff(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL)
        assert ctx.parsed_diff is not None
        assert "main.py" in ctx.parsed_diff.files

    def test_build_stores_ast_summary(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL)
        assert "main.py" in ctx.ast_summary

    def test_build_stores_project_info(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL)
        assert ctx.project_info["language"] == "python"

    def test_build_respects_token_budget(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL, token_budget=500)
        assert ctx.token_budget == 500
        assert ctx.token_used <= ctx.token_budget

    def test_build_with_no_diff(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build({"pr_title": "No diff", "diff_text": ""})
        assert ctx.pr_title == "No diff"
        assert ctx.parsed_diff is not None
        assert ctx.parsed_diff.files == {}

    def test_build_with_small_budget_truncates(self) -> None:
        builder = ContextBuilder()
        ctx = builder.build(_PR_DETAIL, token_budget=10)
        assert ctx.token_used <= 10

    def test_build_uses_diff_files_when_no_changed_files(self) -> None:
        builder = ContextBuilder()
        detail = {
            "pr_title": "T",
            "diff_text": _SAMPLE_DIFF,
        }
        ctx = builder.build(detail)
        assert ctx.parsed_diff is not None
        assert "main.py" in ctx.parsed_diff.files

    def test_estimate_tokens(self) -> None:
        # 1 token ≈ 4 chars
        assert ContextBuilder._estimate_tokens("1234") == 1
        assert ContextBuilder._estimate_tokens("12345678") == 2

    def test_truncate_text(self) -> None:
        result = ContextBuilder._truncate_text("hello world", max_tokens=1)
        assert len(result) <= 4 + len("\n... [truncated]")

    def test_load_nonexistent_file(self) -> None:
        builder = ContextBuilder(project_root=Path("/nonexistent"))
        content = builder._load_file("nonexistent.py")
        assert content is None

    def test_load_file_truncation_with_budget(self) -> None:
        builder = ContextBuilder()
        detail = {
            "pr_title": "T",
            "diff_text": _SAMPLE_DIFF,
            "changed_files": ["app/engine/schemas.py"],
        }
        ctx = builder.build(detail, token_budget=100)
        assert isinstance(ctx, AnalysisContext)
