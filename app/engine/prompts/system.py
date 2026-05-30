from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)


def build_system_prompt() -> str:
    """Render the system role prompt template."""
    template = _env.get_template("system.j2")
    return template.render()
