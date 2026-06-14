from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from planttrace.doc_families import FAMILY_RULES, classify_documents
from planttrace.models import SearchResult
from planttrace.search import search
from planttrace.ui.preview_pane import PreviewPane
from planttrace.ui.views import ACTIVITIES, select_activity_by_name, select_subactivity, set_activity_bar_collapsed

_SEARCH_DEBOUNCE_MS = 250
_SEARCH_LIMIT = 60
_FAMILY_ORDER = [rule.label for rule in FAMILY_RULES] + ["A classer", "Autres"]


@dataclass(frozen=True)
class Command:
    title: str
    group: str
    keywords: str
    run: Callable[[], None]

    @property
    def haystack(self) -> str:
        return f"{self.title} {self.group} {self.keywords}".lower()


@dataclass(frozen=True)
class _Entry:
    run: Callable[[], None]
    result: SearchResult | None = None


class CommandPalette(QDialog):
    def __init__(self, parent: object, commands: list[Command]) -> None:
        super().__init__(parent)
        self.window = parent
        self.commands = commands
        self._families: dict[str, str] | None = None
        self.setWindowTitle("Palette de commande")
        self.setObjectName("commandPalette")
        self.setModal(False)
        self.resize(1000, 600)

        self.search = QLineEdit(self)
        self.search.setObjectName("paletteSearch")
        self.search.setPlaceholderText("Tag ou expression pour chercher dans la base  -  prefixe > pour les commandes")
        self.list = QListWidget(self)
        self.list.setObjectName("paletteList")
        self.preview = PreviewPane()

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self.list, 3)
        body.addWidget(self.preview, 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self.search)
        layout.addLayout(body, 1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_SEARCH_DEBOUNCE_MS)
        self._timer.timeout.connect(self.run_corpus_search)

        self.search.textChanged.connect(self.apply_filter)
        self.search.returnPressed.connect(self.execute_current)
        self.list.itemDoubleClicked.connect(lambda _item: self.execute_current())
        self.list.currentItemChanged.connect(self._on_current_changed)
        self.apply_filter()

    # --- filtering -------------------------------------------------------
    def apply_filter(self) -> None:
        query = self.search.text().strip()
        command_mode = query == "" or query.startswith(">")
        self._render(self._matching_commands(query), corpus_results=[])
        if command_mode:
            self._timer.stop()
        else:
            self._timer.start()

    def accept(self) -> None:
        self._timer.stop()
        super().accept()

    def run_corpus_search(self) -> None:
        query = self.search.text().strip()
        if not query or query.startswith(">"):
            return
        try:
            results = [r for r in search(self.window.project_root(), query, "hybrid", _SEARCH_LIMIT) if r.document_path]
        except Exception:
            results = []
        self._render(self._matching_commands(query), corpus_results=results)

    def _matching_commands(self, query: str) -> list[Command]:
        tokens = [token for token in query.lstrip(">").strip().lower().split() if token]
        if not tokens:
            return self.commands
        return [command for command in self.commands if all(token in command.haystack for token in tokens)]

    # --- rendering -------------------------------------------------------
    def _render(self, commands: list[Command], corpus_results: list[SearchResult]) -> None:
        self.list.clear()
        if commands:
            self._add_header("Commandes")
            for command in commands:
                self._add_entry(f"{command.title}  -  {command.group}", _Entry(run=command.run))
        for label, results in self._group_by_family(corpus_results):
            self._add_header(label)
            for result in results:
                title = f"{result.found_as or result.query}   .   {Path(result.document_path).name}   .   p.{result.page}"
                self._add_entry(title, _Entry(run=lambda r=result: self._open(r), result=result))
        for row in range(self.list.count()):
            if self.list.item(row).flags() & Qt.ItemFlag.ItemIsSelectable:
                self.list.setCurrentRow(row)
                break

    def _add_header(self, text: str) -> None:
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        item.setForeground(QColor("#56635c"))
        self.list.addItem(item)

    def _add_entry(self, text: str, entry: _Entry) -> None:
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, entry)
        self.list.addItem(item)

    def _group_by_family(self, results: list[SearchResult]) -> list[tuple[str, list[SearchResult]]]:
        if not results:
            return []
        families = self._family_map()
        groups: dict[str, list[SearchResult]] = {}
        for result in results:
            label = families.get(result.document_path, "Autres")
            groups.setdefault(label, []).append(result)
        ordered = [(label, groups[label]) for label in _FAMILY_ORDER if label in groups]
        extra = [(label, items) for label, items in groups.items() if label not in _FAMILY_ORDER]
        return ordered + sorted(extra)

    def _family_map(self) -> dict[str, str]:
        if self._families is None:
            try:
                self._families = {family.document_path: family.label for family in classify_documents(self.window.project_root())}
            except Exception:
                self._families = {}
        return self._families

    # --- actions ---------------------------------------------------------
    def _on_current_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        entry = current.data(Qt.ItemDataRole.UserRole) if current else None
        if isinstance(entry, _Entry) and entry.result is not None:
            self.preview.show_result(entry.result)
        else:
            self.preview.clear()

    def execute_current(self) -> None:
        item = self.list.currentItem()
        entry = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not isinstance(entry, _Entry):
            return
        self.accept()
        entry.run()

    def _open(self, result: SearchResult) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(result.document_path))


