from __future__ import annotations

from app.analyzer.schemas import ASTFinding
from app.engine.post_processor import PostProcessor
from app.engine.schemas import EngineFinding


def _make_finding(
    rule_id: str = "R001",
    severity: str = "warning",
    category: str = "security",
    file_path: str = "main.py",
    line_start: int = 1,
    line_end: int = 5,
    confidence: float = 0.9,
    source: str = "ai",
) -> EngineFinding:
    return EngineFinding(
        rule_id=rule_id,
        severity=severity,
        category=category,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        title="Test",
        description="Test finding",
        confidence=confidence,
        source=source,
    )


class TestAstToEngine:
    def test_converts_ast_finding(self) -> None:
        ast = ASTFinding(
            rule_id="SEC001",
            severity="critical",
            category="security",
            file_path="a.py",
            line_start=1,
            line_end=3,
            title="SQL Injection",
            description="Unsafe SQL concat",
            code_snippet="x = 'SELECT * FROM ' + t",
        )
        ef = PostProcessor.ast_to_engine(ast)
        assert isinstance(ef, EngineFinding)
        assert ef.rule_id == "SEC001"
        assert ef.source == "ast"
        assert ef.confidence == 1.0
        assert ef.suggestion == "x = 'SELECT * FROM ' + t"

    def test_ast_confidence_can_be_customized(self) -> None:
        ast = ASTFinding(
            rule_id="X",
            severity="warning",
            category="style",
            file_path="b.py",
            line_start=1,
            line_end=1,
            title="T",
            description="D",
        )
        ef = PostProcessor.ast_to_engine(ast, confidence=0.85)
        assert ef.confidence == 0.85


class TestDedup:
    def test_identical_findings_keep_higher_confidence(self) -> None:
        f1 = _make_finding(rule_id="R1", confidence=0.7)
        f2 = _make_finding(rule_id="R1", confidence=0.9)
        result = PostProcessor._deduplicate([f1, f2])
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_different_rule_ids_kept(self) -> None:
        f1 = _make_finding(rule_id="R1")
        f2 = _make_finding(rule_id="R2")
        result = PostProcessor._deduplicate([f1, f2])
        assert len(result) == 2

    def test_different_files_kept(self) -> None:
        f1 = _make_finding(rule_id="R1", file_path="a.py")
        f2 = _make_finding(rule_id="R1", file_path="b.py")
        result = PostProcessor._deduplicate([f1, f2])
        assert len(result) == 2

    def test_non_overlapping_lines_kept(self) -> None:
        f1 = _make_finding(rule_id="R1", line_start=1, line_end=2)
        f2 = _make_finding(rule_id="R1", line_start=10, line_end=20)
        result = PostProcessor._deduplicate([f1, f2])
        assert len(result) == 2

    def test_overlapping_lines_deduped(self) -> None:
        f1 = _make_finding(rule_id="R1", line_start=1, line_end=5)
        f2 = _make_finding(rule_id="R1", line_start=3, line_end=7)
        result = PostProcessor._deduplicate([f1, f2])
        assert len(result) == 1

    def test_empty_findings(self) -> None:
        result = PostProcessor._deduplicate([])
        assert result == []


class TestConfidenceFilter:
    def test_critical_min_confidence(self) -> None:
        good = _make_finding(severity="critical", confidence=0.6)
        bad = _make_finding(severity="critical", confidence=0.59)
        result = PostProcessor._filter_by_confidence([good, bad])
        assert len(result) == 1
        assert result[0].confidence == 0.6

    def test_warning_min_confidence(self) -> None:
        good = _make_finding(severity="warning", confidence=0.8)
        bad = _make_finding(severity="warning", confidence=0.79)
        result = PostProcessor._filter_by_confidence([good, bad])
        assert len(result) == 1
        assert result[0].confidence == 0.8

    def test_suggestion_min_confidence(self) -> None:
        good = _make_finding(severity="suggestion", confidence=0.9)
        bad = _make_finding(severity="suggestion", confidence=0.89)
        result = PostProcessor._filter_by_confidence([good, bad])
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_mixed_severities(self) -> None:
        findings = [
            _make_finding(rule_id="R1", severity="critical", confidence=0.6),
            _make_finding(rule_id="R2", severity="warning", confidence=0.5),
            _make_finding(rule_id="R3", severity="suggestion", confidence=0.95),
            _make_finding(rule_id="R4", severity="suggestion", confidence=0.5),
        ]
        result = PostProcessor._filter_by_confidence(findings)
        assert len(result) == 2
        assert {f.rule_id for f in result} == {"R1", "R3"}


