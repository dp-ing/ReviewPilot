from __future__ import annotations

import json
import os
import re

import pytest

from app.engine.prompts.stage1 import build_stage1_prompt
from app.engine.prompts.stage2 import (
    build_stage2_logic_prompt,
    build_stage2_performance_prompt,
    build_stage2_security_prompt,
    build_stage2_style_prompt,
)
from app.engine.prompts.system import build_system_prompt


def _get_api_key() -> str:
    return os.environ.get("AI_API_KEY", "")


def _call_ai(messages: list[dict], model: str = "deepseek-v4-flash") -> dict:
    import urllib.request

    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.1,
    }).encode()
    req = urllib.request.Request(
        f"https://api.deepseek.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Content-Type": "application/json",
        },
    )
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read())


def _extract_json(content: str) -> dict | None:
    # Strip markdown code fences
    c = content.strip()
    if c.startswith("```"):
        c = c.removeprefix("```json").removeprefix("```").strip()
    # Try direct parse first
    try:
        return json.loads(c)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        pass
    # Try to extract proper JSON substring (handles trailing text)
    for start in range(len(c)):
        if c[start] == "{":
            depth = 0
            for end in range(start, len(c)):
                if c[end] == "{":
                    depth += 1
                elif c[end] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(c[start:end + 1])  # type: ignore[no-any-return]
                        except json.JSONDecodeError:
                            break
            break
    return None


SAMPLE_DIFF = """\
diff --git a/app/api/users.py b/app/api/users.py
new file mode 100644
--- /dev/null
+++ b/app/api/users.py
@@ -0,0 +1,20 @@
+from flask import request, jsonify
+import sqlite3
+
+def search_users():
+    name = request.args.get("name", "")
+    conn = sqlite3.connect("app.db")
+    query = "SELECT * FROM users WHERE name = '" + name + "'"
+    cursor.execute(query)
+    return jsonify(cursor.fetchall())
+
+def delete_user(user_id):
+    conn = sqlite3.connect("app.db")
+    query = f"DELETE FROM users WHERE id = {user_id}"
+    conn.execute(query)
+    conn.commit()
+    return jsonify({"status": "deleted"})
+"""


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


@pytest.mark.e2e
class TestAIE2E:
    """End-to-end prompt tests against real AI API (requires AI_API_KEY)."""

    def test_stage1_flash_returns_valid_summary(self) -> None:
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("AI_API_KEY not set")

        system_prompt = build_system_prompt()
        stage1 = build_stage1_prompt(
            pr_title="Add user search API",
            pr_description="New endpoint for searching users.",
            changed_files=["app/api/users.py"],
            diff_stats={"total_files": 2, "additions": 25, "deletions": 5},
            diff_abbreviated=SAMPLE_DIFF,
        )
        result = _call_ai([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": stage1},
        ], model="deepseek-v4-flash")

        content = result["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        assert parsed is not None, f"Failed to parse JSON from: {content[:300]}"
        assert "risk_level" in parsed or "summary" in parsed
        assert result["model"] == "deepseek-v4-flash"

    def test_stage2_pro_security_detects_sql_injection(self) -> None:
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("AI_API_KEY not set")

        system_prompt = build_system_prompt()
        stage2 = build_stage2_security_prompt(
            pr_title="Add user search API",
            phase1_summary="SQL injection risk in user search and delete functions.",
            risk_level="high",
            files={"app/api/users.py": SAMPLE_DIFF},
            language="python",
        )
        result = _call_ai([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": stage2},
        ], model="deepseek-v4-pro")

        content = result["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        assert parsed is not None, f"Failed to parse JSON from: {content[:300]}"
        findings = parsed.get("findings", [])
        assert isinstance(findings, list)
        assert len(findings) > 0, "Should detect at least one issue"

        # Verify finding structure
        for f in findings:
            assert "rule_id" in f
            assert "severity" in f
            assert "file_path" in f
            assert "title" in f
            assert "confidence" in f

        severities = [f["severity"] for f in findings]
        assert "critical" in severities, (
            f"Expected critical finding for SQL injection, got: {severities}"
        )

    def test_stage2_pro_returns_valid_json_format(self) -> None:
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("AI_API_KEY not set")

        system_prompt = build_system_prompt()
        stage2 = build_stage2_style_prompt(
            pr_title="Add user search API",
            phase1_summary="Minor code style issues noted.",
            files={"app/api/users.py": SAMPLE_DIFF},
            language="python",
        )
        result = _call_ai([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": stage2},
        ], model="deepseek-v4-pro")

        content = result["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        assert parsed is not None, f"Failed to parse JSON: {content[:300]}"
        assert "findings" in parsed

    def test_both_models_available(self) -> None:
        api_key = _get_api_key()
        if not api_key:
            pytest.skip("AI_API_KEY not set")

        result = _call_ai([
            {"role": "user", "content": "Say 'ok'"},
        ], model="deepseek-v4-flash")
        assert result["model"] == "deepseek-v4-flash"

        result2 = _call_ai([
            {"role": "user", "content": "Say 'ok'"},
        ], model="deepseek-v4-pro")
        assert result2["model"] == "deepseek-v4-pro"