def open_command_palette(window: object) -> None:
    palette = CommandPalette(window, build_commands(window))
    window.command_palette = palette
    palette.show()
    palette.raise_()
    palette.activateWindow()
    palette.search.setFocus()


def build_commands(window: object) -> list[Command]:
    commands: list[Command] = [
        Command("Indexer", "Corpus", "index pdf documents", window.start_index),
        Command("Vectoriser", "Corpus", "semantic embeddings", window.start_embed),
        Command("Exporter livrable ZIP", "Livrables", "package export", window.export_project_pack),
        Command("Diagnostic environnement", "Outils", "ocr semantique paths", lambda: _show_environment_diagnostic(window)),
        Command("Parametres", "Outils", "ocr resultats configuration", lambda: _open_settings(window)),
        Command("Guide HTML local", "Aide", "documentation tuto", window.open_guide_html),
        Command(
            "Replier activity bar",
            "Affichage",
            "navigation compacte",
            lambda: set_activity_bar_collapsed(window, window.activity_buttons, window.activity_toggle_button, True),
        ),
        Command(
            "Deplier activity bar",
            "Affichage",
            "navigation complete",
            lambda: set_activity_bar_collapsed(window, window.activity_buttons, window.activity_toggle_button, False),
        ),
        Command("Focus recherche", "Recherche", "query chercher tag", lambda: _focus_search(window)),
    ]
    for activity, subactivities in _subactivities(window).items():
        commands.append(Command(activity, "Navigation", activity, lambda name=activity: select_activity_by_name(window, name)))
        for subactivity in subactivities:
            commands.append(
                Command(
                    f"{activity} > {subactivity}",
                    "Navigation",
                    f"{activity} {subactivity}",
                    lambda activity=activity, subactivity=subactivity: select_subactivity(window, activity, subactivity),
                )
            )
    return commands


def _subactivities(window: object) -> dict[str, list[str]]:
    return {
        activity: [tabs.tabText(index) for index in range(tabs.count())]
        for activity, tabs in window.subactivity_tabs.items()
        if activity in ACTIVITIES
    }


def _focus_search(window: object) -> None:
    select_subactivity(window, "Recherche", "Recherche")
    window.query_edit.setFocus()


def _open_settings(window: object) -> None:
    from planttrace.ui.menu import open_settings

    open_settings(window)


def _show_environment_diagnostic(window: object) -> None:
    from planttrace.ui.menu import show_environment_diagnostic

    show_environment_diagnostic(window)
