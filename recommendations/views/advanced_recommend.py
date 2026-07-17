from __future__ import annotations

import logging
import time
from copy import deepcopy
from typing import Any

from django.core.cache import cache
from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.services.book_matcher import (
    build_keyword_fallback_suggestions,
    merge_with_library,
    prompt_fingerprint,
)
from recommendations.services.llm_service import LLMRecommendationError, get_llm_book_suggestions

logger = logging.getLogger(__name__)

ADVANCED_RECOMMENDATION_CACHE_TTL = 60 * 60
ADVANCED_RECOMMENDATION_LIMIT = 5
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60 * 60


def advanced_recommend_page(request):
    return render(request, 'recommendations/advanced_search.html')


def _client_key(request) -> str:
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        return f'user:{user.pk}'
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    ip_address = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    return f'anon:{ip_address or "unknown"}'


def _increment_rate_limit(request) -> tuple[bool, int]:
    window = int(time.time() // RATE_LIMIT_WINDOW_SECONDS)
    key = f'advanced_recommend:rate:{_client_key(request)}:{window}'
    current = cache.get(key)
    if current is None:
        cache.set(key, 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
        return False, RATE_LIMIT_REQUESTS - 1
    try:
        current_count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
        current_count = 1
    limited = current_count > RATE_LIMIT_REQUESTS
    return limited, max(0, RATE_LIMIT_REQUESTS - current_count)


def _cache_key(user_prompt: str) -> str:
    return f'advanced_recommend:prompt:{prompt_fingerprint(user_prompt)}'


def _build_response(user_prompt: str, suggestions: list[dict[str, Any]], *, fallback_used: bool) -> dict[str, Any]:
    recommendations = merge_with_library(suggestions, limit=ADVANCED_RECOMMENDATION_LIMIT)
    return {
        'schema': 'advanced_recommendation_v1',
        'prompt': user_prompt,
        'count': len(recommendations),
        'fallback_used': fallback_used,
        'recommendations': recommendations,
    }


class AdvancedRecommendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_prompt = (request.data.get('user_prompt') or request.POST.get('user_prompt') or '').strip()
        if not user_prompt:
            return Response({'error': 'user_prompt is required.'}, status=400)

        limited, remaining = _increment_rate_limit(request)
        if limited:
            return Response(
                {
                    'error': 'Rate limit exceeded. Please try again later.',
                    'rate_limit': {
                        'limit': RATE_LIMIT_REQUESTS,
                        'remaining': 0,
                        'window_seconds': RATE_LIMIT_WINDOW_SECONDS,
                    },
                },
                status=429,
            )

        key = _cache_key(user_prompt)
        cached = cache.get(key)
        if isinstance(cached, dict):
            payload = deepcopy(cached)
            payload['cached'] = True
            payload['rate_limit'] = {
                'limit': RATE_LIMIT_REQUESTS,
                'remaining': remaining,
                'window_seconds': RATE_LIMIT_WINDOW_SECONDS,
            }
            return Response(payload)

        fallback_used = False
        try:
            suggestions = get_llm_book_suggestions(user_prompt)
            if len(suggestions) < ADVANCED_RECOMMENDATION_LIMIT:
                fallback = build_keyword_fallback_suggestions(user_prompt, limit=ADVANCED_RECOMMENDATION_LIMIT)
                suggestions = suggestions + fallback
                fallback_used = True
        except LLMRecommendationError as exc:
            logger.info('Using advanced recommendation fallback for prompt=%r: %s', user_prompt[:120], exc)
            suggestions = build_keyword_fallback_suggestions(user_prompt, limit=ADVANCED_RECOMMENDATION_LIMIT)
            fallback_used = True

        payload = _build_response(user_prompt, suggestions, fallback_used=fallback_used)
        payload['cached'] = False
        payload['rate_limit'] = {
            'limit': RATE_LIMIT_REQUESTS,
            'remaining': remaining,
            'window_seconds': RATE_LIMIT_WINDOW_SECONDS,
        }

        cache_payload = deepcopy(payload)
        cache_payload.pop('cached', None)
        cache_payload.pop('rate_limit', None)
        cache.set(key, cache_payload, timeout=ADVANCED_RECOMMENDATION_CACHE_TTL)
        return Response(payload)
