import pytest

from app.analyzer.python_analyzer import PythonAnalyzer
from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import CodeStructure


class TestPythonAnalyzer:
    def test_is_ast_analyzer(self) -> None:
        a = PythonAnalyzer()
        assert isinstance(a, ASTAnalyzer)

    def test_get_supported_language(self) -> None:
        a = PythonAnalyzer()
        assert a.get_supported_language() == "python"

    def test_extract_structure_returns_code_structure(self) -> None:
        a = PythonAnalyzer()
        result = a.extract_structure("test.py", "x = 1")
        assert isinstance(result, CodeStructure)
        assert result.file_path == "test.py"
        assert result.language == "python"

    def test_extract_structure_imports(self) -> None:
        a = PythonAnalyzer()
        result = a.extract_structure("test.py", "import os\nfrom sys import path\nx = 1")
        assert "os" in result.imports
        assert "sys.path" in result.imports

    def test_extract_structure_functions(self) -> None:
        a = PythonAnalyzer()
        source = "def hello(name):\n    return f'Hi {name}'\n"
        result = a.extract_structure("test.py", source)
        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"
        assert result.functions[0].args == ["name"]

    def test_extract_structure_classes(self) -> None:
        a = PythonAnalyzer()
        source = "class MyClass:\n    def method(self):\n        pass\n"
        result = a.extract_structure("test.py", source)
        assert len(result.classes) == 1
        assert result.classes[0].name == "MyClass"

    def test_extract_empty_file(self) -> None:
        a = PythonAnalyzer()
        result = a.extract_structure("empty.py", "")
        assert result.imports == []
        assert result.functions == []
        assert result.classes == []

    def test_analyze_file_not_implemented(self) -> None:
        a = PythonAnalyzer()
        with pytest.raises(NotImplementedError):
            a.analyze_file("test.py", "x = 1")
