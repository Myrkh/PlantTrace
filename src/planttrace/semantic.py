from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .models import ProjectPaths, SearchResult
from .store import PlantTraceStore


@dataclass(frozen=True)
class SemanticStatus:
    available: bool
    message: str


def model_path(project_root: Path) -> Path:
    configured = os.environ.get("PLANTTRACE_EMBED_MODEL")
    if configured:
        return Path(configured).expanduser().resolve()
    return ProjectPaths(project_root.resolve()).data_dir / "models" / "embedding-model"


def semantic_status(project_root: Path) -> SemanticStatus:
    try:
        import sentence_transformers  # noqa: F401
    except Exception:
        return SemanticStatus(False, "sentence-transformers not installed")
    path = model_path(project_root)
    if not path.exists():
        return SemanticStatus(False, f"local embedding model not found: {path}")
    return SemanticStatus(True, str(path))


def rebuild_embeddings(project_root: Path, batch_size: int = 64) -> int:
    status = semantic_status(project_root)
    if not status.available:
        raise RuntimeError(status.message)

    from sentence_transformers import SentenceTransformer

    paths = ProjectPaths(project_root.resolve())
    store = PlantTraceStore(paths)
    chunks = store.all_chunks()
    texts = [chunk["text"] for chunk in chunks]
    if not texts:
        paths.embedding_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(paths.embedding_path, np.empty((0, 0), dtype=np.float32))
        return 0

    model = SentenceTransformer(str(model_path(project_root)), local_files_only=True)
    vectors = model.encode(texts, batch_size=batch_size, convert_to_numpy=True, normalize_embeddings=True)
    vectors = np.asarray(vectors, dtype=np.float32)
    paths.embedding_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(paths.embedding_path, vectors)
    store.set_embedding_offsets([int(chunk["id"]) for chunk in chunks])
    return len(chunks)


def semantic_search(project_root: Path, query: str, limit: int = 25) -> list[SearchResult]:
    status = semantic_status(project_root)
    paths = ProjectPaths(project_root.resolve())
    if not status.available or not paths.embedding_path.exists():
        return []

    from sentence_transformers import SentenceTransformer

    store = PlantTraceStore(paths)
    chunks = store.embedded_chunks()
    if not chunks:
        return []
    embeddings = np.load(paths.embedding_path)
    if embeddings.size == 0:
        return []

    model = SentenceTransformer(str(model_path(project_root)), local_files_only=True)
    query_vector = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0].astype(np.float32)
    scores = embeddings @ query_vector
    top_indexes = np.argsort(scores)[::-1][:limit]

    results: list[SearchResult] = []
    for index in top_indexes:
        if index >= len(chunks):
            continue
        chunk = chunks[int(index)]
        score = float(scores[int(index)])
        if score <= 0:
            continue
        results.append(
            SearchResult(
                query=query,
                match_type="semantic",
                document_path=chunk["path"],
                page=int(chunk["page_number"]),
                score=score,
                found_as="",
                excerpt=chunk["text"],
                page_status=chunk["page_status"],
                document_status=chunk["document_status"],
            )
        )
    return results
