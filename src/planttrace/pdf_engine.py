from __future__ import annotations

import hashlib
import shutil
from io import BytesIO
from pathlib import Path

import fitz

from .models import PdfPage


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_pages(path: Path, enable_ocr: bool = False, ocr_lang: str = "eng") -> tuple[list[PdfPage], str]:
    try:
        document = fitz.open(path)
    except Exception as exc:
        return [], f"extract_error: {exc}"

    if document.needs_pass:
        document.close()
        return [], "encrypted"

    pages: list[PdfPage] = []
    try:
        for index, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True) or ""
            status = "ok" if text.strip() else "ocr_required"
            if not text.strip() and enable_ocr:
                text, status = ocr_page(page, ocr_lang)
            pages.append(PdfPage(page_number=index, text=text, status=status))
    except Exception as exc:
        document.close()
        return pages, f"partial_extract_error: {exc}"
    finally:
        document.close()

    if not pages:
        return pages, "no_pages"
    if all(page.status in {"ocr_required", "ocr_failed"} for page in pages):
        return pages, "ocr_required"
    if any(page.status in {"ocr_required", "ocr_failed"} for page in pages):
        return pages, "partial_text"
    return pages, "ok"


def ocr_available() -> bool:
    return shutil.which("tesseract") is not None


def ocr_page(page: fitz.Page, lang: str) -> tuple[str, str]:
    if not ocr_available():
        return "", "ocr_required"
    try:
        from PIL import Image
        import pytesseract

        pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        image = Image.open(BytesIO(pixmap.tobytes("png")))
        text = pytesseract.image_to_string(image, lang=lang)
    except Exception:
        return "", "ocr_failed"
    return (text, "ocr_ok") if text.strip() else ("", "ocr_failed")


def render_page_png(path: Path, page_number: int, output: Path, zoom: float = 1.5) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(path) as document:
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pixmap.save(output)
