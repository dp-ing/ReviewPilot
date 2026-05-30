from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Optional, Tuple

from app.engine.context_builder import ContextBuilder
from app.engine.post_processor import PostProcessor
from app.engine.prompts.stage1 import build_stage1_prompt
from app.engine.prompts.stage2 import (
    build_stage2_logic_prompt,
    build_stage2_performance_prompt,
    build_stage2_security_prompt,
    build_stage2_style_prompt,
)
from app.engine.prompts.system import build_system_prompt
from app.engine.provider import AIProvider
from app.engine.schemas import (
    AnalysisResult,
    AnalysisStats,
    EngineFinding,
    Message,
    Phase1Result,
)

_STAGE2_BUILDERS: dict[str, Tuple[Callable[..., str], set[str]]] = {
    "security": (
        build_stage2_security_prompt,
        {"risk_level", "files", "ast_findings"},
    ),
    "logic": (
        build_stage2_logic_prompt,
        {"files", "ast_structure"},
    ),
    "performance": (
        build_stage2_performance_prompt,
        {"files"},
    ),
    "style": (
        build_stage2_style_prompt,
        {"files", "ast_structure"},
    ),
}

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class AnalysisOrchestrator:
    """Two-phase PR analysis orchestrator.

    Phase 1: fast model — risk assessment + analysis directions
    Phase 2: strong model — deep dives per direction, then merge + post-process
    """

    def __init__(
        self,
        provider_fast: AIProvider,
        provider_strong: Optional[AIProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
        post_processor: Optional[PostProcessor] = None,
    ) -> None:
        self.provider_fast = provider_fast
        self.provider_strong = provider_strong or provider_fast
        self.context_builder = context_builder or ContextBuilder()
        self.post_processor = post_processor or PostProcessor()

    def analyze(
        self,
        pr_detail: dict[str, Any],
        token_budget: int = 4000,
        enabled_directions: Optional[list[str]] = None,
    ) -> AnalysisResult:
        """Run the full two-phase analysis on a PR.

        Args:
            pr_detail: PR metadata dict with keys like pr_title, pr_description,
                       diff_text, changed_files, ast_summary, project_info.
            token_budget: Maximum token budget for context building.
            enabled_directions: Specific directions to analyze, or None for all
                                from Phase 1 recommendation.
        """
        start_time = time.perf_counter()
        total_tokens: dict[str, int] = {}

        # Build context
        ctx = self.context_builder.build(pr_detail, token_budget)

        # Phase 1: Risk assessment via fast model
        system_prompt = build_system_prompt()
        pr_title = pr_detail.get("pr_title", "")
        pr_description = pr_detail.get("pr_description", "")

        # Build diff summary for Phase 1
        diff_stats = {
            "total_files": len(ctx.parsed_diff.files) if ctx.parsed_diff else 0,
            "additions": sum(
                s[0] for s in (ctx.parsed_diff.stats.values() if ctx.parsed_diff else {})
            ),
            "deletions": sum(
                s[1] for s in (ctx.parsed_diff.stats.values() if ctx.parsed_diff else {})
            ),
        }
        diff_text = pr_detail.get("diff_text", "")
        diff_abbreviated = diff_text[:3000]  # Limit for Phase 1

        stage1_prompt = build_stage1_prompt(
            pr_title=pr_title,
            pr_description=pr_description,
            changed_files=list(ctx.file_contents.keys()) or list(
                ctx.parsed_diff.files.keys() if ctx.parsed_diff else []
            ),
            diff_stats=diff_stats,
            diff_abbreviated=diff_abbreviated,
        )

        phase1_messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=stage1_prompt),
        ]

        phase1_response = self.provider_fast.chat(phase1_messages)
        tokens_used = phase1_response.usage.get("total_tokens", 0)
        total_tokens["phase1"] = tokens_used

        phase1_result = self._parse_phase1(phase1_response.content)

        # Phase 2: Deep analysis per direction
        directions = enabled_directions or phase1_result.analysis_directions
        if not directions:
            # Default to all directions
            directions = ["security", "logic", "performance", "style"]

        all_findings: list[EngineFinding] = []
        for direction in directions:
            if direction not in _STAGE2_BUILDERS:
                continue

            builder, param_names = _STAGE2_BUILDERS[direction]
            kwargs: dict[str, Any] = {
                "pr_title": pr_title,
                "phase1_summary": phase1_result.summary,
            }
            if "risk_level" in param_names:
                kwargs["risk_level"] = phase1_result.risk_level
            if "files" in param_names:
                kwargs["files"] = ctx.file_contents
            if "ast_findings" in param_names:
                kwargs["ast_findings"] = []  # AST findings merged after
            if "ast_structure" in param_names:
                kwargs["ast_structure"] = ctx.ast_summary
            direction_prompt = builder(**kwargs)

            phase2_messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=direction_prompt),
            ]

            phase2_response = self.provider_strong.chat(phase2_messages)
            total_tokens[direction] = phase2_response.usage.get("total_tokens", 0)

            findings = self._parse_findings(phase2_response.content)
            all_findings.extend(findings)

        # Post-process
        processed = self.post_processor.process(all_findings)

        # Build stats
        by_severity: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for f in processed:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
            by_category[f.category] = by_category.get(f.category, 0) + 1

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        stats = AnalysisStats(
            total_findings=len(processed),
            by_severity=by_severity,
            by_category=by_category,
            token_usage=total_tokens,
            duration_ms=duration_ms,
        )

        return AnalysisResult(
            pr_url=pr_detail.get("pr_url", ""),
            findings=processed,
            phase1=phase1_result,
            stats=stats,
        )

    @staticmethod
    def _parse_phase1(content: str) -> Phase1Result:
        """Parse Phase 1 AI response JSON into Phase1Result."""
        data = AnalysisOrchestrator._extract_json(content)
        if not data:
            return Phase1Result(
                summary="Failed to parse Phase 1 response",
                risk_level="medium",
            )
        return Phase1Result(
            summary=data.get("summary", ""),
            risk_level=data.get("risk_level", "low"),
            key_changes=data.get("key_changes", []),
            analysis_directions=data.get("analysis_directions", []),
        )

    @staticmethod
    def _parse_findings(content: str) -> list[EngineFinding]:
        """Parse Phase 2 AI response JSON into a list of EngineFinding."""
        data = AnalysisOrchestrator._extract_json(content)
        if not data:
            return []

        findings_data = data.get("findings", [])
        if not isinstance(findings_data, list):
            return []

        result: list[EngineFinding] = []
        for item in findings_data:
            if not isinstance(item, dict):
                continue
            try:
                result.append(
                    EngineFinding(
                        rule_id=item.get("rule_id", "AI-UNKNOWN"),
                        severity=item.get("severity", "warning"),
                        category=item.get("category", "logic"),
                        file_path=item.get("file_path", ""),
                        line_start=item.get("line_start", 1),
                        line_end=item.get("line_end", 1),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", ""),
                        confidence=item.get("confidence", 0.5),
                        source="ai",
                    )
                )
            except (TypeError, KeyError):
                continue
        return result

    @staticmethod
    def _extract_json(content: str) -> Optional[dict[str, Any]]:
        """Extract JSON object from AI response, handling markdown fences."""
        # Try markdown code block first
        m = _JSON_BLOCK_RE.search(content)
        if m:
            try:
                return json.loads(m.group(1))  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # Try extracting JSON object directly
        try:
            first_brace = content.index("{")
            last_brace = content.rindex("}")
            json_str = content[first_brace : last_brace + 1]
            return json.loads(json_str)  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            return None
