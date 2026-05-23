import json

import pytest
from django.core.cache import cache
from django.urls import reverse

from accounts.models import Book
from accounts.services.cover_utils import PLACEHOLDER_COVER_URL, normalize_cover
from accounts.services.mood_recommender import MoodRecommender
from accounts.services.recommendation_facade import (
    RecommendationUnavailableError,
    get_recommendations_for_mood,
)
from accounts.services.sentiment_analysis import SentimentAnalyzer


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_recommendation_cache():
    cache.clear()
    yield
    cache.clear()

SAMPLE_MOODS = [
    'I feel anxious and need something calming',
    "I'm feeling happy and want something fun and uplifting",
    'I feel sad and need comfort',
    "I'm excited and want an adventure",
    'I need inspiration and motivation',
    "I'm feeling romantic and dreamy",
]


def _sample_recommendation(*, title='Sample Book', source='mood'):
    return [
        {
            'book_id': 1,
            'title': title,
            'author': 'Test Author',
            'genre': 'Fiction',
            'cover_image': PLACEHOLDER_COVER_URL,
            'dominant_mood': 'happy',
            'recommendation_reason': 'A strong match for the requested mood.',
            'sentiment_score': 0.82,
            'match_percent': 82,
            'source': source,
        }
    ]


@pytest.mark.parametrize('mood_text', SAMPLE_MOODS)
def test_recommendations_page_renders_cards_for_sample_moods(client, monkeypatch, mood_text):
    monkeypatch.setattr('accounts.views.get_recommendations_for_mood', lambda *args, **kwargs: _sample_recommendation())

    response = client.post(reverse('recommendations'), {'mood': mood_text, 'improve_mood': 'on'})

    assert response.status_code == 200
    body = response.content.decode('utf-8')
    assert 'Your Personalized Recommendations' in body
    assert 'Sample Book' in body
    assert 'Ready to find your perfect book?' not in body


