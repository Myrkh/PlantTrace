from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from planttrace.indexer import index_folder
from planttrace.revisions import compare_revision_folders
from planttrace.semantic import rebuild_embeddings


class IndexWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, project_root: Path, pdf_root: Path, force: bool, enable_ocr: bool, ocr_lang: str) -> None:
        super().__init__()
        self.project_root = project_root
        self.pdf_root = pdf_root
        self.force = force
        self.enable_ocr = enable_ocr
        self.ocr_lang = ocr_lang

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(index_folder(self.project_root, self.pdf_root, self.force, self.enable_ocr, self.ocr_lang))
        except Exception as exc:
            self.failed.emit(str(exc))


class EmbedWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self.project_root = project_root

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(rebuild_embeddings(self.project_root))
        except Exception as exc:
            self.failed.emit(str(exc))


class RevisionCompareWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, project_root: Path, old_pdf_root: Path, new_pdf_root: Path, enable_ocr: bool, ocr_lang: str) -> None:
        super().__init__()
        self.project_root = project_root
        self.old_pdf_root = old_pdf_root
        self.new_pdf_root = new_pdf_root
        self.enable_ocr = enable_ocr
        self.ocr_lang = ocr_lang

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(compare_revision_folders(self.project_root, self.old_pdf_root, self.new_pdf_root, enable_ocr=self.enable_ocr, ocr_lang=self.ocr_lang))
        except Exception as exc:
            self.failed.emit(str(exc))
