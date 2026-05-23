"""
Utilities for ensuring book cover URLs are present.
"""
from __future__ import annotations

from typing import Dict, List


PLACEHOLDER_COVER_PATH = "/static/images/placeholder.svg"

try:
    from django.templatetags.static import static
    PLACEHOLDER_COVER_URL = static("images/placeholder.svg") or PLACEHOLDER_COVER_PATH
except Exception:
    PLACEHOLDER_COVER_URL = PLACEHOLDER_COVER_PATH


def _clean_candidate(url) -> str:
    if not isinstance(url, str):
        return ""
    candidate = url.strip()
    if not candidate or candidate.lower() in {"null", "none"}:
        return ""
    if candidate.startswith("http://"):
        candidate = "https://" + candidate[len("http://"):]
    return candidate


def is_placeholder_cover(url) -> bool:
    candidate = _clean_candidate(url)
    if not candidate:
        return True
    lowered = candidate.lower()
    placeholder_path = PLACEHOLDER_COVER_PATH.lower()
    placeholder_url = PLACEHOLDER_COVER_URL.lower()
    return (
        lowered == placeholder_path
        or lowered == placeholder_url
        or lowered.endswith("/images/placeholder.svg")
        or lowered.endswith("placeholder.svg")
    )


def is_usable_cover_url(url, *, allow_placeholder: bool = False) -> bool:
    candidate = _clean_candidate(url)
    if not candidate:
        return False

    lowered = candidate.lower()
    if "example.com/covers/" in lowered or "example.com/placeholder" in lowered:
        return False
    if is_placeholder_cover(candidate):
        return allow_placeholder
    return candidate.startswith(("https://", "/static/"))


def normalize_cover(url) -> str:
    """
    Normalize a cover URL, returning a placeholder if the value is invalid.
    """
    candidate = _clean_candidate(url)
    if not is_usable_cover_url(candidate):
        return PLACEHOLDER_COVER_URL
    return candidate


def get_isbn_based_cover_url(isbn_13: str = '', isbn_10: str = '') -> str:
    """
    Generate an OpenLibrary cover URL from ISBN.
    
    NOTE: OpenLibrary returns 1×1 px "not found" images for ISBNs it doesn't have.
    Use carefully and validate the actual cover before displaying.
    Returns the cover URL string, or empty string if no valid ISBN provided.
    """
    for isbn in [isbn_13, isbn_10]:
        if not isbn:
            continue
        clean_isbn = isbn.replace('-', '').strip()
        if len(clean_isbn) in (10, 13) and clean_isbn.isdigit():
            return f'https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg'
    return ''


def fill_missing_covers(books_list: List[Dict]) -> List[Dict]:
    """
    Ensure each book has a non-empty cover_url field.

    Existing cover_url values are preserved. Missing or blank values are
    filled with PLACEHOLDER_COVER_URL. The original order is preserved.
    """
    if not books_list:
        return books_list

    for book in books_list:
        if not isinstance(book, dict):
            continue
        book["cover_url"] = normalize_cover(book.get("cover_url"))
        if "cover_image" in book:
            book["cover_image"] = normalize_cover(book.get("cover_image"))

    return books_list
