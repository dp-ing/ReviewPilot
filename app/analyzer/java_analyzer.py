from typing import Any, Tuple

import javalang  # type: ignore[import-untyped]

from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import (
    ASTFinding,
    ASTResult,
    CallInfo,
    ClassInfo,
    CodeStructure,
    FunctionInfo,
)


class JavaAnalyzer(ASTAnalyzer):
    """AST analyzer for Java source code."""

    def get_supported_language(self) -> str:
        return "java"

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        try:
            tree = javalang.parse.parse(source)
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError):
            return CodeStructure(file_path=filename, language="java")

        imports: list[str] = []
        classes: list[ClassInfo] = []
        methods: list[FunctionInfo] = []
        calls: list[CallInfo] = []

        for _, node in tree:
            if isinstance(node, javalang.tree.Import):
                imports.append(node.path)

        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                class_methods: list[FunctionInfo] = []
                if node.body:
                    for member in node.body:
                        if isinstance(member, javalang.tree.MethodDeclaration):
                            class_methods.append(self._to_function_info(member))
                            methods.append(class_methods[-1])
                        elif isinstance(member, javalang.tree.ConstructorDeclaration):
                            class_methods.append(self._constructor_to_function_info(member))
                            methods.append(class_methods[-1])

                bases: list[str] = []
                if node.extends:
                    bases.append(node.extends.name)
                if node.implements:
                    for iface in node.implements:
                        bases.append(iface.name)

                line_no = node.position.line if node.position else 1
                classes.append(
                    ClassInfo(
                        name=node.name,
                        line_start=line_no,
                        line_end=line_no,
                        bases=bases,
                        methods=class_methods,
                    )
                )

            if isinstance(node, javalang.tree.MethodDeclaration):
                # Methods already extracted via class visitor above
                pass

        for _, node in tree:
            if isinstance(node, javalang.tree.MethodInvocation):
                args = [str(a.value) if hasattr(a, 'value') else str(a) for a in node.arguments]
                line_no = node.position.line if node.position else 1
                calls.append(
                    CallInfo(
                        function_name=node.member,
                        line=line_no,
                        args=args,
                    )
                )

        lines = source.splitlines()

        return CodeStructure(
            file_path=filename,
            language="java",
            imports=imports,
            classes=classes,
            functions=methods,
            calls=calls,
            lines_of_code=len(lines),
        )

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        try:
            tree = javalang.parse.parse(source)
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as exc:
            return ASTResult(
                language="java",
                success=False,
                error_message=str(exc),
            )

        structure = self.extract_structure(filename, source)
        findings: list[ASTFinding] = []

        tree_nodes = list(tree)
        findings.extend(_JavaCommandInjectionDetector(filename).run(tree_nodes))
        findings.extend(_JavaUnsafeDeserialDetector(filename).run(tree_nodes))
        findings.extend(_JavaSQLConcatDetector(filename).run(tree_nodes))
        findings.extend(_JavaResourceLeakDetector(filename).run(tree_nodes))
        findings.extend(_JavaHardcodedSecretDetector(filename).run(tree_nodes))
        findings.extend(_JavaComplexityDetector(filename).run(tree_nodes))

        return ASTResult(
            language="java",
            success=True,
            findings=findings,
            structure=structure,
        )

    @staticmethod
    def _to_function_info(node: javalang.tree.MethodDeclaration) -> FunctionInfo:
        line_no = node.position.line if node.position else 1
        args = [p.name for p in node.parameters] if node.parameters else []
        return_type = node.return_type.name if node.return_type and hasattr(node.return_type, 'name') else None
        annotations = [f"@{a.name}" for a in node.annotations] if node.annotations else []
        return FunctionInfo(
            name=node.name,
            line_start=line_no,
            line_end=line_no,
            args=args,
            returns=return_type,
            decorators=annotations,
            complexity=1,
        )

    @staticmethod
    def _constructor_to_function_info(node: javalang.tree.ConstructorDeclaration) -> FunctionInfo:
        line_no = node.position.line if node.position else 1
        args = [p.name for p in node.parameters] if node.parameters else []
        return FunctionInfo(
            name=node.name,
            line_start=line_no,
            line_end=line_no,
            args=args,
            decorators=[],
            complexity=1,
        )


