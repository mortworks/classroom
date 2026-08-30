from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt

from teachlib.config import (
    CONTENT_BOTTOM,
    CONTENT_TOP,
    EMU_PER_INCH,
    MARGIN_X,
    SLIDES_OUT,
    TEMPLATE_PATH,
    TITLE_H,
    TITLE_Y,
)

from teachlib.config import SLIDE_W as _SLIDE_W_CFG, SLIDE_H as _SLIDE_H_CFG
SLIDE_W = _SLIDE_W_CFG
SLIDE_H = _SLIDE_H_CFG

from teachlib.formatting import caption_from_meta
from teachlib.models import Block
from teachlib.media import image_aspect_ratio, youtube_thumbnail_path
from teachlib.bookmarks import resolve_image_path, resolve_snippet_image, resolve_youtube

TOP_PAD = 0.25
CAP_FONT_GALLERY = 11
CAP_FONT_IMAGE = 16
CAP_FONT_LANDSCAPE = 14
CAP_FONT_STACKED = 10

def add_textbox(slide, x, y, w, h, text, *, font_size=32, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True            # <-- add this
    tf.margin_left = 0             # optional: slightly cleaner caption edges
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0

    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    return box

def add_bullets(slide, x, y, w, h, bullets: List[str], *, font_size=28):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.clear()

    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = b
        p.level = 0
        # Initial size; PowerPoint will shrink if needed
        for r in p.runs:
            r.font.size = Pt(font_size)
    return box

def add_picture_fit(slide, img_path: Path, box: Tuple[float, float, float, float]):
    """Fit image into (x,y,w,h) keeping aspect ratio, centred within box."""
    x, y, w, h = box
    ar = image_aspect_ratio(img_path)

    # If we can't read dimensions, just set width and hope
    if ar is None:
        return slide.shapes.add_picture(str(img_path), Inches(x), Inches(y), width=Inches(w))

    box_ar = w / h
    if ar >= box_ar:
        # Image is wider than box: fit width
        pic_w = w
        pic_h = w / ar
    else:
        # Image is taller: fit height
        pic_h = h
        pic_w = h * ar

    px = x + (w - pic_w) / 2
    py = y + (h - pic_h) / 2
    return slide.shapes.add_picture(str(img_path), Inches(px), Inches(py), width=Inches(pic_w), height=Inches(pic_h))

def add_youtube_thumbnail(slide, yt: Dict[str, str], box: Tuple[float, float, float, float]) -> bool:
    """
    Place a YouTube thumbnail in box and hyperlink it.
    Returns True if thumbnail placed.
    Returns False if network blocked / fetch failed.
    Never raises.
    """
    url = (yt.get("youtube_url") or "").strip()
    vid = (yt.get("video_id") or "").strip()

    if not url or not vid:
        return False

    try:
        thumb_path = youtube_thumbnail_path(vid)
        pic = add_picture_fit(slide, thumb_path, box)
        pic.click_action.hyperlink.address = url
        return True

    except Exception:
        # Network blocked, thumbnail fetch failed, etc.
        # Fail soft — render_slide will fall back to text.
        return False

def infer_layout(block: Block, bookmarks: Dict[str, Any]) -> str:
    """If block.layout empty, infer based on content."""
    if block.layout:
        return block.layout

    # If no bullets and exactly one media item, treat as image slide.
    media = [(t, k) for (t, k) in block.macros if t in ("img", "snippet")]
    if not block.bullets and len(media) == 1:
        return "image"

    # If there's media, infer portrait/landscape from first media aspect ratio
    if media:
        t, k = media[0]
        if t == "img":
            img_path, _ = resolve_image_path(bookmarks, k)
        else:
            img_path, _ = resolve_snippet_image(bookmarks, k)

        ar = image_aspect_ratio(img_path)
        if ar is None:
            # sensible default if Pillow missing
            return "landscape"
        return "landscape" if ar >= 1.1 else "portrait"

    # Default for pure text slides
    return "portrait"

def get_layout(prs: Presentation, kind: str):
    """
    Return a slide layout by intent rather than by index.
    kind: "blank" | "title"
    """
    # Normalise names
    want = kind.lower()

    # Try by common layout names first
    for layout in prs.slide_layouts:
        name = (layout.name or "").lower()
        if want == "blank" and ("blank" in name or "empty" in name):
            return layout
        if want == "title" and ("title slide" in name or name == "title"):
            return layout

    # Sensible fallbacks:
    # - for title: use the first layout
    # - for blank: use the last layout (often the emptiest)
    if want == "title":
        return prs.slide_layouts[0]
    return prs.slide_layouts[len(prs.slide_layouts) - 1]

def render_slide(prs: Presentation, block: Block, bookmarks: Dict[str, Any], bullets: List[str]) -> None:
    """Render a single slide for this block with the given bullet list."""
    layout = infer_layout(block, bookmarks)
    slide = prs.slides.add_slide(get_layout(prs, "blank"))

    # Title (optional)
    if block.title.strip():
        add_textbox(
            slide,
            MARGIN_X,
            TITLE_Y,
            SLIDE_W - 2 * MARGIN_X,
            TITLE_H,
            block.title.strip(),
            font_size=44,
            bold=True,
        )

    # Teacher notes -> speaker notes
    if block.teacher_notes.strip():
        slide.notes_slide.notes_text_frame.text = block.teacher_notes.strip()

    # Collect macros
    media_items: List[Tuple[str, str]] = [(t, k) for (t, k) in block.macros if t in ("img", "snippet")]
    yt_items: List[Tuple[str, str]] = [(t, k) for (t, k) in block.macros if t == "yt"]

    # Convenience: first YouTube entry if present
    yt = resolve_youtube(bookmarks, yt_items[0][1]) if yt_items else None

    # Guard-rail: if there are 2 media items and layout isn't explicitly chosen,
    # force gallery (if no bullets) otherwise portrait stacking.
    if not block.layout and len(media_items) >= 2 and layout in ("landscape", "image", "portrait"):
        layout = "gallery" if not bullets else "portrait"

    # --- Helper: render a media item into a box + caption strip ---
    def place_media_item(
        t: str,
        k: str,
        img_box: Tuple[float, float, float, float],
        cap_box: Tuple[float, float, float, float],
        cap_font: int,
    ) -> None:
        if t == "img":
            img_path, meta = resolve_image_path(bookmarks, k)
            add_picture_fit(slide, img_path, img_box)
            cap = caption_from_meta(meta)
            if cap:
                add_textbox(slide, cap_box[0], cap_box[1], cap_box[2], cap_box[3], cap, font_size=cap_font)
        else:
            img_path, meta = resolve_snippet_image(bookmarks, k)
            add_picture_fit(slide, img_path, img_box)
            title = (meta.get("title") or "").strip()
            if title:
                add_textbox(slide, cap_box[0], cap_box[1], cap_box[2], cap_box[3], title, font_size=cap_font)

    # --- Helper: add small YT thumbnail + label in a known safe strip ---
    def place_youtube_strip(
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        label_h: float = 0.35,
        font_size: int = 12,
    ) -> None:
        """
        Places a clickable thumbnail (left) and a label (right) within the given strip box.
        Never overlaps other elements if you allocate the strip space.
        """
        if not yt:
            return

        thumb_h = h
        thumb_w = min(3.0, w * 0.35)  # cap thumbnail width
        thumb_box = (x, y, thumb_w, thumb_h)

        placed = False
        try:
            placed = add_youtube_thumbnail(slide, yt, thumb_box)
        except Exception:
            placed = False

        label = yt.get("title") or yt_items[0][1]
        if (not placed) and yt.get("youtube_url"):
            label += f" — {yt['youtube_url']}"

        # Text area to the right of thumb
        tx = x + thumb_w + 0.25
        tw = max(0.5, w - (thumb_w + 0.25))
        add_textbox(slide, tx, y, tw, h, label, font_size=font_size)

    # --- Special case: YouTube-only slide (big clickable thumbnail) ---
    if yt and not media_items:
        top = CONTENT_TOP + TOP_PAD
        cap_h = 0.6
        cap_gap = 0.15

        img_box = (MARGIN_X, top, SLIDE_W - 2 * MARGIN_X, SLIDE_H - top - CONTENT_BOTTOM - cap_h - cap_gap)
        cap_box = (MARGIN_X, top + (SLIDE_H - top - CONTENT_BOTTOM - cap_h), SLIDE_W - 2 * MARGIN_X, cap_h)

        placed = False
        try:
            placed = add_youtube_thumbnail(slide, yt, img_box)
        except Exception:
            placed = False

        label = yt.get("title") or yt_items[0][1]
        if (not placed) and yt.get("youtube_url"):
            label += f" — {yt['youtube_url']}"
        add_textbox(slide, cap_box[0], cap_box[1], cap_box[2], cap_box[3], label, font_size=16)

        # Keep bullets out of the way (notes)
        if bullets:
            existing = slide.notes_slide.notes_text_frame.text or ""
            extra = "\n".join(f"- {b}" for b in bullets)
            slide.notes_slide.notes_text_frame.text = (existing + "\n\n" + extra).strip()

        return

    # ------------------ LAYOUTS ------------------

    if layout == "gallery":
        # Two media items side-by-side, big, with captions underneath.
        top = CONTENT_TOP + TOP_PAD

        gap_x = 0.35
        cap_h = 0.6
        cap_gap = 0.18

        total_w = SLIDE_W - 2 * MARGIN_X
        col_w = (total_w - gap_x) / 2
        img_h = SLIDE_H - top - CONTENT_BOTTOM - cap_h - cap_gap

        left_img_box = (MARGIN_X, top, col_w, img_h)
        right_img_box = (MARGIN_X + col_w + gap_x, top, col_w, img_h)

        left_cap_box = (MARGIN_X, top + img_h + cap_gap, col_w, cap_h)
        right_cap_box = (MARGIN_X + col_w + gap_x, top + img_h + cap_gap, col_w, cap_h)

        items = media_items[:2]
        if len(items) >= 1:
            t, k = items[0]
            place_media_item(t, k, left_img_box, left_cap_box, cap_font=CAP_FONT_GALLERY)
        if len(items) >= 2:
            t, k = items[1]
            place_media_item(t, k, right_img_box, right_cap_box, cap_font=CAP_FONT_GALLERY)

        # If there *are* bullets, shove them into speaker notes to avoid clutter.
        if bullets:
            existing = slide.notes_slide.notes_text_frame.text or ""
            extra = "\n".join(f"- {b}" for b in bullets)
            slide.notes_slide.notes_text_frame.text = (existing + "\n\n" + extra).strip()

        # If there is a YouTube item, add a small strip above the bottom margin
        if yt:
            strip_h = 0.45
            strip_y = SLIDE_H - CONTENT_BOTTOM - strip_h
            place_youtube_strip(MARGIN_X, strip_y, SLIDE_W - 2 * MARGIN_X, strip_h, font_size=12)

        return

    if layout == "image":
        # Big image, full width, caption at bottom.
        top = CONTENT_TOP + TOP_PAD
        cap_h = 0.5

        # Reserve an extra strip for YouTube if present
        yt_strip_h = 0.45 if yt else 0.0
        yt_gap = 0.10 if yt else 0.0

        img_box = (
            MARGIN_X,
            top,
            SLIDE_W - 2 * MARGIN_X,
            SLIDE_H - top - CONTENT_BOTTOM - cap_h - yt_strip_h - yt_gap,
        )
        cap_box = (
            MARGIN_X,
            SLIDE_H - CONTENT_BOTTOM - cap_h - yt_strip_h - yt_gap,
            SLIDE_W - 2 * MARGIN_X,
            cap_h,
        )

        if media_items:
            t, k = media_items[0]
            place_media_item(t, k, img_box, cap_box, cap_font=CAP_FONT_IMAGE)

        if yt:
            strip_y = SLIDE_H - CONTENT_BOTTOM - yt_strip_h
            place_youtube_strip(MARGIN_X, strip_y, SLIDE_W - 2 * MARGIN_X, yt_strip_h, font_size=12)

        return

    if layout == "landscape":
        # Title at top. Image below, bullets below image.
        top = CONTENT_TOP + TOP_PAD
        img_h = 3.6
        cap_h = 0.35

        # Reserve a bottom strip for YouTube if present
        yt_strip_h = 0.45 if yt else 0.0
        yt_gap = 0.10 if yt else 0.0

        img_box = (MARGIN_X, top, SLIDE_W - 2 * MARGIN_X, img_h - cap_h)
        cap_box = (MARGIN_X, top + (img_h - cap_h), SLIDE_W - 2 * MARGIN_X, cap_h)

        text_top = top + img_h + 0.25
        text_box = (
            MARGIN_X,
            text_top,
            SLIDE_W - 2 * MARGIN_X,
            SLIDE_H - text_top - CONTENT_BOTTOM - yt_strip_h - yt_gap,
        )

        if media_items:
            t, k = media_items[0]
            place_media_item(t, k, img_box, cap_box, cap_font=CAP_FONT_LANDSCAPE)

        if bullets:
            add_bullets(slide, *text_box, bullets, font_size=28)

        if yt:
            strip_y = SLIDE_H - CONTENT_BOTTOM - yt_strip_h
            place_youtube_strip(MARGIN_X, strip_y, SLIDE_W - 2 * MARGIN_X, yt_strip_h, font_size=12)

        return

    # portrait (default)
    top = CONTENT_TOP + TOP_PAD
    left_w = 7.3
    gap = 0.4
    right_x = MARGIN_X + left_w + gap
    right_w = SLIDE_W - right_x - MARGIN_X

    # Reserve a strip at the bottom-left for YouTube thumbnail + label
    yt_strip_h = 0.9 if yt else 0.0

    text_box = (MARGIN_X, top, left_w, SLIDE_H - top - CONTENT_BOTTOM - yt_strip_h)

    if bullets:
        add_bullets(slide, *text_box, bullets, font_size=28)

    if media_items:
        items = media_items[:2]
        available_h = SLIDE_H - top - CONTENT_BOTTOM
        slot_h = available_h / len(items)

        cap_h = 0.85
        gap_y = 0.12

        for i, (t, k) in enumerate(items):
            slot_y = top + i * slot_h
            img_box = (right_x, slot_y, right_w, slot_h - cap_h - gap_y)
            cap_box = (right_x, slot_y + (slot_h - cap_h), right_w, cap_h)
            place_media_item(t, k, img_box, cap_box, cap_font=CAP_FONT_STACKED)

    if yt:
        strip_y = SLIDE_H - CONTENT_BOTTOM - yt_strip_h
        place_youtube_strip(MARGIN_X, strip_y, left_w, yt_strip_h, font_size=12)

def build_ppt(blocks: List[Block], bookmarks: Dict[str, Any]) -> None:
    # Use your template so slide size + fonts are consistent
    prs = Presentation(str(TEMPLATE_PATH))


    # IMPORTANT: sync global slide width/height with the real presentation
    global SLIDE_W, SLIDE_H
    SLIDE_W = prs.slide_width / EMU_PER_INCH
    SLIDE_H = prs.slide_height / EMU_PER_INCH

    # Title slide
    for b in blocks:
        if b.kind == "title":
            slide = prs.slides.add_slide(get_layout(prs, "blank"))  # or prs.slide_layouts[0] if that's your blank
            add_textbox(
                slide,
                MARGIN_X,
                2.4,  # tweak vertical position
                SLIDE_W - 2 * MARGIN_X,
                1.2,
                b.title,
                font_size=54,
                bold=True,
            )
            break

    # Content slides
    for b in blocks:
        if b.kind != "slide":
            continue

        if b.reveal == "cumulative" and b.bullets:
            for i in range(1, len(b.bullets) + 1):
                render_slide(prs, b, bookmarks, b.bullets[:i])
        else:
            render_slide(prs, b, bookmarks, b.bullets)

    prs.save(SLIDES_OUT)
    return SLIDES_OUT

