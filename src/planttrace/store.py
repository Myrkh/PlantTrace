from __future__ import annotations

import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable

from .models import PdfPage, ProjectPaths, SearchResult
from .normalization import compact_identifier, compact_ocr_identifier, fold_text, query_tokens


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    page_count INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    ocr_normalized_text TEXT NOT NULL,
    status TEXT NOT NULL,
    UNIQUE(document_id, page_number)
);

CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
    text,
    normalized_text,
    filename,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    embedding_offset INTEGER,
    UNIQUE(page_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    page_id INTEGER,
    stage TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class PlantTraceStore:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def init(self) -> None:
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.paths.db_path)
        con.row_factory = sqlite3.Row
        return con

    def upsert_document(self, pdf_path: Path, sha256: str, size: int, mtime: float, pages: list[PdfPage], status: str) -> int:
        self.init()
        with self.connect() as con:
            con.execute(
                """
                INSERT INTO documents(path, filename, sha256, size, mtime, page_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    filename=excluded.filename,
                    sha256=excluded.sha256,
                    size=excluded.size,
                    mtime=excluded.mtime,
                    page_count=excluded.page_count,
                    status=excluded.status
                """,
                (str(pdf_path), pdf_path.name, sha256, size, mtime, len(pages), status),
            )
            document_id = int(con.execute("SELECT id FROM documents WHERE path = ?", (str(pdf_path),)).fetchone()[0])
            page_ids = [row[0] for row in con.execute("SELECT id FROM pages WHERE document_id = ?", (document_id,))]
            if page_ids:
                con.executemany("DELETE FROM pages_fts WHERE rowid = ?", [(page_id,) for page_id in page_ids])
            con.execute("DELETE FROM chunks WHERE page_id IN (SELECT id FROM pages WHERE document_id = ?)", (document_id,))
            con.execute("DELETE FROM pages WHERE document_id = ?", (document_id,))
            for page in pages:
                page_cur = con.execute(
                    """
                    INSERT INTO pages(document_id, page_number, text, normalized_text, ocr_normalized_text, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        page.page_number,
                        page.text,
                        compact_identifier(page.text),
                        compact_ocr_identifier(page.text),
                        page.status,
                    ),
                )
                page_id = int(page_cur.lastrowid)
                con.execute(
                    "INSERT INTO pages_fts(rowid, text, normalized_text, filename) VALUES (?, ?, ?, ?)",
                    (page_id, page.text, compact_identifier(page.text), pdf_path.name),
                )
                for index, chunk in enumerate(chunk_text(page.text), start=1):
                    con.execute(
                        "INSERT INTO chunks(page_id, chunk_index, text, normalized_text) VALUES (?, ?, ?, ?)",
                        (page_id, index, chunk, compact_identifier(chunk)),
                    )
            return document_id

    def document_is_current(self, pdf_path: Path, size: int, mtime: float) -> bool:
        self.init()
        with self.connect() as con:
            row = con.execute("SELECT size, mtime FROM documents WHERE path = ?", (str(pdf_path),)).fetchone()
        return bool(row and int(row["size"]) == size and float(row["mtime"]) == mtime)

    def exact_search(self, query: str) -> list[SearchResult]:
        needle = compact_identifier(query)
        ocr_needle = compact_ocr_identifier(query)
        if not needle:
            return []
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT d.path, d.status AS document_status, p.page_number, p.text, p.status AS page_status,
                       CASE
                           WHEN p.normalized_text LIKE ? THEN 'exact_normalized'
                           WHEN p.ocr_normalized_text LIKE ? THEN 'ocr_confusion_normalized'
                           ELSE 'unknown'
                       END AS match_type
                FROM pages p
                JOIN documents d ON d.id = p.document_id
                WHERE p.normalized_text LIKE ? OR p.ocr_normalized_text LIKE ?
                ORDER BY d.path, p.page_number
                """,
                (f"%{needle}%", f"%{ocr_needle}%", f"%{needle}%", f"%{ocr_needle}%"),
            ).fetchall()
        return [
            SearchResult(
                query=query,
                match_type=row["match_type"],
                document_path=row["path"],
                page=int(row["page_number"]),
                score=100.0,
                found_as=find_surface(row["text"], needle),
                excerpt=excerpt_around(row["text"], needle),
                page_status=row["page_status"],
                document_status=row["document_status"],
            )
            for row in rows
        ]

    def fts_search(self, query: str, limit: int = 50) -> list[SearchResult]:
        fts_query = build_fts_query(query)
        if not fts_query:
            return []
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT d.path, d.status AS document_status, p.page_number, p.status AS page_status,
                       bm25(pages_fts) AS rank,
                       snippet(pages_fts, 0, '[', ']', ' ... ', 24) AS snippet
                FROM pages_fts
                JOIN pages p ON p.id = pages_fts.rowid
                JOIN documents d ON d.id = p.document_id
                WHERE pages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
        return [
            SearchResult(
                query=query,
                match_type="text_bm25",
                document_path=row["path"],
                page=int(row["page_number"]),
                score=float(-row["rank"]),
                found_as="",
                excerpt=row["snippet"],
                page_status=row["page_status"],
                document_status=row["document_status"],
            )
            for row in rows
        ]

    def fuzzy_search(self, query: str, limit: int = 25, minimum_score: float = 0.72) -> list[SearchResult]:
        tokens = query_tokens(query)
        if not tokens:
            return []
        candidates: list[SearchResult] = []
        with self.connect() as con:
            rows = con.execute(
                """
                SELECT d.path, d.status AS document_status, p.page_number, p.status AS page_status, c.text
                FROM chunks c
                JOIN pages p ON p.id = c.page_id
                JOIN documents d ON d.id = p.document_id
                WHERE c.text <> ''
                """
            ).fetchall()
        for row in rows:
            score = fuzzy_score(tokens, row["text"])
            if score < minimum_score:
                continue
            candidates.append(
                SearchResult(
                    query=query,
                    match_type="fuzzy_text",
                    document_path=row["path"],
                    page=int(row["page_number"]),
                    score=score,
                    found_as="",
                    excerpt=" ".join(row["text"][:500].split()),
                    page_status=row["page_status"],
                    document_status=row["document_status"],
                )
            )
        candidates.sort(key=lambda item: (-item.score, item.document_path, item.page or 0))
        return candidates[:limit]

    def coverage(self) -> dict[str, int]:
        self.init()
        with self.connect() as con:
            row = con.execute(
                """
                SELECT
                    COUNT(DISTINCT d.id) AS documents,
                    COUNT(p.id) AS pages,
                    SUM(CASE WHEN p.status IN ('ok', 'ocr_ok') THEN 1 ELSE 0 END) AS text_pages,
                    SUM(CASE WHEN p.status = 'ocr_required' THEN 1 ELSE 0 END) AS ocr_required_pages,
                    SUM(CASE WHEN p.status = 'ocr_failed' THEN 1 ELSE 0 END) AS ocr_failed_pages
                FROM documents d
                LEFT JOIN pages p ON p.document_id = d.id
                """
            ).fetchone()
        return {key: int(row[key] or 0) for key in row.keys()}

    def all_chunks(self) -> list[sqlite3.Row]:
        self.init()
        with self.connect() as con:
            return con.execute(
                """
                SELECT c.id, c.text
                FROM chunks c
                JOIN pages p ON p.id = c.page_id
                JOIN documents d ON d.id = p.document_id
                WHERE c.text <> ''
                ORDER BY d.path, p.page_number, c.chunk_index
                """
            ).fetchall()

    def set_embedding_offsets(self, chunk_ids: list[int]) -> None:
        self.init()
        with self.connect() as con:
            con.execute("UPDATE chunks SET embedding_offset = NULL")
            con.executemany(
                "UPDATE chunks SET embedding_offset = ? WHERE id = ?",
                [(offset, chunk_id) for offset, chunk_id in enumerate(chunk_ids)],
            )

    def embedded_chunks(self) -> list[sqlite3.Row]:
        self.init()
        with self.connect() as con:
            return con.execute(
                """
                SELECT c.id, c.text, c.embedding_offset, d.path, d.status AS document_status,
                       p.page_number, p.status AS page_status
                FROM chunks c
                JOIN pages p ON p.id = c.page_id
                JOIN documents d ON d.id = p.document_id
                WHERE c.embedding_offset IS NOT NULL
                ORDER BY c.embedding_offset
                """
            ).fetchall()

    def indexed_pages(self) -> list[sqlite3.Row]:
        self.init()
        with self.connect() as con:
            return con.execute(
                """
                SELECT d.path, d.status AS document_status, p.page_number, p.text, p.status AS page_status
                FROM pages p
                JOIN documents d ON d.id = p.document_id
                WHERE p.text <> ''
                ORDER BY d.path, p.page_number
                """
            ).fetchall()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 180) -> Iterable[str]:
    compact = " ".join(text.split())
    if not compact:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(compact):
        end = min(len(compact), start + max_chars)
        chunks.append(compact[start:end])
        if end == len(compact):
            break
        start = max(0, end - overlap)
    return chunks


