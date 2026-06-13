from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QFileDialog,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from planttrace.batch import BatchReferenceResult, load_reference_file, parse_references, run_batch_search
from planttrace.export import export_batch


class BatchPanel(QWidget):
    def __init__(self, project_root: Callable[[], Path]) -> None:
        super().__init__()
        self.project_root = project_root
        self.results: list[BatchReferenceResult] = []
        self.references_edit = QPlainTextEdit()
        self.mode_combo = QComboBox()
        self.load_button = QPushButton("Charger liste")
        self.run_button = QPushButton("Analyser batch")
        self.export_button = QPushButton("Exporter matrice")
        self.status_label = QLabel()
        self.table = QTableWidget(0, 7)
        self.build_ui()

    def build_ui(self) -> None:
        self.references_edit.setPlaceholderText("Coller une reference par ligne : FV1100, 10-P-12345, JDY...")
        self.mode_combo.addItems(["hybrid", "auto", "exact", "text", "fuzzy"])
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Batch: colle ou charge une liste, puis lance l'analyse sur l'index local.")
        self.load_button.setObjectName("secondaryButton")
        self.export_button.setObjectName("secondaryButton")
        self.load_button.clicked.connect(self.load_references)
        self.run_button.clicked.connect(self.run_batch)
        self.export_button.clicked.connect(self.export_results)
        self.configure_table()

        actions = QHBoxLayout()
        actions.addWidget(self.mode_combo)
        actions.addWidget(self.load_button)
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)
        actions.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addWidget(self.references_edit, 1)
        layout.addLayout(actions)
        layout.addWidget(self.table, 3)

    def configure_table(self) -> None:
        headers = ["Reference", "Statut", "Hits", "Documents", "Pages", "Match", "Extrait"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {3, 6} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def load_references(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Liste de references", str(self.project_root()), "Listes (*.xlsx *.csv *.txt);;Tous les fichiers (*.*)")
        if not path:
            return
        try:
            references = load_reference_file(Path(path))
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Impossible de charger la liste: {exc}")
            return
        self.references_edit.setPlainText("\n".join(references))
        self.status_label.setText(f"{len(references)} reference(s) chargee(s).")

    def run_batch(self) -> None:
        references = parse_references(self.references_edit.toPlainText())
        if not references:
            QMessageBox.warning(self, "PlantTrace", "Aucune reference batch a analyser.")
            return
        self.results = run_batch_search(self.project_root(), references, self.mode_combo.currentText())
        self.fill_table()
        found = sum(1 for result in self.results if result.status == "found")
        self.status_label.setText(f"Batch termine: {found}/{len(self.results)} reference(s) trouvee(s) dans l'index.")

    def export_results(self) -> None:
        if not self.results:
            QMessageBox.warning(self, "PlantTrace", "Aucun resultat batch a exporter.")
            return
        output = self.pick_export_path()
        if output:
            try:
                export_batch(self.results, output)
            except Exception as exc:
                QMessageBox.warning(self, "PlantTrace", f"Export batch impossible: {exc}")
                return
            self.status_label.setText(f"Export batch: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export batch XLSX", str(self.project_root() / "planttrace-batch.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        rows = [batch_row_values(result) for result in self.results]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def batch_row_values(result: BatchReferenceResult) -> list[str]:
    return [
        result.reference,
        result.status,
        str(result.hit_count),
        result.documents,
        result.pages,
        result.best_match_type,
        result.best_excerpt,
    ]
