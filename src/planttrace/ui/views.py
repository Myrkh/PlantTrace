from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QStyle,
)

from .icons import activity_icon, line_icon, logo_pixmap

ACTIVITIES = ["Recherche", "Corpus", "Inventaire", "Controle", "Livrables"]


class ClickableLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


def build_activity_bar(window: object) -> QWidget:
    bar = QFrame()
    bar.setObjectName("activityBar")
    bar.setFixedWidth(148)
    layout = QVBoxLayout(bar)
    layout.setContentsMargins(8, 12, 8, 8)
    layout.setSpacing(3)
    window.activity_bar = bar
    window.activity_collapsed = False

    brand = QFrame()
    brand.setObjectName("brandBlock")
    brand_layout = QHBoxLayout(brand)
    brand_layout.setContentsMargins(10, 8, 8, 10)
    logo = QLabel()
    logo.setPixmap(logo_pixmap(34))
    title = QLabel("PlantTrace")
    title.setObjectName("brandTitle")
    brand_layout.addWidget(logo)
    brand_layout.addWidget(title)
    window.activity_brand_title = title
    layout.addWidget(brand)

    buttons: list[QPushButton] = []
    window.activity_buttons = buttons
    toggle = QPushButton("Replier")
    toggle.setObjectName("activityButton")
    toggle.setIcon(line_icon("collapse"))
    toggle.setIconSize(QSize(18, 18))
    toggle.setToolTip("Replier la barre d'activite")
    toggle.clicked.connect(lambda: toggle_activity_bar(window, buttons, toggle))
    window.activity_toggle_button = toggle
    for index, name in enumerate(ACTIVITIES):
        button = QPushButton(name)
        button.setObjectName("activityButton")
        button.setCheckable(True)
        button.setIcon(activity_icon(name))
        button.setToolTip(name)
        button.clicked.connect(lambda _checked=False, i=index: select_activity(window, buttons, i))
        if index == 0:
            button.setChecked(True)
        buttons.append(button)
        layout.addWidget(button)
    layout.addStretch()
    layout.addWidget(toggle)
    return bar


def toggle_activity_bar(window: object, buttons: list[QPushButton], toggle: QPushButton) -> None:
    set_activity_bar_collapsed(window, buttons, toggle, not window.activity_collapsed)


def set_activity_bar_collapsed(window: object, buttons: list[QPushButton], toggle: QPushButton, collapsed: bool) -> None:
    if window.activity_collapsed == collapsed:
        return
    window.activity_collapsed = collapsed
    animate_activity_bar_width(window, 62 if window.activity_collapsed else 148)
    window.activity_brand_title.setVisible(not window.activity_collapsed)
    toggle.setText(">" if window.activity_collapsed else "Replier")
    toggle.setIcon(line_icon("expand" if window.activity_collapsed else "collapse"))
    toggle.setIconSize(QSize(18, 18))
    toggle.setToolTip("Deplier la barre d'activite" if window.activity_collapsed else "Replier la barre d'activite")
    for index, button in enumerate(buttons):
        button.setText("" if window.activity_collapsed else ACTIVITIES[index])


def animate_activity_bar_width(window: object, end_width: int) -> None:
    start_width = window.activity_bar.width() or window.activity_bar.maximumWidth() or 148
    group = QParallelAnimationGroup(window.activity_bar)
    for property_name in [b"minimumWidth", b"maximumWidth"]:
        animation = QPropertyAnimation(window.activity_bar, property_name)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setDuration(170)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(animation)
    group.finished.connect(lambda: window.activity_bar.setFixedWidth(end_width))
    window.activity_bar_animation = group
    group.start()


def select_activity(window: object, buttons: list[QPushButton], index: int) -> None:
    window.stack.setCurrentIndex(index)
    if hasattr(window, "on_activity_selected"):
        window.on_activity_selected(index)
    for button_index, button in enumerate(buttons):
        button.setChecked(button_index == index)


def select_activity_by_name(window: object, name: str) -> None:
    select_activity(window, window.activity_buttons, ACTIVITIES.index(name))


def select_subactivity(window: object, activity: str, subactivity: str) -> None:
    select_activity_by_name(window, activity)
    tabs = window.subactivity_tabs[activity]
    for index in range(tabs.count()):
        if tabs.tabText(index) == subactivity:
            tabs.setCurrentIndex(index)
            return
    raise ValueError(f"Unknown subactivity: {activity}/{subactivity}")


def build_stack(window: object) -> QWidget:
    window.subactivity_tabs = {}
    window.stack.addWidget(tabbed_view(window, "Recherche", [("Recherche", search_view(window)), ("Fiche", reference_view(window))]))
    window.stack.addWidget(tabbed_view(window, "Corpus", [("Couverture", coverage_view(window)), ("Familles", families_view(window))]))
    window.stack.addWidget(tabbed_view(window, "Inventaire", [("Regles", rules_view(window)), ("Extraction", extraction_view(window)), ("Templates", templates_view(window))]))
    window.stack.addWidget(tabbed_view(window, "Controle", [("Batch", batch_view(window)), ("Matrice", matrix_view(window)), ("Conflits", conflicts_view(window)), ("Revisions", revisions_view(window))]))
    window.stack.addWidget(tabbed_view(window, "Livrables", [("Exports", exports_view(window)), ("Master Register", master_register_view(window))]))
    return window.stack


