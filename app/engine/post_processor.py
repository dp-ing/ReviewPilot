from __future__ import annotations

from typing import Optional

from app.analyzer.schemas import ASTFinding
from app.engine.schemas import EngineFinding

# Confidence thresholds by severity
_CONFIDENCE_THRESHOLDS = {
    "critical": 0.6,
    "warning": 0.8,
    "suggestion": 0.9,
}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "suggestion": 2}


class PostProcessor:
    """Merge, deduplicate, filter, and sort findings."""

    def __init__(
        self,
        ignore_patterns: Optional[list[str]] = None,
        ignore_rule_ids: Optional[list[str]] = None,
        enabled_categories: Optional[list[str]] = None,
    ) -> None:
        self.ignore_patterns = ignore_patterns or []
        self.ignore_rule_ids = ignore_rule_ids or []
        self.enabled_categories = enabled_categories

    def process(self, findings: list[EngineFinding]) -> list[EngineFinding]:
        """Run the full post-processing pipeline on a list of findings."""
        result = self._deduplicate(findings)
        result = self._filter_by_confidence(result)
        result = self._apply_ignore_rules(result)
        result = self._filter_categories(result)
        result = self._sort(result)
        return result

    @staticmethod
    def ast_to_engine(
        ast: ASTFinding,
        confidence: float = 1.0,
    ) -> EngineFinding:
        """Convert an ASTFinding to an EngineFinding."""
        return EngineFinding(
            rule_id=ast.rule_id,
            severity=ast.severity,
            category=ast.category,
            file_path=ast.file_path,
            line_start=ast.line_start,
            line_end=ast.line_end,
            title=ast.title,
            description=ast.description,
            suggestion=ast.code_snippet or "",
            confidence=confidence,
            source="ast",
        )

    @staticmethod
    def _deduplicate(findings: list[EngineFinding]) -> list[EngineFinding]:
        """Remove duplicates: same file + overlapping lines + same rule_id → keep higher confidence."""
        if not findings:
            return []

        kept: list[EngineFinding] = []
        for finding in findings:
            duplicate_idx: Optional[int] = None
            for i, existing in enumerate(kept):
                if PostProcessor._is_duplicate(finding, existing):
                    # Keep the one with higher confidence
                    if finding.confidence > existing.confidence:
                        duplicate_idx = i
                    else:
                        duplicate_idx = -1  # Signal to skip
                    break
            if duplicate_idx is not None and duplicate_idx >= 0:
                kept[duplicate_idx] = finding
            elif duplicate_idx is None:
                kept.append(finding)
        return kept

    @staticmethod
    def _is_duplicate(a: EngineFinding, b: EngineFinding) -> bool:
        """Check if two findings are duplicates."""
        if a.rule_id != b.rule_id:
            return False
        if a.file_path != b.file_path:
            return False
        # Line ranges overlap
        if a.line_end < b.line_start or b.line_end < a.line_start:
            return False
        return True

    @staticmethod
    def _filter_by_confidence(
        findings: list[EngineFinding],
    ) -> list[EngineFinding]:
        """Filter findings based on confidence thresholds by severity."""
        return [
            f
            for f in findings
            if f.confidence >= _CONFIDENCE_THRESHOLDS.get(f.severity, 0.9)
        ]

    def _apply_ignore_rules(
        self, findings: list[EngineFinding]
    ) -> list[EngineFinding]:
        """Remove findings matching ignore patterns or rule IDs."""
        result: list[EngineFinding] = []
        for f in findings:
            if f.rule_id in self.ignore_rule_ids:
                continue
            if any(pattern in f.file_path for pattern in self.ignore_patterns):
                continue
            result.append(f)
        return result

    def _filter_categories(
        self, findings: list[EngineFinding]
    ) -> list[EngineFinding]:
        """Filter findings to only include enabled categories."""
        if self.enabled_categories is None:
            return findings
        return [f for f in findings if f.category in self.enabled_categories]

    @staticmethod
    def _sort(findings: list[EngineFinding]) -> list[EngineFinding]:
        """Sort by severity (desc) then confidence (desc)."""
        return sorted(
            findings,
            key=lambda f: (
                _SEVERITY_ORDER.get(f.severity, 99),
                -f.confidence,
            ),
        )