class _JavaCommandInjectionDetector:
    """Detect Runtime.exec() calls — rule java-command-injection."""

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []
        for path, node in nodes:
            if isinstance(node, javalang.tree.MethodInvocation) and node.member == "exec":
                findings.append(
                    ASTFinding(
                        rule_id="java-command-injection",
                        severity="critical",
                        category="security",
                        file_path=self.filename,
                        line_start=node.position.line if node.position else 1,
                        line_end=node.position.line if node.position else 1,
                        title="Runtime.exec() command injection risk",
                        description=(
                            "Using Runtime.exec() with untrusted input can lead to "
                            "command injection. Use ProcessBuilder with a list of "
                            "arguments instead of passing a command string."
                        ),
                    )
                )
        return findings


class _JavaUnsafeDeserialDetector:
    """Detect ObjectInputStream.readObject() / readUnshared() — rule java-unsafe-deserial."""

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []
        unsafe_methods = {"readObject", "readUnshared"}
        for _path, node in nodes:
            if isinstance(node, javalang.tree.MethodInvocation) and node.member in unsafe_methods:
                findings.append(
                    ASTFinding(
                        rule_id="java-unsafe-deserial",
                        severity="critical",
                        category="security",
                        file_path=self.filename,
                        line_start=node.position.line if node.position else 1,
                        line_end=node.position.line if node.position else 1,
                        title="Unsafe deserialization via ObjectInputStream",
                        description=(
                            "Deserializing untrusted data with ObjectInputStream can lead "
                            "to remote code execution. Validate or filter input before "
                            "deserialization, or use a type-checking ObjectInputFilter."
                        ),
                    )
                )
        return findings


class _JavaSQLConcatDetector:
    """Detect SQL string concatenation — rule java-sql-concat."""

    _SQL_METHODS = {"executeQuery", "executeUpdate", "execute", "addBatch"}

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []
        for _path, node in nodes:
            if isinstance(node, javalang.tree.MethodInvocation) and node.member in self._SQL_METHODS:
                if self._has_string_concat(node):
                    findings.append(
                        ASTFinding(
                            rule_id="java-sql-concat",
                            severity="warning",
                            category="security",
                            file_path=self.filename,
                            line_start=node.position.line if node.position else 1,
                            line_end=node.position.line if node.position else 1,
                            title="SQL string concatenation may cause SQL injection",
                            description=(
                                "Building SQL queries via string concatenation can "
                                "lead to SQL injection. Use PreparedStatement with "
                                "parameterized queries instead."
                            ),
                        )
                    )
        return findings

    def _has_string_concat(self, node: Any) -> bool:
        for arg in node.arguments:
            for _, child in arg:
                if isinstance(child, javalang.tree.BinaryOperation) and child.operator == "+":
                    return True
        return False


class _JavaResourceLeakDetector:
    """Detect resource creation without try-with-resources — rule java-resource-leak."""

    _RESOURCE_TYPES = {
        "FileInputStream", "FileOutputStream", "FileReader", "FileWriter",
        "BufferedReader", "BufferedWriter", "InputStreamReader",
        "OutputStreamWriter", "PrintWriter", "PrintStream",
        "Socket", "ServerSocket",
    }

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []
        for path, node in nodes:
            if isinstance(node, javalang.tree.ClassCreator) and node.type:
                type_name = node.type.name
                if type_name in self._RESOURCE_TYPES and not self._in_try_resource(path):
                    findings.append(
                        ASTFinding(
                            rule_id="java-resource-leak",
                            severity="warning",
                            category="best_practice",
                            file_path=self.filename,
                            line_start=node.position.line if node.position else 1,
                            line_end=node.position.line if node.position else 1,
                            title="Resource opened without try-with-resources",
                            description=(
                                "Opening a resource outside of try-with-resources "
                                "may lead to resource leaks. Use try-with-resources "
                                "to ensure the resource is properly closed."
                            ),
                        )
                    )
        return findings

    @staticmethod
    def _in_try_resource(path: Tuple[Any, ...]) -> bool:
        for p in path:
            if isinstance(p, javalang.tree.TryResource):
                return True
        return False


