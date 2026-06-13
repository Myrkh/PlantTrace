from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import fitz


def run_root() -> Path:
    path = Path("test-runs") / uuid4().hex
    path.mkdir(parents=True)
    return path


def make_pdf(path: Path, pages: list[str]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(path)
    document.close()
