from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .conflicts import ConflictFinding, detect_conflicts
from .doc_families import classify_documents
from .extractor import extract_references
from .models import ExtractionHit
from .normalization import compact_identifier
from .revisions import RevisionChange


FAMILY_COLUMNS = [
    ("PID_PFD", "PID/PFD"),
    ("LOOP", "Loop"),
    ("DATASHEET", "Datasheet"),
    ("TERMINAL_JB", "Bornier/JB"),
    ("IO_PLC", "IO/Automate"),
    ("INSTRUMENT_LIST", "Liste instruments"),
    ("VENDOR", "Vendor"),
    ("ADMIN_REVIEW", "Review"),
    ("UNKNOWN", "A classer"),
]


@dataclass(frozen=True)
class ProjectMatrixRow:
    kind: str
    reference: str
    occurrence_count: int
    document_count: int
    family_summary: str
    pid_pfd: int
    loop: int
    datasheet: int
    terminal_jb: int
    io_plc: int
    instrument_list: int
    vendor: int
    admin_review: int
    unknown: int
    documents: str
    pages: str
    conflicts: str
    revisions: str
    best_excerpt: str


def build_project_matrix(
    project_root: Path,
    conflict_findings: list[ConflictFinding] | None = None,
    revision_changes: list[RevisionChange] | None = None,
) -> list[ProjectMatrixRow]:
    hits = extract_references(project_root, limit=None)
    family_by_path = {family.document_path: family.family for family in classify_documents(project_root)}
    conflicts = detect_conflicts(project_root) if conflict_findings is None else conflict_findings
    revisions = [] if revision_changes is None else revision_changes
    conflicts_by_ref = group_conflicts(conflicts)
    revisions_by_ref = group_revisions(revisions)

    grouped: dict[tuple[str, str], list[ExtractionHit]] = {}
    for hit in hits:
        grouped.setdefault((hit.kind, hit.value), []).append(hit)

    rows = [
        build_matrix_row(kind, value, items, family_by_path, conflicts_by_ref, revisions_by_ref)
        for (kind, value), items in grouped.items()
    ]
    return sorted(rows, key=lambda row: (kind_order(row.kind), row.reference))


def build_matrix_row(
    kind: str,
    value: str,
    hits: list[ExtractionHit],
    family_by_path: dict[str, str],
    conflicts_by_ref: dict[str, list[ConflictFinding]],
    revisions_by_ref: dict[str, list[RevisionChange]],
) -> ProjectMatrixRow:
    family_counts = {key: 0 for key, _label in FAMILY_COLUMNS}
    documents = sorted({Path(hit.document_path).name for hit in hits})
    pages = sorted({f"{Path(hit.document_path).name} p{hit.page}" for hit in hits})
    for hit in hits:
        family = family_by_path.get(hit.document_path, "UNKNOWN")
        family_counts[family if family in family_counts else "UNKNOWN"] += 1
    present_families = [label for key, label in FAMILY_COLUMNS if family_counts[key] > 0]
    ref_key = compact_identifier(value)
    return ProjectMatrixRow(
        kind=kind,
        reference=value,
        occurrence_count=len(hits),
        document_count=len(documents),
        family_summary=", ".join(present_families) if present_families else "A classer",
        pid_pfd=family_counts["PID_PFD"],
        loop=family_counts["LOOP"],
        datasheet=family_counts["DATASHEET"],
        terminal_jb=family_counts["TERMINAL_JB"],
        io_plc=family_counts["IO_PLC"],
        instrument_list=family_counts["INSTRUMENT_LIST"],
        vendor=family_counts["VENDOR"],
        admin_review=family_counts["ADMIN_REVIEW"],
        unknown=family_counts["UNKNOWN"],
        documents=", ".join(documents),
        pages="; ".join(pages[:8]) + (" ..." if len(pages) > 8 else ""),
        conflicts=conflict_summary(conflicts_by_ref.get(ref_key, [])),
        revisions=revision_summary(revisions_by_ref.get(ref_key, [])),
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
    if not conflicts:
        return ""
    return "; ".join(f"{item.severity}:{item.field}" for item in conflicts[:4])


def revision_summary(changes: list[RevisionChange]) -> str:
    if not changes:
        return ""
    return "; ".join(f"{item.status}:{item.kind}" for item in changes[:4])


def best_excerpt(hits: list[ExtractionHit]) -> str:
    for hit in hits:
        if hit.excerpt:
            return " ".join(hit.excerpt.split())
    return ""


def kind_order(kind: str) -> int:
    return {"TAG": 0, "LINE": 1, "DOC": 2, "INITIALS": 3}.get(kind, 9)
