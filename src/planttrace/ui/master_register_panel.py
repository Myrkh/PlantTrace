from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from planttrace.master_register import MasterRegisterConfig, MasterRegisterResult
from planttrace.ui.workers import MasterRegisterWorker


class MasterRegisterPanel(QWidget):
    def __init__(self, window: object) -> None:
        super().__init__()
        self.window = window
        self.current_result: MasterRegisterResult | None = None
        self.status_label = QLabel()
        self.source_edit = QLineEdit()
        self.tags_template_edit = QLineEdit()
        self.links_template_edit = QLineEdit()
        self.output_edit = QLineEdit()
        self.plant_edit = QLineEdit("HTI199")
        self.site_edit = QLineEdit("GPS")
        self.build_button = QPushButton("Generer Master Register")
        self.table = QTableWidget(0, 7)
        self.build_ui()

    def build_ui(self) -> None:
        self.status_label.setObjectName("metricLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setText(
            "Genere les fichiers client Tags Template et Tags Documents Links Template depuis les listes Excel source et les PDF indexes."
        )
        self.build_button.clicked.connect(self.generate)
        self.configure_table()

        form = QFormLayout()
        form.addRow("Dossier source projet", path_picker_row(self.source_edit, self.choose_source_folder))
        form.addRow("Template Tags", path_picker_row(self.tags_template_edit, lambda: self.choose_file(self.tags_template_edit)))
        form.addRow("Template Links", path_picker_row(self.links_template_edit, lambda: self.choose_file(self.links_template_edit)))
        form.addRow("Dossier export", path_picker_row(self.output_edit, self.choose_output_folder))
        form.addRow("PlantNo", self.plant_edit)
        form.addRow("Site", self.site_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.status_label)
        layout.addLayout(form)
        layout.addWidget(self.build_button)
        layout.addWidget(self.table, 1)

    def configure_table(self) -> None:
        headers = ["TagNo", "Description", "TagType", "System", "Documents", "Preuves", "Deleted"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for index in range(len(headers)):
            mode = QHeaderView.ResizeMode.Stretch if index in {0, 1, 3, 4} else QHeaderView.ResizeMode.ResizeToContents
            self.table.horizontalHeader().setSectionResizeMode(index, mode)

    def generate(self) -> None:
        try:
            config = self.config()
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Master Register impossible: {exc}")
            return
        worker = MasterRegisterWorker(config, self.window.project_root())
        worker.failed.connect(lambda _message: self.build_button.setEnabled(True))
        if self.window.run_worker(worker, self.on_generated):
            self.build_button.setEnabled(False)
            self.window.statusBar().showMessage("Generation Master Register en cours...")

    def on_generated(self, result: MasterRegisterResult) -> None:
        self.build_button.setEnabled(True)
        self.current_result = result
        self.fill_table()
        self.status_label.setText(
            f"Master Register genere: {len(result.tags)} tag(s), {result.link_count} lien(s). Exports: {result.tags_output.name}, {result.links_output.name}."
        )

    def config(self) -> MasterRegisterConfig:
        source_root = Path(self.source_edit.text()).expanduser()
        tags_template = Path(self.tags_template_edit.text()).expanduser()
        links_template = Path(self.links_template_edit.text()).expanduser()
        output_dir = Path(self.output_edit.text()).expanduser()
        for path, label in [(source_root, "dossier source"), (tags_template, "template tags"), (links_template, "template links")]:
            if not path.exists():
                raise ValueError(f"{label} introuvable: {path}")
        if not self.plant_edit.text().strip():
            raise ValueError("PlantNo obligatoire.")
        if not self.site_edit.text().strip():
            raise ValueError("Site obligatoire.")
        return MasterRegisterConfig(
            source_root=source_root,
            tags_template=tags_template,
            links_template=links_template,
            output_dir=output_dir,
            plant_no=self.plant_edit.text().strip(),
            site=self.site_edit.text().strip(),
        )

    def choose_source_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Dossier source projet", self.source_edit.text() or str(self.window.project_root()))
        if path:
            self.source_edit.setText(path)
            if not self.output_edit.text():
                self.output_edit.setText(str(Path(path) / "PlantTrace Master Register"))

    def choose_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Dossier export", self.output_edit.text() or str(self.window.project_root()))
        if path:
            self.output_edit.setText(path)

    def choose_file(self, target: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Template client", target.text() or str(self.window.project_root()), "Excel (*.xlsx)")
        if path:
            target.setText(path)

    def fill_table(self) -> None:
        if self.current_result is None:
            return
        self.table.setRowCount(len(self.current_result.tags))
        for row_index, tag in enumerate(self.current_result.tags):
            values = [
                tag.tag_no,
                tag.description,
                tag.tag_type,
                tag.system,
                " | ".join(sorted(tag.documents)[:6]),
                str(len(tag.evidence)),
                tag.deleted,
            ]
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QTableWidgetItem(value))


def path_picker_row(edit: QLineEdit, callback: object) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    button = QPushButton("...")
    button.setObjectName("secondaryButton")
    button.setFixedWidth(42)
    button.clicked.connect(callback)
    layout.addWidget(edit, 1)
    layout.addWidget(button)
    return row