def test_mood_api_returns_fallback_diagnostics(client, monkeypatch):
    monkeypatch.setattr(
        'accounts.views.get_recommendations_for_mood',
        lambda *args, **kwargs: _sample_recommendation(source='dataset_fallback'),
    )

    response = client.post(
        reverse('api_mood_recommendations'),
        data=json.dumps({'mood': SAMPLE_MOODS[0], 'improve_mood': True, 'limit': 3}),
        content_type='application/json',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['fallback_used'] is True
    assert payload['recommendations'][0]['source'] == 'dataset_fallback'


def test_mood_api_requires_mood(client):
    response = client.post(
        reverse('api_mood_recommendations'),
        data=json.dumps({'mood': ''}),
        content_type='application/json',
    )

    assert response.status_code == 400
    assert response.json()['error'] == 'Mood description is required'


def test_facade_prefers_mood_recommendations(monkeypatch):
    class StubMoodRecommender:
        def recommend_books(self, **kwargs):
            return [
                {
                    'book_id': 11,
                    'title': 'Mood First',
                    'author': 'Tester',
                    'genre': 'Fiction',
                    'cover_image': PLACEHOLDER_COVER_URL,
                    'dominant_mood': 'happy',
                    'recommendation_reason': 'Primary mood recommender result.',
                    'sentiment_score': 0.77,
                    'match_percent': 77,
                }
            ]

    monkeypatch.setattr('accounts.services.recommendation_facade.get_mood_recommender', lambda: StubMoodRecommender())
    monkeypatch.setattr(
        'accounts.services.recommendation_facade.get_dataset_recommender',
        lambda *args, **kwargs: pytest.fail('Dataset fallback should not run when mood results are usable.'),
    )

    recommendations = get_recommendations_for_mood('I feel happy', limit=3, improve_mood=True)

    assert recommendations[0]['title'] == 'Mood First'
    assert recommendations[0]['source'] == 'mood'
    assert {'book_id', 'title', 'author', 'genre', 'cover_image', 'dominant_mood', 'recommendation_reason', 'sentiment_score', 'match_percent', 'source'} <= recommendations[0].keys()


def test_facade_falls_back_when_mood_returns_empty(monkeypatch):
    class StubMoodRecommender:
        def recommend_books(self, **kwargs):
            return []

    class StubDatasetRecommender:
        def recommend(self, *args, **kwargs):
            return [
                {
                    'book_id': '7054',
                    'title': 'Dataset Rescue',
                    'author': 'Fallback Author',
                    'genres': ['Fiction', 'Fantasy'],
                    'cover_image': 'https://covers.example.org/dataset-rescue.jpg',
                    'score': 0.75,
                    'dominant_mood': 'Excited',
                    'explanation': 'Fallback recommendation.',
                }
            ]

    monkeypatch.setattr('accounts.services.recommendation_facade.get_mood_recommender', lambda: StubMoodRecommender())
    monkeypatch.setattr('accounts.services.recommendation_facade.get_dataset_recommender', lambda *args, **kwargs: StubDatasetRecommender())

    recommendations = get_recommendations_for_mood('I feel anxious', limit=3, improve_mood=True)

    assert recommendations[0]['title'] == 'Dataset Rescue'
    assert recommendations[0]['source'] == 'dataset_fallback'
    assert recommendations[0]['genre'] == 'Fiction, Fantasy'
    assert recommendations[0]['cover_image'] == 'https://covers.example.org/dataset-rescue.jpg'


def test_facade_falls_back_when_mood_raises(monkeypatch):
    class StubMoodRecommender:
        def recommend_books(self, **kwargs):
            raise RuntimeError('mood path failed')

    class StubDatasetRecommender:
        def recommend(self, *args, **kwargs):
            return [
                {
                    'book_id': '82',
                    'title': 'Recovered Result',
                    'author': 'Fallback Author',
                    'genres': ['Nonfiction'],
                    'score': 0.66,
                    'dominant_mood': 'Hopeful',
                    'explanation': 'Recovered via fallback.',
                }
            ]

    monkeypatch.setattr('accounts.services.recommendation_facade.get_mood_recommender', lambda: StubMoodRecommender())
    monkeypatch.setattr('accounts.services.recommendation_facade.get_dataset_recommender', lambda *args, **kwargs: StubDatasetRecommender())

    recommendations = get_recommendations_for_mood('I feel anxious', limit=3, improve_mood=True)

    assert recommendations[0]['title'] == 'Recovered Result'
    assert recommendations[0]['source'] == 'dataset_fallback'


def test_facade_raises_when_both_recommenders_fail(monkeypatch):
    class StubMoodRecommender:
        def recommend_books(self, **kwargs):
            raise RuntimeError('mood path failed')

    class StubDatasetRecommender:
        def recommend(self, *args, **kwargs):
            raise RuntimeError('dataset path failed')

    monkeypatch.setattr('accounts.services.recommendation_facade.get_mood_recommender', lambda: StubMoodRecommender())
    monkeypatch.setattr('accounts.services.recommendation_facade.get_dataset_recommender', lambda *args, **kwargs: StubDatasetRecommender())

    with pytest.raises(RecommendationUnavailableError):
        get_recommendations_for_mood('I feel anxious', limit=3, improve_mood=True)


def test_metadata_backed_books_rank_ahead_of_sentiment_only_books(monkeypatch):
    metadata_book = Book.objects.create(
        title='Structured Joy',
        description='A mood-aware title.',
        sentiment_label='positive',
        dominant_mood='happy',
        mood_scores={'happy': 0.8},
    )
    fallback_book = Book.objects.create(
        title='Sentiment Only',
        description='A sentiment-only fallback title.',
        sentiment_label='positive',
    )

    class StubAnalyzer:
        def analyze_text(self, text):
            return {
                'dominant_mood': 'happy',
                'moods': {'happy': 1.0},
                'confidence': 1.0,
                'analysis_method': 'keyword',
            }

        def match_mood(self, user_text, book_moods):
            return 0.5

    recommender = MoodRecommender.__new__(MoodRecommender)
    recommender.analyzer = StubAnalyzer()
    recommender._cover_trace_map = {}
    monkeypatch.setattr(recommender, '_get_candidate_books', lambda *args, **kwargs: [fallback_book, metadata_book])
    monkeypatch.setattr(recommender, '_reset_cover_trace', lambda: None)
    monkeypatch.setattr(recommender, '_log_cover_summary', lambda total: None)
    monkeypatch.setattr(recommender, '_cover_image_for', lambda book: PLACEHOLDER_COVER_URL)

    recommendations = recommender.recommend_books('I feel happy', limit=2, improve_mood=False, min_confidence=0.3)

    assert [item['title'] for item in recommendations[:2]] == ['Structured Joy', 'Sentiment Only']


def test_dataset_api_returns_cover_image_from_dataset(client, monkeypatch):
    class StubDatasetRecommender:
        def recommend(self, *args, **kwargs):
            return [
                {
                    'book_id': '201',
                    'title': 'Dataset Cover',
                    'author': 'Fallback Author',
                    'genres': ['Fantasy'],
                    'cover_image': 'https://covers.example.org/dataset-cover.jpg',
                    'isbn_10': '1234567890',
                    'isbn_13': '9781234567890',
                    'score': 0.81,
                    'dominant_mood': 'Hopeful',
                    'sentiment_score': 0.81,
                    'emotional_intensity': 0.45,
                    'explanation': 'Uses dataset-provided cover.',
                }
            ]

        def analyze_user_mood(self, user_text):
            class Profile:
                dominant_mood = 'hopeful'
                sentiment_score = 0.5
                emotional_intensity = 0.4
                mood_scores = {'hopeful': 1.0}

            return Profile()

    monkeypatch.setattr(
        'accounts.services.dataset_recommender.get_dataset_recommender',
        lambda *args, **kwargs: StubDatasetRecommender(),
    )

    response = client.post(
        reverse('api_dataset_recommendations'),
        data=json.dumps({'mood': 'I need hope', 'limit': 3}),
        content_type='application/json',
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['recommendations'][0]['cover_image'] == 'https://covers.example.org/dataset-cover.jpg'
    assert payload['recommendations'][0]['isbn_10'] == '1234567890'
    assert payload['recommendations'][0]['isbn_13'] == '9781234567890'


def test_normalize_cover_rejects_example_dot_com_urls():
    assert normalize_cover('https://example.com/covers/42.jpg') == PLACEHOLDER_COVER_URL
    assert normalize_cover('https://example.com/placeholder_cover.png') == PLACEHOLDER_COVER_URL


def test_sentiment_analyzer_respects_disabled_transformers(monkeypatch):
    monkeypatch.setenv('ENABLE_TRANSFORMERS', 'false')
    monkeypatch.setattr('accounts.services.sentiment_analysis.SENTENCE_TRANSFORMERS_AVAILABLE', True)
    monkeypatch.setattr('accounts.services.sentiment_analysis.TRANSFORMERS_AVAILABLE', True)
    monkeypatch.setattr('accounts.services.sentiment_analysis.NUMPY_AVAILABLE', True)
    monkeypatch.setattr('accounts.services.sentiment_analysis.SentenceTransformer', lambda *args, **kwargs: pytest.fail('transformer bootstrap should be disabled'))
    monkeypatch.setattr('accounts.services.sentiment_analysis.pipeline', lambda *args, **kwargs: pytest.fail('pipeline bootstrap should be disabled'))

    analyzer = SentimentAnalyzer()

    assert analyzer.embedding_model is None
    assert analyzer.emotion_classifier is None
    assert analyzer.analyze_text('I feel hopeful today')['analysis_method'] == 'keyword'


def test_recommendations_return_best_available_when_threshold_filters_everything(monkeypatch):
    book = Book.objects.create(
        title='Threshold Rescue',
        description='A low-confidence but valid book.',
        sentiment_label='neutral',
    )

    class StubAnalyzer:
        def analyze_text(self, text):
            return {
                'dominant_mood': 'neutral',
                'moods': {'neutral': 1.0},
                'confidence': 1.0,
                'analysis_method': 'transformer',
            }

        def match_mood(self, user_text, book_moods):
            return 0.05

    recommender = MoodRecommender.__new__(MoodRecommender)
    recommender.analyzer = StubAnalyzer()
    recommender._cover_trace_map = {}
    monkeypatch.setattr(recommender, '_get_candidate_books', lambda *args, **kwargs: [book])
    monkeypatch.setattr(recommender, '_reset_cover_trace', lambda: None)
    monkeypatch.setattr(recommender, '_log_cover_summary', lambda total: None)
    monkeypatch.setattr(recommender, '_cover_image_for', lambda current_book: PLACEHOLDER_COVER_URL)
    monkeypatch.setattr(
        recommender,
        '_score_book',
        lambda *args, **kwargs: (0.05, 'Fallback rescue result.', 'neutral'),
    )

    recommendations = recommender.recommend_books('I feel uncertain', limit=1, improve_mood=False, min_confidence=0.3)

    assert len(recommendations) == 1
    assert recommendations[0]['title'] == 'Threshold Rescue'
