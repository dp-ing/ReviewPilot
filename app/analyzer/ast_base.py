from __future__ import annotations

from abc import ABC, abstractmethod

from app.analyzer.schemas import ASTResult, CodeStructure


class ASTAnalyzer(ABC):
    """Abstract base class for language-specific AST analyzers."""

    @abstractmethod
    def get_supported_language(self) -> str:
        """Return the language name this analyzer supports (e.g. 'python', 'java')."""
        ...

    @abstractmethod
    def analyze_file(self, filename: str, source: str) -> ASTResult:
        """Analyze a source file and return findings plus structure."""
        ...

    @abstractmethod
    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        """Extract code structure (functions, classes, imports) without rule checks."""
        ...
