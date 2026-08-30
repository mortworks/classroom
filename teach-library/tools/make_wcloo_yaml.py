#!/usr/bin/env python3
from pathlib import Path
import re

# adjust if your folder differs
IMG_DIR = Path("assets/images/wcloo")

# base metadata (shared across all pages)
BASE = {
    "artist": "William Charles Loo",
    "year": "c. 1930s",
    "source_institution": "St Luke’s College, Exeter",
    "source_page": "",
    "rights": "Unpublished manuscript (family archive). Copyright status unknown.",
}

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")

def main() -> None:
    files = sorted(
        IMG_DIR.glob("wcloo-notebook-*.png"),
        key=lambda p: int(p.stem.split("-")[-1])
    )

    print("images:")
    for f in files:
        n = int(f.stem.split("-")[-1])
        key = f"wcloo-notebook-{n:02d}"
        title = "Teaching college notes (scan)"
        page = f"Page {n}"

        print(f"  {key}:")
        print(f"    title: \"{title}\"")
        print(f"    artist: \"{BASE['artist']}\"")
        print(f"    year: \"{BASE['year']}\"")
        print(f"    source_institution: \"{BASE['source_institution']}\"")
        print(f"    source_page: \"{BASE['source_page']}\"")
        print(f"    image_file: \"{f.as_posix()}\"")
        print(f"    alt: \"Scan from William Charles Loo’s notebook ({page}).\"")
        print(f"    rights: \"{BASE['rights']}\"")

if __name__ == "__main__":
    main()
