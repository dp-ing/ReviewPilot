from __future__ import annotations

import ast

from app.analyzer.ast_base import ASTAnalyzer
from app.analyzer.schemas import (
    ASTFinding,
    ASTResult,
    CallInfo,
    ClassInfo,
    CodeStructure,
    FunctionInfo,
)


class PythonAnalyzer(ASTAnalyzer):
    """AST analyzer for Python source code."""

    def get_supported_language(self) -> str:
        return "python"

    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        tree = ast.parse(source, filename=filename)

        structure = CodeStructure(
            file_path=filename,
            language="python",
            lines_of_code=len(source.splitlines()),
        )

        extractor = _StructureExtractor(source)
        extractor.visit(tree)

        structure.imports = extractor.imports
        structure.functions = extractor.functions
        structure.classes = extractor.classes
        structure.calls = extractor.calls
        structure.variable_assignments = extractor.variable_assignments
        structure.exception_blocks = extractor.exception_blocks

        return structure

    def analyze_file(self, filename: str, source: str) -> ASTResult:
        try:
            tree = ast.parse(source, filename=filename)
        except SyntaxError as exc:
            return ASTResult(
                language="python",
                success=False,
                error_message=str(exc),
            )

        structure = self.extract_structure(filename, source)

        findings: list[ASTFinding] = []
        findings.extend(_ExecEvalDetector(filename).run(tree))

        return ASTResult(
            language="python",
            success=True,
            findings=findings,
            structure=structure,
        )


class _StructureExtractor(ast.NodeVisitor):
    """Visitor that extracts code structure from a Python AST."""

    def __init__(self, source: str) -> None:
        self.source_lines = source.splitlines()
        self.imports: list[str] = []
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.calls: list[CallInfo] = []
        self.variable_assignments: list[str] = []
        self.exception_blocks: list[tuple[int, int]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = [arg.arg for arg in node.args.args]
        returns = None
        if node.returns and isinstance(node.returns, ast.Name):
            returns = node.returns.id
        decorators = [self._decorator_name(d) for d in node.decorator_list]
        complexity = self._compute_complexity(node)

        fn = FunctionInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            args=args,
            returns=returns,
            decorators=decorators,
            complexity=complexity,
        )
        self.functions.append(fn)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [self._base_name(b) for b in node.bases]
        decorators = [self._decorator_name(d) for d in node.decorator_list]

        cls = ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            bases=bases,
            decorators=decorators,
        )
        self.classes.append(cls)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_name(node.func)
        args_list = [self._arg_repr(a) for a in node.args]
        kw_list = [kw.arg or "" for kw in node.keywords if kw.arg]

        self.calls.append(
            CallInfo(function_name=name, line=node.lineno, args=args_list, keyword_args=kw_list)
        )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_assignments.append(target.id)
            elif isinstance(target, ast.Attribute):
                self.variable_assignments.append(ast.unparse(target))
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            if hasattr(handler, "lineno") and hasattr(handler, "end_lineno"):
                self.exception_blocks.append(
                    (handler.lineno, handler.end_lineno or handler.lineno)
                )
        self.generic_visit(node)

    def _decorator_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return f"@{node.id}"
        if isinstance(node, ast.Attribute):
            return f"@{ast.unparse(node)}"
        return f"@{ast.unparse(node)}"

    def _base_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    def _call_name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    def _arg_repr(self, node: ast.expr) -> str:
        if isinstance(node, ast.Constant):
            return repr(node.value)
        return ast.unparse(node)

    def _compute_complexity(self, node: ast.FunctionDef) -> int:
        """Compute cyclomatic complexity (1 + branching points)."""
        counter = _ComplexityCounter()
        counter.visit(node)
        return counter.count


class _ComplexityCounter(ast.NodeVisitor):
    """Count branching nodes for cyclomatic complexity."""

    def __init__(self) -> None:
        self.count = 1  # base complexity

    def visit_If(self, node: ast.If) -> None:
        self.count += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.count += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.count += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.count += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.count += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # and / or add complexity for each extra operand beyond the first
        self.count += len(node.values) - 1
        self.generic_visit(node)


class _ExecEvalDetector(ast.NodeVisitor):
    """Detect exec() and eval() calls — rule python-exec-eval."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[ASTFinding] = []

    def run(self, tree: ast.AST) -> list[ASTFinding]:
        self.visit(tree)
        return self.findings

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name_helper(node.func)
        if name in ("exec", "eval"):
            self.findings.append(
                ASTFinding(
                    rule_id="python-exec-eval",
                    severity="critical",
                    category="security",
                    file_path=self.filename,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    title=f"Detected {name}() call",
                    description=f"Use of {name}() can execute arbitrary code and may lead to code injection vulnerabilities. Avoid using {name}() with untrusted input.",
                )
            )
        self.generic_visit(node)


def _call_name_helper(node: ast.expr) -> str:
    """Extract the name of a callable expression."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return ast.unparse(node)
    return ast.unparse(node)
