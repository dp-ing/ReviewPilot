from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ASTFinding:
    """A single deterministic finding from AST analysis."""

    rule_id: str
    severity: str  # critical, warning, suggestion
    category: str  # security, best_practice, style
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    code_snippet: Optional[str] = None


@dataclass
class FunctionInfo:
    name: str
    line_start: int
    line_end: int
    args: list[str] = field(default_factory=list)
    returns: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    complexity: int = 0


@dataclass
class ClassInfo:
    name: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


@dataclass
class CallInfo:
    function_name: str
    line: int
    args: list[str] = field(default_factory=list)
    keyword_args: list[str] = field(default_factory=list)


@dataclass
class CodeStructure:
    file_path: str
    language: str
    imports: list[str] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)
    variable_assignments: list[str] = field(default_factory=list)
    exception_blocks: list[tuple[int, int]] = field(default_factory=list)
    lines_of_code: int = 0


@dataclass
class ASTResult:
    findings: list[ASTFinding] = field(default_factory=list)
    structure: Optional[CodeStructure] = None
    language: str = "unknown"
    success: bool = True
    error_message: Optional[str] = None
