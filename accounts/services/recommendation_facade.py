from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.cache import cache

from accounts.models import Book

from .cover_utils import PLACEHOLDER_COVER_URL, normalize_cover

logger = logging.getLogger(__name__)


class RecommendationUnavailableError(RuntimeError):
    """Raised when neither recommendation engine can produce usable results."""


def get_mood_recommender():
    from .mood_recommender import get_mood_recommender as _get

    return _get()


def get_dataset_recommender(dataset_path: str):
    from .dataset_recommender import get_dataset_recommender as _get

    return _get(dataset_path)


def _resolve_dataset_path() -> str:
    candidates = [
        Path(settings.BASE_DIR) / "books_dataset_5000.json",
        Path(settings.BASE_DIR) / "data" / "books_dataset_5000.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])


def _recommendation_mode() -> str:
    mode = str(getattr(settings, 'RECOMMENDER_MODE', 'hybrid') or 'hybrid').strip().lower()
    return mode if mode in {'hybrid', 'dataset', 'mood'} else 'hybrid'


def _recommendation_cache_timeout() -> int:
    try:
        return max(0, int(getattr(settings, 'RECOMMENDATION_CACHE_TTL', 900)))
    except (TypeError, ValueError):
        return 900


def _build_cache_key(user_mood: str, limit: int, improve_mood: bool) -> str:
    dataset_path = Path(_resolve_dataset_path())
    try:
        dataset_marker = f"{dataset_path.name}:{int(dataset_path.stat().st_mtime)}"
    except OSError:
        dataset_marker = f"{dataset_path.name}:missing"

    payload = json.dumps(
        {
            'mood': user_mood.strip().lower(),
            'limit': limit,
            'improve_mood': improve_mood,
            'mode': _recommendation_mode(),
            'dataset_marker': dataset_marker,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    return f"recommendations:{digest}"


def _engine_order() -> tuple[str, ...]:
    mode = _recommendation_mode()
    if mode == 'dataset':
        return ('dataset', 'mood')
    if mode == 'mood':
        return ('mood', 'dataset')
    return ('mood', 'dataset')


def _coerce_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(score, 1.0))


def _coerce_match_percent(score: float, raw_percent: Any = None) -> int:
    if raw_percent is not None:
        try:
            return max(0, min(int(raw_percent), 100))
        except (TypeError, ValueError):
            pass
    return max(0, min(int(round(score * 100)), 100))


def _normalize_genre(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(items[:3])
    return ""


def _normalize_mood_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = str(item.get("title") or "").strip()
    if not title:
        return None

    score = _coerce_score(item.get("sentiment_score"))
    return {
        "book_id": item.get("book_id"),
        "title": title,
        "author": str(item.get("author") or "Author unknown").strip() or "Author unknown",
        "genre": _normalize_genre(item.get("genre")),
        "cover_image": normalize_cover(item.get("cover_image") or PLACEHOLDER_COVER_URL),
        "isbn_10": str(item.get("isbn_10") or "").strip(),
        "isbn_13": str(item.get("isbn_13") or "").strip(),
        "dominant_mood": str(item.get("dominant_mood") or "").strip(),
        "recommendation_reason": str(
            item.get("recommendation_reason") or "This book is a strong mood-based match."
        ).strip(),
        "sentiment_score": score,
        "match_percent": _coerce_match_percent(score, item.get("match_percent")),
        "source": "mood",
        "description": str(item.get("description") or "").strip(),
        "_cover_resolved": bool(item.get("_cover_resolved")),
        "_cover_source": str(item.get("_cover_source") or "").strip(),
    }


def _normalize_dataset_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = str(item.get("title") or "").strip()
    if not title:
        return None

    match_score = _coerce_score(item.get("score"))
    return {
        "book_id": item.get("book_id"),
        "title": title,
        "author": str(item.get("author") or "Author unknown").strip() or "Author unknown",
        "genre": _normalize_genre(item.get("genres")),
        "cover_image": normalize_cover(item.get("cover_image") or PLACEHOLDER_COVER_URL),
        "isbn_10": str(item.get("isbn_10") or "").strip(),
        "isbn_13": str(item.get("isbn_13") or "").strip(),
        "dominant_mood": str(item.get("dominant_mood") or "").strip(),
        "recommendation_reason": str(
            item.get("explanation") or "This book is a strong dataset-based fallback match."
        ).strip(),
        "sentiment_score": match_score,
        "match_percent": _coerce_match_percent(match_score),
        "source": "dataset_fallback",
        "description": str(item.get("description") or "").strip(),
    }


def _normalize_items(
    items: list[dict[str, Any]] | None,
    normalizer,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        normalized_item = normalizer(item)
        if normalized_item:
            normalized.append(normalized_item)
    return normalized


def _recommendations_are_usable(items: list[dict[str, Any]]) -> bool:
    return bool(items) and all(item.get("title") and item.get("recommendation_reason") for item in items)


def _recommendation_book_lookup_key(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _is_valid_cover_url(value: str) -> bool:
    return isinstance(value, str) and normalize_cover(value) == value


def _is_google_cover(value: str) -> bool:
    lowered = str(value or "").lower()
    return "google" in lowered or "googleusercontent" in lowered


def _infer_cover_source(
    item: dict[str, Any],
    book: Book | None,
    cover: str,
    placeholder_cover: str,
) -> str:
    if cover == placeholder_cover:
        return "placeholder"

    explicit_source = str(item.get("_cover_source") or "").strip()
    if explicit_source and explicit_source != "unknown":
        return explicit_source

    if book:
        stored_cover = normalize_cover(book.cover_image)
        if stored_cover != placeholder_cover and cover == stored_cover:
            return "db_cover"

        for ident in (book.isbn_13, book.isbn_10):
            clean_ident = (ident or "").replace("-", "").strip()
            if not clean_ident:
                continue
            openlibrary = f"https://covers.openlibrary.org/b/isbn/{clean_ident}-L.jpg"
            if cover == openlibrary:
                return "openlibrary_isbn"

    return "google_books" if _is_google_cover(cover) else "external"


def finalize_recommendations_payload(recommendations_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not recommendations_list:
        return recommendations_list

    placeholder_cover = PLACEHOLDER_COVER_URL
    source_counts: dict[str, int] = {}
    lookup_ids = [
        key
        for key in (_recommendation_book_lookup_key(item.get("book_id")) for item in recommendations_list)
        if key is not None
    ]
    books_by_id = {book.id: book for book in Book.objects.filter(id__in=lookup_ids)}
    finalized: list[dict[str, Any]] = []

    for recommendation in recommendations_list:
        item = dict(recommendation)
        raw_cover = item.get("cover_image") or item.get("thumbnail") or ""
        cover = normalize_cover(raw_cover)
        lookup_key = _recommendation_book_lookup_key(item.get("book_id"))
        book = books_by_id.get(lookup_key)
        cover_source = _infer_cover_source(item, book, cover, placeholder_cover)

        logger.info(
            "recommendations.cover: book_id=%s title=%s raw=%s resolved=%s source=%s",
            item.get("book_id"),
            item.get("title"),
            raw_cover,
            cover,
            cover_source,
        )

        if settings.DEBUG and not _is_valid_cover_url(cover):
            logger.warning(
                "recommendations: invalid cover_image detected for "
                "book_id=%s title=%s value=%r - falling back to placeholder.",
                item.get("book_id"),
                item.get("title"),
                cover,
            )
            cover = placeholder_cover
            cover_source = "placeholder"

        item["cover_image"] = normalize_cover(cover)
        item["sentiment_score"] = _coerce_score(item.get("sentiment_score"))
        item["match_percent"] = _coerce_match_percent(
            item["sentiment_score"],
            item.get("match_percent"),
        )
        item.pop("_cover_source", None)
        item.pop("_cover_resolved", None)
        finalized.append(item)
        source_counts[cover_source] = source_counts.get(cover_source, 0) + 1

    total = len(finalized)
    if total:
        placeholder_count = source_counts.get("placeholder", 0)
        logger.info(
            "recommendations.cover_summary total=%s db_cover=%s openlibrary=%s google_books=%s "
            "placeholder=%s placeholder_pct=%.1f other=%s",
            total,
            source_counts.get("db_cover", 0),
            source_counts.get("openlibrary_isbn", 0),
            source_counts.get("google_books", 0),
            placeholder_count,
            (placeholder_count / total) * 100,
            source_counts.get("external", 0),
        )

    return finalized


def get_recommendations_for_mood(
    user_mood: str,
    limit: int,
    improve_mood: bool,
) -> list[dict[str, Any]]:
    mood_text = (user_mood or "").strip()
    if not mood_text:
        return []

    try:
        limit_value = max(1, min(int(limit), 20))
    except (TypeError, ValueError) as exc:
        raise RecommendationUnavailableError("Invalid recommendation limit.") from exc

    cache_timeout = _recommendation_cache_timeout()
    cache_key = _build_cache_key(mood_text, limit_value, improve_mood)
    if cache_timeout:
        cached = cache.get(cache_key)
        if isinstance(cached, list):
            return cached[:limit_value]

    mood_error: Exception | None = None
    dataset_error: Exception | None = None

    for engine in _engine_order():
        if engine == 'mood':
            try:
                mood_items = get_mood_recommender().recommend_books(
                    user_mood=mood_text,
                    limit=limit_value,
                    improve_mood=improve_mood,
                    min_confidence=0.3,
                )
                normalized_mood_items = finalize_recommendations_payload(
                    _normalize_items(mood_items, _normalize_mood_item)
                )
                if _recommendations_are_usable(normalized_mood_items):
                    if cache_timeout:
                        cache.set(cache_key, normalized_mood_items[:limit_value], cache_timeout)
                    return normalized_mood_items[:limit_value]
                logger.warning("Mood recommender returned no usable recommendations for mood=%s", mood_text)
            except Exception as exc:  # pragma: no cover - exercised via facade tests with monkeypatch
                mood_error = exc
                logger.warning("Mood recommender failed for mood=%s: %s", mood_text, exc)
        elif engine == 'dataset':
            try:
                dataset_path = _resolve_dataset_path()
                dataset_items = get_dataset_recommender(dataset_path).recommend(mood_text, top_n=limit_value)
                normalized_dataset_items = finalize_recommendations_payload(
                    _normalize_items(dataset_items, _normalize_dataset_item)
                )
                if _recommendations_are_usable(normalized_dataset_items):
                    if cache_timeout:
                        cache.set(cache_key, normalized_dataset_items[:limit_value], cache_timeout)
                    return normalized_dataset_items[:limit_value]
                logger.warning("Dataset recommender returned no usable recommendations for mood=%s", mood_text)
            except Exception as exc:  # pragma: no cover - exercised via facade tests with monkeypatch
                dataset_error = exc
                logger.warning("Dataset recommender failed for mood=%s: %s", mood_text, exc)

    if mood_error or dataset_error:
        raise RecommendationUnavailableError("Unable to generate recommendations at this time.") from (
            dataset_error or mood_error
        )

    raise RecommendationUnavailableError("No recommendations available for the supplied mood.")
