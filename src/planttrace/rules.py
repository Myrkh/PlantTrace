from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import ExtractionRule, ProjectPaths


DEFAULT_RULES = [
    ExtractionRule(
        name="Instrument tags",
        kind="TAG",
        pattern=r"\b[A-Z]{2,4}[-_]?\d{2,5}[A-Z]?\b",
        confidence="medium",
    ),
    ExtractionRule(
        name="Pipe lines",
        kind="LINE",
        pattern=r"\b\d{1,3}[-_ ][A-Z]{1,4}[-_ ]\d{3,6}[A-Z]?\b",
    ),
    ExtractionRule(
        name="Project document numbers",
        kind="DOC",
        pattern=r"\b[A-Z]{2,6}\d{2,4}(?:[-_ ][A-Z0-9]{2,8}){3,8}\b",
    ),
    ExtractionRule(
        name="Initials",
        kind="INITIALS",
        pattern=r"\b[A-Z]{2,4}\b",
        enabled=False,
        confidence="low",
    ),
]


def load_rules(project_root: Path) -> list[ExtractionRule]:
    paths = ProjectPaths(project_root.resolve())
    if not paths.rules_path.exists():
        return DEFAULT_RULES
    with paths.rules_path.open("r", encoding="utf-8") as handle:
        raw_rules = json.load(handle)
    return [ExtractionRule(**item) for item in raw_rules]


def save_rules(project_root: Path, rules: list[ExtractionRule]) -> None:
    paths = ProjectPaths(project_root.resolve())
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    with paths.rules_path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(rule) for rule in rules], handle, ensure_ascii=False, indent=2)


def load_stoplist(project_root: Path) -> set[str]:
    paths = ProjectPaths(project_root.resolve())
    if not paths.stoplist_path.exists():
        return set()
    with paths.stoplist_path.open("r", encoding="utf-8") as handle:
        return {line.strip().upper() for line in handle if line.strip() and not line.strip().startswith("#")}


def save_stoplist(project_root: Path, values: set[str]) -> None:
    paths = ProjectPaths(project_root.resolve())
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    normalized = sorted({value.strip().upper() for value in values if value.strip()})
    with paths.stoplist_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(normalized))
        if normalized:
            handle.write("\n")