def tabbed_view(window: object, activity: str, tabs: list[tuple[str, QWidget]]) -> QWidget:
    page, layout = page_shell(activity)
    tab_widget = QTabWidget()
    tab_widget.setObjectName("activityTabs")
    for label, widget in tabs:
        tab_widget.addTab(scroll_content(widget), label)
    tab_widget.currentChanged.connect(lambda _index, name=activity: window.on_subactivity_selected(name))
    window.subactivity_tabs[activity] = tab_widget
    layout.addWidget(tab_widget, 1)
    return page


def scroll_content(widget: QWidget) -> QScrollArea:
    scroller = QScrollArea()
    scroller.setObjectName("contentScroller")
    scroller.setWidgetResizable(True)
    scroller.setFrameShape(QFrame.Shape.NoFrame)
    scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    viewport = scroller.viewport()
    viewport.setObjectName("contentViewport")
    viewport.setStyleSheet("QWidget#contentViewport { background: #f4f5f3; }")
    scroller.setWidget(widget)
    return scroller


def path_row(window: object, line_edit: object, slot: object) -> QHBoxLayout:
    line_edit.setMinimumWidth(0)
    line_edit.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
    button = QPushButton()
    button.setObjectName("folderButton")
    button.setFixedWidth(46)
    button.setIcon(line_icon("index", "#26312b"))
    button.clicked.connect(slot)
    row = QHBoxLayout()
    row.addWidget(line_edit, 1)
    row.addWidget(button)
    return row


def index_row(window: object) -> QVBoxLayout:
    window.index_button.setText("Indexer")
    window.index_button.setMinimumWidth(128)
    window.index_button.setIcon(line_icon("index"))
    window.index_button.clicked.connect(window.start_index)
    window.embed_button.setMinimumWidth(128)
    window.embed_button.clicked.connect(window.start_embed)
    buttons = QHBoxLayout()
    buttons.addWidget(window.index_button, 1)
    buttons.addWidget(window.embed_button, 1)
    options = QHBoxLayout()
    options.addWidget(window.force_check)
    options.addWidget(window.ocr_check)
    options.addWidget(QLabel("Langue OCR"))
    options.addWidget(window.ocr_lang_edit)
    options.addStretch()
    layout = QVBoxLayout()
    layout.addLayout(buttons)
    layout.addLayout(options)
    return layout


def search_row(window: object) -> QHBoxLayout:
    window.search_button.setIcon(activity_icon("Recherche"))
    window.search_button.clicked.connect(window.start_search)
    window.search_export_button.setObjectName("secondaryButton")
    window.search_export_button.setIcon(activity_icon("Exports", "#1f2522"))
    window.search_export_button.clicked.connect(window.export_search_xlsx)
    row = QHBoxLayout()
    row.addWidget(window.mode_combo, 1)
    row.addWidget(window.search_button, 2)
    row.addWidget(window.search_export_button, 1)
    return row


def search_view(window: object) -> QWidget:
    page, layout = page_shell("Recherche")
    layout.addWidget(window.query_edit)
    layout.addLayout(search_row(window))
    configure_table(
        window.search_table,
        ["Type", "Fichier", "Page", "Score", "Trouve", "Extrait", "Page status", "Doc status"],
        stretch_columns=[1, 5],
    )
    window.search_table.cellDoubleClicked.connect(window.open_search_result)
    window.search_table.currentCellChanged.connect(window.preview_search_result)
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.setObjectName("searchSplitter")
    splitter.addWidget(window.search_table)
    splitter.addWidget(window.preview_pane)
    splitter.setStretchFactor(0, 3)
    splitter.setStretchFactor(1, 2)
    splitter.setSizes([780, 560])
    layout.addWidget(splitter, 1)
    return page


def extraction_view(window: object) -> QWidget:
    page, layout = page_shell("Extraction")
    row = QHBoxLayout()
    window.extract_button.setIcon(activity_icon("Extraction"))
    window.extract_button.clicked.connect(window.run_extraction)
    window.extract_export_button.setObjectName("secondaryButton")
    window.extract_export_button.setIcon(activity_icon("Exports", "#1f2522"))
    window.extract_export_button.clicked.connect(window.export_extraction_xlsx)
    row.addWidget(window.extract_button)
    row.addWidget(window.extract_export_button)
    row.addWidget(field_label("Detecte TAG, LINE, DOC et INITIALS selon les regles projet."))
    row.addStretch()
    layout.addLayout(row)
    configure_table(
        window.extract_table,
        ["Type", "Valeur", "Regle", "Fichier", "Page", "Extrait", "Confiance", "Page status", "Doc status"],
        stretch_columns=[3, 5],
    )
    layout.addWidget(window.extract_table, 1)
    return page


