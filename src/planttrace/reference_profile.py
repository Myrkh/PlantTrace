from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .conflicts import ConflictFinding, detect_conflicts
from .doc_families import FAMILY_RULES, classify_documents
from .extractor import extract_references
from .models import ExtractionHit, SearchResult
from .normalization import compact_identifier
from .revisions import RevisionChange
from .search import search


@dataclass(frozen=True)
class ReferenceOccurrence:
    family: str
    document_path: str
    filename: str
    page: int
    match_type: str
    found_as: str
    excerpt: str
    page_status: str
    document_status: str


@dataclass(frozen=True)
class ReferenceAssociation:
    kind: str
    value: str
    evidence_count: int
    documents: str
    pages: str
    excerpt: str


@dataclass(frozen=True)
class ReferenceAlert:
    source: str
    severity: str
    field: str
    values: str
    documents: str
    pages: str
    summary: str


@dataclass(frozen=True)
class ReferenceProfile:
    query: str
    occurrence_count: int
    document_count: int
    family_summary: str
    association_count: int
    alert_count: int
    occurrences: list[ReferenceOccurrence]
    associations: list[ReferenceAssociation]
    alerts: list[ReferenceAlert]
    completeness: list[tuple[str, bool]] = field(default_factory=list)


# Familles documentaires attendues pour qu'un instrument soit considere complet.
EXPECTED_FAMILIES = ("PID_PFD", "LOOP", "DATASHEET", "IO_PLC")


def compute_completeness(occurrences: list[ReferenceOccurrence]) -> list[tuple[str, bool]]:
    present = {occurrence.family for occurrence in occurrences}
    label_by_code = {rule.family: rule.label for rule in FAMILY_RULES}
    return [(label_by_code[code], label_by_code[code] in present) for code in EXPECTED_FAMILIES]


def build_reference_profile(
    project_root: Path,
    query: str,
    conflict_findings: list[ConflictFinding] | None = None,
    revision_changes: list[RevisionChange] | None = None,
) -> ReferenceProfile:
    clean_query = query.strip()
    query_key = compact_identifier(clean_query)
    if not clean_query or not query_key:
        raise ValueError("Saisir une reference avant de generer la fiche.")

    results = [result for result in search(project_root, clean_query, "hybrid", 500) if result.match_type != "not_found_in_indexed_text"]
    family_by_path = {family.document_path: family.label for family in classify_documents(project_root)}
    occurrences = [occurrence_from_result(result, family_by_path) for result in results if result.page is not None]
    occurrence_pages = {(occurrence.document_path, occurrence.page) for occurrence in occurrences}
    hits = extract_references(project_root, limit=None, page_filter=occurrence_pages)
    associations = collect_associations(query_key, occurrences, hits)
    conflicts = detect_conflicts(project_root) if conflict_findings is None else conflict_findings
    revisions = [] if revision_changes is None else revision_changes
    alerts = collect_alerts(query_key, conflicts, revisions)
    families = sorted({occurrence.family for occurrence in occurrences if occurrence.family})

    return ReferenceProfile(
        query=clean_query,
        occurrence_count=len(occurrences),
        document_count=len({occurrence.document_path for occurrence in occurrences}),
        family_summary=", ".join(families) if families else "Aucune famille document liee.",
        association_count=len(associations),
        alert_count=len(alerts),
        occurrences=occurrences,
        associations=associations,
        alerts=alerts,
        completeness=compute_completeness(occurrences),
    )


def occurrence_from_result(result: SearchResult, family_by_path: dict[str, str]) -> ReferenceOccurrence:
    return ReferenceOccurrence(
        family=family_by_path.get(result.document_path, "A classer"),
        document_path=result.document_path,
        filename=Path(result.document_path).name,
        page=int(result.page or 0),
        match_type=result.match_type,
        found_as=result.found_as,
        excerpt=" ".join(result.excerpt.split()),
        page_status=result.page_status,
        document_status=result.document_status,
    )


def collect_associations(query_key: str, occurrences: list[ReferenceOccurrence], hits: list[ExtractionHit]) -> list[ReferenceAssociation]:
    pages = {(occurrence.document_path, occurrence.page) for occurrence in occurrences}
    grouped: dict[tuple[str, str], list[ExtractionHit]] = {}
    for hit in hits:
        hit_key = compact_identifier(hit.value)
        if hit_key == query_key:
            continue
        if (hit.document_path, hit.page) not in pages and query_key not in compact_identifier(hit.excerpt):
            continue
        grouped.setdefault((hit.kind, hit.value), []).append(hit)

    associations = [association_from_hits(kind, value, items) for (kind, value), items in grouped.items()]
    return sorted(associations, key=lambda item: (kind_order(item.kind), item.value))


def association_from_hits(kind: str, value: str, hits: list[ExtractionHit]) -> ReferenceAssociation:
    documents = sorted({Path(hit.document_path).name for hit in hits})
    pages = sorted({str(hit.page) for hit in hits}, key=lambda page: int(page))
    excerpt = next((hit.excerpt for hit in hits if hit.excerpt), "")
    return ReferenceAssociation(
        kind=kind,
        value=value,
        evidence_count=len(hits),
        documents=", ".join(documents),
        pages=", ".join(pages),
        excerpt=" ".join(excerpt.split()),
    )


def collect_alerts(
    query_key: str,
    conflicts: list[ConflictFinding],
    revisions: list[RevisionChange],
) -> list[ReferenceAlert]:
    alerts: list[ReferenceAlert] = []
    for conflict in conflicts:
        if compact_identifier(conflict.reference) == query_key:
            alerts.append(
                ReferenceAlert(
                    source="Conflits",
                    severity=conflict.severity,
                    field=conflict.field,
                    values=conflict.values,
                    documents=conflict.documents,
                    pages=conflict.pages,
                    summary=conflict.summary,
                )
            )
    for change in revisions:
        if compact_identifier(change.reference) == query_key:
            alerts.append(
                ReferenceAlert(
                    source="Revisions",
                    severity="medium",
                    field=change.kind,
                    values=change.status,
                    documents=change.old_locations or change.new_locations,
                    pages="",
                    summary=change.summary,
                )
            )
    return alerts


def kind_order(kind: str) -> int:
    return {"LINE": 0, "DOC": 1, "TAG": 2, "INITIALS": 3}.get(kind, 9)
