from app.analyzer.python_analyzer import PythonAnalyzer
from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import ASTResult, CodeStructure


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

    def test_extract_structure_calls(self) -> None:
        a = PythonAnalyzer()
        source = "print('hello')\nlen([1, 2, 3])\n"
        result = a.extract_structure("test.py", source)
        names = [c.function_name for c in result.calls]
        assert "print" in names
        assert "len" in names

    def test_extract_structure_calls_with_args_and_kwargs(self) -> None:
        a = PythonAnalyzer()
        source = "json.dumps(obj, indent=2)\n"
        result = a.extract_structure("test.py", source)
        assert len(result.calls) == 1
        assert result.calls[0].function_name == "json.dumps"
        assert "obj" in result.calls[0].args
        assert "indent" in result.calls[0].keyword_args

    def test_extract_structure_variable_assignments(self) -> None:
        a = PythonAnalyzer()
        source = "x = 1\ny = 2\nself.name = 'test'\n"
        result = a.extract_structure("test.py", source)
        assert "x" in result.variable_assignments
        assert "y" in result.variable_assignments
        assert "self.name" in result.variable_assignments

    def test_extract_structure_exception_blocks(self) -> None:
        a = PythonAnalyzer()
        source = "try:\n    x = 1\nexcept ValueError:\n    pass\nexcept KeyError:\n    pass\n"
        result = a.extract_structure("test.py", source)
        assert len(result.exception_blocks) == 2

    def test_extract_structure_function_decorators(self) -> None:
        a = PythonAnalyzer()
        source = (
            "@staticmethod\n"
            "@auth.require('admin')\n"
            "def admin_only():\n"
            "    pass\n"
        )
        result = a.extract_structure("test.py", source)
        assert len(result.functions) == 1
        assert "@staticmethod" in result.functions[0].decorators
        assert any("@auth.require" in d for d in result.functions[0].decorators)

    def test_extract_structure_function_return_type(self) -> None:
        a = PythonAnalyzer()
        source = "def add(a: int, b: int) -> int:\n    return a + b\n"
        result = a.extract_structure("test.py", source)
        assert result.functions[0].returns == "int"

    def test_extract_structure_async_function(self) -> None:
        a = PythonAnalyzer()
        source = "async def fetch(url):\n    return await http.get(url)\n"
        result = a.extract_structure("test.py", source)
        assert len(result.functions) == 1
        assert result.functions[0].name == "fetch"

    def test_extract_structure_class_with_bases(self) -> None:
        a = PythonAnalyzer()
        source = "class Child(Parent, Mixin):\n    pass\n"
        result = a.extract_structure("test.py", source)
        assert len(result.classes) == 1
        assert "Parent" in result.classes[0].bases
        assert "Mixin" in result.classes[0].bases

    def test_extract_structure_class_decorators(self) -> None:
        a = PythonAnalyzer()
        source = "@dataclass\nclass Point:\n    x: int\n    y: int\n"
        result = a.extract_structure("test.py", source)
        assert len(result.classes) == 1
        assert "@dataclass" in result.classes[0].decorators

    def test_extract_structure_lines_of_code(self) -> None:
        a = PythonAnalyzer()
        source = "a = 1\nb = 2\nc = 3\n"
        result = a.extract_structure("test.py", source)
        assert result.lines_of_code == 3

    def test_extract_structure_complexity(self) -> None:
        a = PythonAnalyzer()
        source = (
            "def complex_fn(x):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2:\n"
            "                return i\n"
            "    return 0\n"
        )
        result = a.extract_structure("test.py", source)
        assert result.functions[0].complexity >= 4  # base + if + for + if

    def test_extract_structure_mixed_async_and_sync(self) -> None:
        a = PythonAnalyzer()
        source = (
            "def sync_fn():\n"
            "    pass\n"
            "async def async_fn():\n"
            "    pass\n"
        )
        result = a.extract_structure("test.py", source)
        assert len(result.functions) == 2

    def test_extract_structure_nested_classes_and_functions(self) -> None:
        a = PythonAnalyzer()
        source = (
            "class Outer:\n"
            "    def method(self):\n"
            "        def inner():\n"
            "            pass\n"
            "        return inner\n"
            "    class Inner:\n"
            "        pass\n"
        )
        result = a.extract_structure("test.py", source)
        assert len(result.classes) >= 1
        class_names = [c.name for c in result.classes]
        assert "Outer" in class_names

    def test_extract_structure_lambda_is_not_function(self) -> None:
        a = PythonAnalyzer()
        source = "f = lambda x: x * 2\n"
        result = a.extract_structure("test.py", source)
        assert len(result.functions) == 0

    def test_extract_structure_module_docstring(self) -> None:
        a = PythonAnalyzer()
        source = '"""Module docstring."""\n\nx = 1\n'
        result = a.extract_structure("test.py", source)
        assert result.lines_of_code == 3

    def test_extract_structure_no_exception_blocks(self) -> None:
        a = PythonAnalyzer()
        source = "x = 1\n"
        result = a.extract_structure("test.py", source)
        assert result.exception_blocks == []


class TestExecEvalRule:
    def test_detect_exec_call(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "exec(code)")
        assert result.success
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "python-exec-eval"
        assert f.severity == "critical"
        assert f.category == "security"
        assert f.file_path == "test.py"

    def test_detect_eval_call(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "eval(user_input)")
        assert len(result.findings) == 1
        assert result.findings[0].rule_id == "python-exec-eval"

    def test_detect_both_exec_and_eval(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "exec(x)\neval(y)")
        assert len(result.findings) == 2

    def test_detect_exec_inside_function(self) -> None:
        a = PythonAnalyzer()
        source = "def f():\n    exec(data)\n"
        result = a.analyze_file("test.py", source)
        assert len(result.findings) == 1

    def test_no_false_positive_on_safe_calls(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "print('hello')\nlen([1,2])\nint('42')")
        assert len(result.findings) == 0

    def test_no_false_positive_on_attributed_exec(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "os.exec('ls')")
        assert len(result.findings) == 0

    def test_analyze_file_returns_ast_result(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "x = 1")
        assert isinstance(result, ASTResult)
        assert result.language == "python"
        assert result.success is True
        assert result.structure is not None

    def test_analyze_file_with_syntax_error(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "def broken(")
        assert result.success is False
        assert result.error_message is not None