def reference_view(window: object) -> QWidget:
    page, layout = page_shell("Fiche reference")
    layout.addWidget(window.reference_panel, 1)
    return page


def batch_view(window: object) -> QWidget:
    page, layout = page_shell("Batch")
    layout.addWidget(window.batch_panel, 1)
    return page


def families_view(window: object) -> QWidget:
    page, layout = page_shell("Familles")
    layout.addWidget(window.families_panel, 1)
    return page


def matrix_view(window: object) -> QWidget:
    page, layout = page_shell("Matrice")
    layout.addWidget(window.matrix_panel, 1)
    return page


def templates_view(window: object) -> QWidget:
    page, layout = page_shell("Templates")
    layout.addWidget(window.templates_panel, 1)
    return page


def conflicts_view(window: object) -> QWidget:
    page, layout = page_shell("Conflits")
    layout.addWidget(window.conflicts_panel, 1)
    return page


def revisions_view(window: object) -> QWidget:
    page, layout = page_shell("Revisions")
    layout.addWidget(window.revisions_panel, 1)
    return page


def exports_view(window: object) -> QWidget:
    page, layout = page_shell("Exports")
    layout.addWidget(window.exports_panel, 1)
    return page


def master_register_view(window: object) -> QWidget:
    page, layout = page_shell("Master Register")
    layout.addWidget(window.master_register_panel, 1)
    return page


def rules_view(window: object) -> QWidget:
    page, layout = page_shell("Regles")
    layout.addWidget(window.rules_panel, 1)
    return page


def coverage_view(window: object) -> QWidget:
    page, layout = page_shell("Couverture")
    layout.addWidget(window.coverage_panel, 1)
    return page


def guide_view(window: object) -> QWidget:
    page, layout = page_shell("Guide")
    cards = [
        ("1. Indexer", "Choisir le dossier PDF puis lancer Indexer. L'OCR reste optionnel et visible."),
        ("2. Chercher", "Saisir FV1100, JDY ou fournisseur cafe. Chaque resultat donne fichier, page et extrait."),
        ("3. Fiche", "Consolider une reference en occurrences, familles, associations, conflits et revisions."),
        ("4. Templates", "Generer un tableau metier type registre TAG depuis les preuves extraites."),
        ("5. Matrice", "Agreger toutes les references extraites par familles documentaires, conflits et revisions."),
        ("6. Familles", "Classer les PDF en PID, loop, datasheet, bornier, IO ou vendor avec preuve."),
        ("7. Batch", "Coller ou charger une liste de references et produire une matrice de presence."),
        ("8. Conflits", "Comparer les valeurs associees a une meme reference et verifier les preuves."),
        ("9. Revisions", "Comparer deux dossiers PDF et isoler les references ajoutees, supprimees ou modifiees."),
        ("10. Regles", "Creer les formats de tags du projet avec le constructeur metier du panneau gauche."),
        ("11. Extraire", "Lancer Extraction pour inventorier tous les TAG, LINE, DOC et INITIALS reconnus."),
        ("12. Couverture", "Verifier les pages lisibles, OCR requis et OCR echec avant de conclure."),
        ("13. Exporter", "Produire un XLSX exploitable comme livrable de preuve ou de cross-reference."),
    ]
    for title, text in cards:
        card = QLabel(f"{title}\n{text}")
        card.setObjectName("guideCard")
        card.setWordWrap(True)
        layout.addWidget(card)
    button = QPushButton("Ouvrir le guide HTML local")
    button.setObjectName("secondaryButton")
    button.clicked.connect(window.open_guide_html)
    layout.addWidget(button)
    layout.addStretch()
    return page


def placeholder_view(title: str, message: str) -> QWidget:
    page, layout = page_shell(title)
    label = QLabel(message)
    label.setObjectName("metricLabel")
    layout.addWidget(label)
    layout.addStretch()
    return page


def page_shell(title: str) -> tuple[QWidget, QVBoxLayout]:
    page = QWidget()
    page.setObjectName("pageRoot")
    layout = QVBoxLayout(page)
    layout.setContentsMargins(16, 16, 16, 12)
    layout.setSpacing(10)
    heading = QLabel(title)
    heading.setObjectName("appTitle")
    layout.addWidget(heading)
    return page, layout


def configure_table(table: QTableWidget, headers: list[str], stretch_columns: list[int]) -> None:
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    for index in range(len(headers)):
        mode = QHeaderView.ResizeMode.Stretch if index in stretch_columns else QHeaderView.ResizeMode.ResizeToContents
        table.horizontalHeader().setSectionResizeMode(index, mode)


def section_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("panelTitle")
    return label


def field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("mutedLabel")
    return label
