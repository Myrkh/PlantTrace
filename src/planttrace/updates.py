from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from . import __version__

RELEASES_API = "https://api.github.com/repos/Myrkh/PlantTrace/releases/latest"
RELEASES_PAGE = "https://github.com/Myrkh/PlantTrace/releases/latest"


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str
    url: str
    available: bool
    asset_url: str = ""
    asset_name: str = ""


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
    asset_url, asset_name = _zip_asset(payload)
    return UpdateInfo(
        current=__version__,
        latest=latest,
        url=url,
        available=is_newer(latest, __version__),
        asset_url=asset_url,
        asset_name=asset_name,
    )


def _zip_asset(payload: dict) -> tuple[str, str]:
    for asset in payload.get("assets") or []:
        name = str(asset.get("name") or "")
        if name.lower().endswith(".zip"):
            return str(asset.get("browser_download_url") or ""), name
    return "", ""


def download_release(url: str, dest: Path, on_progress: Callable[[int], None] | None = None, timeout: float = 30.0) -> Path:
    """Telecharge l'asset de release vers dest (streaming + progression %)."""
    request = urllib.request.Request(url, headers={"User-Agent": "PlantTrace"})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=timeout) as response, dest.open("wb") as handle:
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        while True:
            chunk = response.read(256 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            downloaded += len(chunk)
            if on_progress and total:
                on_progress(int(downloaded * 100 / total))
    return dest
