from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Tuple

from teachlib.bookmarks import resolve_image_path, resolve_snippet_image, resolve_youtube
from teachlib.config import LIBRARY_OUT, PROJECT_ROOT
from teachlib.formatting import caption_from_meta
from teachlib.media import youtube_thumbnail_path


from pathlib import Path
import os

def _rel_from_output(target: Path, out_file: Path) -> str:
    """
    Return a browser-friendly relative path from the HTML output folder
    to the target file.
    """
    out_dir = out_file.parent.resolve()
    tgt = target.resolve()
    return os.path.relpath(tgt, out_dir).replace(os.sep, "/")


def _tags(entry: Dict[str, Any]) -> List[str]:
    tags = entry.get("tags") or []
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return []


def build_library_html(bookmarks: Dict[str, Any], out_path: Path | None = None) -> Path:
    out_path = out_path or LIBRARY_OUT
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parts: List[str] = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>Teach library</title>")

    parts.append(
        "<style>"
        "body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:1.5rem;line-height:1.35;}"
        "h1{margin:0 0 0.75rem 0;}"
        ".bar{display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;margin:0 0 1rem 0;}"
        "input{padding:0.55rem 0.7rem;border:1px solid #ccc;border-radius:10px;min-width:260px;}"
        ".pill{display:inline-block;padding:0.2rem 0.55rem;border:1px solid #ddd;border-radius:999px;"
        "font-size:0.9rem;cursor:pointer;user-select:none;}"
        ".pill.active{border-color:#000;}"
        ".section{margin:1.75rem 0;}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;}"
        ".card{border:1px solid #ddd;border-radius:14px;overflow:hidden;background:#fff;"
        "box-shadow:0 1px 0 rgba(0,0,0,0.04);}"
        ".thumb{width:100%;height:170px;object-fit:cover;display:block;background:#f3f3f3;}"
        ".content{padding:0.85rem 0.95rem;}"
        ".k{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:0.9rem;opacity:0.8;}"
        ".t{font-weight:650;margin:0.25rem 0 0.35rem 0;}"
        ".m{font-size:0.95rem;opacity:0.9;}"
        ".tags{margin-top:0.6rem;display:flex;gap:0.35rem;flex-wrap:wrap;}"
        ".tag{font-size:0.85rem;padding:0.15rem 0.45rem;border:1px solid #eee;border-radius:999px;opacity:0.9;}"
        ".meta{margin-top:0.35rem;font-size:0.9rem;opacity:0.8;}"
        ".linkrow{margin-top:0.55rem;font-size:0.9rem;}"
        ".linkrow a{opacity:0.9;}"
        "</style>"
    )

    # tiny client-side filter
    parts.append(
        "<script>"
        "let activeTag='';"
        "function setTag(t){activeTag=(activeTag===t?'':t);"
        "document.querySelectorAll('.pill').forEach(p=>p.classList.toggle('active',p.dataset.tag===activeTag));"
        "applyFilter();}"
        "function applyFilter(){"
        "const q=(document.getElementById('q').value||'').toLowerCase();"
        "document.querySelectorAll('[data-search]').forEach(el=>{"
        "const s=(el.dataset.search||'').toLowerCase();"
        "const tags=(el.dataset.tags||'');"
        "const okQ=!q||s.includes(q);"
        "const okT=!activeTag||tags.split(',').includes(activeTag);"
        "el.style.display=(okQ&&okT)?'':'none';"
        "});}"
        "</script>"
    )

    parts.append("</head><body>")
    parts.append("<h1>Teach library</h1>")

    # Build a tag cloud across all sections
    tag_counts: Dict[str, int] = {}
    for section in ("images", "snippets", "youtube"):
        for _, entry in (bookmarks.get(section) or {}).items():
            for t in _tags(entry):
                tag_counts[t] = tag_counts.get(t, 0) + 1

    parts.append("<div class='bar'>")
    parts.append("<input id='q' placeholder='Search (key, title, tags…)…' oninput='applyFilter()'>")
    # pills (sorted by popularity then alpha)
    for t, _n in sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:40]:
        parts.append(f"<span class='pill' data-tag='{html.escape(t)}' onclick='setTag(this.dataset.tag)'>#{html.escape(t)}</span>")
    parts.append("</div>")

    def add_section(title: str, items_html: List[str]) -> None:
        parts.append(f"<div class='section'><h2>{html.escape(title)}</h2>")
        parts.append("<div class='grid'>")
        parts.extend(items_html)
        parts.append("</div></div>")

    # --- IMAGES ---
    image_cards: List[str] = []
    for key, entry in sorted((bookmarks.get("images") or {}).items(), key=lambda kv: kv[0]):
        try:
            img_path, meta = resolve_image_path(bookmarks, key)
            src = (entry.get("image_url") or "").strip() or _rel_from_output(img_path, out_path)
        except Exception:
            # Skip entries that are not actual image assets
            continue
        page = (entry.get("source_page") or meta.get("source_page") or "").strip()
        cap = caption_from_meta(meta).strip()
        tags = _tags(entry)
        search_blob = " ".join([key, entry.get("title", ""), entry.get("artist", ""), entry.get("year", ""), " ".join(tags), page])

        card = []
        card.append(
            f"<div class='card' data-search='{html.escape(search_blob)}' data-tags='{html.escape(','.join(tags))}'>"
        )
        if page:
            card.append(f"<a href='{html.escape(page)}' target='_blank' rel='noreferrer'>")
        card.append(f"<img class='thumb' src='{html.escape(src)}' loading='lazy'>")
        if page:
            card.append("</a>")
        card.append("<div class='content'>")
        card.append(f"<div class='k'>{html.escape(key)}</div>")
        card.append(f"<div class='t'>{html.escape(entry.get('title','') or meta.get('title','') or key)}</div>")
        if cap:
            card.append(f"<div class='m'>{html.escape(cap)}</div>")
        if page:
            card.append(f"<div class='linkrow'><a href='{html.escape(page)}' target='_blank' rel='noreferrer'>source page</a></div>")
        if tags:
            card.append("<div class='tags'>" + "".join(f"<span class='tag'>#{html.escape(t)}</span>" for t in tags) + "</div>")
        card.append("</div></div>")
        image_cards.append("".join(card))

    # --- SNIPPETS ---
    snippet_cards: List[str] = []
    for key, entry in sorted((bookmarks.get("snippets") or {}).items(), key=lambda kv: kv[0]):
        img_path, meta = resolve_snippet_image(bookmarks, key)
        src = _rel_from_output(img_path, out_path)
        tags = _tags(entry)
        title = entry.get("title") or meta.get("title") or key
        search_blob = " ".join([key, title, entry.get("source", ""), entry.get("date", ""), " ".join(tags)])

        card = []
        card.append(f"<div class='card' data-search='{html.escape(search_blob)}' data-tags='{html.escape(','.join(tags))}'>")
        card.append(f"<img class='thumb' src='{html.escape(src)}' loading='lazy'>")
        card.append("<div class='content'>")
        card.append(f"<div class='k'>{html.escape(key)}</div>")
        card.append(f"<div class='t'>{html.escape(title)}</div>")

        meta_line = " — ".join([x for x in [entry.get("source", ""), entry.get("date", "")] if x])
        if meta_line:
            card.append(f"<div class='meta'>{html.escape(meta_line)}</div>")

        if tags:
            card.append("<div class='tags'>" + "".join(f"<span class='tag'>#{html.escape(t)}</span>" for t in tags) + "</div>")
        card.append("</div></div>")
        snippet_cards.append("".join(card))

    # --- YOUTUBE ---
    yt_cards: List[str] = []
    for key, entry in sorted((bookmarks.get("youtube") or {}).items(), key=lambda kv: kv[0]):
        yt = resolve_youtube(bookmarks, key)
        url = (yt.get("youtube_url") or "").strip()
        home = (yt.get("homepage") or "").strip()
        vid = (yt.get("video_id") or "").strip()
        tags = _tags(entry)

        thumb_src = ""
        if vid:
            try:
                p = youtube_thumbnail_path(vid)
                thumb_src = _rel_from_output(p, out_path)
            except Exception:
                thumb_src = ""  # fail soft

        title = yt.get("title") or key
        who = yt.get("speaker") or ""
        yr = yt.get("year") or ""
        provider = yt.get("provider") or ""
        line = " — ".join([x for x in [who, yr, provider] if x])

        search_blob = " ".join([key, title, who, yr, provider, " ".join(tags), url, home])

        card = []
        card.append(f"<div class='card' data-search='{html.escape(search_blob)}' data-tags='{html.escape(','.join(tags))}'>")
        if url:
            card.append(f"<a href='{html.escape(url)}' target='_blank' rel='noreferrer'>")
        if thumb_src:
            card.append(f"<img class='thumb' src='{html.escape(thumb_src)}' loading='lazy'>")
        else:
            # simple placeholder if no thumb
            card.append("<div class='thumb' style='display:flex;align-items:center;justify-content:center;'>▶</div>")
        if url:
            card.append("</a>")
        card.append("<div class='content'>")
        card.append(f"<div class='k'>{html.escape(key)}</div>")
        card.append(f"<div class='t'>{html.escape(title)}</div>")
        if line:
            card.append(f"<div class='meta'>{html.escape(line)}</div>")
        links = []
        if url:
            links.append(f"<a href='{html.escape(url)}' target='_blank' rel='noreferrer'>youtube</a>")
        if home:
            links.append(f"<a href='{html.escape(home)}' target='_blank' rel='noreferrer'>homepage</a>")
        if links:
            card.append("<div class='linkrow'>" + " · ".join(links) + "</div>")
        if tags:
            card.append("<div class='tags'>" + "".join(f"<span class='tag'>#{html.escape(t)}</span>" for t in tags) + "</div>")
        card.append("</div></div>")
        yt_cards.append("".join(card))

    add_section("images", image_cards)
    add_section("snippets", snippet_cards)
    add_section("youtube", yt_cards)

    parts.append("<script>applyFilter();</script>")
    parts.append("</body></html>")

    out_path.write_text("".join(parts), encoding="utf-8")
    return out_path
