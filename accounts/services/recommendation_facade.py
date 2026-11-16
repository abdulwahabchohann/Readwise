from __future__ import annotations

import hashlib
import json
import logging
import random
import secrets
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .cover_utils import PLACEHOLDER_COVER_URL, normalize_cover, get_isbn_based_cover_url

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
        Path(settings.BASE_DIR) / "books_dataset_100k_real_covers.json",
        Path(settings.BASE_DIR) / "books_dataset_100k_with_covers.json",
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
    
    # Use database cover if available, otherwise placeholder
    # Note: OpenLibrary ISBN fallback skipped due to many 1px broken images
    cover_image = normalize_cover(item.get("cover_image") or PLACEHOLDER_COVER_URL)
    
    return {
        "book_id": item.get("book_id"),
        "title": title,
        "author": str(item.get("author") or "Author unknown").strip() or "Author unknown",
        "genre": _normalize_genre(item.get("genre")),
        "cover_image": cover_image,
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
    }


def _normalize_dataset_item(item: dict[str, Any]) -> dict[str, Any] | None:
    title = str(item.get("title") or "").strip()
    if not title:
        return None

    match_score = _coerce_score(item.get("score"))
    
    # Use database cover if available, otherwise placeholder
    # Note: OpenLibrary ISBN fallback skipped due to many 1px broken images
    cover_image = normalize_cover(item.get("cover_image") or PLACEHOLDER_COVER_URL)
    
    return {
        "book_id": item.get("book_id"),
        "title": title,
        "author": str(item.get("author") or "Author unknown").strip() or "Author unknown",
        "genre": _normalize_genre(item.get("genres")),
        "cover_image": cover_image,
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


def _open_library_subject_for_mood(mood_text: str) -> str:
    text = mood_text.lower()
    subject_keywords = (
        (("anxious", "anxiety", "calm", "stress", "worried"), "psychology"),
        (("sad", "lonely", "comfort", "grief"), "fiction"),
        (("romantic", "romance", "love"), "romance"),
        (("excited", "adventure", "fun"), "adventure"),
        (("motivated", "productive", "success", "career"), "self-help"),
        (("happy", "joy", "funny", "humor"), "humor"),
    )
    for keywords, subject in subject_keywords:
        if any(keyword in text for keyword in keywords):
            return subject
    return "fiction"


def _get_open_library_recommendations(
    mood_text: str,
    limit: int,
    exclude_titles: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return a keyless last-resort catalogue from Open Library."""
    from .external import fetch_open_library_books

    subject = _open_library_subject_for_mood(mood_text)
    # Use different subject pages so repeated requests don't always return
    # the same first few popular titles.
    page = secrets.randbelow(5) + 1
    books = fetch_open_library_books(subject, page)
    if len(books) > limit:
        books = random.SystemRandom().sample(books, limit)
    excluded = {title.casefold() for title in (exclude_titles or set())}
    recommendations: list[dict[str, Any]] = []
    for book in books[:limit]:
        title = str(book.title or "").strip()
        if not title or title.casefold() in excluded:
            continue
        authors = ", ".join(author for author in book.authors if author)
        categories = ", ".join(category for category in book.categories[:3] if category)
        recommendations.append(
            {
                "book_id": book.id,
                "title": title,
                "author": authors or "Author unknown",
                "genre": categories or subject.replace("-", " ").title(),
                "cover_image": normalize_cover(book.thumbnail or PLACEHOLDER_COVER_URL),
                "isbn_10": "",
                "isbn_13": "",
                "dominant_mood": "",
                "recommendation_reason": (
                    f"Open Library match for the {subject.replace('-', ' ')} theme "
                    f"based on your mood."
                ),
                "sentiment_score": 0.5,
                "match_percent": 50,
                "source": "open_library",
                "description": str(book.description or "").strip(),
            }
        )
    return recommendations


def get_recommendations_for_mood(
    user_mood: str,
    limit: int,
    improve_mood: bool,
    exclude_titles: set[str] | None = None,
) -> list[dict[str, Any]]:
    mood_text = (user_mood or "").strip()
    if not mood_text:
        return []

    try:
        limit_value = max(1, min(int(limit), 20))
    except (TypeError, ValueError) as exc:
        raise RecommendationUnavailableError("Invalid recommendation limit.") from exc

    cache_timeout = _recommendation_cache_timeout()
    excluded_titles = {title.casefold() for title in (exclude_titles or set())}
    cache_key = _build_cache_key(
        f"{mood_text}|exclude:{','.join(sorted(excluded_titles))}",
        limit_value,
        improve_mood,
    )
    if cache_timeout:
        cached = cache.get(cache_key)
        if isinstance(cached, list) and not any(
            isinstance(item, dict) and item.get("source") == "open_library"
            for item in cached
        ):
            filtered_cached = [
                item for item in cached
                if str(item.get("title") or "").casefold() not in excluded_titles
            ]
            if filtered_cached:
                return filtered_cached[:limit_value]

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
                normalized_mood_items = _normalize_items(mood_items, _normalize_mood_item)
                if excluded_titles:
                    filtered_mood_items = [
                        item for item in normalized_mood_items
                        if str(item.get("title") or "").casefold() not in excluded_titles
                    ]
                    if filtered_mood_items:
                        normalized_mood_items = filtered_mood_items
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
                normalized_dataset_items = _normalize_items(dataset_items, _normalize_dataset_item)
                if excluded_titles:
                    filtered_dataset_items = [
                        item for item in normalized_dataset_items
                        if str(item.get("title") or "").casefold() not in excluded_titles
                    ]
                    if filtered_dataset_items:
                        normalized_dataset_items = filtered_dataset_items
                if _recommendations_are_usable(normalized_dataset_items):
                    if cache_timeout:
                        cache.set(cache_key, normalized_dataset_items[:limit_value], cache_timeout)
                    return normalized_dataset_items[:limit_value]
                logger.warning("Dataset recommender returned no usable recommendations for mood=%s", mood_text)
            except Exception as exc:  # pragma: no cover - exercised via facade tests with monkeypatch
                dataset_error = exc
                logger.warning("Dataset recommender failed for mood=%s: %s", mood_text, exc)

    try:
        open_library_items = _get_open_library_recommendations(
            mood_text,
            limit_value,
            excluded_titles,
        )
        if _recommendations_are_usable(open_library_items):
            if cache_timeout:
                cache.set(cache_key, open_library_items[:limit_value], cache_timeout)
            return open_library_items[:limit_value]
        logger.warning("Open Library returned no usable recommendations for mood=%s", mood_text)
    except Exception as exc:
        logger.warning("Open Library recommender failed for mood=%s: %s", mood_text, exc)

    if mood_error or dataset_error:
        raise RecommendationUnavailableError("Unable to generate recommendations at this time.") from (
            dataset_error or mood_error
        )

    raise RecommendationUnavailableError("No recommendations available for the supplied mood.")
