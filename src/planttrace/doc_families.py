from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import ProjectPaths
from .store import PlantTraceStore


@dataclass(frozen=True)
class FamilyRule:
    family: str
    label: str
    filename_terms: tuple[str, ...]
    text_terms: tuple[str, ...]


@dataclass(frozen=True)
class DocumentFamily:
    family: str
    label: str
    confidence: str
    score: int
    document_path: str
    filename: str
    pages: int
    evidence: str
    document_status: str


FAMILY_RULES = [
    FamilyRule(
        "PID_PFD",
        "PID / PFD",
        ("PID", "P&ID", "PFD"),
        ("PIPING AND INSTRUMENTATION", "PIPING & INSTRUMENTATION", "PROCESS FLOW DIAGRAM", "P&ID", "PFD"),
    ),
    FamilyRule(
        "LOOP",
        "Loop diagram",
        ("LOOP", "BOUCLE"),
        ("LOOP DIAGRAM", "LOOP DRAWING", "SCHEMA DE BOUCLE", "BOUCLE INSTRUMENT"),
    ),
    FamilyRule(
        "DATASHEET",
        "Datasheet",
        ("DATASHEET", "DATA-SHEET", "FICHE"),
        ("DATA SHEET", "DATASHEET", "FICHE TECHNIQUE", "SPECIFICATION SHEET"),
    ),
    FamilyRule(
        "TERMINAL_JB",
        "Bornier / JB",
        ("TERMINAL", "BORNIER", "JUNCTION", "JB", "WIRING"),
        ("TERMINAL", "BORNIER", "JUNCTION BOX", "BOITE DE JONCTION", "WIRING DIAGRAM", "CONNECTION DIAGRAM"),
    ),
    FamilyRule(
        "IO_PLC",
        "IO / Automate",
        ("IO", "I-O", "PLC", "AUTOMATE", "AFFECTATION"),
        ("I/O LIST", "IO LIST", "PLC", "AUTOMATE", "AFFECTATION AUTOMATE", "INPUT OUTPUT"),
    ),
    FamilyRule(
        "INSTRUMENT_LIST",
        "Liste instruments",
        ("INSTRUMENT-LIST", "INSTRUMENT_LIST", "LISTE-INSTRUMENT"),
        ("INSTRUMENT LIST", "LISTE INSTRUMENT", "INSTRUMENT INDEX", "MEASURING POINT"),
    ),
    FamilyRule(
        "VENDOR",
        "Vendor / Fournisseur",
        ("VENDOR", "SUPPLIER", "FOURNISSEUR", "MANUAL", "NOTICE"),
        ("VENDOR", "SUPPLIER", "FOURNISSEUR", "OPERATING MANUAL", "INSTALLATION MANUAL", "NOTICE TECHNIQUE"),
    ),
    FamilyRule(
        "ADMIN_REVIEW",
        "Review / Commentaires",
        ("COMMENT", "REVIEW", "VISA", "TRANSMITTAL"),
        ("COMMENT RESPONSE", "REVIEW SHEET", "COMMENTAIRES", "BORDEREAU", "TRANSMITTAL", "VISA"),
    ),
]


def classify_documents(project_root: Path) -> list[DocumentFamily]:
    pages_by_document: dict[str, list[dict[str, object]]] = {}
    store = PlantTraceStore(ProjectPaths(Path(project_root).resolve()))
    for row in store.indexed_pages():
        pages_by_document.setdefault(row["path"], []).append(
            {
                "page": int(row["page_number"]),
                "text": str(row["text"]),
                "document_status": str(row["document_status"]),
            }
        )
    families = [classify_document(path, pages) for path, pages in sorted(pages_by_document.items())]
    return sorted(families, key=lambda item: (item.family == "UNKNOWN", item.family, item.filename.lower()))


def classify_document(document_path: str, pages: list[dict[str, object]]) -> DocumentFamily:
    filename = Path(document_path).name
    text = "\n".join(str(page["text"]) for page in sorted(pages, key=lambda page: int(page["page"]))[:3])
    best_rule, score, evidence = best_family(filename, text)
    if best_rule is None:
        family = "UNKNOWN"
        label = "A classer"
        confidence = "low"
        evidence_text = "Aucune preuve de famille trouvee dans le nom ou les premieres pages."
    else:
        family = best_rule.family
        label = best_rule.label
        confidence = confidence_for(score)
        evidence_text = "; ".join(evidence[:4])
    return DocumentFamily(
        family=family,
        label=label,
        confidence=confidence,
        score=score,
        document_path=document_path,
        filename=filename,
        pages=max((int(page["page"]) for page in pages), default=0),
        evidence=evidence_text,
        document_status=str(pages[0]["document_status"]) if pages else "unknown",
    )


def best_family(filename: str, text: str) -> tuple[FamilyRule | None, int, list[str]]:
    filename_upper = normalize(filename)
    text_upper = normalize(text)
    best: tuple[FamilyRule | None, int, list[str]] = (None, 0, [])
    for rule in FAMILY_RULES:
        score = 0
        evidence: list[str] = []
        for term in rule.filename_terms:
            if normalize(term) in filename_upper:
                score += 4
                evidence.append(f"nom fichier: {term}")
        for term in rule.text_terms:
            if normalize(term) in text_upper:
                score += 3
                evidence.append(f"texte: {term}")
        if score > best[1]:
            best = (rule, score, evidence)
    if best[1] < 3:
        return None, 0, []
    return best


def normalize(value: str) -> str:
    return value.upper().replace("_", " ").replace("-", " ")


def confidence_for(score: int) -> str:
    if score >= 7:
        return "high"
    if score >= 4:
        return "medium"
    return "low"
