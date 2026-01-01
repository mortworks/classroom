#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
import html

ROOT = Path(__file__).parent

SOURCE = ROOT / "source.md"
TEMPLATE = ROOT / "template.html"
OUTPUT = ROOT / "output.html"

def parse_bookmarks(md: str) -> dict[str, dict[str, str]]:
    lines = md.splitlines()
    resources: dict[str, dict[str, str]] = {}
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = re.match(r"^@(video|link)\s+([a-zA-Z0-9_\-]+)\s*$", line)
        if not m:
            i += 1
            continue
        rtype, rid = m.group(1), m.group(2)
        item = {"type": rtype, "label": "", "url": "", "desc": ""}
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if re.match(r"^@(video|link)\s+", nxt):
                break
            kv = re.match(r"^(label|url|desc)\s*:\s*(.+)\s*$", nxt)
            if kv:
                item[kv.group(1)] = kv.group(2).strip()
            i += 1
        resources[rid] = item
    return resources

def video_block(rid: str, resources: dict[str, dict[str, str]]) -> str:
    item = resources.get(rid)
    if not item or not item.get("url"):
        return (
            "<div class='video'>"
            "<div class='video-top'>"
            "<div class='video-title'><span class='tag'>Video</span> Missing bookmark: "
            f"<code>{html.escape(rid)}</code></div>"
            "</div></div>"
        )

    url = item["url"]
    label = (item.get("label","Video") or "Video").strip()
    desc = (item.get("desc","") or "").strip()

    vid = None
    m = re.search(r"youtu\.be/([^?&/]+)", url)
    if m: vid = m.group(1)
    m = re.search(r"youtube\.com/watch\?v=([^?&/]+)", url)
    if m: vid = m.group(1)

    safe_url = html.escape(url, quote=True)
    safe_label = html.escape(label)
    safe_desc = html.escape(desc)

    thumb_html = ""
    if vid:
        thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        thumb_html = (
            f"<a class='video-thumb' href=\"{safe_url}\" target=\"_blank\" rel=\"noreferrer\">"
            f"<img alt='Video thumbnail' src=\"{html.escape(thumb, quote=True)}\"></a>"
        )

    top = []
    top.append("<div class='video-top'>")
    top.append(thumb_html)
    top.append(
        f"<div class='video-title'><span class='tag'>Video</span> "
        f"<a href=\"{safe_url}\" target=\"_blank\" rel=\"noreferrer\"><strong>{safe_label}</strong></a></div>"
    )
    if desc:
        top.append(f"<p class='video-desc'>{safe_desc}</p>")
    top.append("</div>")  # video-top

    bottom = (
        "<div class='video-bottom'>"
        f"<p class='video-open'><a href=\"{safe_url}\" target=\"_blank\" rel=\"noreferrer\">Open on YouTube</a></p>"
        "</div>"
    )

    return "<div class='video'>" + "".join(top) + bottom + "</div>"

def local_prompts_block(prompts: dict[str, object], resources: dict[str, dict[str, str]]) -> str:
    sections: list[str] = []

    task = (prompts.get("task") or "").strip()
    if task:
        task_html = inline_format(expand_inline_refs(task, resources))
        sections.append(
            "<div class='prompt-section'>"
            "<div class='prompt-title'>Task</div>"
            f"<p>{task_html}</p>"
            "</div>"
        )

    watch = prompts.get("watch") or []
    if isinstance(watch, list) and watch:
        items = []
        for item in watch:
            txt = inline_format(expand_inline_refs(str(item), resources))
            items.append(f"<li>{txt}</li>")
        sections.append(
            "<div class='prompt-section'>"
            "<div class='prompt-title'>Watch for</div>"
            f"<ul>{''.join(items)}</ul>"
            "</div>"
        )

    after = prompts.get("after") or []
    if isinstance(after, list) and after:
        items = []
        for item in after:
            txt = inline_format(expand_inline_refs(str(item), resources))
            items.append(f"<li>{txt}</li>")
        sections.append(
            "<div class='prompt-section'>"
            "<div class='prompt-title'>After watching</div>"
            f"<ul>{''.join(items)}</ul>"
            "</div>"
        )

    if not sections:
        return ""

    return (
        "<div class='local-prompts'>"
        "<div class='local-prompts-title'>Local prompts</div>"
        + "".join(sections)
        + "</div>"
    )

