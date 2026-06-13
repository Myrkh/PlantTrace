from __future__ import annotations

import re
from pathlib import Path

from .models import ExtractionHit, ExtractionRule, ProjectPaths
from .rules import load_rules, load_stoplist
from .store import PlantTraceStore


def extract_references(
    project_root: Path,
    rules: list[ExtractionRule] | None = None,
    limit: int | None = 10000,
    page_filter: set[tuple[str, int]] | None = None,
) -> list[ExtractionHit]:
    paths = ProjectPaths(project_root.resolve())
    active_rules = [rule for rule in (rules or load_rules(paths.root)) if rule.enabled]
    stoplist = load_stoplist(paths.root)
    store = PlantTraceStore(paths)
    hits: list[ExtractionHit] = []
    seen: set[tuple[str, str, str, int]] = set()

    for page in store.indexed_pages():
        page_key = (page["path"], int(page["page_number"]))
        if page_filter is not None and page_key not in page_filter:
            continue
        text = page["text"]
        for rule in active_rules:
            for match in re.finditer(rule.pattern, text, flags=re.IGNORECASE):
                value = normalize_value(match.group(0))
                if value in stoplist or not valid_value(value, rule.kind):
                    continue
                key = (rule.kind, value, page["path"], int(page["page_number"]))
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    ExtractionHit(
                        kind=rule.kind,
                        value=value,
                        rule=rule.name,
                        document_path=page["path"],
                        page=int(page["page_number"]),
                        excerpt=match_excerpt(text, match.start(), match.end()),
                        confidence=rule.confidence,
                        page_status=page["page_status"],
                        document_status=page["document_status"],
                    )
                )
                if limit is not None and len(hits) >= limit:
                    return sorted_hits(hits)
    return sorted_hits(hits)


def sorted_hits(hits: list[ExtractionHit]) -> list[ExtractionHit]:
    confidence_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(hits, key=lambda hit: (hit.kind, hit.value, confidence_order.get(hit.confidence, 9), hit.document_path, hit.page))


def normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper().replace("_", "-")


def valid_value(value: str, kind: str) -> bool:
    if kind == "INITIALS":
        return value not in {"PDF", "DOC", "PAGE", "THE", "AND", "FOR", "LES", "DES", "SUR", "AVEC"}
    if kind == "TAG":
        return bool(re.search(r"[A-Z]", value) and re.search(r"\d", value))
    return True


def match_excerpt(text: str, start: int, end: int, width: int = 90) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return " ".join(text[left:right].split())
