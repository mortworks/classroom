from __future__ import annotations

import html
import re
from typing import Any, Dict, List
from teachlib.formatting import caption_from_meta
from teachlib.bookmarks import resolve_image_path, resolve_snippet_image, resolve_youtube
from teachlib.config import HTML_OUT
from teachlib.models import Block

def build_html(blocks: List[Block], bookmarks: Dict[str, Any]) -> None:
    parts: List[str] = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>TeachMeet</title>")
    parts.append(
        "<style>"
        "body{font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin:2rem; line-height:1.35;}"
        "h1{margin-top:0;}"
        "section{margin:2rem 0; padding:1.25rem 1.5rem; border:1px solid #ddd; border-radius:12px;}"
        "figure{margin:1rem 0;}"
        "figcaption{font-size:0.95rem; opacity:0.8;}"
        ".teacher{margin-top:1rem; padding:0.75rem 1rem; background:#f5f5f5; border-radius:10px;}"
        ".teacher summary{cursor:pointer; font-weight:600;}"
        "img{max-width:100%; height:auto; border-radius:10px;}"
        "</style>"
    )
    parts.append("</head><body>")

    title = next((b.title for b in blocks if b.kind == "title"), "TeachMeet")
    parts.append(f"<h1>{html.escape(title)}</h1>")

    for b in blocks:
        if b.kind != "slide":
            continue
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(b.title)}</h2>")

        if b.bullets:
            parts.append("<ul>")
            for bullet in b.bullets:
                parts.append(f"<li>{html.escape(bullet)}</li>")
            parts.append("</ul>")

        for macro_type, key in b.macros:
            if macro_type == "img":
                img_path, meta = resolve_image_path(bookmarks, key)
                entry = bookmarks["images"][key]
                src = entry.get("image_url") or entry.get("image_file") or str(img_path)
                alt = entry.get("alt") or ""
                cap = caption_from_meta(meta)
                source = meta.get("source_page") or ""
                parts.append("<figure>")
                parts.append(f"<img src='{html.escape(src)}' alt='{html.escape(alt)}'>")
                if cap or source:
                    out = html.escape(cap)
                    if source:
                        out += f" — <a href='{html.escape(source)}'>source</a>"
                    parts.append(f"<figcaption>{out}</figcaption>")
                parts.append("</figure>")

            elif macro_type == "snippet":
                img_path, meta = resolve_snippet_image(bookmarks, key)
                rel = img_path.as_posix()
                parts.append("<figure>")
                parts.append(f"<img src='{html.escape(rel)}' alt=''>")
                if meta.get("title"):
                    parts.append(f"<figcaption>{html.escape(meta['title'])}</figcaption>")
                parts.append("</figure>")

            elif macro_type == "yt":
                yt = resolve_youtube(bookmarks, key)
                label = html.escape(yt.get("title") or key)
                url = yt.get("youtube_url") or ""
                home = yt.get("homepage") or ""
                vid = yt.get("video_id") or ""
                start = (yt.get("start_time") or "").strip()

                # Turn start_time into seconds if it's a plain integer; otherwise ignore
                start_q = ""
                if start.isdigit():
                    start_q = f"?start={start}"

                parts.append("<div style='margin:1rem 0'>")
                if vid:
                    parts.append(
                        f"<iframe width='800' height='450' "
                        f"src='https://www.youtube-nocookie.com/embed/{html.escape(vid)}{start_q}' "
                        f"frameborder='0' "
                        f"allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture' "
                        f"allowfullscreen></iframe>"
                    )
                    parts.append(f"<div style='opacity:0.8; margin-top:0.25rem'>{label}</div>")
                    if home:
                        parts.append(f"<div style='opacity:0.8'><a href='{html.escape(home)}'>homepage</a></div>")
                else:
                    parts.append("<p><strong>Video:</strong> ")
                    if url:
                        parts.append(f"<a href='{html.escape(url)}'>{label}</a>")
                    else:
                        parts.append(label)
                    if home:
                        parts.append(f" (<a href='{html.escape(home)}'>homepage</a>)")
                    parts.append("</p>")
                parts.append("</div>")

        if b.teacher_notes.strip():
            parts.append("<details class='teacher'><summary>Teacher notes</summary>")
            parts.append(f"<pre>{html.escape(b.teacher_notes.strip())}</pre>")
            parts.append("</details>")

        parts.append("</section>")

    parts.append("</body></html>")
    HTML_OUT.write_text("".join(parts), encoding="utf-8")
    return HTML_OUT