def build_fts_query(query: str) -> str:
    tokens = [token for token in query.replace('"', " ").split() if len(token.strip()) >= 2]
    if not tokens:
        return ""
    return " AND ".join(f'"{token}"' for token in tokens[:12])


def excerpt_around(text: str, compact_query: str, width: int = 120) -> str:
    normalized = compact_identifier(text)
    position = normalized.find(compact_query)
    if position < 0:
        return " ".join(text[: width * 2].split())
    surface, offsets = normalized_offsets(text)
    original_start = offsets[min(position, len(offsets) - 1)] if offsets else 0
    start = max(0, original_start - width)
    end = min(len(text), original_start + width)
    return " ".join(text[start:end].split())


def find_surface(text: str, compact_query: str) -> str:
    normalized, offsets = normalized_offsets(text)
    position = normalized.find(compact_query)
    if position < 0 or not offsets:
        return ""
    start = offsets[position]
    end = offsets[min(position + len(compact_query) - 1, len(offsets) - 1)] + 1
    return text[start:end]


def normalized_offsets(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    offsets: list[int] = []
    for index, char in enumerate(text):
        if char.isalnum():
            chars.append(char.upper())
            offsets.append(index)
    return "".join(chars), offsets


def fuzzy_score(query_terms: list[str], text: str) -> float:
    words = query_tokens(text)
    if not words:
        return 0.0
    folded = fold_text(text)
    total = 0.0
    for term in query_terms:
        if term in folded:
            total += 1.0
            continue
        total += max(SequenceMatcher(None, term, word).ratio() for word in words)
    return total / len(query_terms)
