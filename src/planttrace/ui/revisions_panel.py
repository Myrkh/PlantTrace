from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from planttrace.export import export_revisions
from planttrace.revisions import RevisionChange, RevisionComparison
from planttrace.ui.icons import line_icon
from planttrace.ui.workers import RevisionCompareWorker


class RevisionsPanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.comparison: RevisionComparison | None = None
        self.changes: list[RevisionChange] = []
        self.old_edit = QLineEdit()
        self.new_edit = QLineEdit()
        self.status_label = QLabel()
        self.run_button = QPushButton("Comparer revisions")
        self.export_button = QPushButton("Exporter delta")
        self.table = QTableWidget(0, 6)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText("Comparer deux dossiers PDF. PlantTrace signale les references ajoutees, supprimees ou modifiees avec preuves.")
        self.old_edit.setPlaceholderText("Dossier ancienne revision")
        self.new_edit.setPlaceholderText("Dossier nouvelle revision")
        self.export_button.setObjectName("secondaryButton")
        self.run_button.clicked.connect(self.run_comparison)
        self.export_button.clicked.connect(self.export_results)
        self.configure_table()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(self.folder_row("Ancienne revision", self.old_edit, self.choose_old_folder))
        layout.addLayout(self.folder_row("Nouvelle revision", self.new_edit, self.choose_new_folder))
        actions = QHBoxLayout()
        actions.addWidget(self.run_button)
        actions.addWidget(self.export_button)
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(self.table, 1)

    def folder_row(self, label_text: str, edit: QLineEdit, slot: object) -> QHBoxLayout:
        button = QPushButton()
        button.setObjectName("folderButton")
        button.setIcon(line_icon("index", "#26312b"))
        button.clicked.connect(slot)
        row = QHBoxLayout()
        row.addWidget(QLabel(label_text))
        row.addWidget(edit, 1)
        row.addWidget(button)
        return row

    def configure_table(self) -> None:
        headers = ["Statut", "Type", "Reference", "Ancienne preuve", "Nouvelle preuve", "Synthese"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {3, 4, 5} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def choose_old_folder(self) -> None:
        self.choose_folder(self.old_edit, "Choisir ancienne revision")

    def choose_new_folder(self) -> None:
        self.choose_folder(self.new_edit, "Choisir nouvelle revision")

    def choose_folder(self, edit: QLineEdit, title: str) -> None:
        folder = QFileDialog.getExistingDirectory(self, title, str(self.window.project_root()))
        if folder:
            edit.setText(folder)

    def run_comparison(self) -> None:
        old_root = Path(self.old_edit.text()).expanduser()
        new_root = Path(self.new_edit.text()).expanduser()
        if not old_root.exists() or not new_root.exists():
            QMessageBox.warning(self, "PlantTrace", "Choisir les deux dossiers de revisions avant comparaison.")
            return
        worker = RevisionCompareWorker(
            self.window.project_root(),
            old_root,
            new_root,
            self.window.ocr_check.isChecked(),
            self.window.ocr_lang_edit.text().strip() or "eng",
        )
        worker.failed.connect(lambda _message: self.set_controls_enabled(True))
        self.set_controls_enabled(False)
        self.status_label.setText("Comparaison en cours: indexation isolee des deux revisions puis extraction des deltas...")
        if not self.window.run_worker(worker, self.on_comparison_finished):
            self.set_controls_enabled(True)

    def on_comparison_finished(self, comparison: RevisionComparison) -> None:
        self.set_controls_enabled(True)
        self.comparison = comparison
        self.changes = comparison.changes
        self.fill_table()
        self.status_label.setText(
            f"{len(self.changes)} delta(s). Ancienne rev: {comparison.old_report.total_pdfs} PDF. Nouvelle rev: {comparison.new_report.total_pdfs} PDF."
        )

    def set_controls_enabled(self, enabled: bool) -> None:
        self.run_button.setEnabled(enabled)
        self.export_button.setEnabled(enabled)

    def export_results(self) -> None:
        if not self.changes:
            QMessageBox.warning(self, "PlantTrace", "Aucun delta a exporter.")
            return
        output = self.pick_export_path()
        if output:
            export_revisions(self.changes, output)
            self.status_label.setText(f"Export delta revisions: {output}")

    def pick_export_path(self) -> Path | None:
        output, _ = QFileDialog.getSaveFileName(self, "Export delta revisions", str(self.window.project_root() / "planttrace-revisions.xlsx"), "Excel (*.xlsx);;CSV (*.csv)")
        return Path(output) if output else None

    def fill_table(self) -> None:
        rows = [revision_row_values(change) for change in self.changes]
        self.table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def revision_row_values(change: RevisionChange) -> list[str]:
    return [
        change.status,
        change.kind,
        change.reference,
        change.old_locations,
        change.new_locations,
        change.summary,
    ]
