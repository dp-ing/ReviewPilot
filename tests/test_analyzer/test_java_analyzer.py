from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.java_analyzer import JavaAnalyzer
from app.analyzer.schemas import ASTResult, CodeStructure


class TestJavaAnalyzer:
    def test_is_ast_analyzer(self) -> None:
        a = JavaAnalyzer()
        assert isinstance(a, ASTAnalyzer)

    def test_get_supported_language(self) -> None:
        a = JavaAnalyzer()
        assert a.get_supported_language() == "java"

    def test_extract_structure_returns_code_structure(self) -> None:
        a = JavaAnalyzer()
        result = a.extract_structure("Test.java", "public class Test {}")
        assert isinstance(result, CodeStructure)
        assert result.file_path == "Test.java"
        assert result.language == "java"

    def test_extract_structure_imports(self) -> None:
        a = JavaAnalyzer()
        source = "import java.util.List;\nimport java.io.File;\npublic class Test {}"
        result = a.extract_structure("Test.java", source)
        assert "java.util.List" in result.imports
        assert "java.io.File" in result.imports

    def test_extract_structure_class(self) -> None:
        a = JavaAnalyzer()
        source = "public class MyClass {\n    public void method() {}\n}"
        result = a.extract_structure("MyClass.java", source)
        assert len(result.classes) == 1
        assert result.classes[0].name == "MyClass"

    def test_extract_structure_class_with_inheritance(self) -> None:
        a = JavaAnalyzer()
        source = "public class Child extends Parent implements Serializable {}"
        result = a.extract_structure("Child.java", source)
        assert len(result.classes) == 1
        assert "Parent" in result.classes[0].bases
        assert "Serializable" in result.classes[0].bases

    def test_extract_structure_methods(self) -> None:
        a = JavaAnalyzer()
        source = "public class App {\n    public String getName() { return \"test\"; }\n}"
        result = a.extract_structure("App.java", source)
        assert len(result.functions) == 1
        assert result.functions[0].name == "getName"
        assert result.functions[0].returns == "String"

    def test_extract_structure_calls(self) -> None:
        a = JavaAnalyzer()
        source = "public class App {\n    public void run() {\n        System.out.println(\"hello\");\n    }\n}"
        result = a.extract_structure("App.java", source)
        call_names = [c.function_name for c in result.calls]
        assert "println" in call_names

    def test_extract_structure_lines_of_code(self) -> None:
        a = JavaAnalyzer()
        source = "// line1\n// line2\n// line3\npublic class App {}"
        result = a.extract_structure("App.java", source)
        assert result.lines_of_code == 4

    def test_extract_structure_empty_file(self) -> None:
        a = JavaAnalyzer()
        result = a.extract_structure("Empty.java", "")
        assert result.language == "java"
        assert result.imports == []
        assert result.classes == []

    def test_analyze_file_returns_ast_result(self) -> None:
        a = JavaAnalyzer()
        result = a.analyze_file("Test.java", "public class Test {}")
        assert isinstance(result, ASTResult)
        assert result.language == "java"
        assert result.success is True
        assert result.structure is not None

    def test_analyze_file_with_syntax_error(self) -> None:
        a = JavaAnalyzer()
        result = a.analyze_file("Bad.java", "this is not valid java @@@")
        assert result.success is False
        assert result.error_message is not None


class TestJavaCommandInjectionRule:
    def test_detect_runtime_exec(self) -> None:
        a = JavaAnalyzer()
        source = "public class App {\n    public void run() {\n        Runtime.getRuntime().exec(\"ls\");\n    }\n}"
        result = a.analyze_file("App.java", source)
        assert any(f.rule_id == "java-command-injection" for f in result.findings)

    def test_no_alert_on_safe_call(self) -> None:
        a = JavaAnalyzer()
        source = "public class App {\n    public void run() {\n        System.out.println(\"hello\");\n    }\n}"
        result = a.analyze_file("App.java", source)
        findings = [f for f in result.findings if f.rule_id == "java-command-injection"]
        assert len(findings) == 0


class TestJavaUnsafeDeserialRule:
    def test_detect_read_object(self) -> None:
        a = JavaAnalyzer()
        source = (
            "import java.io.ObjectInputStream;\n"
            "public class App {\n"
            "    public void load() throws Exception {\n"
            "        ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());\n"
            "        ois.readObject();\n"
            "    }\n"
            "}"
        )
        result = a.analyze_file("App.java", source)
        assert any(f.rule_id == "java-unsafe-deserial" for f in result.findings)

    def test_detect_read_unshared(self) -> None:
        a = JavaAnalyzer()
        source = (
            "import java.io.ObjectInputStream;\n"
            "public class App {\n"
            "    public void load() throws Exception {\n"
            "        ObjectInputStream ois = new ObjectInputStream(socket.getInputStream());\n"
            "        ois.readUnshared();\n"
            "    }\n"
            "}"
        )
        result = a.analyze_file("App.java", source)
        assert any(f.rule_id == "java-unsafe-deserial" for f in result.findings)

    def test_no_alert_on_safe_call(self) -> None:
        a = JavaAnalyzer()
        source = (
            "import java.io.FileInputStream;\n"
            "public class App {\n"
            "    public void run() {\n"
            "        FileInputStream fis = new FileInputStream(\"data.txt\");\n"
            "        int b = fis.read();\n"
            "    }\n"
            "}"
        )
        result = a.analyze_file("App.java", source)
        findings = [f for f in result.findings if f.rule_id == "java-unsafe-deserial"]
        assert len(findings) == 0
