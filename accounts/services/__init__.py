"""Service layer helpers with lazy imports to avoid heavy startup cost."""


def get_sentiment_analyzer():
    """Import the analyzer lazily so package import stays cheap."""
    from accounts.services.sentiment_analysis import get_sentiment_analyzer as _get

    return _get()


def get_mood_recommender():
    """Import the recommender lazily so Django startup is not blocked."""
    from accounts.services.mood_recommender import get_mood_recommender as _get

    return _get()


__all__ = ["get_sentiment_analyzer", "get_mood_recommender"]
