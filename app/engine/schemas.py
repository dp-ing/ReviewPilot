from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Message:
    """A chat message for AI provider interaction."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from an AI provider."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


@dataclass
class EngineFinding:
    """An AI-generated finding, complementary to ASTFinding."""

    rule_id: str
    severity: str  # critical, warning, suggestion
    category: str  # security, logic, performance, style
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    suggestion: str = ""
    confidence: float = 0.0
    source: str = "ai"  # "ai" or "ast"


@dataclass
class Phase1Result:
    """Phase 1 — quick summary from a fast model."""

    summary: str
    risk_level: str = "low"  # low, medium, high
    key_changes: list[str] = field(default_factory=list)
    analysis_directions: list[str] = field(default_factory=list)


@dataclass
class AnalysisStats:
    """Statistics about an analysis run."""

    total_findings: int = 0
    by_severity: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)
    duration_ms: int = 0


@dataclass
class AnalysisResult:
    """Final result from the analysis orchestrator."""

    pr_url: str = ""
    findings: list[EngineFinding] = field(default_factory=list)
    phase1: Optional[Phase1Result] = None
    stats: AnalysisStats = field(default_factory=AnalysisStats)


@dataclass
class DiffLine:
    """A single line in a diff hunk."""

    kind: str  # "+", "-", " "
    content: str
    old_line: Optional[int] = None
    new_line: Optional[int] = None


@dataclass
class DiffHunk:
    """A single hunk from a unified diff."""

    header: str  # @@ -old_start,old_count +new_start,new_count @@
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass
class ParsedDiff:
    """Complete parsed diff for a PR."""

    files: dict[str, list[DiffHunk]] = field(default_factory=dict)
    stats: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class AnalysisContext:
    """Context assembled for AI analysis."""

    pr_title: str = ""
    pr_description: str = ""
    parsed_diff: Optional[ParsedDiff] = None
    ast_summary: dict[str, object] = field(default_factory=dict)
    file_contents: dict[str, str] = field(default_factory=dict)
    project_info: dict[str, object] = field(default_factory=dict)
    token_budget: int = 0
    token_used: int = 0
