from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)


def build_stage1_prompt(
    pr_title: str,
    pr_description: str,
    changed_files: list[str],
    diff_stats: dict[str, int],
    diff_abbreviated: str,
) -> str:
    """Render the Phase 1 change summary prompt."""
    template = _env.get_template("stage1.j2")
    return template.render(
        pr_title=pr_title,
        pr_description=pr_description,
        changed_files=changed_files,
        diff_stats=diff_stats,
        diff_abbreviated=diff_abbreviated,
    )
