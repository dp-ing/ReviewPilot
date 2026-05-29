import pytest

from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import ASTResult, CodeStructure


class _ConcreteAnalyzer(ASTAnalyzer):
    def get_supported_language(self) -> str:
        return "test-lang"

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        return ASTResult(language=self.get_supported_language())

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        return CodeStructure(file_path=filename, language=self.get_supported_language())


class TestASTAnalyzer:
    def test_get_supported_language(self) -> None:
        analyzer = _ConcreteAnalyzer()
        assert analyzer.get_supported_language() == "test-lang"

    def test_analyze_file_returns_ast_result(self) -> None:
        analyzer = _ConcreteAnalyzer()
        result = analyzer.analyze_file("test.py", "x = 1")
        assert isinstance(result, ASTResult)
        assert result.language == "test-lang"

    def test_extract_structure_returns_code_structure(self) -> None:
        analyzer = _ConcreteAnalyzer()
        structure = analyzer.extract_structure("test.py", "x = 1")
        assert isinstance(structure, CodeStructure)
        assert structure.file_path == "test.py"
        assert structure.language == "test-lang"

    def test_cannot_instantiate_abstract(self) -> None:
        with pytest.raises(TypeError):
            ASTAnalyzer()  # type: ignore[abstract]
