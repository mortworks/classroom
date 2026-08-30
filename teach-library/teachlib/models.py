from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class CaptionSpec:
    max_chars: int = 160
    font_size: int = 12
    one_line: bool = True


@dataclass
class Block:
    kind: str  # title, slide
    title: str = ""
    bullets: List[str] = field(default_factory=list)
    macros: List[Tuple[str, str]] = field(default_factory=list)  # (type, key)
    teacher_notes: str = ""
    layout: str = ""  # image|landscape|portrait|gallery|"" (infer)
    reveal: str = ""  # cumulative|""
