from __future__ import annotations

import csv
import json
from io import BytesIO, StringIO
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from . import __version__
from .batch import BatchReferenceResult
from .conflicts import ConflictFinding
from .coverage import coverage_documents, coverage_verdict
from .export import (
    BATCH_HEADERS,
    CONFLICT_HEADERS,
    COVERAGE_HEADERS,
    DOC_FAMILY_HEADERS,
    EXTRACTION_HEADERS,
    HEADERS,
    REVISION_HEADERS,
    batch_to_row,
    conflict_to_row,
    coverage_to_row,
    doc_family_to_row,
    extraction_to_row,
    revision_change_to_row,
    result_to_row,
)
from .models import ExtractionHit, ProjectPaths, SearchResult
from .doc_families import DocumentFamily
from .reference_exports import reference_profile_xlsx_bytes
from .reference_profile import ReferenceProfile
from .project_matrix import ProjectMatrixRow
from .matrix_exports import PROJECT_MATRIX_HEADERS, project_matrix_to_row
from .master_register import MasterRegisterResult
from .revisions import RevisionChange
from .templates import TemplateRun
from .template_exports import TAG_REGISTER_HEADERS, tag_register_to_row
from .semantic import semantic_status
from .store import PlantTraceStore


@dataclass(frozen=True)
class DeliverablePack:
    output: Path
    included_files: list[str]
    manifest: dict[str, object]


def build_deliverable_pack(
    project_root: Path,
    output: Path,
    search_results: list[SearchResult],
    batch_results: list[BatchReferenceResult],
    extraction_hits: list[ExtractionHit],
    conflict_findings: list[ConflictFinding] | None = None,
    revision_changes: list[RevisionChange] | None = None,
    doc_families: list[DocumentFamily] | None = None,
    reference_profile: ReferenceProfile | None = None,
    project_matrix: list[ProjectMatrixRow] | None = None,
    template_run: TemplateRun | None = None,
    master_register: MasterRegisterResult | None = None,
    with_snippets: bool = True,
) -> DeliverablePack:
    root = Path(project_root).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    coverage_summary = PlantTraceStore(ProjectPaths(root)).coverage()
    coverage_docs = coverage_documents(root)
    semantic = semantic_status(root)
    conflicts = conflict_findings or []
    revisions = revision_changes or []
    families = doc_families or []
    profile = reference_profile
    matrix = project_matrix or []
    template = template_run
    master = master_register
    included: list[str] = []

    manifest: dict[str, object] = {
        "tool": "PlantTrace",
        "version": __version__,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "coverage": coverage_summary,
        "coverage_verdict": coverage_verdict(coverage_summary),
        "semantic": {"available": semantic.available, "message": semantic.message},
        "counts": {
            "search_results": len(search_results),
            "batch_rows": len(batch_results),
            "extraction_hits": len(extraction_hits),
            "reference_profile": 1 if profile else 0,
            "project_matrix_rows": len(matrix),
            "template_rows": len(template.rows) if template else 0,
            "master_register_tags": len(master.tags) if master else 0,
            "master_register_links": master.link_count if master else 0,
            "doc_families": len(families),
            "conflicts": len(conflicts),
            "revision_changes": len(revisions),
            "coverage_documents": len(coverage_docs),
        },
    }

    files: list[tuple[str, bytes | str]] = []
    included.extend(["README.txt", "manifest.json"])
    if search_results:
        add_xlsx(files, included, "exports/search-results.xlsx", [result_to_row(result) for result in search_results], HEADERS, "search")
    if with_snippets and search_results:
        add_evidence_snippets(files, included, search_results)
    if batch_results:
        add_xlsx(files, included, "exports/batch-matrix.xlsx", [batch_to_row(result) for result in batch_results], BATCH_HEADERS, "batch")
    if extraction_hits:
        add_xlsx(files, included, "exports/extraction-inventory.xlsx", [extraction_to_row(hit) for hit in extraction_hits], EXTRACTION_HEADERS, "extraction")
    if profile:
        included.append("exports/reference-profile.xlsx")
        files.append(("exports/reference-profile.xlsx", reference_profile_xlsx_bytes(profile)))
    if matrix:
        add_xlsx(files, included, "exports/project-matrix.xlsx", [project_matrix_to_row(row) for row in matrix], PROJECT_MATRIX_HEADERS, "project_matrix")
    if template:
        add_xlsx(files, included, "exports/tag-register-template.xlsx", [tag_register_to_row(row) for row in template.rows], TAG_REGISTER_HEADERS, "tag_register")
    if master:
        add_file(files, included, "exports/master-register/Tags Template - PlantTrace.xlsx", master.tags_output)
        add_file(files, included, "exports/master-register/Tags Documents Links Template - PlantTrace.xlsx", master.links_output)
        add_file(files, included, "exports/master-register/PlantTrace Master Register Evidence.xlsx", master.evidence_output)
    if families:
        add_xlsx(files, included, "exports/document-families.xlsx", [doc_family_to_row(family) for family in families], DOC_FAMILY_HEADERS, "doc_families")
    if conflicts:
        add_xlsx(files, included, "exports/conflicts.xlsx", [conflict_to_row(finding) for finding in conflicts], CONFLICT_HEADERS, "conflicts")
    if revisions:
        add_xlsx(files, included, "exports/revision-compare.xlsx", [revision_change_to_row(change) for change in revisions], REVISION_HEADERS, "revisions")
    if coverage_docs:
        add_xlsx(files, included, "exports/coverage-report.xlsx", [coverage_to_row(document) for document in coverage_docs], COVERAGE_HEADERS, "coverage")
    if any(result.status == "absent_indexed_text" for result in batch_results):
        included.append("audit/absences-qualifiees.csv")
        files.append(("audit/absences-qualifiees.csv", absences_csv_bytes(batch_results, coverage_verdict(coverage_summary))))

    manifest["counts"]["evidence_snippets"] = sum(1 for name in included if name.startswith("evidence-snippets/"))
    manifest["included_files"] = included
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("README.txt", readme_text(manifest, batch_results))
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for name, payload in files:
            archive.writestr(name, payload)
    return DeliverablePack(output=output, included_files=included, manifest=manifest)


