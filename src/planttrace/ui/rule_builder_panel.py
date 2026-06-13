from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from planttrace.models import ExtractionRule
from planttrace.rule_builder import RuleBuildRequest, TEMPLATES, TEMPLATE_KINDS, TEMPLATE_REGEX, build_pattern


class RuleBuilderPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sideContent")
        self.template = QComboBox()
        self.name = QLineEdit()
        self.prefixes = QLineEdit()
        self.min_digits = QComboBox()
        self.max_digits = QComboBox()
        self.allow_no_separator = QCheckBox("Aucun")
        self.allow_dash = QCheckBox("-")
        self.allow_underscore = QCheckBox("_")
        self.allow_space = QCheckBox("Espace")
        self.suffix_letter = QCheckBox("Suffixe lettre")
        self.advanced = QCheckBox("Mode avance")
        self.pattern = QLineEdit()
        self.confidence = QComboBox()
        self.enabled = QCheckBox("Regle active")
        self.build_ui()

    def build_ui(self) -> None:
        self.template.addItems(TEMPLATES)
        self.template.currentTextChanged.connect(self.on_template_changed)
        self.advanced.toggled.connect(lambda _checked: self.on_template_changed(self.template.currentText()))
        self.name.setPlaceholderText("Ex: Tags instrumentation projet")
        self.prefixes.setPlaceholderText("Ex: FV, PV, PT, TT")
        for combo in [self.min_digits, self.max_digits]:
            combo.addItems([str(value) for value in range(1, 13)])
            combo.setMaximumWidth(86)
        self.min_digits.setCurrentText("2")
        self.max_digits.setCurrentText("5")
        self.allow_no_separator.setChecked(True)
        self.allow_dash.setChecked(True)
        self.allow_underscore.setChecked(True)
        self.suffix_letter.setChecked(True)
        self.pattern.setPlaceholderText("Regex generee ou pattern avance")
        self.confidence.addItems(["high", "medium", "low"])
        self.enabled.setChecked(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        layout.addWidget(title("Parametres de regle"))
        layout.addWidget(hint("Exemple : FV1100 contient le prefixe FV et 4 chiffres."))
        layout.addWidget(label("Modele metier"))
        layout.addWidget(self.template)
        layout.addWidget(label("Nom"))
        layout.addWidget(self.name)
        layout.addWidget(label("Prefixes autorises"))
        layout.addWidget(self.prefixes)
        layout.addWidget(label("Chiffres de la reference"))
        layout.addLayout(number_row(self.min_digits, self.max_digits))
        layout.addWidget(label("Separateurs acceptes"))
        layout.addLayout(check_row(self.allow_no_separator, self.allow_dash))
        layout.addLayout(check_row(self.allow_underscore, self.allow_space))
        layout.addWidget(self.suffix_letter)
        layout.addWidget(self.enabled)
        layout.addWidget(label("Confiance"))
        layout.addWidget(self.confidence)
        layout.addWidget(self.advanced)
        layout.addWidget(self.pattern)
        layout.addStretch()
        self.on_template_changed(self.template.currentText())

    def current_rule(self) -> ExtractionRule:
        template = self.template.currentText()
        pattern = build_pattern(
            RuleBuildRequest(
                template=template,
                prefixes=self.prefixes.text(),
                min_digits=int(self.min_digits.currentText()),
                max_digits=int(self.max_digits.currentText()),
                allow_dash=self.allow_dash.isChecked(),
                allow_underscore=self.allow_underscore.isChecked(),
                allow_space=self.allow_space.isChecked(),
                allow_no_separator=self.allow_no_separator.isChecked(),
                suffix_letter=self.suffix_letter.isChecked(),
                custom_pattern=self.pattern.text(),
            )
        )
        self.pattern.setText(pattern)
        name = self.name.text().strip() or template
        return ExtractionRule(name, TEMPLATE_KINDS[template], pattern, self.enabled.isChecked(), self.confidence.currentText())

    def set_rule(self, rule: ExtractionRule) -> None:
        self.template.setCurrentText(TEMPLATE_REGEX)
        self.name.setText(rule.name)
        self.pattern.setText(rule.pattern)
        self.enabled.setChecked(rule.enabled)
        self.confidence.setCurrentText(rule.confidence)

    def on_template_changed(self, template: str) -> None:
        advanced = template == TEMPLATE_REGEX or self.advanced.isChecked()
        for widget in [self.prefixes, self.min_digits, self.max_digits, self.allow_no_separator, self.allow_dash, self.allow_underscore, self.allow_space, self.suffix_letter]:
            widget.setEnabled(template != TEMPLATE_REGEX)
        self.pattern.setReadOnly(template != TEMPLATE_REGEX)
        self.pattern.setVisible(advanced)


def title(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName("panelTitle")
    return widget


def label(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName("mutedLabel")
    widget.setWordWrap(True)
    return widget


def hint(text: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName("metricLabel")
    widget.setWordWrap(True)
    return widget


def number_row(minimum: QComboBox, maximum: QComboBox) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addWidget(QLabel("min"))
    row.addWidget(minimum)
    row.addWidget(QLabel("max"))
    row.addWidget(maximum)
    return row


def check_row(*checks: QCheckBox) -> QHBoxLayout:
    row = QHBoxLayout()
    for check in checks:
        row.addWidget(check)
    return row
