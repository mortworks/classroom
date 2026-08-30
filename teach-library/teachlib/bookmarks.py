from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from teachlib.config import PROJECT_ROOT
from teachlib.media import download_to_cache, youtube_id_from_url


def load_bookmarks(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for section in ("images", "youtube", "snippets"):
        data.setdefault(section, {})
    return data


def resolve_image_path(bookmarks: Dict[str, Any], key: str) -> Tuple[Path, Dict[str, str]]:
    entry = bookmarks["images"].get(key)
    if not entry:
        raise KeyError(f"Unknown image key: {key}")

    url = (entry.get("image_url") or "").strip()
    local = (entry.get("image_file") or "").strip()

    if local:
        p = PROJECT_ROOT / local
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {p}")
        img_path = p
    elif url:
        img_path = download_to_cache(url, f"img-{key}")
    else:
        raise ValueError(f"Image entry has neither image_file nor image_url: {key}")

    meta = {
        "title": entry.get("title", ""),
        "artist": entry.get("artist", ""),
        "year": entry.get("year", ""),
        "source_institution": entry.get("source_institution", ""),
        "source_page": entry.get("source_page", ""),
    }
    return img_path, meta


def resolve_snippet_image(bookmarks: Dict[str, Any], key: str) -> Tuple[Path, Dict[str, str]]:
    entry = bookmarks["snippets"].get(key)
    if not entry:
        raise KeyError(f"Unknown snippet key: {key}")

    image_file = (entry.get("image_file") or "").strip()
    if not image_file:
        raise ValueError(f"Snippet entry missing image_file: {key}")

    p = PROJECT_ROOT / image_file
    if not p.exists():
        raise FileNotFoundError(f"Snippet image not found: {p}")

    meta = {
        "title": entry.get("title", ""),
        "source": entry.get("source", ""),
        "date": entry.get("date", ""),
    }
    return p, meta


def resolve_youtube(bookmarks: Dict[str, Any], key: str) -> Dict[str, str]:
    entry = bookmarks["youtube"].get(key)
    if not entry:
        raise KeyError(f"Unknown youtube key: {key}")

    url = (entry.get("youtube_url") or "").strip()
    vid = (entry.get("video_id") or "").strip() or (youtube_id_from_url(url) or "")

    return {
        "title": entry.get("title", ""),
        "speaker": entry.get("speaker", ""),
        "year": entry.get("year", ""),
        "provider": entry.get("provider", ""),
        "youtube_url": url,
        "homepage": entry.get("homepage", ""),
        "video_id": vid,
        "start_time": entry.get("start_time", ""),
        "description": entry.get("description", ""),
        "notes": entry.get("notes", ""),
    }
