from .store import DocumentStore
from .outline import build_text_tree
from .quote_verify import normalize_for_quote_match, verify_quote, locate_quote

__all__ = [
    'DocumentStore', 'build_text_tree',
    'normalize_for_quote_match', 'verify_quote', 'locate_quote',
]
