from __future__ import annotations
from pathlib import Path

_PAGE_BREAK = '\f'


def extract_text_pages(path: Path) -> tuple[list[str], dict]:
    text = path.read_text(encoding='utf-8', errors='replace')
    if _PAGE_BREAK in text:
        pages = [p.strip() for p in text.split(_PAGE_BREAK) if p.strip()]
    else:
        pages = [text]
    return pages, {'format': path.suffix.lower(), 'page_count': len(pages)}
