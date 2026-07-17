from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are an expert literary advisor and empathetic reading coach. Your role is
to deeply understand what a user needs - intellectually, emotionally, and
situationally - and recommend exactly 5 books that will genuinely help or
resonate with them.

When analyzing the user's input:
- Detect emotional state (sad, anxious, curious, motivated, lost, angry, etc.)
- Detect topic interest (finance, science, fiction, self-help, religion, tech, etc.)
- Detect life situation (career stress, relationship conflict, seeking growth, etc.)
- Infer reading level and preferred complexity (beginner, intermediate, advanced)
- Infer whether they want comfort, challenge, escape, or learning

For each of the 5 books, return a JSON object with:
{
  "rank": 1-5,
  "title": "Book Title",
  "author": "Author Name",
  "reason": "A 2-3 sentence explanation of WHY this book matches the user's exact prompt, mood, and need. Be specific and personal.",
  "mood_tag": "e.g. comforting / mind-expanding / motivating / educational",
  "match_score": 0-100,
  "genre": "e.g. Self-help / Finance / Fiction / Science",
  "difficulty": "Beginner / Intermediate / Advanced"
}

Return ONLY a valid JSON array of 5 book objects. No preamble, no explanation,
no markdown. Pure JSON only.
"""


class LLMRecommendationError(RuntimeError):
    """Raised when the LLM cannot provide a usable recommendation payload."""


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _extract_json_array(content: str) -> list[Any]:
    text = (content or '').strip()
    if not text:
        raise LLMRecommendationError('The LLM returned an empty response.')

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find('[')
        end = text.rfind(']')
        if start < 0 or end <= start:
            raise LLMRecommendationError('The LLM response did not contain a JSON array.')
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMRecommendationError('The LLM response was not valid JSON.') from exc

    if isinstance(parsed, dict):
        parsed = parsed.get('recommendations') or parsed.get('books') or parsed.get('results')

    if not isinstance(parsed, list):
        raise LLMRecommendationError('The LLM response was not a JSON list.')
    return parsed


def _sanitize_item(raw_item: Any, rank: int) -> dict[str, Any] | None:
    if not isinstance(raw_item, dict):
        return None

    title = str(raw_item.get('title') or '').strip()
    author = str(raw_item.get('author') or '').strip()
    if not title:
        return None

    score = _coerce_int(raw_item.get('match_score'), default=max(70, 96 - rank * 3))
    score = max(0, min(score, 100))
    difficulty = str(raw_item.get('difficulty') or 'Intermediate').strip() or 'Intermediate'

    return {
        'rank': rank,
        'title': title,
        'author': author or 'Author unknown',
        'reason': str(raw_item.get('reason') or '').strip()
        or 'This book is a strong fit for the request you described.',
        'mood_tag': str(raw_item.get('mood_tag') or 'thoughtful').strip().lower() or 'thoughtful',
        'match_score': score,
        'genre': str(raw_item.get('genre') or 'General').strip() or 'General',
        'difficulty': difficulty.title(),
        'source': 'llm',
    }


def parse_recommendations_payload(content: str) -> list[dict[str, Any]]:
    raw_items = _extract_json_array(content)
    normalized: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for raw_item in raw_items:
        item = _sanitize_item(raw_item, rank=len(normalized) + 1)
        if not item:
            continue
        identity = item['title'].casefold()
        if identity in seen_titles:
            continue
        seen_titles.add(identity)
        normalized.append(item)
        if len(normalized) >= 5:
            break

    if not normalized:
        raise LLMRecommendationError('The LLM returned no usable book recommendations.')
    return normalized


def get_llm_book_suggestions(user_prompt: str) -> list[dict[str, Any]]:
    prompt = (user_prompt or '').strip()
    if not prompt:
        raise LLMRecommendationError('A user prompt is required.')

    api_key = (getattr(settings, 'OPENAI_API_KEY', '') or '').strip()
    if not api_key:
        raise LLMRecommendationError('OPENAI_API_KEY is not configured.')

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMRecommendationError('The openai package is not installed.') from exc

    model = (getattr(settings, 'OPENAI_RECOMMENDATION_MODEL', '') or 'gpt-4o').strip()
    timeout = getattr(settings, 'OPENAI_RECOMMENDATION_TIMEOUT', 30)
    try:
        timeout_value = max(5, int(timeout))
    except (TypeError, ValueError):
        timeout_value = 30

    client = OpenAI(api_key=api_key, timeout=timeout_value)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ],
            temperature=0.72,
            max_tokens=1800,
        )
    except Exception as exc:  # pragma: no cover - depends on external API availability
        logger.warning('Advanced recommendation LLM call failed: %s', exc)
        raise LLMRecommendationError('The LLM API is unavailable.') from exc

    try:
        content = response.choices[0].message.content or ''
    except (AttributeError, IndexError) as exc:
        raise LLMRecommendationError('The LLM response was missing message content.') from exc

    return parse_recommendations_payload(content)
