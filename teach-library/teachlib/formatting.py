from __future__ import annotations

from typing import Dict

def caption_from_meta(meta: Dict[str, str]) -> str:
    bits = []
    artist = meta.get("artist", "").strip()
    title = meta.get("title", "").strip()
    year = meta.get("year", "").strip()
    inst = meta.get("source_institution", "").strip()

    if artist:
        bits.append(artist)
    if title:
        bits.append(title)
    if year:
        bits.append(year)

    cap = " — ".join(bits)
    if inst:
        cap = f"{cap} ({inst})" if cap else inst
    return cap

def one_line(text: str) -> str:
    return " ".join((text or "").split())

def truncate(text: str, n: int = 70) -> str:
    t = one_line(text)
    return (t[: n - 1] + "…") if len(t) > n else t

def format_caption(text: str, spec: CaptionSpec) -> str:
    t = one_line(text) if spec.one_line else (text or "").strip()
    if spec.one_line:
        return truncate(t, spec.max_chars)
    # multi-line: still cap length, but don't squash whitespace
    return (t[: spec.max_chars - 1] + "…") if len(t) > spec.max_chars else t

def caption_from_meta(meta: Dict[str, str]) -> str:
    bits = []
    artist = meta.get("artist", "").strip()
    title = meta.get("title", "").strip()
    year = meta.get("year", "").strip()
    inst = meta.get("source_institution", "").strip()

    if artist:
        bits.append(artist)
    if title:
        bits.append(title)
    if year:
        bits.append(year)

    cap = " — ".join(bits)
    if inst:
        cap = f"{cap} ({inst})" if cap else inst
    return cap
