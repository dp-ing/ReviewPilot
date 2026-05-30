from __future__ import annotations

from app.engine.prompts.stage1 import build_stage1_prompt
from app.engine.prompts.stage2 import (
    build_stage2_logic_prompt,
    build_stage2_performance_prompt,
    build_stage2_security_prompt,
    build_stage2_style_prompt,
)
from app.engine.prompts.system import build_system_prompt


class TestSystemPrompt:
    def test_build_system_prompt_returns_string(self) -> None:
        result = build_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 0
        assert "code reviewer" in result.lower()

    def test_build_system_prompt_contains_json_format(self) -> None:
        result = build_system_prompt()
        assert "JSON" in result
        assert "findings" in result


class TestStage1Prompt:
    def test_build_stage1_prompt_returns_string(self) -> None:
        result = build_stage1_prompt(
            pr_title="Test PR",
            pr_description="Testing",
            changed_files=["main.py"],
            diff_stats={"total_files": 1, "additions": 5, "deletions": 2},
            diff_abbreviated="+new line",
        )
        assert isinstance(result, str)
        assert "Test PR" in result
        assert "main.py" in result

    def test_stage1_includes_risk_assessment(self) -> None:
        result = build_stage1_prompt(
            pr_title="Fix",
            pr_description="Bug fix",
            changed_files=["a.py"],
            diff_stats={"total_files": 1, "additions": 0, "deletions": 0},
            diff_abbreviated="",
        )
        assert "risk_level" in result


class TestStage2Prompts:
    def test_build_security_prompt(self) -> None:
        result = build_stage2_security_prompt(
            pr_title="Test",
            phase1_summary="Minor changes",
            risk_level="low",
            files={"main.py": "print('hello')"},
        )
        assert isinstance(result, str)
        assert "Security" in result
        assert "findings" in result

    def test_build_logic_prompt(self) -> None:
        result = build_stage2_logic_prompt(
            pr_title="Test",
            phase1_summary="Changes",
            files={"main.py": "x = 1"},
        )
        assert isinstance(result, str)
        assert "Logic" in result

    def test_build_performance_prompt(self) -> None:
        result = build_stage2_performance_prompt(
            pr_title="Test",
            phase1_summary="Changes",
            files={"main.py": "x = 1"},
        )
        assert isinstance(result, str)
        assert "Performance" in result

    def test_build_style_prompt(self) -> None:
        result = build_stage2_style_prompt(
            pr_title="Test",
            phase1_summary="Changes",
            files={"main.py": "x = 1"},
        )
        assert isinstance(result, str)
        assert "Style" in result
