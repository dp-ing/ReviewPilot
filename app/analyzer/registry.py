from __future__ import annotations

from typing import Optional

from app.analyzer.ast_base import ASTAnalyzer


class AnalyzerRegistry:
    """Registry for language-specific AST analyzers."""

    def __init__(self) -> None:
        self._analyzers: dict[str, ASTAnalyzer] = {}

    def register(self, analyzer: ASTAnalyzer) -> None:
        lang = analyzer.get_supported_language()
        self._analyzers[lang] = analyzer

    def get(self, language: str) -> Optional[ASTAnalyzer]:
        return self._analyzers.get(language)

    def detect_language(self, filename: str) -> Optional[str]:
        extensions = {
            ".py": "python",
            ".pyx": "python",
            ".pyi": "python",
            ".java": "java",
        }
        for ext, lang in extensions.items():
            if filename.endswith(ext):
                return lang
        return None
