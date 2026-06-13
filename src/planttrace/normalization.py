from __future__ import annotations

import re
import unicodedata


OCR_CONFUSIONS = str.maketrans({
    "O": "0",
    "o": "0",
    "I": "1",
    "l": "1",
})


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").upper()


def compact_identifier(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", fold_text(value))


def compact_ocr_identifier(value: str) -> str:
    return compact_identifier(value.translate(OCR_CONFUSIONS))


def query_tokens(value: str) -> list[str]:
    return re.findall(r"[A-Z0-9]{2,}", fold_text(value))


def is_probable_identifier(query: str) -> bool:
    compact = compact_identifier(query)
    if len(compact) < 3:
        return False
    return bool(re.search(r"[A-Z]", compact) and re.search(r"\d", compact))


def exact_variants(query: str) -> set[str]:
    compact = compact_identifier(query)
    variants = {query.strip(), compact}
    match = re.match(r"^([A-Z]+)(\d+)$", compact)
    if match:
        prefix, digits = match.groups()
        variants.add(f"{prefix}-{digits}")
        variants.add(f"{prefix} {digits}")
        variants.add(f"{prefix}_{digits}")
    return {item for item in variants if item}

