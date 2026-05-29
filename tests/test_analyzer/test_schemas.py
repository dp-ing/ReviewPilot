from app.analyzer.schemas import (
    ASTFinding,
    FunctionInfo,
    ClassInfo,
    CallInfo,
    CodeStructure,
    ASTResult,
)


class TestASTFinding:
    def test_basic_finding(self) -> None:
        f = ASTFinding(
            rule_id="python-exec-eval",
            severity="critical",
            category="security",
            file_path="src/main.py",
            line_start=10,
            line_end=10,
            title="Unsafe exec() call",
            description="Using exec() with user input is dangerous",
        )
        assert f.rule_id == "python-exec-eval"
        assert f.severity == "critical"
        assert f.category == "security"
        assert f.code_snippet is None

    def test_with_code_snippet(self) -> None:
        f = ASTFinding(
            rule_id="test-rule",
            severity="warning",
            category="best_practice",
            file_path="app.py",
            line_start=5,
            line_end=7,
            title="Test",
            description="Test finding",
            code_snippet="exec(user_input)\n",
        )
        assert f.code_snippet == "exec(user_input)\n"


class TestFunctionInfo:
    def test_basic_function(self) -> None:
        fn = FunctionInfo(
            name="process_data",
            line_start=10,
            line_end=25,
            args=["input_path", "options"],
            returns="bool",
            decorators=["@staticmethod"],
            complexity=5,
        )
        assert fn.name == "process_data"
        assert fn.line_start == 10
        assert fn.line_end == 25
        assert len(fn.args) == 2
        assert fn.returns == "bool"
        assert "@staticmethod" in fn.decorators
        assert fn.complexity == 5

    def test_defaults(self) -> None:
        fn = FunctionInfo(name="simple", line_start=1, line_end=3)
        assert fn.args == []
        assert fn.returns is None
        assert fn.decorators == []
        assert fn.complexity == 0


class TestClassInfo:
    def test_basic_class(self) -> None:
        cls = ClassInfo(
            name="MyService",
            line_start=5,
            line_end=50,
            bases=["BaseService"],
            decorators=["@dataclass"],
        )
        assert cls.name == "MyService"
        assert cls.line_start == 5
        assert cls.line_end == 50
        assert "BaseService" in cls.bases
        assert "@dataclass" in cls.decorators
        assert cls.methods == []

    def test_class_with_methods(self) -> None:
        method = FunctionInfo(name="do_work", line_start=10, line_end=15)
        cls = ClassInfo(
            name="Worker", line_start=1, line_end=20, methods=[method]
        )
        assert len(cls.methods) == 1
        assert cls.methods[0].name == "do_work"


class TestCallInfo:
    def test_basic_call(self) -> None:
        call = CallInfo(
            function_name="open",
            line=10,
            args=["file.txt", "r"],
            keyword_args=["encoding"],
        )
        assert call.function_name == "open"
        assert call.line == 10
        assert "file.txt" in call.args
        assert "encoding" in call.keyword_args


class TestCodeStructure:
    def test_full_structure(self) -> None:
        s = CodeStructure(
            file_path="src/main.py",
            language="python",
            imports=["os", "sys", "json"],
            functions=[
                FunctionInfo(name="main", line_start=1, line_end=10),
                FunctionInfo(name="helper", line_start=12, line_end=15),
            ],
            classes=[ClassInfo(name="App", line_start=20, line_end=50)],
            variable_assignments=["config = {}", "db = Database()"],
            exception_blocks=[(5, 8), (30, 33)],
            lines_of_code=50,
        )
        assert s.file_path == "src/main.py"
        assert s.language == "python"
        assert len(s.imports) == 3
        assert len(s.functions) == 2
        assert len(s.classes) == 1
        assert len(s.variable_assignments) == 2
        assert len(s.exception_blocks) == 2
        assert s.lines_of_code == 50

    def test_defaults(self) -> None:
        s = CodeStructure(file_path="empty.py", language="python")
        assert s.imports == []
        assert s.functions == []
        assert s.classes == []
        assert s.calls == []
        assert s.variable_assignments == []
        assert s.exception_blocks == []
        assert s.lines_of_code == 0


class TestASTResult:
    def test_successful_result(self) -> None:
        findings = [
            ASTFinding(
                rule_id="r1", severity="warning", category="security",
                file_path="app.py", line_start=1, line_end=1,
                title="Issue", description="Found an issue",
            )
        ]
        structure = CodeStructure(file_path="app.py", language="python")
        result = ASTResult(findings=findings, structure=structure, language="python")
        assert result.success is True
        assert len(result.findings) == 1
        assert result.structure is not None
        assert result.language == "python"
        assert result.error_message is None

    def test_failed_result(self) -> None:
        result = ASTResult(
            success=False,
            error_message="Syntax error at line 5",
            language="python",
        )
        assert result.success is False
        assert result.error_message == "Syntax error at line 5"
        assert result.findings == []
        assert result.structure is None
