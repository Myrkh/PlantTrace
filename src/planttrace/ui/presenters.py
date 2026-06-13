from __future__ import annotations

from planttrace.models import SearchResult


def result_row_values(result: SearchResult) -> list[str]:
    return [
        result.match_type,
        result.document_path,
        str(result.page or ""),
        f"{result.score:.4f}",
        result.found_as,
        result.excerpt,
        result.page_status,
        result.document_status,
    ]


def extraction_row_values(hit: object) -> list[str]:
    return [
        hit.kind,
        hit.value,
        hit.rule,
        hit.document_path,
        str(hit.page),
        hit.excerpt,
        hit.confidence,
        hit.page_status,
        hit.document_status,
    ]
