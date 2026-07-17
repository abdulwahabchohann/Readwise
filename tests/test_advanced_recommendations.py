import json

import pytest
from django.core.cache import cache
from django.urls import reverse

from accounts.models import Author, Book


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_advanced_recommendation_cache():
    cache.clear()
    yield
    cache.clear()


def _post_prompt(client, prompt):
    return client.post(
        reverse('advanced_recommend'),
        data=json.dumps({'user_prompt': prompt}),
        content_type='application/json',
    )


def test_advanced_recommend_uses_keyword_fallback_without_openai_key(client, settings):
    settings.OPENAI_API_KEY = ''

    response = _post_prompt(client, 'I am sad and feeling lonely')

    assert response.status_code == 200
    payload = response.json()
    assert payload['fallback_used'] is True
    assert payload['count'] == 5
    assert len(payload['recommendations']) == 5
    assert {'title', 'author', 'reason', 'mood_tag', 'match_score', 'genre', 'difficulty', 'in_library'} <= payload['recommendations'][0].keys()


def test_advanced_recommend_marks_local_library_matches(client, settings):
    settings.OPENAI_API_KEY = ''
    author = Author.objects.create(full_name='Morgan Housel')
    book = Book.objects.create(title='The Psychology of Money', description='Timeless lessons on wealth.')
    book.authors.add(author)

    response = _post_prompt(client, 'I want to understand how money works')

    assert response.status_code == 200
    payload = response.json()
    local_matches = [item for item in payload['recommendations'] if item['in_library']]
    assert local_matches
    assert local_matches[0]['book_id'] == book.pk
    assert local_matches[0]['book_url']


def test_advanced_recommend_caches_near_identical_prompts(client, monkeypatch):
    calls = []

    def fake_llm(prompt):
        calls.append(prompt)
        return [
            {
                'rank': index,
                'title': f'Finance Pick {index}',
                'author': 'Test Author',
                'reason': 'A precise match for learning finance.',
                'mood_tag': 'educational',
                'match_score': 90,
                'genre': 'Finance',
                'difficulty': 'Beginner',
                'source': 'llm',
            }
            for index in range(1, 6)
        ]

    monkeypatch.setattr('recommendations.views.advanced_recommend.get_llm_book_suggestions', fake_llm)

    first = _post_prompt(client, 'books on finance')
    second = _post_prompt(client, 'finance books!')

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['cached'] is False
    assert second.json()['cached'] is True
    assert len(calls) == 1


def test_advanced_recommend_rate_limits_per_client(client, settings):
    settings.OPENAI_API_KEY = ''

    for _ in range(10):
        response = _post_prompt(client, 'I need a comforting book')
        assert response.status_code == 200

    response = _post_prompt(client, 'I need a comforting book')

    assert response.status_code == 429
    assert response.json()['rate_limit']['remaining'] == 0
