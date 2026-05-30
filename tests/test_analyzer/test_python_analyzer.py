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


class TestUnsafePickleRule:
    def test_detect_pickle_loads(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "pickle.loads(data)")
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "python-unsafe-pickle"
        assert f.severity == "critical"
        assert f.category == "security"

    def test_detect_pickle_load(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "pickle.load(f)")
        assert len(result.findings) >= 1
        rule_ids = [f.rule_id for f in result.findings]
        assert "python-unsafe-pickle" in rule_ids

    def test_detect_dill_loads(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "dill.loads(data)")
        assert any(f.rule_id == "python-unsafe-pickle" for f in result.findings)

    def test_no_false_positive_on_json_loads(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "json.loads(data)")
        pickle_findings = [f for f in result.findings if f.rule_id == "python-unsafe-pickle"]
        assert len(pickle_findings) == 0

    def test_no_false_positive_on_pickle_module(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "import pickle\nx = pickle.HIGHEST_PROTOCOL")
        assert len(result.findings) == 0


class TestShellInjectionRule:
    def test_detect_os_system(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "os.system(cmd)")
        assert len(result.findings) == 1
        f = result.findings[0]
        assert f.rule_id == "python-shell-injection"
        assert f.severity == "critical"
        assert f.category == "security"

    def test_detect_os_popen(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "os.popen(cmd)")
        assert any(f.rule_id == "python-shell-injection" for f in result.findings)

    def test_detect_subprocess_call_shell_true(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "subprocess.call(cmd, shell=True)")
        assert any(f.rule_id == "python-shell-injection" for f in result.findings)

    def test_detect_subprocess_run_shell_true(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "subprocess.run(cmd, shell=True)")
        assert any(f.rule_id == "python-shell-injection" for f in result.findings)

    def test_detect_subprocess_popen_shell_true(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "subprocess.Popen(cmd, shell=True)")
        assert any(f.rule_id == "python-shell-injection" for f in result.findings)

    def test_no_alert_on_subprocess_without_shell(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "subprocess.run(['ls', '-la'])")
        findings = [f for f in result.findings if f.rule_id == "python-shell-injection"]
        assert len(findings) == 0

    def test_no_alert_on_subprocess_shell_false(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "subprocess.call(cmd, shell=False)")
        findings = [f for f in result.findings if f.rule_id == "python-shell-injection"]
        assert len(findings) == 0

    def test_no_alert_on_safe_calls(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "os.path.join('/a', 'b')\nos.getcwd()")
        findings = [f for f in result.findings if f.rule_id == "python-shell-injection"]
        assert len(findings) == 0


class TestSQLConcatRule:
    def test_detect_execute_with_string_concat(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "cursor.execute('SELECT * FROM t WHERE id=' + uid)")
        assert any(f.rule_id == "python-sql-concat" for f in result.findings)

    def test_detect_execute_with_fstring(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", 'cursor.execute(f"SELECT * FROM {table}")')
        assert any(f.rule_id == "python-sql-concat" for f in result.findings)

    def test_detect_execute_with_percent_format(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "cursor.execute('SELECT * FROM %s' % table)")
        assert any(f.rule_id == "python-sql-concat" for f in result.findings)

    def test_detect_executemany_with_concat(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "conn.executemany('INSERT INTO t VALUES(' + v + ')')")
        assert any(f.rule_id == "python-sql-concat" for f in result.findings)

    def test_no_alert_on_parameterized_query(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "cursor.execute('SELECT * FROM t WHERE id=?', (uid,))")
        findings = [f for f in result.findings if f.rule_id == "python-sql-concat"]
        assert len(findings) == 0

    def test_no_alert_on_static_query(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "cursor.execute('SELECT COUNT(*) FROM users')")
        findings = [f for f in result.findings if f.rule_id == "python-sql-concat"]
        assert len(findings) == 0

    def test_no_alert_on_safe_function(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", 'print("hello " + name)')
        findings = [f for f in result.findings if f.rule_id == "python-sql-concat"]
        assert len(findings) == 0


class TestBareExceptRule:
    def test_detect_bare_except(self) -> None:
        a = PythonAnalyzer()
        source = "try:\n    x = 1\nexcept:\n    pass\n"
        result = a.analyze_file("test.py", source)
        assert any(f.rule_id == "python-bare-except" for f in result.findings)

    def test_no_alert_on_typed_except(self) -> None:
        a = PythonAnalyzer()
        source = "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        result = a.analyze_file("test.py", source)
        findings = [f for f in result.findings if f.rule_id == "python-bare-except"]
        assert len(findings) == 0

    def test_no_alert_on_multiple_except(self) -> None:
        a = PythonAnalyzer()
        source = "try:\n    x = 1\nexcept (ValueError, TypeError):\n    pass\n"
        result = a.analyze_file("test.py", source)
        findings = [f for f in result.findings if f.rule_id == "python-bare-except"]
        assert len(findings) == 0

    def test_no_alert_on_no_try(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "x = 1\ny = 2\n")
        findings = [f for f in result.findings if f.rule_id == "python-bare-except"]
        assert len(findings) == 0


class TestHardcodedSecretRule:
    def test_detect_password(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "password = 'super_secret_123'")
        assert any(f.rule_id == "python-hardcoded-secret" for f in result.findings)

    def test_detect_api_key(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "API_KEY = 'sk-abc123def456'")
        assert any(f.rule_id == "python-hardcoded-secret" for f in result.findings)

    def test_detect_token(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "secret_token = 'my_token_value'")
        assert any(f.rule_id == "python-hardcoded-secret" for f in result.findings)

    def test_no_alert_on_env_read(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "password = os.getenv('DB_PASSWORD')")
        findings = [f for f in result.findings if f.rule_id == "python-hardcoded-secret"]
        assert len(findings) == 0

    def test_no_alert_on_test_value(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "password = 'test_password'")
        findings = [f for f in result.findings if f.rule_id == "python-hardcoded-secret"]
        assert len(findings) == 0

    def test_no_alert_on_empty_string(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "password = ''")
        findings = [f for f in result.findings if f.rule_id == "python-hardcoded-secret"]
        assert len(findings) == 0

    def test_no_alert_on_normal_variable(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "username = 'alice'")
        findings = [f for f in result.findings if f.rule_id == "python-hardcoded-secret"]
        assert len(findings) == 0


class TestFileLeakRule:
    def test_detect_open_without_with(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", "f = open('data.txt')\ndata = f.read()")
        assert any(f.rule_id == "python-file-leak" for f in result.findings)

    def test_no_alert_on_with_open(self) -> None:
        a = PythonAnalyzer()
        source = "with open('data.txt') as f:\n    data = f.read()\n"
        result = a.analyze_file("test.py", source)
        findings = [f for f in result.findings if f.rule_id == "python-file-leak"]
        assert len(findings) == 0

    def test_no_alert_on_with_open_multiline(self) -> None:
        a = PythonAnalyzer()
        source = "with open('a.txt') as fa, open('b.txt') as fb:\n    pass\n"
        result = a.analyze_file("test.py", source)
        findings = [f for f in result.findings if f.rule_id == "python-file-leak"]
        assert len(findings) == 0

    def test_no_alert_on_other_call(self) -> None:
        a = PythonAnalyzer()
        result = a.analyze_file("test.py", 'print("hello")')
        findings = [f for f in result.findings if f.rule_id == "python-file-leak"]
        assert len(findings) == 0
