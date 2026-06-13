from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from planttrace.coverage import CoverageDocument, CoverageTask, coverage_documents, coverage_tasks, coverage_verdict
from planttrace.export import export_coverage, export_coverage_tasks
from planttrace.models import ProjectPaths
from planttrace.store import PlantTraceStore


class CoveragePanel(QWidget):
    def __init__(self, project_root: Callable[[], Path]) -> None:
        super().__init__()
        self.project_root = project_root
        self.documents: list[CoverageDocument] = []
        self.tasks: list[CoverageTask] = []
        self.summary_label = QLabel()
        self.verdict_label = QLabel()
        self.filter_combo = QComboBox()
        self.refresh_button = QPushButton("Actualiser")
        self.open_button = QPushButton("Ouvrir PDF")
        self.export_button = QPushButton("Exporter rapport")
        self.export_tasks_button = QPushButton("Exporter triage OCR")
        self.table = QTableWidget(0, 9)
        self.task_table = QTableWidget(0, 6)
        self.build_ui()

    def build_ui(self) -> None:
        for label in [self.summary_label, self.verdict_label]:
            label.setObjectName("metricLabel")
            label.setWordWrap(True)
        for button in [self.open_button, self.export_button, self.export_tasks_button]:
            button.setObjectName("secondaryButton")
        self.filter_combo.addItems(["Tous", "A traiter OCR", "OCR requis", "OCR echec", "OK"])
        self.filter_combo.currentTextChanged.connect(lambda _text: self.fill_table())
        self.refresh_button.clicked.connect(self.refresh)
        self.open_button.clicked.connect(self.open_selected_pdf)
        self.export_button.clicked.connect(self.export_report)
        self.export_tasks_button.clicked.connect(self.export_triage)
        self.configure_table()
        self.configure_task_table()

        actions = QHBoxLayout()
        actions.addWidget(self.filter_combo)
        actions.addWidget(self.refresh_button)
        actions.addWidget(self.open_button)
        actions.addWidget(self.export_button)
        actions.addWidget(self.export_tasks_button)
        actions.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.verdict_label)
        layout.addLayout(actions)
        layout.addWidget(self.table, 1)
        layout.addWidget(section("Pages a traiter OCR"))
        layout.addWidget(self.task_table, 1)
        self.refresh()

    def configure_table(self) -> None:
        headers = ["Fichier", "Triage", "Statut", "Pages", "Texte", "OCR requis", "OCR echec", "Couverture", "Chemin"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(lambda row, _column: self.open_document_pdf(row))
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {0, 8} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def configure_task_table(self) -> None:
        headers = ["Fichier", "Page", "Statut page", "Action", "Raison", "Chemin"]
        self.task_table.setHorizontalHeaderLabels(headers)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.cellDoubleClicked.connect(lambda row, _column: self.open_task_pdf(row))
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {0, 4, 5} else QHeaderView.ResizeMode.ResizeToContents
            self.task_table.horizontalHeader().setSectionResizeMode(index, mode)

    def refresh(self) -> None:
        store = PlantTraceStore(ProjectPaths(self.project_root()))
        summary = store.coverage()
        self.documents = coverage_documents(self.project_root())
        self.tasks = coverage_tasks(self.project_root())
        self.summary_label.setText(
            "docs {documents} | pages {pages} | texte {text_pages} | OCR requis {ocr_required_pages} | OCR echec {ocr_failed_pages}".format(**summary)
        )
        self.verdict_label.setText(coverage_verdict(summary))
        self.fill_table()
        self.fill_task_table()

    def export_report(self) -> None:
        if not self.documents:
            QMessageBox.warning(self, "PlantTrace", "Aucun document de couverture a exporter.")
            return
        output = self.pick_export_path()
        if output:
            try:
                export_coverage(self.documents, output)
            except Exception as exc:
                QMessageBox.warning(self, "PlantTrace", f"Export couverture impossible: {exc}")

    def export_triage(self) -> None:
        if not self.tasks:
            QMessageBox.warning(self, "PlantTrace", "Aucune page OCR a traiter.")
            return
        output = self.pick_triage_export_path()
        if output:
            try:
                export_coverage_tasks(self.tasks, output)
            except Exception as exc:
                QMessageBox.warning(self, "PlantTrace", f"Export triage impossible: {exc}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export couverture XLSX", str(self.project_root() / "planttrace-coverage.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def pick_triage_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export triage OCR", str(self.project_root() / "planttrace-ocr-triage.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def open_selected_pdf(self) -> None:
        task_row = self.task_table.currentRow()
        if task_row >= 0:
            self.open_task_pdf(task_row)
            return
        row = self.table.currentRow()
        if row >= 0:
            self.open_document_pdf(row)

    def open_document_pdf(self, row: int) -> None:
        if 0 <= row < self.table.rowCount():
            item = self.table.item(row, 8)
            if item and item.text():
                QDesktopServices.openUrl(QUrl.fromLocalFile(item.text()))

    def open_task_pdf(self, row: int) -> None:
        if 0 <= row < self.task_table.rowCount():
            item = self.task_table.item(row, 5)
            if item and item.text():
                QDesktopServices.openUrl(QUrl.fromLocalFile(item.text()))

    def fill_table(self) -> None:
        rows = [coverage_row_values(document) for document in self.filtered_documents()]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))

    def fill_task_table(self) -> None:
        rows = [coverage_task_row_values(task) for task in self.tasks]
        self.task_table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.task_table.setItem(row_index, column, QTableWidgetItem(value))

    def filtered_documents(self) -> list[CoverageDocument]:
        selected = self.filter_combo.currentText()
        if selected == "A traiter OCR":
            return [document for document in self.documents if document.triage in {"ocr_required", "ocr_failed", "incomplete"}]
        if selected == "OCR requis":
            return [document for document in self.documents if document.triage == "ocr_required"]
        if selected == "OCR echec":
            return [document for document in self.documents if document.triage == "ocr_failed"]
        if selected == "OK":
            return [document for document in self.documents if document.triage == "ok"]
        return self.documents


def coverage_row_values(document: CoverageDocument) -> list[str]:
    return [
        document.filename,
        document.triage,
        document.status,
        str(document.pages),
        str(document.text_pages),
        str(document.ocr_required_pages),
        str(document.ocr_failed_pages),
        f"{document.coverage_percent:.1f}%",
        document.path,
    ]


def coverage_task_row_values(task: CoverageTask) -> list[str]:
    return [
        task.filename,
        str(task.page),
        task.page_status,
        task.action,
        task.reason,
        task.path,
    ]


def section(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("panelTitle")
    return label
