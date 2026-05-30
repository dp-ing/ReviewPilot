from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)


def build_stage2_security_prompt(
    pr_title: str,
    phase1_summary: str,
    risk_level: str,
    files: dict[str, str],
    language: str = "text",
    ast_findings: Optional[list[dict[str, Any]]] = None,
) -> str:
    """Render the Stage 2 security analysis prompt."""
    template = _env.get_template("stage2_security.j2")
    return template.render(
        pr_title=pr_title,
        phase1_summary=phase1_summary,
        risk_level=risk_level,
        files=files,
        language=language,
        ast_findings=ast_findings or [],
    )


def build_stage2_logic_prompt(
    pr_title: str,
    phase1_summary: str,
    files: dict[str, str],
    language: str = "text",
    ast_structure: Optional[dict[str, Any]] = None,
) -> str:
    """Render the Stage 2 logic analysis prompt."""
    template = _env.get_template("stage2_logic.j2")
    return template.render(
        pr_title=pr_title,
        phase1_summary=phase1_summary,
        files=files,
        language=language,
        ast_structure=ast_structure or {},
    )


def build_stage2_performance_prompt(
    pr_title: str,
    phase1_summary: str,
    files: dict[str, str],
    language: str = "text",
) -> str:
    """Render the Stage 2 performance analysis prompt."""
    template = _env.get_template("stage2_performance.j2")
    return template.render(
        pr_title=pr_title,
        phase1_summary=phase1_summary,
        files=files,
        language=language,
    )


def build_stage2_style_prompt(
    pr_title: str,
    phase1_summary: str,
    files: dict[str, str],
    language: str = "text",
    ast_structure: Optional[dict[str, Any]] = None,
) -> str:
    """Render the Stage 2 style analysis prompt."""
    template = _env.get_template("stage2_style.j2")
    return template.render(
        pr_title=pr_title,
        phase1_summary=phase1_summary,
        files=files,
        language=language,
        ast_structure=ast_structure or {},
    )
