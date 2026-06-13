from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .conflicts import ConflictFinding, collect_evidence, detect_conflicts
from .doc_families import classify_documents
from .extractor import extract_references
from .models import ExtractionHit
from .normalization import compact_identifier
from .revisions import RevisionChange


TAG_REGISTER_TEMPLATE = "Registre TAG"


@dataclass(frozen=True)
class TemplateRun:
    name: str
    rows: list["TagRegisterRow"]


@dataclass(frozen=True)
class TagRegisterRow:
    tag: str
    description: str
    lines: str
    documents: str
    families: str
    source_documents: str
    source_pages: str
    evidence_count: int
    conflicts: str
    revisions: str
    best_excerpt: str


def available_templates() -> list[str]:
    return [TAG_REGISTER_TEMPLATE]


def run_template(
    project_root: Path,
    template_name: str,
    conflict_findings: list[ConflictFinding] | None = None,
    revision_changes: list[RevisionChange] | None = None,
) -> TemplateRun:
    if template_name != TAG_REGISTER_TEMPLATE:
        raise ValueError(f"Template inconnu: {template_name}")
    return TemplateRun(template_name, build_tag_register(project_root, conflict_findings, revision_changes))


def build_tag_register(
    project_root: Path,
    conflict_findings: list[ConflictFinding] | None = None,
    revision_changes: list[RevisionChange] | None = None,
) -> list[TagRegisterRow]:
    hits = extract_references(project_root, limit=None)
    tag_hits = [hit for hit in hits if hit.kind == "TAG"]
    evidences = collect_evidence(hits)
    family_by_path = {family.document_path: family.label for family in classify_documents(project_root)}
    conflicts = detect_conflicts(project_root) if conflict_findings is None else conflict_findings
    revisions = [] if revision_changes is None else revision_changes
    conflicts_by_ref = group_conflicts(conflicts)
    revisions_by_ref = group_revisions(revisions)

    grouped: dict[str, list[ExtractionHit]] = {}
    for hit in tag_hits:
        grouped.setdefault(hit.value, []).append(hit)

    rows = [
        build_tag_row(tag, items, evidences, family_by_path, conflicts_by_ref, revisions_by_ref)
        for tag, items in grouped.items()
    ]
    return sorted(rows, key=lambda row: row.tag)


def build_tag_row(
    tag: str,
    hits: list[ExtractionHit],
    evidences: list[object],
    family_by_path: dict[str, str],
    conflicts_by_ref: dict[str, list[ConflictFinding]],
    revisions_by_ref: dict[str, list[RevisionChange]],
) -> TagRegisterRow:
    tag_evidence = [item for item in evidences if getattr(item, "reference") == tag]
    descriptions = sorted({getattr(item, "value") for item in tag_evidence if getattr(item, "field") == "DESCRIPTION"})
    lines = sorted({getattr(item, "value") for item in tag_evidence if getattr(item, "field") == "LINE"})
    documents = sorted({getattr(item, "value") for item in tag_evidence if getattr(item, "field") == "DOC"})
    families = sorted({family_by_path.get(hit.document_path, "A classer") for hit in hits})
    source_documents = sorted({Path(hit.document_path).name for hit in hits})
    source_pages = sorted({f"{Path(hit.document_path).name} p{hit.page}" for hit in hits})
    key = compact_identifier(tag)
    return TagRegisterRow(
        tag=tag,
        description=join_values(descriptions),
        lines=join_values(lines),
        documents=join_values(documents),
        families=join_values(families),
        source_documents=join_values(source_documents),
        source_pages=join_values(source_pages, limit=8),
        evidence_count=len(hits),
        conflicts=conflict_summary(conflicts_by_ref.get(key, [])),
        revisions=revision_summary(revisions_by_ref.get(key, [])),
        best_excerpt=best_excerpt(hits),
    )


def group_conflicts(conflicts: list[ConflictFinding]) -> dict[str, list[ConflictFinding]]:
    grouped: dict[str, list[ConflictFinding]] = {}
    for finding in conflicts:
        grouped.setdefault(compact_identifier(finding.reference), []).append(finding)
    return grouped


def group_revisions(changes: list[RevisionChange]) -> dict[str, list[RevisionChange]]:
    grouped: dict[str, list[RevisionChange]] = {}
    for change in changes:
        grouped.setdefault(compact_identifier(change.reference), []).append(change)
    return grouped


def conflict_summary(conflicts: list[ConflictFinding]) -> str:
    return "; ".join(f"{item.severity}:{item.field}" for item in conflicts[:4])


def revision_summary(changes: list[RevisionChange]) -> str:
    return "; ".join(f"{item.status}:{item.kind}" for item in changes[:4])


def best_excerpt(hits: list[ExtractionHit]) -> str:
    for hit in hits:
        if hit.excerpt:
            return " ".join(hit.excerpt.split())
    return ""


def join_values(values: list[str], limit: int = 6) -> str:
    head = [value for value in values if value][:limit]
    suffix = " ..." if len(values) > limit else ""
    return " | ".join(head) + suffix
