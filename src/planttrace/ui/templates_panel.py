from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QComboBox, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.template_exports import export_template_run
from planttrace.templates import TagRegisterRow, TemplateRun, available_templates, run_template


class TemplatesPanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.current_run: TemplateRun | None = None
        self.status_label = QLabel()
        self.template_combo = QComboBox()
        self.run_button = QPushButton("Executer template")
        self.export_button = QPushButton("Exporter template")
        self.table = QTableWidget(0, 9)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Genere un tableau metier depuis les references extraites. Les cellules sont remplies uniquement avec preuves locales.")
        self.template_combo.addItems(available_templates())
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.execute_template)
        self.export_button.clicked.connect(self.export_results)
        self.configure_table()

        actions = QHBoxLayout()
        actions.addWidget(QLabel("Template"))
        actions.addWidget(self.template_combo, 1)
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(actions)
        layout.addWidget(self.table, 1)

    def configure_table(self) -> None:
        headers = ["TAG", "Description", "Lignes", "Documents", "Familles", "Sources", "Preuves", "Alertes", "Extrait"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {0, 1, 2, 3, 5, 8} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def execute_template(self) -> None:
        try:
            self.current_run = run_template(
                self.window.project_root(),
                self.template_combo.currentText(),
                self.window.conflicts_panel.findings,
                self.window.revisions_panel.changes,
            )
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Template impossible: {exc}")
            return
        self.fill_table()
        self.status_label.setText(f"{self.current_run.name}: {len(self.current_run.rows)} ligne(s) generee(s). Export Excel conseille pour le detail complet.")

    def export_results(self) -> None:
        if self.current_run is None:
            QMessageBox.warning(self, "PlantTrace", "Executer un template avant export.")
            return
        output = self.pick_export_path()
        if output:
            export_template_run(self.current_run, output)
            self.status_label.setText(f"Export template: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export template", str(self.window.project_root() / "planttrace-template.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        if self.current_run is None:
            return
        rows = [template_row_values(row) for row in self.current_run.rows]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def template_row_values(row: TagRegisterRow) -> list[str]:
    alerts = "; ".join(value for value in [row.conflicts, row.revisions] if value)
    return [
        row.tag,
        row.description,
        row.lines,
        row.documents,
        row.families,
        row.source_documents,
        str(row.evidence_count),
        alerts,
        row.best_excerpt,
    ]
