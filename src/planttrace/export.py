from __future__ import annotations

import csv
from pathlib import Path

from .batch import BatchReferenceResult
from .conflicts import ConflictFinding
from .coverage import CoverageDocument, CoverageTask
from .doc_families import DocumentFamily
from .models import ExtractionHit, SearchResult
from .revisions import RevisionChange


HEADERS = [
    "query",
    "match_type",
    "document_path",
    "page",
    "score",
    "found_as",
    "excerpt",
    "page_status",
    "document_status",
]

EXTRACTION_HEADERS = [
    "kind",
    "value",
    "rule",
    "document_path",
    "page",
    "excerpt",
    "confidence",
    "page_status",
    "document_status",
]

BATCH_HEADERS = [
    "reference",
    "status",
    "hit_count",
    "documents",
    "pages",
    "best_match_type",
    "best_excerpt",
]

COVERAGE_HEADERS = [
    "filename",
    "path",
    "triage",
    "status",
    "pages",
    "text_pages",
    "ocr_required_pages",
    "ocr_failed_pages",
    "coverage_percent",
]

COVERAGE_TASK_HEADERS = [
    "filename",
    "path",
    "page",
    "page_status",
    "action",
    "reason",
]

CONFLICT_HEADERS = [
    "reference",
    "field",
    "severity",
    "values",
    "documents",
    "pages",
    "evidence_count",
    "summary",
]

REVISION_HEADERS = [
    "status",
    "kind",
    "reference",
    "old_count",
    "new_count",
    "old_locations",
    "new_locations",
    "old_excerpt",
    "new_excerpt",
    "summary",
]

DOC_FAMILY_HEADERS = [
    "family",
    "label",
    "confidence",
    "score",
    "document_path",
    "filename",
    "pages",
    "evidence",
    "document_status",
]

def export_results(results: list[SearchResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [result_to_row(result) for result in results]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output)
    else:
        export_csv(rows, output)


def result_to_row(result: SearchResult) -> dict[str, object]:
    return {
        "query": result.query,
        "match_type": result.match_type,
        "document_path": result.document_path,
        "page": result.page or "",
        "score": f"{result.score:.6f}",
        "found_as": result.found_as,
        "excerpt": result.excerpt,
        "page_status": result.page_status,
        "document_status": result.document_status,
    }


def export_extraction(hits: list[ExtractionHit], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [extraction_to_row(hit) for hit in hits]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, EXTRACTION_HEADERS, "extraction")
    else:
        export_csv(rows, output, EXTRACTION_HEADERS)


def export_batch(results: list[BatchReferenceResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [batch_to_row(result) for result in results]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, BATCH_HEADERS, "batch")
    else:
        export_csv(rows, output, BATCH_HEADERS)


def export_coverage(documents: list[CoverageDocument], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [coverage_to_row(document) for document in documents]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, COVERAGE_HEADERS, "coverage")
    else:
        export_csv(rows, output, COVERAGE_HEADERS)


def export_coverage_tasks(tasks: list[CoverageTask], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [coverage_task_to_row(task) for task in tasks]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, COVERAGE_TASK_HEADERS, "ocr_triage")
    else:
        export_csv(rows, output, COVERAGE_TASK_HEADERS)


def export_conflicts(findings: list[ConflictFinding], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [conflict_to_row(finding) for finding in findings]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, CONFLICT_HEADERS, "conflicts")
    else:
        export_csv(rows, output, CONFLICT_HEADERS)


def export_revisions(changes: list[RevisionChange], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [revision_change_to_row(change) for change in changes]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, REVISION_HEADERS, "revisions")
    else:
        export_csv(rows, output, REVISION_HEADERS)


def export_doc_families(families: list[DocumentFamily], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [doc_family_to_row(family) for family in families]
    if output.suffix.lower() == ".xlsx":
        export_xlsx(rows, output, DOC_FAMILY_HEADERS, "doc_families")
    else:
        export_csv(rows, output, DOC_FAMILY_HEADERS)


def extraction_to_row(hit: ExtractionHit) -> dict[str, object]:
    return {
        "kind": hit.kind,
        "value": hit.value,
        "rule": hit.rule,
        "document_path": hit.document_path,
        "page": hit.page,
        "excerpt": hit.excerpt,
        "confidence": hit.confidence,
        "page_status": hit.page_status,
        "document_status": hit.document_status,
    }


def batch_to_row(result: BatchReferenceResult) -> dict[str, object]:
    return {
        "reference": result.reference,
        "status": result.status,
        "hit_count": result.hit_count,
        "documents": result.documents,
        "pages": result.pages,
        "best_match_type": result.best_match_type,
        "best_excerpt": result.best_excerpt,
    }


def coverage_to_row(document: CoverageDocument) -> dict[str, object]:
    return {
        "filename": document.filename,
        "path": document.path,
        "triage": document.triage,
        "status": document.status,
        "pages": document.pages,
        "text_pages": document.text_pages,
        "ocr_required_pages": document.ocr_required_pages,
        "ocr_failed_pages": document.ocr_failed_pages,
        "coverage_percent": document.coverage_percent,
    }


def coverage_task_to_row(task: CoverageTask) -> dict[str, object]:
    return {
        "filename": task.filename,
        "path": task.path,
        "page": task.page,
        "page_status": task.page_status,
        "action": task.action,
        "reason": task.reason,
    }


def conflict_to_row(finding: ConflictFinding) -> dict[str, object]:
    return {
        "reference": finding.reference,
        "field": finding.field,
        "severity": finding.severity,
        "values": finding.values,
        "documents": finding.documents,
        "pages": finding.pages,
        "evidence_count": finding.evidence_count,
        "summary": finding.summary,
    }


def revision_change_to_row(change: RevisionChange) -> dict[str, object]:
    return {
        "status": change.status,
        "kind": change.kind,
        "reference": change.reference,
        "old_count": change.old_count,
        "new_count": change.new_count,
        "old_locations": change.old_locations,
        "new_locations": change.new_locations,
        "old_excerpt": change.old_excerpt,
        "new_excerpt": change.new_excerpt,
        "summary": change.summary,
    }


def doc_family_to_row(family: DocumentFamily) -> dict[str, object]:
    return {
        "family": family.family,
        "label": family.label,
        "confidence": family.confidence,
        "score": family.score,
        "document_path": family.document_path,
        "filename": family.filename,
        "pages": family.pages,
        "evidence": family.evidence,
        "document_status": family.document_status,
    }


def export_csv(rows: list[dict[str, object]], output: Path, headers: list[str] = HEADERS) -> None:
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def export_xlsx(rows: list[dict[str, object]], output: Path, headers: list[str] = HEADERS, sheet_name: str = "results") -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(headers)
    for row in rows:
        sheet.append([row[header] for header in headers])
    workbook.save(output)
