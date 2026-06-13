from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.matrix_exports import export_project_matrix
from planttrace.project_matrix import ProjectMatrixRow, build_project_matrix


class MatrixPanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.rows: list[ProjectMatrixRow] = []
        self.status_label = QLabel()
        self.run_button = QPushButton("Construire matrice")
        self.export_button = QPushButton("Exporter matrice")
        self.table = QTableWidget(0, 10)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Construit une matrice projet par reference extraite, famille documentaire, conflits et revisions.")
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.build_matrix)
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
        headers = ["Type", "Reference", "Occ.", "Docs", "Familles", "PID/PFD", "Loop", "Datasheet", "Alertes", "Preuve"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {1, 4, 8, 9} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def build_matrix(self) -> None:
        try:
            self.rows = build_project_matrix(self.window.project_root(), self.window.conflicts_panel.findings, self.window.revisions_panel.changes)
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Matrice impossible: {exc}")
            return
        self.fill_table()
        alerted = sum(1 for row in self.rows if row.conflicts or row.revisions)
        self.status_label.setText(f"{len(self.rows)} reference(s), {alerted} ligne(s) avec alerte conflit ou revision.")

    def export_results(self) -> None:
        if not self.rows:
            QMessageBox.warning(self, "PlantTrace", "Construire la matrice avant export.")
            return
        output = self.pick_export_path()
        if output:
            export_project_matrix(self.rows, output)
            self.status_label.setText(f"Export matrice projet: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export matrice projet", str(self.window.project_root() / "planttrace-matrice.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        rows = [matrix_row_values(row) for row in self.rows]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def matrix_row_values(row: ProjectMatrixRow) -> list[str]:
    alerts = "; ".join(value for value in [row.conflicts, row.revisions] if value)
    return [
        row.kind,
        row.reference,
        str(row.occurrence_count),
        str(row.document_count),
        row.family_summary,
        str(row.pid_pfd),
        str(row.loop),
        str(row.datasheet),
        alerts,
        row.best_excerpt,
    ]
