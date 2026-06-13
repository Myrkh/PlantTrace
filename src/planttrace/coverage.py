from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ProjectPaths
from .store import PlantTraceStore


@dataclass(frozen=True)
class CoverageDocument:
    filename: str
    path: str
    triage: str
    status: str
    pages: int
    text_pages: int
    ocr_required_pages: int
    ocr_failed_pages: int
    coverage_percent: float


@dataclass(frozen=True)
class CoverageTask:
    filename: str
    path: str
    page: int
    page_status: str
    action: str
    reason: str


def coverage_documents(project_root: Path) -> list[CoverageDocument]:
    store = PlantTraceStore(ProjectPaths(Path(project_root).resolve()))
    store.init()
    with store.connect() as con:
        rows = con.execute(
            """
            SELECT
                d.filename,
                d.path,
                d.status,
                d.page_count,
                SUM(CASE WHEN p.status IN ('ok', 'ocr_ok') THEN 1 ELSE 0 END) AS text_pages,
                SUM(CASE WHEN p.status = 'ocr_required' THEN 1 ELSE 0 END) AS ocr_required_pages,
                SUM(CASE WHEN p.status = 'ocr_failed' THEN 1 ELSE 0 END) AS ocr_failed_pages
            FROM documents d
            LEFT JOIN pages p ON p.document_id = d.id
            GROUP BY d.id
            ORDER BY d.path
            """
        ).fetchall()
    documents: list[CoverageDocument] = []
    for row in rows:
        pages = int(row["page_count"] or 0)
        text_pages = int(row["text_pages"] or 0)
        documents.append(
            CoverageDocument(
                filename=row["filename"],
                path=row["path"],
                triage=coverage_triage(
                    pages,
                    text_pages,
                    int(row["ocr_required_pages"] or 0),
                    int(row["ocr_failed_pages"] or 0),
                ),
                status=row["status"],
                pages=pages,
                text_pages=text_pages,
                ocr_required_pages=int(row["ocr_required_pages"] or 0),
                ocr_failed_pages=int(row["ocr_failed_pages"] or 0),
                coverage_percent=round((text_pages / pages) * 100, 1) if pages else 0.0,
            )
        )
    return documents


def coverage_tasks(project_root: Path) -> list[CoverageTask]:
    store = PlantTraceStore(ProjectPaths(Path(project_root).resolve()))
    store.init()
    with store.connect() as con:
        rows = con.execute(
            """
            SELECT d.filename, d.path, p.page_number, p.status
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            WHERE p.status IN ('ocr_required', 'ocr_failed')
            ORDER BY d.path, p.page_number
            """
        ).fetchall()
    return [
        CoverageTask(
            filename=row["filename"],
            path=row["path"],
            page=int(row["page_number"]),
            page_status=row["status"],
            action=task_action(row["status"]),
            reason=task_reason(row["status"]),
        )
        for row in rows
    ]


def task_action(page_status: str) -> str:
    if page_status == "ocr_failed":
        return "Verifier PDF/OCR"
    return "Indexer avec OCR"


def task_reason(page_status: str) -> str:
    if page_status == "ocr_failed":
        return "OCR tente mais texte inexploitable."
    return "Page sans texte exploitable dans l'index."


def coverage_triage(pages: int, text_pages: int, ocr_required_pages: int, ocr_failed_pages: int) -> str:
    if pages == 0:
        return "vide"
    if ocr_failed_pages:
        return "ocr_failed"
    if ocr_required_pages:
        return "ocr_required"
    if text_pages < pages:
        return "incomplete"
    return "ok"


def coverage_verdict(summary: dict[str, int]) -> str:
    if summary["documents"] == 0:
        return "Corpus vide: indexer un dossier PDF avant de conclure."
    missing = summary["ocr_required_pages"] + summary["ocr_failed_pages"]
    if missing:
        return f"Couverture incomplete: {missing} page(s) non lisible(s). Toute absence reste qualifiee."
    return "Couverture complete sur l'index: les absences sont qualifiees sur le corpus indexe."