class _JavaHardcodedSecretDetector:
    """Detect hardcoded secrets in variable assignments — rule java-hardcoded-secret."""

    _SECRET_PATTERNS = [
        "password", "passwd", "pwd", "secret", "api_key", "apikey",
        "api_token", "apitoken", "token", "access_key", "accesskey",
        "private_key", "privatekey", "credential",
    ]

    _TEST_VALUES = {"", "test", "password", "secret", "changeme", "null", "example"}

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []
        for _path, node in nodes:
            if isinstance(node, javalang.tree.VariableDeclarator):
                name_lower = node.name.lower()
                if self._matches_secret_pattern(name_lower) and node.initializer:
                    if isinstance(node.initializer, javalang.tree.Literal):
                        value = str(node.initializer.value).strip('"').strip("'")
                        if value.lower() not in self._TEST_VALUES and len(value) > 1:
                            findings.append(
                                ASTFinding(
                                    rule_id="java-hardcoded-secret",
                                    severity="warning",
                                    category="security",
                                    file_path=self.filename,
                                    line_start=node.position.line if node.position else 1,
                                    line_end=node.position.line if node.position else 1,
                                    title=f"Hardcoded secret in variable '{node.name}'",
                                    description=(
                                        f"Variable '{node.name}' appears to contain a "
                                        "hardcoded secret. Use environment variables or "
                                        "a secrets manager instead."
                                    ),
                                )
                            )
        return findings

    @classmethod
    def _matches_secret_pattern(cls, name: str) -> bool:
        for pattern in cls._SECRET_PATTERNS:
            if pattern in name:
                return True
        return False


class _JavaComplexityDetector:
    """Flag Java methods with high cyclomatic complexity — rule java-complexity."""

    _THRESHOLD = 10

    _DECISION_TYPES = (
        javalang.tree.IfStatement,
        javalang.tree.ForStatement,
        javalang.tree.WhileStatement,
        javalang.tree.DoStatement,
        javalang.tree.SwitchStatementCase,
        javalang.tree.CatchClause,
        javalang.tree.TernaryExpression,
    )

    def __init__(self, filename: str) -> None:
        self.filename = filename

    def run(self, nodes: list[Tuple[Any, Any]]) -> list[ASTFinding]:
        findings: list[ASTFinding] = []

        for path, node in nodes:
            if isinstance(node, (javalang.tree.MethodDeclaration, javalang.tree.ConstructorDeclaration)):
                complexity = self._compute_complexity(nodes, node)
                if complexity > self._THRESHOLD:
                    findings.append(
                        ASTFinding(
                            rule_id="java-complexity",
                            severity="warning",
                            category="style",
                            file_path=self.filename,
                            line_start=node.position.line if node.position else 1,
                            line_end=node.position.line if node.position else 1,
                            title=f"High cyclomatic complexity ({complexity}) in method '{node.name}'",
                            description=(
                                f"Method '{node.name}' has a cyclomatic complexity "
                                f"of {complexity} (threshold: {self._THRESHOLD}). "
                                "Consider refactoring into smaller methods."
                            ),
                        )
                    )
        return findings

    def _compute_complexity(
        self, nodes: list[Tuple[Any, Any]], method_node: Any
    ) -> int:
        count = 1
        for path, node in nodes:
            if isinstance(node, self._DECISION_TYPES):
                if self._in_subtree(path, method_node):
                    count += 1
            elif isinstance(node, javalang.tree.BinaryOperation):
                if node.operator in ("&&", "||") and self._in_subtree(path, method_node):
                    count += 1
        return count

    @staticmethod
    def _in_subtree(path: Tuple[Any, ...], method_node: Any) -> bool:
        for p in path:
            if p is method_node:
                return True
        return False
