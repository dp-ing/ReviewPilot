import pytest

from app.analyzer.python_analyzer import PythonAnalyzer
from app.analyzer.ast_base import ASTAnalyzer


class TestPythonAnalyzerSkeleton:
    def test_is_ast_analyzer(self) -> None:
        a = PythonAnalyzer()
        assert isinstance(a, ASTAnalyzer)

    def test_get_supported_language(self) -> None:
        a = PythonAnalyzer()
        assert a.get_supported_language() == "python"

    def test_extract_structure_not_implemented(self) -> None:
        a = PythonAnalyzer()
        with pytest.raises(NotImplementedError):
            a.extract_structure("test.py", "x = 1")

    def test_analyze_file_not_implemented(self) -> None:
        a = PythonAnalyzer()
        with pytest.raises(NotImplementedError):
            a.analyze_file("test.py", "x = 1")
