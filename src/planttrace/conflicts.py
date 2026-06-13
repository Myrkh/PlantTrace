from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .extractor import extract_references, normalize_value
from .models import ExtractionHit


@dataclass(frozen=True)
class ConflictEvidence:
    reference: str
    field: str
    value: str
    document_path: str
    page: int
    excerpt: str
    confidence: str


@dataclass(frozen=True)
class ConflictFinding:
    reference: str
    field: str
    severity: str
    values: str
    documents: str
    pages: str
    evidence_count: int
    summary: str


def detect_conflicts(project_root: Path) -> list[ConflictFinding]:
    hits = extract_references(project_root)
    evidences = collect_evidence(hits)
    grouped: dict[tuple[str, str], list[ConflictEvidence]] = {}
    for evidence in evidences:
        grouped.setdefault((evidence.reference, evidence.field), []).append(evidence)

    findings: list[ConflictFinding] = []
    for (reference, field), items in grouped.items():
        value_keys = {normalize_conflict_value(item.value) for item in items}
        if len(value_keys) < 2:
            continue
        values = sorted({item.value for item in items}, key=normalize_conflict_value)
        documents = sorted({Path(item.document_path).name for item in items})
        pages = sorted({str(item.page) for item in items})
        findings.append(
            ConflictFinding(
                reference=reference,
                field=field,
                severity=severity_for(field),
                values=" | ".join(values),
                documents=", ".join(documents),
                pages=", ".join(pages),
                evidence_count=len(items),
                summary=" ; ".join(f"{item.value} @ {Path(item.document_path).name} p{item.page}" for item in items[:6]),
            )
        )
    return sorted(findings, key=lambda item: (severity_order(item.severity), item.reference, item.field))


def collect_evidence(hits: list[ExtractionHit]) -> list[ConflictEvidence]:
    by_page: dict[tuple[str, int], list[ExtractionHit]] = {}
    for hit in hits:
        by_page.setdefault((hit.document_path, hit.page), []).append(hit)

    evidences: list[ConflictEvidence] = []
    for hit in hits:
        if hit.kind != "TAG":
            continue
        page_hits = by_page.get((hit.document_path, hit.page), [])
        for candidate in page_hits:
            if candidate.kind not in {"LINE", "DOC"}:
                continue
            if candidate.value in hit.excerpt or hit.value in candidate.excerpt:
                evidences.append(evidence_from_hit(hit, candidate.kind, candidate.value, "medium"))
        description = description_candidate(hit)
        if description:
            evidences.append(evidence_from_hit(hit, "DESCRIPTION", description, "low"))
    return dedupe_evidence(evidences)


def evidence_from_hit(tag_hit: ExtractionHit, field: str, value: str, confidence: str) -> ConflictEvidence:
    return ConflictEvidence(
        reference=tag_hit.value,
        field=field,
        value=normalize_value(value) if field in {"LINE", "DOC"} else " ".join(value.split()),
        document_path=tag_hit.document_path,
        page=tag_hit.page,
        excerpt=tag_hit.excerpt,
        confidence=confidence,
    )


def description_candidate(hit: ExtractionHit) -> str:
    patterns = [
        r"\b(?:description|desc|designation|service)\s*[:=-]\s*([A-Za-z0-9 /_.-]{3,80})",
        r"\b(?:descr|libelle)\s*[:=-]\s*([A-Za-z0-9 /_.-]{3,80})",
    ]
    for pattern in patterns:
        match = re.search(pattern, hit.excerpt, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .;-")
    return ""


def dedupe_evidence(items: list[ConflictEvidence]) -> list[ConflictEvidence]:
    seen: set[tuple[str, str, str, str, int]] = set()
    output: list[ConflictEvidence] = []
    for item in items:
        key = (item.reference, item.field, normalize_conflict_value(item.value), item.document_path, item.page)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def normalize_conflict_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().upper().replace("_", "-"))


def severity_for(field: str) -> str:
    if field == "LINE":
        return "high"
    if field == "DOC":
        return "medium"
    return "low"


def severity_order(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity, 9)
