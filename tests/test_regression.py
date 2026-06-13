from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook

from planttrace.batch import load_reference_file, parse_references, run_batch_search

from planttrace.cli import main
from planttrace.export import export_batch, export_results
from planttrace.extractor import extract_references
from planttrace.models import ExtractionRule
from planttrace.normalization import compact_identifier, compact_ocr_identifier, exact_variants
from planttrace.rule_packs import export_rule_pack, import_rule_pack, load_preset_pack, project_rule_pack
from planttrace.rules import load_rules, load_stoplist, save_rules, save_stoplist
from planttrace.search import search
from tests.support import make_pdf, run_root


def test_normalization_covers_industrial_tag_variants() -> None:
    assert compact_identifier("FV-1100") == "FV1100"
    assert compact_ocr_identifier("FO-IIOO") == "F01100"
    assert {"FV-1100", "FV 1100", "FV_1100"}.issubset(exact_variants("FV1100"))


def test_rules_roundtrip_to_project_file() -> None:
    root = run_root()
    rules = [ExtractionRule(name="Custom tags", kind="TAG", pattern=r"\b[A-Z]{2}\d{4}\b")]

    save_rules(root, rules)
    loaded = load_rules(root)

    assert loaded == rules


def test_rule_pack_roundtrip_and_preset_loading() -> None:
    root = run_root()
    preset = load_preset_pack("Instrumentation")

    assert preset.rules
    assert any(rule.kind == "TAG" for rule in preset.rules)

    custom = project_rule_pack("Client A", [ExtractionRule(name="Client tags", kind="TAG", pattern=r"\bAA\d{4}\b")], {"RJ45"})
    output = root / "client-a-rule-pack.json"
    export_rule_pack(custom, output)
    imported = import_rule_pack(output)

    assert imported.name == "Client A"
    assert imported.rules == custom.rules
    assert imported.stoplist == {"RJ45"}


def test_stoplist_roundtrip_and_extraction_filtering() -> None:
    root = run_root()
    pdf_root = root / "pdfs"
    pdf_root.mkdir()
    make_pdf(pdf_root / "refs.pdf", ["RJ45 and FV-1100 are both visible."])
    main(["index", "--project", str(root), "--pdf-root", str(pdf_root)])

    save_stoplist(root, {"RJ45"})
    values = {hit.value for hit in extract_references(root)}

    assert load_stoplist(root) == {"RJ45"}
    assert "RJ45" not in values
    assert "FV-1100" in values


def test_batch_search_reads_reference_list_and_exports_matrix() -> None:
    root = run_root()
    pdf_root = root / "pdfs"
    pdf_root.mkdir()
    make_pdf(pdf_root / "refs.pdf", ["FV-1100 appears here. JDY checked the package."])
    main(["index", "--project", str(root), "--pdf-root", str(pdf_root)])

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["TAG"])
    sheet.append(["FV1100"])
    sheet.append(["JDY"])
    sheet.append(["ZZ9999"])
    reference_file = root / "references.xlsx"
    workbook.save(reference_file)

    references = load_reference_file(reference_file)
    results = run_batch_search(root, references, "hybrid")
    output = root / "batch.xlsx"
    export_batch(results, output)

    assert references == ["FV1100", "JDY", "ZZ9999"]
    assert parse_references("FV1100; JDY\nFV1100") == ["FV1100", "JDY"]
    assert [result.status for result in results] == ["found", "found", "absent_indexed_text"]
    assert output.exists()
    assert load_workbook(output).active["A1"].value == "reference"


def test_cli_index_search_coverage_and_extract(capsys: object) -> None:
    root = run_root()
    pdf_root = root / "pdfs"
    pdf_root.mkdir()
    make_pdf(pdf_root / "loop.pdf", ["FV-1100 and line 10-P-12345 are visible."])

    assert main(["index", "--project", str(root), "--pdf-root", str(pdf_root)]) == 0
    assert main(["search", "--project", str(root), "--query", "FV1100", "--mode", "exact"]) == 0
    assert main(["coverage", "--project", str(root)]) == 0
    assert main(["extract", "--project", str(root), "--limit", "10"]) == 0

    output = capsys.readouterr().out
    assert "exact_normalized" in output
    assert "FV-1100" in output
    assert "10-P-12345" in output


def test_export_results_xlsx_has_expected_headers() -> None:
    root = run_root()
    pdf_root = root / "pdfs"
    pdf_root.mkdir()
    make_pdf(pdf_root / "loop.pdf", ["FV-1100 appears here."])
    main(["index", "--project", str(root), "--pdf-root", str(pdf_root)])
    results = search(root, "FV1100", mode="exact")

    output = root / "results.xlsx"
    export_results(results, output)

    workbook = load_workbook(output)
    sheet = workbook.active
    assert [cell.value for cell in sheet[1]][:4] == ["query", "match_type", "document_path", "page"]


def test_runtime_has_no_network_imports() -> None:
    source_root = Path("src") / "planttrace"
    forbidden = ("requests", "httpx", "urllib", "socket")
    offenders: list[str] = []
    for path in source_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            if f"import {name}" in text or f"from {name}" in text:
                offenders.append(f"{path}:{name}")

    assert offenders == []
