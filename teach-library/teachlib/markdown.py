from __future__ import annotations

from typing import List, Optional

from teachlib.config import LAYOUT_RE, MACRO_RE, REVEAL_RE
from teachlib.models import Block


def parse_markdown(md_text: str) -> List[Block]:
    blocks: List[Block] = []
    current: Optional[Block] = None
    in_teacher = False
    teacher_lines: List[str] = []

    for raw in md_text.splitlines():
        line = raw.rstrip()

        # Teacher notes block
        if line.strip().startswith(":::teacher"):
            in_teacher = True
            teacher_lines = []
            continue

        if in_teacher:
            if line.strip() == ":::":  # end teacher block
                in_teacher = False
                if current:
                    current.teacher_notes = "\n".join(teacher_lines).strip()
                continue
            teacher_lines.append(line)
            continue

        s = line.strip()
        if not s:
            continue

        if s.startswith("# "):
            blocks.append(Block(kind="title", title=s[2:].strip()))
            current = None
            continue

        if s.startswith("## "):
            current = Block(kind="slide", title=s[3:].strip())
            blocks.append(current)
            continue

        if current:
            m_layout = LAYOUT_RE.match(s)
            if m_layout:
                current.layout = m_layout.group(1).lower()
                continue

            m_reveal = REVEAL_RE.match(s)
            if m_reveal:
                current.reveal = m_reveal.group(1).lower()
                continue

            m = MACRO_RE.match(s)
            if m:
                macro_type, key = m.group(1), m.group(2)
                current.macros.append((macro_type.lower(), key))
                continue

            if s.startswith("- "):
                current.bullets.append(s[2:].strip())
                continue

            # Any other line: treat as bullet-ish paragraph (keeps it forgiving)
            current.bullets.append(s)

    return blocks
