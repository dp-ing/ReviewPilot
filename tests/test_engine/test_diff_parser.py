from __future__ import annotations

from app.engine.diff_parser import DiffParser
from app.engine.schemas import ParsedDiff

_SINGLE_HUNK_DIFF = """\
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

_MULTI_FILE_DIFF = """\
diff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1,2 +1,2 @@
-old
+new
@@ -10,2 +10,3 @@
 context
+added
 context
diff --git a/b.py b/b.py
--- a/b.py
+++ b/b.py
@@ -5,1 +5,1 @@
-removed
+added
"""

_EMPTY_DIFF = ""


class TestDiffParser:
    def test_empty_diff(self) -> None:
        parser = DiffParser()
        result = parser.parse(_EMPTY_DIFF)
        assert isinstance(result, ParsedDiff)
        assert result.files == {}
        assert result.stats == {}

    def test_single_hunk_parses_file(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        assert "main.py" in result.files

    def test_single_hunk_count(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        assert len(result.files["main.py"]) == 1

    def test_hunk_header(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        hunk = result.files["main.py"][0]
        assert hunk.old_start == 1
        assert hunk.new_start == 1

    def test_hunk_lines(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        hunk = result.files["main.py"][0]
        assert len(hunk.lines) == 5

    def test_stats_added_removed(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        assert "main.py" in result.stats
        added, removed = result.stats["main.py"]
        assert added == 2  # "new" + "extra"
        assert removed == 1  # "old"

    def test_multi_file_diff(self) -> None:
        parser = DiffParser()
        result = parser.parse(_MULTI_FILE_DIFF)
        assert "a.py" in result.files
        assert "b.py" in result.files

    def test_multi_file_hunks(self) -> None:
        parser = DiffParser()
        result = parser.parse(_MULTI_FILE_DIFF)
        assert len(result.files["a.py"]) == 2
        assert len(result.files["b.py"]) == 1

    def test_group_by_file(self) -> None:
        parser = DiffParser()
        result = parser.parse(_MULTI_FILE_DIFF)
        grouped = DiffParser.group_by_file(result)
        assert set(grouped.keys()) == {"a.py", "b.py"}

    def test_extract_changed_lines(self) -> None:
        parser = DiffParser()
        result = parser.parse(_SINGLE_HUNK_DIFF)
        hunk = result.files["main.py"][0]
        changed = DiffParser.extract_changed_lines(hunk)
        # Should contain the two added lines
        assert len(changed) >= 1
        contents = [c for _, c in changed]
        assert any('print("new")' in c for c in contents)

    def test_binary_file_diff_is_ignored(self) -> None:
        diff = (
            "diff --git a/image.png b/image.png\n"
            "Binary files a/image.png and b/image.png differ\n"
        )
        parser = DiffParser()
        result = parser.parse(diff)
        # Binary diff has no hunks
        assert "image.png" not in result.files or len(result.files.get("image.png", [])) == 0

    def test_no_newline_at_eof(self) -> None:
        diff = (
            "diff --git a/f.py b/f.py\n"
            "--- a/f.py\n"
            "+++ b/f.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-old\n"
            "\\ No newline at end of file\n"
            "+new\n"
            "\\ No newline at end of file\n"
        )
        parser = DiffParser()
        result = parser.parse(diff)
        assert "f.py" in result.files

    def test_filename_with_spaces(self) -> None:
        diff = (
            'diff --git "a/my file.py" "b/my file.py"\n'
            "--- a/my file.py\n"
            "+++ b/my file.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-a\n"
            "+b\n"
        )
        parser = DiffParser()
        result = parser.parse(diff)
        assert len(result.files) > 0
