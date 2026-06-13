from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ProjectPaths
from .pdf_engine import extract_pages, sha256_file
from .store import PlantTraceStore


@dataclass(frozen=True)
class IndexReport:
    total_pdfs: int
    indexed: int
    skipped: int
    failed: int


def index_folder(project_root: Path, pdf_root: Path, force: bool = False, enable_ocr: bool = False, ocr_lang: str = "eng") -> IndexReport:
    paths = ProjectPaths(Path(project_root).resolve())
    store = PlantTraceStore(paths)
    store.init()

    pdfs = sorted(path for path in Path(pdf_root).resolve().rglob("*.pdf") if path.is_file())
    indexed = 0
    skipped = 0
    failed = 0
    for pdf in pdfs:
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
    return IndexReport(total_pdfs=len(pdfs), indexed=indexed, skipped=skipped, failed=failed)
