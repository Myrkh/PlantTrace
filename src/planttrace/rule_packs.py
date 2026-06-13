from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import ExtractionRule


PACK_VERSION = 1


@dataclass(frozen=True)
class RulePack:
    name: str
    rules: list[ExtractionRule]
    stoplist: set[str]


def available_preset_names() -> list[str]:
    return ["Instrumentation", "Tuyauterie", "Documents projet"]


def load_preset_pack(name: str) -> RulePack:
    if name == "Instrumentation":
        return RulePack(
            name=name,
            rules=[
                ExtractionRule("Instrument tags", "TAG", r"\b(?:FV|PV|PT|TT|FT|LT|XV|HV|HS|LS|PS|ZS)[-_ ]?\d{3,5}[A-Z]?\b", confidence="high"),
                ExtractionRule("Junction boxes", "TAG", r"\b(?:JB|JBD|JBA)[-_ ]?\d{2,5}[A-Z]?\b", confidence="medium"),
                ExtractionRule("Initials", "INITIALS", r"\b[A-Z]{2,4}\b", enabled=False, confidence="low"),
            ],
            stoplist={"RJ45", "BP13"},
        )
    if name == "Tuyauterie":
        return RulePack(
            name=name,
            rules=[
                ExtractionRule("Pipe lines", "LINE", r"\b\d{1,3}[-_ ][A-Z]{1,4}[-_ ]\d{3,6}[A-Z]?\b", confidence="high"),
                ExtractionRule("Pipe specs", "LINE", r"\b[A-Z]{1,3}\d{1,3}[-_ ][A-Z]{1,4}\b", confidence="medium"),
            ],
            stoplist={"ISO", "PID"},
        )
    if name == "Documents projet":
        return RulePack(
            name=name,
            rules=[
                ExtractionRule("Project document numbers", "DOC", r"\b[A-Z]{2,6}\d{2,4}(?:[-_ ][A-Z0-9]{2,10}){2,10}\b", confidence="high"),
                ExtractionRule("Revision codes", "DOC", r"\bREV[-_ ]?[A-Z0-9]{1,3}\b", confidence="medium"),
                ExtractionRule("Initials", "INITIALS", r"\b[A-Z]{2,4}\b", enabled=False, confidence="low"),
            ],
            stoplist={"PLAN619"},
        )
    raise ValueError(f"Pack de regles inconnu: {name}")


def project_rule_pack(name: str, rules: list[ExtractionRule], stoplist: set[str]) -> RulePack:
    return RulePack(name=name.strip() or "PlantTrace project rules", rules=rules, stoplist=normalized_stoplist(stoplist))


def export_rule_pack(pack: RulePack, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": PACK_VERSION,
        "name": pack.name,
        "rules": [asdict(rule) for rule in pack.rules],
        "stoplist": sorted(pack.stoplist),
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def import_rule_pack(path: Path) -> RulePack:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload.get("version", 0)) != PACK_VERSION:
        raise ValueError("Version de pack non supportee.")
    rules = [ExtractionRule(**item) for item in payload.get("rules", [])]
    if not rules:
        raise ValueError("Le pack ne contient aucune regle.")
    return RulePack(
        name=str(payload.get("name") or path.stem),
        rules=rules,
        stoplist=normalized_stoplist(set(payload.get("stoplist", []))),
    )


def normalized_stoplist(values: set[str]) -> set[str]:
    return {value.strip().upper() for value in values if value.strip()}
