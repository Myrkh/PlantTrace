from __future__ import annotations

from pathlib import Path
import ctypes

from PySide6.QtCore import QObject, Qt, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .extractor import extract_references
from .indexer import IndexReport
from .models import ExtractionHit, ProjectPaths, SearchResult
from .pdf_engine import ocr_available
from .search import search
from .semantic import semantic_status
from .store import PlantTraceStore
from .ui.batch_panel import BatchPanel
from .ui.conflicts_panel import ConflictsPanel
from .ui.coverage_panel import CoveragePanel
from .ui.export_actions import ExportActionsMixin
from .ui.icons import line_icon
from .ui.exports_panel import ExportsPanel
from .ui.families_panel import FamiliesPanel
from .ui.master_register_panel import MasterRegisterPanel
from .ui.matrix_panel import MatrixPanel
from .ui.menu import build_menu_bar
from .ui.presenters import extraction_row_values, result_row_values
from .ui.preview_pane import PreviewPane
from .ui.reference_panel import ReferencePanel
from .ui.revisions_panel import RevisionsPanel
from .ui.rules_panel import RulesPanel
from .ui.templates_panel import TemplatesPanel
from .ui.theme import APP_STYLESHEET
from .ui.views import ACTIVITIES, ClickableLabel, build_activity_bar, build_stack, field_label, index_row, path_row, section_label
from .ui.window_actions import NavigationActionsMixin, PathActionsMixin, app_icon_path
from .ui.workers import EmbedWorker, IndexWorker


