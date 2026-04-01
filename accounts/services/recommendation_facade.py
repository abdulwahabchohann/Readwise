from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from django.conf import settings

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
    return {
        "book_id": item.get("book_id"),
        "title": title,
        "author": str(item.get("author") or "Author unknown").strip() or "Author unknown",
        "genre": _normalize_genre(item.get("genres")),
        "cover_image": normalize_cover(item.get("cover_image") or PLACEHOLDER_COVER_URL),
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

    mood_error: Exception | None = None
    try:
        mood_items = get_mood_recommender().recommend_books(
            user_mood=mood_text,
            limit=limit_value,
            improve_mood=improve_mood,
            min_confidence=0.3,
        )
        normalized_mood_items = _normalize_items(mood_items, _normalize_mood_item)
        if _recommendations_are_usable(normalized_mood_items):
            return normalized_mood_items[:limit_value]
        logger.warning("Mood recommender returned no usable recommendations for mood=%s", mood_text)
    except Exception as exc:  # pragma: no cover - exercised via facade tests with monkeypatch
        mood_error = exc
        logger.warning("Mood recommender failed for mood=%s: %s", mood_text, exc)

    dataset_error: Exception | None = None
    try:
        dataset_path = _resolve_dataset_path()
        dataset_items = get_dataset_recommender(dataset_path).recommend(mood_text, top_n=limit_value)
        normalized_dataset_items = _normalize_items(dataset_items, _normalize_dataset_item)
        if _recommendations_are_usable(normalized_dataset_items):
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
