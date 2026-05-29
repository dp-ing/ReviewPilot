from __future__ import annotations

from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import ASTResult, CodeStructure


class PythonAnalyzer(ASTAnalyzer):
    """AST analyzer for Python source code."""

    def get_supported_language(self) -> str:
        return "python"

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        raise NotImplementedError

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        raise NotImplementedError
