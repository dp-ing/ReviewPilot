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
            javalang.parse.parse(source)
        except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as exc:
            return ASTResult(
                language="java",
                success=False,
                error_message=str(exc),
            )

        structure = self.extract_structure(filename, source)
        findings: list[ASTFinding] = []

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
