from __future__ import annotations
from pathlib import Path


def extract_pdf_pages(path: Path) -> tuple[list[str], dict]:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError('pypdf is required for PDF extraction: pip install pypdf')

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ''
        pages.append(text.strip())
    meta = {
        'format': 'pdf',
        'page_count': len(pages),
        'pdf_page_count': len(reader.pages),
    }
    if reader.metadata:
        meta['title'] = reader.metadata.get('/Title', '')
    return pages, meta
