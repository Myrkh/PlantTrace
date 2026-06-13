from __future__ import annotations

import re
from dataclasses import dataclass


TEMPLATE_INSTRUMENT = "Instrument tag"
TEMPLATE_LINE = "Ligne tuyauterie"
TEMPLATE_DOCUMENT = "Numero document"
TEMPLATE_INITIALS = "Initiales"
TEMPLATE_REGEX = "Regex avancee"

TEMPLATES = [TEMPLATE_INSTRUMENT, TEMPLATE_LINE, TEMPLATE_DOCUMENT, TEMPLATE_INITIALS, TEMPLATE_REGEX]

TEMPLATE_KINDS = {
    TEMPLATE_INSTRUMENT: "TAG",
    TEMPLATE_LINE: "LINE",
    TEMPLATE_DOCUMENT: "DOC",
    TEMPLATE_INITIALS: "INITIALS",
    TEMPLATE_REGEX: "CUSTOM",
}


@dataclass(frozen=True)
class RuleBuildRequest:
    template: str
    prefixes: str = ""
    min_digits: int = 2
    max_digits: int = 5
    allow_dash: bool = True
    allow_underscore: bool = True
    allow_space: bool = False
    allow_no_separator: bool = True
    suffix_letter: bool = True
    custom_pattern: str = ""


def build_pattern(request: RuleBuildRequest) -> str:
    if request.template == TEMPLATE_REGEX:
        return validate_regex(request.custom_pattern)
    if request.min_digits < 1 or request.max_digits < request.min_digits:
        raise ValueError("La plage de chiffres est invalide.")

    prefixes = parse_prefixes(request.prefixes)
    separator = separator_pattern(request)
    suffix = r"[A-Z]?" if request.suffix_letter else ""

    if request.template == TEMPLATE_INSTRUMENT:
        prefix_pattern = alternatives(prefixes) if prefixes else r"[A-Z]{2,4}"
        return rf"\b{prefix_pattern}{separator}\d{{{request.min_digits},{request.max_digits}}}{suffix}\b"

    if request.template == TEMPLATE_LINE:
        service_pattern = alternatives(prefixes) if prefixes else r"[A-Z]{1,4}"
        return rf"\b\d{{1,3}}{separator}{service_pattern}{separator}\d{{3,6}}{suffix}\b"

    if request.template == TEMPLATE_DOCUMENT:
        project_pattern = alternatives(prefixes) if prefixes else r"[A-Z]{2,6}"
        return rf"\b{project_pattern}\d{{2,4}}(?:[-_ ][A-Z0-9]{{2,10}}){{2,10}}\b"

    if request.template == TEMPLATE_INITIALS:
        return rf"\b{alternatives(prefixes)}\b" if prefixes else r"\b[A-Z]{2,4}\b"

    raise ValueError(f"Modele de regle inconnu: {request.template}")


def parse_prefixes(raw: str) -> list[str]:
    values = []
    for item in raw.replace(";", ",").split(","):
        value = item.strip().upper()
        if value:
            values.append(value)
    return sorted(set(values), key=values.index)


def separator_pattern(request: RuleBuildRequest) -> str:
    choices = []
    if request.allow_dash:
        choices.append("-")
    if request.allow_underscore:
        choices.append("_")
    if request.allow_space:
        choices.append(r"\s")
    if request.allow_no_separator or not choices:
        quantifier = "?"
    else:
        quantifier = ""
    return rf"(?:{'|'.join(choices)}){quantifier}" if choices else ""


def alternatives(values: list[str]) -> str:
    return rf"(?:{'|'.join(re.escape(value) for value in values)})"


def validate_regex(pattern: str) -> str:
    value = pattern.strip()
    if not value:
        raise ValueError("Le pattern technique est obligatoire.")
    re.compile(value)
    return value