class TestIgnoreRules:
    def test_ignore_rule_id(self) -> None:
        pp = PostProcessor(ignore_rule_ids=["SKIPME"])
        f = _make_finding(rule_id="SKIPME")
        result = pp._apply_ignore_rules([f])
        assert result == []

    def test_ignore_pattern(self) -> None:
        pp = PostProcessor(ignore_patterns=["test_", "_mock"])
        f = _make_finding(file_path="test_main.py")
        result = pp._apply_ignore_rules([f])
        assert result == []

    def test_ignore_pattern_partial_match(self) -> None:
        pp = PostProcessor(ignore_patterns=["/migrations/"])
        f1 = _make_finding(file_path="app/migrations/0001.py")
        f2 = _make_finding(file_path="app/models.py")
        result = pp._apply_ignore_rules([f1, f2])
        assert len(result) == 1
        assert result[0].file_path == "app/models.py"


class TestCategoryFilter:
    def test_enabled_categories_filters_disabled(self) -> None:
        pp = PostProcessor(enabled_categories=["security"])
        f1 = _make_finding(category="security")
        f2 = _make_finding(category="style")
        result = pp._filter_categories([f1, f2])
        assert len(result) == 1
        assert result[0].category == "security"

    def test_none_categories_keeps_all(self) -> None:
        pp = PostProcessor(enabled_categories=None)
        f1 = _make_finding(category="security")
        f2 = _make_finding(category="style")
        result = pp._filter_categories([f1, f2])
        assert len(result) == 2


class TestSort:
    def test_sort_by_severity_then_confidence(self) -> None:
        findings = [
            _make_finding(rule_id="R1", severity="suggestion", confidence=0.95),
            _make_finding(rule_id="R2", severity="critical", confidence=0.5),
            _make_finding(rule_id="R3", severity="warning", confidence=0.9),
            _make_finding(rule_id="R4", severity="critical", confidence=0.9),
        ]
        result = PostProcessor._sort(findings)
        assert result[0].rule_id == "R4"  # critical, conf 0.9
        assert result[1].rule_id == "R2"  # critical, conf 0.5
        assert result[2].rule_id == "R3"  # warning, conf 0.9
        assert result[3].rule_id == "R1"  # suggestion, conf 0.95


class TestPipeline:
    def test_full_pipeline(self) -> None:
        pp = PostProcessor(
            ignore_rule_ids=["IGNORE"],
            ignore_patterns=["/vendor/"],
            enabled_categories=["security", "logic"],
        )
        findings = [
            # duplicate pair — keep higher confidence
            _make_finding(rule_id="SEC001", category="security",
                          line_start=1, line_end=3, confidence=0.7),
            _make_finding(rule_id="SEC001", category="security",
                          line_start=2, line_end=4, confidence=0.9),
            # below confidence threshold
            _make_finding(rule_id="SEC002", category="security",
                          severity="warning", confidence=0.5),
            # ignored rule
            _make_finding(rule_id="IGNORE", category="security",
                          confidence=0.95),
            # vendor file
            _make_finding(rule_id="SEC003", category="security",
                          file_path="/vendor/lib.py", confidence=0.95),
            # disabled category
            _make_finding(rule_id="STY001", category="style", confidence=0.95),
            # good finding
            _make_finding(rule_id="LOG001", category="logic",
                          severity="critical", confidence=0.85),
        ]
        result = pp.process(findings)
        assert len(result) == 2
        # SEC001 (deduped, kept higher confidence) and LOG001
        rule_ids = {f.rule_id for f in result}
        assert rule_ids == {"SEC001", "LOG001"}
        # Verify the SEC001 kept has higher confidence
        sec = next(f for f in result if f.rule_id == "SEC001")
        assert sec.confidence == 0.9
