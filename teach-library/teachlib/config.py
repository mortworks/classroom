from __future__ import annotations

import re
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(".")
BOOKMARKS_PATH = PROJECT_ROOT / "bookmarks.yml"
LESSON_PATH = PROJECT_ROOT / "lessons" / "teachmeet.md"
TEMPLATE_PATH = PROJECT_ROOT / "template.pptx"

BUILD_DIR = PROJECT_ROOT / "build"
LIBRARY_OUT = BUILD_DIR / "html" / "library.html"
SLIDES_OUT = BUILD_DIR / "slides" / "teachmeet.pptx"
HTML_OUT = BUILD_DIR / "html" / "teachmeet.html"
CACHE_DIR = BUILD_DIR / "cache"
LIBRARY_OUT = BUILD_DIR / "html" / "library.html"

# Markdown directives / macros
MACRO_RE = re.compile(r"^\{\{(\w+):([a-zA-Z0-9_-]+)\}\}$")
LAYOUT_RE = re.compile(r"^!layout:\s*(image|landscape|portrait|gallery)\s*$", re.I)
REVEAL_RE = re.compile(r"^!reveal:\s*(cumulative)\s*$", re.I)

# Slide geometry (default widescreen: 13.333" x 7.5")
EMU_PER_INCH = 914400
SLIDE_W = 13.333
SLIDE_H = 7.5

MARGIN_X = 0.7
TITLE_Y = 0.35
TITLE_H = 0.8

CONTENT_TOP = 1.3
CONTENT_BOTTOM = 0.6
