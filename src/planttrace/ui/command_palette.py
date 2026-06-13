from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from planttrace.ui.views import ACTIVITIES, select_activity_by_name, select_subactivity, set_activity_bar_collapsed


@dataclass(frozen=True)
class Command:
    title: str
    group: str
    keywords: str
    run: Callable[[], None]

    @property
    def haystack(self) -> str:
        return f"{self.title} {self.group} {self.keywords}".lower()


class CommandPalette(QDialog):
    def __init__(self, parent: object, commands: list[Command]) -> None:
        super().__init__(parent)
        self.commands = commands
        self.filtered_commands: list[Command] = []
        self.setWindowTitle("Palette de commande")
        self.setObjectName("commandPalette")
        self.setModal(False)
        self.resize(620, 520)

        self.search = QLineEdit(self)
        self.search.setObjectName("paletteSearch")
        self.search.setPlaceholderText("Chercher une commande, un ecran, une action...")
        self.list = QListWidget(self)
        self.list.setObjectName("paletteList")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)

        self.search.textChanged.connect(self.apply_filter)
        self.search.returnPressed.connect(self.execute_current)
        self.list.itemDoubleClicked.connect(lambda _item: self.execute_current())
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search.text().strip().lower()
        tokens = [token for token in query.split() if token]
        self.filtered_commands = [command for command in self.commands if all(token in command.haystack for token in tokens)]
        self.list.clear()
        for index, command in enumerate(self.filtered_commands):
            item = QListWidgetItem(f"{command.title}  -  {command.group}")
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def execute_current(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        command = self.filtered_commands[item.data(Qt.ItemDataRole.UserRole)]
        self.accept()
        command.run()


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
