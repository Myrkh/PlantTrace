from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from . import __version__

RELEASES_API = "https://api.github.com/repos/Myrkh/PlantTrace/releases/latest"
RELEASES_PAGE = "https://github.com/Myrkh/PlantTrace/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    url: str
    available: bool


def _version_tuple(value: str) -> tuple[int, ...]:
    numbers: list[int] = []
    for part in value.strip().lstrip("vV").split("."):
        digits = "".join(char for char in part if char.isdigit())
        numbers.append(int(digits) if digits else 0)
    return tuple(numbers)


def is_newer(latest: str, current: str) -> bool:
    return _version_tuple(latest) > _version_tuple(current)


def check_for_update(timeout: float = 4.0) -> UpdateInfo | None:
    """Interroge la derniere Release GitHub. Renvoie None hors ligne ou si indisponible."""
    request = urllib.request.Request(
        RELEASES_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "PlantTrace"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except Exception:
        return None
    latest = str(payload.get("tag_name") or "").lstrip("vV")
    if not latest:
        return None
    url = str(payload.get("html_url") or RELEASES_PAGE)
    return UpdateInfo(current=__version__, latest=latest, url=url, available=is_newer(latest, __version__))
