from __future__ import annotations

from typing import Any

from app.engine.orchestrator import AnalysisOrchestrator
from app.engine.provider import AIProvider
from app.engine.schemas import (
    AnalysisResult,
    ChatResponse,
    Message,
    Phase1Result,
)


class _MockProvider(AIProvider):
    """Mock provider that returns pre-configured responses."""

    def __init__(self, responses: list[str], model: str = "mock") -> None:
        self.responses = responses
        self.calls: list[list[Message]] = []
        self._model = model
        self._idx = 0

    def chat(self, messages: list[Message], **kwargs: Any) -> ChatResponse:
        self.calls.append(messages)
        content = ""
        if self._idx < len(self.responses):
            content = self.responses[self._idx]
            self._idx += 1
        return ChatResponse(
            content=content,
            model=self._model,
            usage={"total_tokens": 100},
        )

    def get_model_name(self) -> str:
        return self._model

    def get_max_tokens(self) -> int:
        return 4096


_PHASE1_RESPONSE = """```json
{
  "summary": "Simple test PR with one file change",
  "risk_level": "low",
  "key_changes": ["Add print statement"],
  "analysis_directions": ["security", "style"]
}
```"""

_PHASE2_SECURITY_RESPONSE = """```json
{
  "findings": [
    {
      "rule_id": "AI-SEC001",
      "severity": "critical",
      "category": "security",
      "file_path": "main.py",
      "line_start": 1,
      "line_end": 3,
      "title": "Test security finding",
      "description": "Found a security issue",
      "suggestion": "Fix it",
      "confidence": 0.9
    }
  ]
}
```"""

_PHASE2_STYLE_RESPONSE = """```json
{
  "findings": [
    {
      "rule_id": "AI-STY001",
      "severity": "suggestion",
      "category": "style",
      "file_path": "main.py",
      "line_start": 5,
      "line_end": 5,
      "title": "Style issue",
      "description": "Line too long",
      "suggestion": "Wrap it",
      "confidence": 0.95
    }
  ]
}
```"""

_PR_DETAIL = {
    "pr_title": "Test PR",
    "pr_description": "A test pull request",
    "diff_text": (
        "diff --git a/main.py b/main.py\n"
        "--- a/main.py\n"
        "+++ b/main.py\n"
        "@@ -1,3 +1,4 @@\n"
        " def hello():\n"
        "-    print('old')\n"
        "+    print('new')\n"
        "+    print('extra')\n"
        "     return 0\n"
    ),
    "changed_files": ["main.py"],
}


class TestAnalysisOrchestrator:
    def test_analyze_returns_analysis_result(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE, _PHASE2_STYLE_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL)
        assert isinstance(result, AnalysisResult)
        assert isinstance(result.phase1, Phase1Result)
        assert result.stats.total_findings > 0

    def test_phase1_output_drives_phase2(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE, _PHASE2_STYLE_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL)
        assert result.phase1 is not None
        assert result.phase1.risk_level == "low"
        assert "security" in result.phase1.analysis_directions

    def test_phase2_findings_are_merged(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE, _PHASE2_STYLE_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL)
        categories = {f.category for f in result.findings}
        assert "security" in categories
        assert "style" in categories

    def test_custom_directions_override(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL, enabled_directions=["security"])
        assert "security" in {f.category for f in result.findings}

    def test_defaults_to_all_directions_when_phase1_empty(self) -> None:
        phase1_empty = '{"summary":"x","risk_level":"low","key_changes":[],"analysis_directions":[]}'
        fast = _MockProvider([phase1_empty])
        strong = _MockProvider(
            [_PHASE2_SECURITY_RESPONSE, _PHASE2_STYLE_RESPONSE,
             _MINIMAL_LOGIC, _MINIMAL_PERF]
        )
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL)
        assert result.phase1 is not None

    def test_token_usage_is_tracked(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL, enabled_directions=["security"])
        assert "phase1" in result.stats.token_usage
        assert "security" in result.stats.token_usage

    def test_stats_duration(self) -> None:
        fast = _MockProvider([_PHASE1_RESPONSE])
        strong = _MockProvider([_PHASE2_SECURITY_RESPONSE])
        orch = AnalysisOrchestrator(fast, strong)
        result = orch.analyze(_PR_DETAIL, enabled_directions=["security"])
        assert result.stats.duration_ms >= 0


class TestParsePhase1:
    def test_parses_valid_json(self) -> None:
        content = '{"summary":"s","risk_level":"high","key_changes":["a"],"analysis_directions":["security"]}'
        result = AnalysisOrchestrator._parse_phase1(content)
        assert result.summary == "s"
        assert result.risk_level == "high"
        assert result.key_changes == ["a"]
        assert result.analysis_directions == ["security"]

    def test_parses_markdown_fenced_json(self) -> None:
        result = AnalysisOrchestrator._parse_phase1(_PHASE1_RESPONSE)
        assert result.summary == "Simple test PR with one file change"
        assert result.risk_level == "low"

    def test_graceful_on_invalid_json(self) -> None:
        result = AnalysisOrchestrator._parse_phase1("not json at all")
        assert result.risk_level == "medium"
        assert "Failed" in result.summary


class TestParseFindings:
    def test_parses_findings_list(self) -> None:
        findings = AnalysisOrchestrator._parse_findings(_PHASE2_SECURITY_RESPONSE)
        assert len(findings) == 1
        assert findings[0].rule_id == "AI-SEC001"
        assert findings[0].source == "ai"

    def test_empty_on_invalid_json(self) -> None:
        findings = AnalysisOrchestrator._parse_findings("invalid")
        assert findings == []

    def test_empty_on_missing_findings_key(self) -> None:
        findings = AnalysisOrchestrator._parse_findings('{"other": []}')
        assert findings == []

    def test_skips_invalid_finding_items(self) -> None:
        content = '{"findings": [{"rule_id": "ok", "severity": "w", "category": "c"}, "not_a_dict"]}'
        findings = AnalysisOrchestrator._parse_findings(content)
        assert len(findings) == 1


class TestExtractJson:
    def test_extracts_from_markdown_fence(self) -> None:
        content = "```json\n{\"a\": 1}\n```"
        result = AnalysisOrchestrator._extract_json(content)
        assert result == {"a": 1}

    def test_extracts_bare_json(self) -> None:
        content = 'some text {"key": "value"} more text'
        result = AnalysisOrchestrator._extract_json(content)
        assert result == {"key": "value"}

    def test_returns_none_on_invalid(self) -> None:
        result = AnalysisOrchestrator._extract_json("no json here")
        assert result is None

    def test_extracts_nested_json(self) -> None:
        content = '{"a": {"b": [1, 2, 3]}, "c": "d"}'
        result = AnalysisOrchestrator._extract_json(content)
        assert result == {"a": {"b": [1, 2, 3]}, "c": "d"}


# Minimal responses for default directions test
_MINIMAL_LOGIC = """```json
{"findings": []}
```"""

_MINIMAL_PERF = """```json
{"findings": []}
```"""
