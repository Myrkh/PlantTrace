from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .models import ProjectPaths
from .pdf_engine import extract_pages, sha256_file
from .store import PlantTraceStore


@dataclass(frozen=True)
class IndexReport:
    total_pdfs: int
    indexed: int
    skipped: int
    failed: int


def index_folder(
    project_root: Path,
    pdf_root: Path,
    force: bool = False,
    enable_ocr: bool = False,
    ocr_lang: str = "eng",
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> IndexReport:
    paths = ProjectPaths(Path(project_root).resolve())
    store = PlantTraceStore(paths)
    store.init()

    pdfs = sorted(path for path in Path(pdf_root).resolve().rglob("*.pdf") if path.is_file())
    total = len(pdfs)
    indexed = 0
    skipped = 0
    failed = 0
    for position, pdf in enumerate(pdfs):
        if progress_callback is not None:
            progress_callback(position, total, pdf.name)
        stat = pdf.stat()
        if not force and store.document_is_current(pdf, stat.st_size, stat.st_mtime):
            skipped += 1
            continue
        pages, status = extract_pages(pdf, enable_ocr=enable_ocr, ocr_lang=ocr_lang)
        if status.startswith("extract_error") or status == "encrypted":
            failed += 1
        store.upsert_document(
            pdf_path=pdf,
            sha256=sha256_file(pdf),
            size=stat.st_size,
            mtime=stat.st_mtime,
            pages=pages,
            status=status,
        )
        indexed += 1
    if progress_callback is not None:
        progress_callback(total, total, "")
    return IndexReport(total_pdfs=total, indexed=indexed, skipped=skipped, failed=failed)