def add_xlsx(files: list[tuple[str, bytes | str]], included: list[str], name: str, rows: list[dict[str, object]], headers: list[str], sheet_name: str) -> None:
    included.append(name)
    files.append((name, xlsx_bytes(rows, headers, sheet_name)))


def add_file(files: list[tuple[str, bytes | str]], included: list[str], name: str, path: Path) -> None:
    if not path.exists():
        return
    included.append(name)
    files.append((name, path.read_bytes()))


def add_evidence_snippets(files: list[tuple[str, bytes | str]], included: list[str], results: list[SearchResult], limit: int = 50) -> None:
    from .pdf_engine import crop_evidence_png

    count = 0
    for index, result in enumerate(results, start=1):
        if count >= limit:
            break
        if not result.document_path or result.page is None or result.page_status in {"ocr_required", "ocr_failed"}:
            continue
        terms = [term for term in (result.found_as, result.query) if term]
        try:
            png = crop_evidence_png(result.document_path, result.page, terms)
        except Exception:
            png = None
        if png is None:
            continue
        name = f"evidence-snippets/{index:03d}_{Path(result.document_path).stem}_p{result.page}.png"
        included.append(name)
        files.append((name, png))
        count += 1


def xlsx_bytes(rows: list[dict[str, object]], headers: list[str], sheet_name: str) -> bytes:
    from openpyxl import Workbook

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(title=sheet_name)
    sheet.append(headers)
    for row in rows:
        sheet.append([row[header] for header in headers])
    stream = BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


def absences_csv_bytes(results: list[BatchReferenceResult], verdict: str) -> bytes:
    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=["reference", "status", "qualification", "coverage_verdict"])
    writer.writeheader()
    for result in results:
        if result.status == "absent_indexed_text":
            writer.writerow(
                {
                    "reference": result.reference,
                    "status": result.status,
                    "qualification": "Absence dans le texte indexe uniquement.",
                    "coverage_verdict": verdict,
                }
            )
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def readme_text(manifest: dict[str, object], batch_results: list[BatchReferenceResult]) -> str:
    absent = sum(1 for result in batch_results if result.status == "absent_indexed_text")
    return "\n".join(
        [
            "PlantTrace - Pack livrable projet",
            "",
            f"Projet: {manifest['project_root']}",
            f"Genere UTC: {manifest['generated_at_utc']}",
            f"Verdict couverture: {manifest['coverage_verdict']}",
            "",
            "Regle d'audit:",
            "Un resultat positif doit etre relu avec son PDF, sa page et son extrait.",
            "Une absence est qualifiee: elle vaut seulement pour le corpus indexe et lisible.",
            "",
            f"Absences batch qualifiees: {absent}",
        ]
    )
