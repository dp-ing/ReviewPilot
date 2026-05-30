from app.engine.schemas import (
    AnalysisContext,
    AnalysisResult,
    AnalysisStats,
    ChatResponse,
    DiffHunk,
    DiffLine,
    EngineFinding,
    Message,
    ParsedDiff,
    Phase1Result,
)


class TestMessage:
    def test_create_message(self) -> None:
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_system_message(self) -> None:
        msg = Message(role="system", content="You are a code reviewer.")
        assert msg.role == "system"


class TestChatResponse:
    def test_create_chat_response(self) -> None:
        resp = ChatResponse(content="ok", model="gpt-4", finish_reason="stop")
        assert resp.content == "ok"
        assert resp.model == "gpt-4"
        assert resp.finish_reason == "stop"

    def test_default_usage(self) -> None:
        resp = ChatResponse(content="", model="test")
        assert resp.usage == {}


class TestEngineFinding:
    def test_create_finding(self) -> None:
        f = EngineFinding(
            rule_id="test-rule",
            severity="critical",
            category="security",
            file_path="test.py",
            line_start=1,
            line_end=1,
            title="Test finding",
            description="A test finding",
            suggestion="Fix it",
            confidence=0.9,
            source="ai",
        )
        assert f.rule_id == "test-rule"
        assert f.confidence == 0.9
        assert f.source == "ai"

    def test_default_values(self) -> None:
        f = EngineFinding(
            rule_id="r",
            severity="warning",
            category="style",
            file_path="f.py",
            line_start=1,
            line_end=2,
            title="t",
            description="d",
        )
        assert f.suggestion == ""
        assert f.confidence == 0.0
        assert f.source == "ai"


class TestPhase1Result:
    def test_create_phase1_result(self) -> None:
        r = Phase1Result(
            summary="Minor changes",
            risk_level="low",
            key_changes=["renamed variable"],
            analysis_directions=["check security"],
        )
        assert r.summary == "Minor changes"
        assert r.risk_level == "low"
        assert len(r.key_changes) == 1

    def test_default_values(self) -> None:
        r = Phase1Result(summary="ok")
        assert r.risk_level == "low"
        assert r.key_changes == []
        assert r.analysis_directions == []


class TestAnalysisStats:
    def test_create_stats(self) -> None:
        s = AnalysisStats(
            total_findings=10,
            by_severity={"critical": 2, "warning": 8},
            by_category={"security": 5, "style": 5},
            token_usage={"prompt": 1000, "completion": 500},
            duration_ms=3000,
        )
        assert s.total_findings == 10
        assert s.duration_ms == 3000

    def test_default_values(self) -> None:
        s = AnalysisStats()
        assert s.total_findings == 0
        assert s.by_severity == {}
        assert s.duration_ms == 0


class TestAnalysisResult:
    def test_create_analysis_result(self) -> None:
        r = AnalysisResult(pr_url="https://github.com/org/repo/pull/1")
        assert r.pr_url == "https://github.com/org/repo/pull/1"
        assert r.findings == []
        assert r.phase1 is None

    def test_with_findings(self) -> None:
        f = EngineFinding(
            rule_id="r1", severity="critical", category="security",
            file_path="a.py", line_start=1, line_end=1,
            title="t", description="d",
        )
        r = AnalysisResult(pr_url="url", findings=[f])
        assert len(r.findings) == 1

    def test_with_phase1(self) -> None:
        p1 = Phase1Result(summary="summary")
        r = AnalysisResult(pr_url="url", phase1=p1)
        assert r.phase1 is not None
        assert r.phase1.summary == "summary"


class TestDiffLine:
    def test_create_diff_line(self) -> None:
        dl = DiffLine(kind="+", content="x = 1", new_line=10)
        assert dl.kind == "+"
        assert dl.content == "x = 1"
        assert dl.new_line == 10

    def test_default_line_numbers(self) -> None:
        dl = DiffLine(kind=" ", content="context")
        assert dl.old_line is None
        assert dl.new_line is None


class TestDiffHunk:
    def test_create_diff_hunk(self) -> None:
        h = DiffHunk(
            header="@@ -1,3 +1,4 @@",
            old_start=1, old_count=3,
            new_start=1, new_count=4,
        )
        assert h.old_start == 1
        assert h.new_count == 4
        assert h.lines == []

    def test_with_lines(self) -> None:
        lines = [
            DiffLine(kind=" ", content="a", old_line=1, new_line=1),
            DiffLine(kind="-", content="b", old_line=2),
            DiffLine(kind="+", content="c", new_line=2),
        ]
        h = DiffHunk(
            header="@@ -1,2 +1,2 @@",
            old_start=1, old_count=2,
            new_start=1, new_count=2,
            lines=lines,
        )
        assert len(h.lines) == 3


class TestParsedDiff:
    def test_create_parsed_diff(self) -> None:
        pd = ParsedDiff()
        assert pd.files == {}
        assert pd.stats == {}

    def test_with_files(self) -> None:
        hunks = [DiffHunk(header="@@ -1,1 +1,1 @@", old_start=1, old_count=1, new_start=1, new_count=1)]
        pd = ParsedDiff(
            files={"main.py": hunks},
            stats={"main.py": (1, 1)},
        )
        assert "main.py" in pd.files
        assert len(pd.files["main.py"]) == 1


class TestAnalysisContext:
    def test_create_context(self) -> None:
        ctx = AnalysisContext(
            pr_title="Add feature",
            pr_description="Implements a new feature",
            token_budget=8000,
        )
        assert ctx.pr_title == "Add feature"
        assert ctx.token_budget == 8000
        assert ctx.parsed_diff is None

    def test_default_values(self) -> None:
        ctx = AnalysisContext()
        assert ctx.pr_title == ""
        assert ctx.token_budget == 0
        assert ctx.parsed_diff is None
