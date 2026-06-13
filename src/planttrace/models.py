from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def data_dir(self) -> Path:
        return self.root / ".planttrace"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "planttrace.sqlite"

    @property
    def embedding_path(self) -> Path:
        return self.data_dir / "embeddings.npy"

    @property
    def rules_path(self) -> Path:
        return self.data_dir / "rules.json"

    @property
    def stoplist_path(self) -> Path:
        return self.data_dir / "stoplist.txt"


@dataclass(frozen=True)
class PdfPage:
    page_number: int
    text: str
    status: str


@dataclass(frozen=True)
class SearchResult:
    query: str
    match_type: str
    document_path: str
    page: int | None
    score: float
    found_as: str
    excerpt: str
    page_status: str
    document_status: str


@dataclass(frozen=True)
class ExtractionRule:
    name: str
    kind: str
    pattern: str
    enabled: bool = True
    confidence: str = "high"


@dataclass(frozen=True)
class ExtractionHit:
    kind: str
    value: str
    rule: str
    document_path: str
    page: int
    excerpt: str
    confidence: str
    page_status: str
    document_status: str