class MainWindow(PathActionsMixin, ExportActionsMixin, NavigationActionsMixin, QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PlantTrace")
        self.resize(1440, 820)
        self.results: list[SearchResult] = []
        self.extraction_hits: list[ExtractionHit] = []
        self.max_search_results = 500
        self.worker_thread: QThread | None = None
        self.worker: QObject | None = None

        self.project_edit = QLineEdit(str(Path.cwd()))
        self.pdf_edit = QLineEdit("")
        self.query_edit = QLineEdit()
        self.mode_combo = QComboBox()
        self.force_check = QCheckBox("Force")
        self.ocr_check = QCheckBox("OCR")
        self.ocr_lang_edit = QLineEdit("eng")
        self.coverage_label = QLabel()
        self.semantic_label = QLabel()
        self.search_table = QTableWidget(0, 8)
        self.extract_table = QTableWidget(0, 9)
        self.stack = QStackedWidget()
        self.side_stack = QStackedWidget()
        self.side_stack.setObjectName("sideStack")
        self.rules_panel = RulesPanel(self.project_root)
        self.reference_panel = ReferencePanel(self)
        self.matrix_panel = MatrixPanel(self)
        self.templates_panel = TemplatesPanel(self)
        self.batch_panel = BatchPanel(self.project_root)
        self.families_panel = FamiliesPanel(self.project_root)
        self.conflicts_panel = ConflictsPanel(self.project_root)
        self.revisions_panel = RevisionsPanel(self)
        self.coverage_panel = CoveragePanel(self.project_root)
        self.master_register_panel = MasterRegisterPanel(self)
        self.preview_pane = PreviewPane()
        self.exports_panel = ExportsPanel(self)

        self.index_button = QPushButton("Indexer")
        self.embed_button = QPushButton("Vectoriser")
        self.search_button = QPushButton("Chercher")
        self.extract_button = QPushButton("Extraire")
        self.search_export_button = QPushButton("Exporter")
        self.extract_export_button = QPushButton("Exporter")
        self.index_button.setObjectName("primaryButton")
        self.embed_button.setObjectName("secondaryButton")

        self.configure_controls()
        self.build_ui()
        self.refresh_coverage()

    def configure_controls(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)
        self.setWindowIcon(QIcon(str(app_icon_path())))
        self.mode_combo.addItems(["hybrid", "auto", "exact", "text", "fuzzy", "semantic"])
        self.query_edit.setPlaceholderText("FV1100, 10-P-12345, fournisseur cafe...")
        self.query_edit.returnPressed.connect(self.start_search)
        self.ocr_check.setEnabled(ocr_available())
        self.ocr_lang_edit.setMaximumWidth(76)
        for label in [self.coverage_label, self.semantic_label]:
            label.setObjectName("metricLabel")
        for table in [self.search_table, self.extract_table]:
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setSortingEnabled(True)
            table.setWordWrap(False)

    def build_ui(self) -> None:
        self.side_panel_collapsed = False
        shell = QHBoxLayout()
        shell.setContentsMargins(8, 8, 8, 8)
        shell.setSpacing(8)
        shell.addWidget(build_activity_bar(self))
        shell.addWidget(self.build_side_panel())
        shell.addWidget(self.build_side_toggle())
        shell.addWidget(build_stack(self), 1)
        build_menu_bar(self)

        container = QWidget()
        container.setObjectName("appShell")
        container.setLayout(shell)
        self.setCentralWidget(container)
        status_bar = QStatusBar()
        bug_button = QPushButton()
        bug_button.setObjectName("footerBugButton")
        bug_button.setIcon(line_icon("bug", "#cdd6cf"))
        bug_button.setToolTip("Signaler un bug")
        bug_button.setCursor(Qt.CursorShape.PointingHandCursor)
        bug_button.clicked.connect(self.report_bug)
        self.index_progress = QProgressBar()
        self.index_progress.setObjectName("indexProgress")
        self.index_progress.setFixedWidth(160)
        self.index_progress.setTextVisible(False)
        self.index_progress.hide()
        self.version_label = ClickableLabel(f"V{__version__}")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setToolTip("Cliquer pour voir les nouveautes (changelog)")
        self.version_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.version_label.clicked.connect(self.show_changelog)
        status_bar.addPermanentWidget(self.index_progress)
        status_bar.addPermanentWidget(bug_button)
        status_bar.addPermanentWidget(self.version_label)
        self.setStatusBar(status_bar)

    def build_side_toggle(self) -> QPushButton:
        button = QPushButton()
        button.setObjectName("sidePanelToggle")
        button.setFixedWidth(16)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        button.setIcon(line_icon("expand", "#455149"))
        button.setToolTip("Masquer le panneau lateral (Ctrl+B)")
        button.clicked.connect(self.toggle_side_panel)
        self.side_toggle_button = button
        return button

    def build_side_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("sidePanel")
        panel.setFixedWidth(390)
        self.side_panel = panel
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.side_stack)
        self.side_stack.addWidget(self.scroll_side_widget(self.build_corpus_side_panel()))
        self.side_stack.addWidget(self.build_rules_side_panel())
        return panel

    def scroll_side_widget(self, widget: QWidget) -> QScrollArea:
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        scroller = QScrollArea()
        scroller.setObjectName("sideScroller")
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(QFrame.Shape.NoFrame)
        scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        viewport = scroller.viewport()
        viewport.setObjectName("sideViewport")
        viewport.setStyleSheet("QWidget#sideViewport { background: #ffffff; }")
        scroller.setWidget(widget)
        return scroller

    def build_corpus_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sideContent")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(section_label("Corpus"))
        layout.addWidget(field_label("Index local"))
        layout.addLayout(path_row(self, self.project_edit, self.choose_project_folder))
        layout.addWidget(field_label("Dossier PDF source"))
        layout.addLayout(path_row(self, self.pdf_edit, lambda: self.choose_folder(self.pdf_edit)))
        layout.addWidget(section_label("Indexation"))
        layout.addLayout(index_row(self))
        layout.addWidget(self.coverage_label)
        layout.addWidget(self.semantic_label)
        layout.addStretch()
        return panel

    def build_rules_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sideContent")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(section_label("Regles projet"))
        layout.addWidget(field_label("Packs metier"))
        layout.addLayout(self.rules_panel.pack_controls())
        layout.addWidget(self.scroll_side_widget(self.rules_panel.sidebar), 1)
        return panel

    def on_activity_selected(self, index: int) -> None:
        activity = ACTIVITIES[index]
        self.update_side_panel(activity)
        if activity == "Livrables":
            self.exports_panel.refresh()

    def on_subactivity_selected(self, activity: str) -> None:
        self.update_side_panel(activity)
        if activity == "Livrables":
            self.exports_panel.refresh()

    def toggle_side_panel(self) -> None:
        self.side_panel_collapsed = not self.side_panel_collapsed
        self.update_side_panel(ACTIVITIES[self.stack.currentIndex()])

    def update_side_panel(self, activity: str) -> None:
        has_panel = True
        if activity in {"Recherche", "Corpus"}:
            self.side_stack.setCurrentIndex(0)
        elif activity == "Inventaire" and self.current_subactivity(activity) == "Regles":
            self.side_stack.setCurrentIndex(1)
        else:
            has_panel = False
        self.side_toggle_button.setVisible(has_panel)
        self.side_panel.setVisible(has_panel and not self.side_panel_collapsed)
        if has_panel:
            collapsed = self.side_panel_collapsed
            self.side_toggle_button.setIcon(line_icon("collapse" if collapsed else "expand", "#455149"))
            self.side_toggle_button.setToolTip(
                "Afficher le panneau lateral (Ctrl+B)" if collapsed else "Masquer le panneau lateral (Ctrl+B)"
            )

    def current_subactivity(self, activity: str) -> str:
        tabs = self.subactivity_tabs.get(activity)
        if tabs is None:
            return ""
        return tabs.tabText(tabs.currentIndex())

    def start_index(self) -> None:
        pdf_root = Path(self.pdf_edit.text()).expanduser()
        if not pdf_root.exists():
            QMessageBox.warning(self, "PlantTrace", "Dossier PDF introuvable.")
            return
        worker = IndexWorker(self.project_root(), pdf_root, self.force_check.isChecked(), self.ocr_check.isChecked(), self.ocr_lang_edit.text().strip() or "eng")
        worker.progress.connect(self.on_index_progress)
        if self.run_worker(worker, self.on_index_finished):
            self.set_busy(True)
            self.index_progress.setRange(0, 0)
            self.index_progress.show()
            self.statusBar().showMessage("Indexation : analyse du dossier...")

    def start_search(self) -> None:
        query = self.query_edit.text().strip()
        if not query:
            self.statusBar().showMessage("Saisir une recherche avant de lancer.", 5000)
            return
        self.set_busy(True)
        try:
            self.on_search_finished(search(self.project_root(), query, self.mode_combo.currentText(), self.max_search_results))
        except Exception as exc:
            self.on_worker_failed(str(exc))

    def run_extraction(self) -> None:
        self.set_busy(True)
        try:
            self.on_extraction_finished(extract_references(self.project_root()))
        except Exception as exc:
            self.on_worker_failed(str(exc))

    def start_embed(self) -> None:
        if self.run_worker(EmbedWorker(self.project_root()), self.on_embed_finished):
            self.set_busy(True)
            self.statusBar().showMessage("Vectorisation en cours...")

    def run_worker(self, worker: QObject, finished_slot: object) -> bool:
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.information(self, "PlantTrace", "Une operation est deja en cours.")
            return False
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(finished_slot)
        worker.failed.connect(self.on_worker_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: setattr(self, "worker", None))
        thread.finished.connect(lambda: setattr(self, "worker_thread", None))
        self.worker_thread = thread
        self.worker = worker
        thread.start()
        return True

    def start_update(self, info: object) -> None:
        from planttrace.self_update import staging_root
        from planttrace.ui.workers import DownloadWorker

        dest = staging_root() / (info.asset_name or "PlantTrace-update.zip")
        self._update_progress = QProgressDialog("Telechargement de la mise a jour...", None, 0, 100, self)
        self._update_progress.setWindowTitle("Mise a jour PlantTrace")
        self._update_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._update_progress.setMinimumDuration(0)
        self._update_progress.setValue(0)

        thread = QThread(self)
        worker = DownloadWorker(info.asset_url, dest)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._update_progress.setValue)
        worker.finished.connect(self._on_update_downloaded)
        worker.failed.connect(self._on_update_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._update_thread = thread
        self._update_worker = worker
        thread.start()

    def _on_update_downloaded(self, path: object) -> None:
        from planttrace.self_update import apply_update

        self._update_progress.close()
        try:
            apply_update(Path(str(path)))
        except Exception as exc:
            QMessageBox.warning(self, "PlantTrace", f"Mise a jour impossible: {exc}")
            return
        self.statusBar().showMessage("Mise a jour: fermeture et redemarrage...", 4000)
        QApplication.quit()

    def _on_update_failed(self, message: str) -> None:
        self._update_progress.close()
        QMessageBox.warning(self, "PlantTrace", f"Telechargement de la mise a jour impossible: {message}")

    def set_busy(self, busy: bool) -> None:
        for button in [self.index_button, self.embed_button, self.search_button, self.extract_button, self.search_export_button, self.extract_export_button]:
            button.setEnabled(not busy)
        if hasattr(self, "revisions_panel"):
            self.revisions_panel.set_controls_enabled(not busy)

    def on_index_progress(self, done: int, total: int, name: str) -> None:
        if self.index_progress.maximum() != total:
            self.index_progress.setRange(0, total)
        self.index_progress.setValue(done)
        message = f"Indexation {done} / {total}"
        if name:
            message += f" — {name}"
        self.statusBar().showMessage(message)

    def on_index_finished(self, report: IndexReport) -> None:
        self.set_busy(False)
        self.index_progress.hide()
        self.refresh_coverage()
        self.statusBar().showMessage(f"Index termine: {report.indexed} indexes, {report.skipped} ignores, {report.failed} echecs.", 8000)

    def on_search_finished(self, results: list[SearchResult]) -> None:
        self.set_busy(False)
        self.results = results
        self.fill_table(self.search_table, [result_row_values(result) for result in results])
        self._tag_search_rows()
        if results:
            self.search_table.selectRow(0)
        else:
            self.preview_pane.clear()
        self.statusBar().showMessage(f"{len(results)} resultat(s).", 8000)

    def _tag_search_rows(self) -> None:
        for index in range(self.search_table.rowCount()):
            item = self.search_table.item(index, 0)
            if item is not None:
                item.setData(Qt.ItemDataRole.UserRole, index)

    def result_for_row(self, row: int) -> SearchResult | None:
        item = self.search_table.item(row, 0)
        if item is None:
            return None
        index = item.data(Qt.ItemDataRole.UserRole)
        if index is None or not (0 <= index < len(self.results)):
            return None
        return self.results[index]

    def preview_search_result(self, row: int, _column: int = 0, _prev_row: int = -1, _prev_column: int = -1) -> None:
        result = self.result_for_row(row)
        if result is None:
            self.preview_pane.clear()
        else:
            self.preview_pane.show_result(result)

    def on_extraction_finished(self, hits: list[ExtractionHit]) -> None:
        self.set_busy(False)
        self.extraction_hits = hits
        self.fill_table(self.extract_table, [extraction_row_values(hit) for hit in hits])
        self.statusBar().showMessage(f"{len(hits)} reference(s) extraite(s).", 8000)

    def on_embed_finished(self, count: int) -> None:
        self.set_busy(False)
        self.refresh_coverage()
        self.statusBar().showMessage(f"Vectorisation terminee: {count} chunks.", 8000)

    def on_worker_failed(self, message: str) -> None:
        self.set_busy(False)
        self.index_progress.hide()
        self.fill_table(self.search_table, [["error", "", "", "", "", message, "", ""]])
        self.preview_pane.clear()
        QMessageBox.critical(self, "PlantTrace", message)
        self.statusBar().showMessage("Erreur.", 8000)

    def fill_table(self, table: QTableWidget, rows: list[list[str]]) -> None:
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row_index, values in enumerate(rows):
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        table.setSortingEnabled(True)

    def refresh_coverage(self) -> None:
        coverage = PlantTraceStore(ProjectPaths(self.project_root())).coverage()
        self.coverage_label.setText(
            "docs {documents} | pages {pages} | texte {text_pages} | OCR requis {ocr_required_pages} | OCR echec {ocr_failed_pages}".format(**coverage)
        )
        status = semantic_status(self.project_root())
        self.semantic_label.setText(f"semantic {'active' if status.available else 'offline'} | {status.message}")
        self.coverage_panel.refresh()

def main() -> int:
    set_windows_app_id()
    app = QApplication([])
    app.setWindowIcon(QIcon(str(app_icon_path())))
    window = MainWindow()
    window.show()
    return app.exec()


def set_windows_app_id() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PlantTrace.Desktop")
    except Exception:
        pass
