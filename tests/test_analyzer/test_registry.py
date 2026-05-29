from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.registry import AnalyzerRegistry
from app.analyzer.schemas import ASTResult, CodeStructure


class _PyAnalyzer(ASTAnalyzer):
    def get_supported_language(self) -> str:
        return "python"

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        return ASTResult(language="python")

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        return CodeStructure(file_path=filename, language="python")


class _JavaAnalyzer(ASTAnalyzer):
    def get_supported_language(self) -> str:
        return "java"

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        return ASTResult(language="java")

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        return CodeStructure(file_path=filename, language="java")


class TestAnalyzerRegistry:
    @staticmethod
    def _make_registry() -> AnalyzerRegistry:
        registry = AnalyzerRegistry()
        registry.register(_PyAnalyzer())
        registry.register(_JavaAnalyzer())
        return registry

    def test_register_and_get(self) -> None:
        registry = AnalyzerRegistry()
        registry.register(_PyAnalyzer())
        analyzer = registry.get("python")
        assert analyzer is not None
        assert analyzer.get_supported_language() == "python"

    def test_get_invalid_language(self) -> None:
        registry = self._make_registry()
        assert registry.get("ruby") is None

    def test_register_multiple_analyzers(self) -> None:
        registry = self._make_registry()
        assert registry.get("python") is not None
        assert registry.get("java") is not None

    def test_register_overwrites(self) -> None:
        registry = AnalyzerRegistry()
        registry.register(_PyAnalyzer())

        class _BetterPyAnalyzer(ASTAnalyzer):
            def get_supported_language(self) -> str:
                return "python"

            def analyze_file(self, filename: str, source: str) -> ASTResult:
                return ASTResult(language="python")

            def extract_structure(self, filename: str, source: str) -> CodeStructure:
                return CodeStructure(file_path=filename, language="python")

        registry.register(_BetterPyAnalyzer())
        analyzer = registry.get("python")
        assert isinstance(analyzer, _BetterPyAnalyzer)

    @staticmethod
    def _pytest_param_ids(data: object) -> str:
        return str(data)

    def test_detect_language(self) -> None:
        registry = self._make_registry()
        assert registry.detect_language("main.py") == "python"
        assert registry.detect_language("test.pyi") == "python"
        assert registry.detect_language("MyClass.java") == "java"
        assert registry.detect_language("README.md") is None
        assert registry.detect_language("script.js") is None
        assert registry.detect_language("Dockerfile") is None
