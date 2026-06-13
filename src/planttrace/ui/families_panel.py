from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.doc_families import DocumentFamily, classify_documents
from planttrace.export import export_doc_families


class FamiliesPanel(QWidget):
    def __init__(self, project_root: Callable[[], Path]) -> None:
        super().__init__()
        self.project_root = project_root
        self.families: list[DocumentFamily] = []
        self.status_label = QLabel()
        self.run_button = QPushButton("Classifier documents")
        self.export_button = QPushButton("Exporter familles")
        self.table = QTableWidget(0, 6)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Classe les PDF indexés par famille documentaire avec preuve et confiance.")
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.run_classification)
        self.export_button.clicked.connect(self.export_results)
        self.configure_table()

        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)
        actions.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)
        layout.addWidget(self.table, 1)

    def configure_table(self) -> None:
        headers = ["Famille", "Confiance", "Score", "Fichier", "Pages", "Preuve"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {3, 5} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def run_classification(self) -> None:
        try:
            self.families = classify_documents(self.project_root())
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Classification impossible: {exc}")
            return
        self.fill_table()
        unknown = sum(1 for family in self.families if family.family == "UNKNOWN")
        self.status_label.setText(f"{len(self.families)} document(s) classes, {unknown} a classer manuellement.")

    def export_results(self) -> None:
        if not self.families:
            QMessageBox.warning(self, "PlantTrace", "Aucune famille a exporter.")
            return
        output = self.pick_export_path()
        if output:
            export_doc_families(self.families, output)
            self.status_label.setText(f"Export familles: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export familles documentaires", str(self.project_root() / "planttrace-familles.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        rows = [family_row_values(family) for family in self.families]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def family_row_values(family: DocumentFamily) -> list[str]:
    return [family.label, family.confidence, str(family.score), family.filename, str(family.pages), family.evidence]