def inline_link(rid: str, resources: dict[str, dict[str, str]]) -> str:
    item = resources.get(rid)
    if not item or not item.get("url"):
        return f"<code>Missing:{html.escape(rid)}</code>"
    url = item["url"]
    label = (item.get("label","Link") or "Link").strip()
    safe_url = html.escape(url, quote=True)
    safe_label = html.escape(label)
    # Keep inline links compact: label only.
    return f"<a href=\"{safe_url}\" target=\"_blank\" rel=\"noreferrer\">{safe_label}</a>"

def expand_inline_refs(text: str, resources: dict[str, dict[str, str]]) -> str:
    # Replace {{link:id}} inline (keeps list formatting)
    def sub(m: re.Match) -> str:
        rid = m.group(1)
        return inline_link(rid, resources)
    return re.sub(r"\{\{link:([a-zA-Z0-9_\-]+)\}\}", sub, text)

def inline_format(text: str) -> str:
    """
    Minimal inline markdown:
    - **bold**
    - *italic*
    - `code`
    This runs AFTER we have injected safe HTML anchors for inline links.
    We therefore escape everything, then re-insert the anchors placeholders.
    """
    # Protect existing <a ...>...</a> (from inline links)
    anchors: list[str] = []
    def protect(m: re.Match) -> str:
        anchors.append(m.group(0))
        return f"@@ANCHOR{len(anchors)-1}@@"
    protected = re.sub(r"<a\b[^>]*>.*?</a>", protect, text)

    esc = html.escape(protected)

    esc = re.sub(r"`([^`]+)`", r"<code>\1</code>", esc)
    esc = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", esc)
    esc = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", esc)

    # Restore anchors (safe HTML)
    for i, a in enumerate(anchors):
        esc = esc.replace(f"@@ANCHOR{i}@@", a)
    return esc

def linkify_raw_urls(s: str) -> str:
    # Convert raw URLs that remain in text into links.
    url_re = re.compile(r"(https?://[^\s)]+)")
    def repl(m):
        u = m.group(1)
        safe = html.escape(u, quote=True)
        return f'<a href="{safe}" target="_blank" rel="noreferrer">{safe}</a>'
    return url_re.sub(repl, s)

