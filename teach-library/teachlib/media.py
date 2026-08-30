from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Optional

from teachlib.config import CACHE_DIR

# Optional for aspect ratio inference
try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None  # Pillow not installed


def download_to_cache(url: str, key: str) -> Path:
    ext = Path(url.split("?")[0]).suffix or ".img"
    out = CACHE_DIR / f"{key}{ext}"

    if out.exists() and out.stat().st_size > 0:
        return out

    req = urllib.request.Request(url, headers={"User-Agent": "teach-library/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        out.write_bytes(resp.read())
    return out


def image_aspect_ratio(path: Path) -> Optional[float]:
    """Return width/height. Requires Pillow; returns None if unavailable."""
    if Image is None:
        return None
    try:
        with Image.open(path) as im:
            w, h = im.size
        if h == 0:
            return None
        return w / h
    except Exception:
        return None


def youtube_id_from_url(url: str) -> Optional[str]:
    url = (url or "").strip()
    if not url:
        return None

    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    m = re.search(r"youtube\.com/embed/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)

    return None


def youtube_thumbnail_path(video_id: str) -> Path:
    """
    Download a reasonable thumbnail into cache.
    Try maxres, fall back to hq.
    """
    urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
    ]

    last_exc = None
    for u in urls:
        try:
            p = download_to_cache(u, f"yt-{video_id}")
            if p.exists() and p.stat().st_size > 10_000:
                return p
        except Exception as e:
            last_exc = e

    raise RuntimeError(f"Could not fetch thumbnail for {video_id}: {last_exc}")
