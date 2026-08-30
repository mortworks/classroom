from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Inches, Pt
from teachlib.library_render import build_library_html

from teachlib.config import (
    BOOKMARKS_PATH,
    BUILD_DIR,
    CACHE_DIR,
    CONTENT_BOTTOM,
    CONTENT_TOP,
    EMU_PER_INCH,
    LESSON_PATH,
    MARGIN_X,
    SLIDES_OUT,
    SLIDE_H,
    SLIDE_W,
    TEMPLATE_PATH,
    TITLE_H,
    TITLE_Y,
)
from teachlib.models import Block
from teachlib.bookmarks import load_bookmarks, resolve_image_path, resolve_snippet_image, resolve_youtube
from teachlib.media import image_aspect_ratio
from teachlib.markdown import parse_markdown
from teachlib.html_render import build_html
from teachlib.ppt_render import build_ppt

def ensure_dirs() -> None:
    (BUILD_DIR / "slides").mkdir(parents=True, exist_ok=True)
    (BUILD_DIR / "html").mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def main() -> None:
    ensure_dirs()
    bookmarks = load_bookmarks(BOOKMARKS_PATH)
    md_text = LESSON_PATH.read_text(encoding="utf-8")
    blocks = parse_markdown(md_text)

    build_ppt(blocks, bookmarks)
    build_html(blocks, bookmarks)

    ppt_path = build_ppt(blocks, bookmarks)
    html_path = build_html(blocks, bookmarks)
    lib_path = build_library_html(bookmarks)

    print(f"Built: {ppt_path}")
    print(f"Built: {html_path}")
    print(f"Built: {lib_path}")

if __name__ == "__main__":
    main()