def md_to_html(md: str, resources: dict[str, dict[str, str]]) -> str:
    lines = md.splitlines()
    out: list[str] = []

    in_ul = False
    in_ol = False
    in_bq = False
    in_teacher = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>"); in_ul = False
        if in_ol:
            out.append("</ol>"); in_ol = False

    def close_bq():
        nonlocal in_bq
        if in_bq:
            out.append("</blockquote>"); in_bq = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")

        if line.strip() == ":::teacher":
            close_lists(); close_bq()
            if not in_teacher:
                out.append('<div class="teacher-only">'); in_teacher = True
            i += 1
            continue

        if line.strip() == ":::":
            close_lists(); close_bq()
            if in_teacher:
                out.append("</div>"); in_teacher = False
            i += 1
            continue

        mfence = re.match(r"^```video\s+([a-zA-Z0-9_\-]+)\s*$", line.strip())
        if mfence:
            close_lists(); close_bq()
            rid = mfence.group(1)
            prompts: dict[str, object] = {"task": "", "watch": [], "after": []}
            current: str | None = None
            i += 1
            while i < len(lines):
                raw = lines[i].rstrip("\n")
                if raw.strip().startswith("```"):
                    break
                line_in = raw.rstrip()
                mkey = re.match(r"^(task|watch|after)\s*:\s*(.*)$", line_in.strip())
                if mkey:
                    key = mkey.group(1)
                    rest = mkey.group(2).strip()
                    current = key
                    if key == "task":
                        prompts["task"] = rest
                    else:
                        if rest:
                            cast_list = prompts[key]
                            if isinstance(cast_list, list):
                                cast_list.append(rest)
                    i += 1
                    continue

                if current in ("watch", "after"):
                    mitem = re.match(r"^\s*-\s+(.*)$", line_in)
                    if mitem:
                        cast_list = prompts[current]
                        if isinstance(cast_list, list):
                            cast_list.append(mitem.group(1).strip())
                        i += 1
                        continue

                if current == "task" and line_in.strip():
                    task = (prompts.get("task") or "").strip()
                    joiner = " " if task else ""
                    prompts["task"] = f"{task}{joiner}{line_in.strip()}"

                i += 1

            combined = (
                "<div class='video-stack'>"
                + video_block(rid, resources)
                + local_prompts_block(prompts, resources)
                + "</div>"
            )
            out.append(combined)
            if i < len(lines) and lines[i].strip().startswith("```"):
                i += 1
            continue

        # Video blocks should stand alone on a line
        mvid = re.match(r"^\{\{video:([a-zA-Z0-9_\-]+)\}\}\s*$", line.strip())
        if mvid:
            close_lists(); close_bq()
            out.append(video_block(mvid.group(1), resources))
            i += 1
            continue

        if not line.strip():
            close_lists(); close_bq()
            i += 1
            continue

        # headings (#..####)
        mh = re.match(r"^(#{1,4})\s+(.*)$", line.strip())
        if mh:
            close_lists(); close_bq()
            level = len(mh.group(1))
            title = html.escape(mh.group(2).strip())
            cls = "" if level != 1 else " class=\"doc-title\""
            out.append(f"<h{level}{cls}>{title}</h{level}>")
            i += 1
            continue

        # blockquote
        if line.lstrip().startswith(">"):
            close_lists()
            if not in_bq:
                out.append("<blockquote>"); in_bq = True
            txt = inline_format(expand_inline_refs(line.lstrip()[1:].lstrip(), resources))
            out.append(f"<p>{txt}</p>")
            i += 1
            continue
        else:
            close_bq()

        # ordered list
        mol = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
        if mol:
            if in_ul:
                out.append("</ul>"); in_ul = False
            if not in_ol:
                out.append("<ol>"); in_ol = True
            txt = inline_format(expand_inline_refs(mol.group(2).strip(), resources))
            out.append(f"<li>{txt}</li>")
            i += 1
            continue

        # unordered list
        mul = re.match(r"^[-*]\s+(.*)$", line.strip())
        if mul:
            if in_ol:
                out.append("</ol>"); in_ol = False
            if not in_ul:
                out.append("<ul>"); in_ul = True
            txt = inline_format(expand_inline_refs(mul.group(1).strip(), resources))
            out.append(f"<li>{txt}</li>")
            i += 1
            continue

        close_lists()
        txt = inline_format(expand_inline_refs(line.strip(), resources))
        out.append(f"<p>{txt}</p>")
        i += 1

    close_lists(); close_bq()
    if in_teacher:
        out.append("</div>")

    return "\n".join(out)

def main() -> None:
    md = SOURCE.read_text(encoding="utf-8", errors="replace")
    resources = parse_bookmarks(md)
    content = md_to_html(md, resources)

    title = "Poetry declamation"
    m = re.search(r"^#\s+(.+)$", md, flags=re.MULTILINE)
    if m:
        title = m.group(1).strip()

    tpl = TEMPLATE.read_text(encoding="utf-8")
    out = tpl.replace("{{TITLE}}", html.escape(title)).replace("{{CONTENT}}", content)
    OUTPUT.write_text(out, encoding="utf-8")
    print(f"Wrote {OUTPUT.name}")

if __name__ == "__main__":
    main()
