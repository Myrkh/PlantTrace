from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .extractor import extract_references
from .indexer import IndexReport, index_folder
from .models import ExtractionHit, ExtractionRule, ProjectPaths
from .rules import load_rules


@dataclass(frozen=True)
class RevisionEvidence:
    kind: str
    value: str
    relative_document: str
    document_path: str
    page: int
    excerpt: str
    confidence: str
    page_status: str
    document_status: str


@dataclass(frozen=True)
class RevisionChange:
    status: str
    kind: str
    reference: str
    old_count: int
    new_count: int
    old_locations: str
    new_locations: str
    old_excerpt: str
    new_excerpt: str
    summary: str


@dataclass(frozen=True)
class RevisionComparison:
    old_report: IndexReport
    new_report: IndexReport
    changes: list[RevisionChange]


def compare_revision_folders(
    project_root: Path,
    old_pdf_root: Path,
    new_pdf_root: Path,
    rules: list[ExtractionRule] | None = None,
    enable_ocr: bool = False,
    ocr_lang: str = "eng",
) -> RevisionComparison:
    root = Path(project_root).resolve()
    old_source = Path(old_pdf_root).resolve()
    new_source = Path(new_pdf_root).resolve()
    if not old_source.exists():
        raise FileNotFoundError(f"Ancienne revision introuvable: {old_source}")
    if not new_source.exists():
        raise FileNotFoundError(f"Nouvelle revision introuvable: {new_source}")

    old_project = reset_revision_project(root, "old")
    new_project = reset_revision_project(root, "new")
    old_report = index_folder(old_project, old_source, force=True, enable_ocr=enable_ocr, ocr_lang=ocr_lang)
    new_report = index_folder(new_project, new_source, force=True, enable_ocr=enable_ocr, ocr_lang=ocr_lang)

    active_rules = rules or load_rules(root)
    old_hits = extract_references(old_project, rules=active_rules, limit=None)
    new_hits = extract_references(new_project, rules=active_rules, limit=None)
    changes = compare_hits(old_hits, new_hits, old_source, new_source)
    return RevisionComparison(old_report=old_report, new_report=new_report, changes=changes)


def reset_revision_project(project_root: Path, name: str) -> Path:
    revisions_root = ProjectPaths(project_root).data_dir / "revisions"
    target = revisions_root / name
    resolved_root = revisions_root.resolve()
    resolved_target = target.resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("Chemin de revision invalide.") from exc
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    return target


def compare_hits(
    old_hits: list[ExtractionHit],
    new_hits: list[ExtractionHit],
    old_pdf_root: Path,
    new_pdf_root: Path,
) -> list[RevisionChange]:
    old_index = evidence_index(old_hits, old_pdf_root)
    new_index = evidence_index(new_hits, new_pdf_root)
    changes: list[RevisionChange] = []
    for kind, reference in sorted(set(old_index) | set(new_index)):
        old_evidence = old_index.get((kind, reference), [])
        new_evidence = new_index.get((kind, reference), [])
        if not old_evidence:
            changes.append(build_change("added", kind, reference, old_evidence, new_evidence))
        elif not new_evidence:
            changes.append(build_change("removed", kind, reference, old_evidence, new_evidence))
        elif evidence_signature(old_evidence) != evidence_signature(new_evidence):
            changes.append(build_change("modified", kind, reference, old_evidence, new_evidence))
    return sorted(changes, key=lambda change: (status_order(change.status), change.kind, change.reference))


def evidence_index(hits: list[ExtractionHit], pdf_root: Path) -> dict[tuple[str, str], list[RevisionEvidence]]:
    index: dict[tuple[str, str], list[RevisionEvidence]] = {}
    for hit in hits:
        evidence = RevisionEvidence(
            kind=hit.kind,
            value=hit.value,
            relative_document=relative_document(hit.document_path, pdf_root),
            document_path=hit.document_path,
            page=hit.page,
            excerpt=compact_text(hit.excerpt),
            confidence=hit.confidence,
            page_status=hit.page_status,
            document_status=hit.document_status,
        )
        index.setdefault((hit.kind, hit.value), []).append(evidence)
    return index


def build_change(status: str, kind: str, reference: str, old_evidence: list[RevisionEvidence], new_evidence: list[RevisionEvidence]) -> RevisionChange:
    return RevisionChange(
        status=status,
        kind=kind,
        reference=reference,
        old_count=len(old_evidence),
        new_count=len(new_evidence),
        old_locations=locations(old_evidence),
        new_locations=locations(new_evidence),
        old_excerpt=excerpts(old_evidence),
        new_excerpt=excerpts(new_evidence),
        summary=summary(status),
    )


def relative_document(document_path: str, pdf_root: Path) -> str:
    path = Path(document_path).resolve()
    try:
        return str(path.relative_to(pdf_root.resolve()))
    except ValueError:
        return path.name


def evidence_signature(evidence: list[RevisionEvidence]) -> set[tuple[str, int, str]]:
    return {(item.relative_document.lower(), item.page, item.excerpt.upper()) for item in evidence}


def locations(evidence: list[RevisionEvidence], limit: int = 5) -> str:
    values = []
    for item in evidence:
        location = f"{item.relative_document} p{item.page}"
        if location not in values:
            values.append(location)
        if len(values) >= limit:
            break
    suffix = " ..." if len(evidence) > limit else ""
    return "; ".join(values) + suffix


def excerpts(evidence: list[RevisionEvidence], limit: int = 2) -> str:
    values = []
    for item in evidence:
        if item.excerpt not in values:
            values.append(item.excerpt)
        if len(values) >= limit:
            break
    suffix = " ..." if len(evidence) > limit else ""
    return " | ".join(values) + suffix


def compact_text(text: str) -> str:
    return " ".join(text.split())


def status_order(status: str) -> int:
    return {"removed": 0, "modified": 1, "added": 2}.get(status, 9)


def summary(status: str) -> str:
    if status == "added":
        return "Reference presente en nouvelle revision uniquement."
    if status == "removed":
        return "Reference presente en ancienne revision uniquement."
    return "Reference conservee mais preuve, page ou extrait different."
