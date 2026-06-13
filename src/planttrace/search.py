from __future__ import annotations

from pathlib import Path

from .models import ProjectPaths, SearchResult
from .normalization import is_probable_identifier
from .semantic import semantic_search
from .store import PlantTraceStore


def search(project_root: Path, query: str, mode: str = "hybrid", limit: int = 50) -> list[SearchResult]:
    store = PlantTraceStore(ProjectPaths(Path(project_root).resolve()))
    store.init()
    mode = mode.lower()
    results: list[SearchResult] = []
    if mode in {"exact", "hybrid"}:
        results.extend(store.exact_search(query))
    if mode in {"text", "hybrid"}:
        results.extend(store.fts_search(query, limit=limit))
    if mode in {"semantic", "hybrid"}:
        results.extend(semantic_search(project_root, query, limit=limit))
    if mode == "fuzzy" or (mode == "hybrid" and not results):
        results.extend(store.fuzzy_search(query, limit=limit))
    if mode == "auto":
        if is_probable_identifier(query):
            results.extend(store.exact_search(query))
        results.extend(store.fts_search(query, limit=limit))
        if not results:
            results.extend(store.fuzzy_search(query, limit=limit))
    return ranked_unique(query, results, limit)


def ranked_unique(query: str, results: list[SearchResult], limit: int) -> list[SearchResult]:
    priority = {
        "exact_normalized": 0,
        "ocr_confusion_normalized": 1,
        "text_bm25": 2,
        "semantic": 3,
        "not_found_in_indexed_text": 9,
    }
    seen: set[tuple[str, int | None, str]] = set()
    unique: list[SearchResult] = []
    for result in sorted(results, key=lambda item: (priority.get(item.match_type, 5), -item.score, item.document_path, item.page or 0)):
        key = (result.document_path, result.page, result.match_type)
        if key in seen:
            continue
        seen.add(key)
        unique.append(result)
    if unique:
        return unique[:limit]
    return [
        SearchResult(
            query=query,
            match_type="not_found_in_indexed_text",
            document_path="",
            page=None,
            score=0.0,
            found_as="",
            excerpt="No hit in indexed text. Check project coverage for OCR-required or failed PDFs.",
            page_status="",
            document_status="",
        )
    ]
