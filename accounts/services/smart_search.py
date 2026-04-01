"""
Phase 2: Smart Search with Filters

Implements intelligent search combining mood-based, genre, rating, and user preference filters.
"""

import logging
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, F, Value
from django.db.models.functions import Lower
from decimal import Decimal

logger = logging.getLogger(__name__)


class SmartSearchFilter:
    """Advanced search with mood, genre, rating, and preference filters."""
    
    @staticmethod
    def build_search(
        query: str = "",
        moods: Optional[List[str]] = None,
        genres: Optional[List[str]] = None,
        min_rating: float = 0.0,
        min_ratings_count: int = 0,
        sentiment: Optional[str] = None,  # 'positive', 'negative', 'neutral'
        sort_by: str = 'relevance',  # 'relevance', 'rating', 'newest', 'mood_match'
        user=None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List, int]:
        """
        Build a smart search query combining multiple filters.
        
        Args:
            query: Text search query
            moods: List of mood tags to filter by
            genres: List of genre names to filter by
            min_rating: Minimum average rating
            min_ratings_count: Minimum number of ratings
            sentiment: Sentiment label filter ('positive', 'negative', 'neutral')
            sort_by: Sort order
            user: Optional Django User for personalized results
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            Tuple of (books_list, total_count)
        """
        from accounts.models import Book, Genre
        from accounts.services.preference_learner import PreferenceFilter
        
        queryset = Book.objects.all()
        
        # Text search
        if query and query.strip():
            search_query = Q(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(description__icontains=query) |
                Q(authors__full_name__icontains=query) |
                Q(genres__name__icontains=query)
            )
            queryset = queryset.filter(search_query)
        
        # Sentiment label filter
        if sentiment:
            queryset = queryset.filter(sentiment_label=sentiment)
        
        # Minimum rating filter
        if min_rating > 0:
            queryset = queryset.filter(average_rating__gte=Decimal(str(min_rating)))
        
        # Minimum ratings count
        if min_ratings_count > 0:
            queryset = queryset.filter(ratings_count__gte=min_ratings_count)
        
        # Genre filter
        if genres:
            genre_objs = Genre.objects.filter(name__in=genres)
            if genre_objs:
                queryset = queryset.filter(genres__in=genre_objs).distinct()
        
        # Mood filter (by dominant mood or mood_scores)
        if moods:
            mood_filter = Q()
            for mood in moods:
                # Match books with this mood as dominant or with mood score > 0.5
                mood_filter |= (
                    Q(dominant_mood__iexact=mood) |
                    Q(mood_scores__contains={mood: True})
                )
            queryset = queryset.filter(mood_filter).distinct()
        
        # Apply user preferences if authenticated and user has profiles
        if user and user.is_authenticated:
            queryset = PreferenceFilter.apply_user_filters(user, queryset)
        
        # Get total count before pagination
        total_count = queryset.distinct().count()
        
        # Sort
        if sort_by == 'rating':
            queryset = queryset.order_by('-average_rating', '-ratings_count')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'mood_match' and moods:
            # Sort by how many requested moods match
            queryset = queryset.order_by('-dominant_mood')  # Simple implementation
        else:  # 'relevance'
            # Default: prioritize by rating and match
            queryset = queryset.order_by('-average_rating', '-ratings_count')
        
        # Pagination
        queryset = queryset.prefetch_related('authors', 'genres')[offset:offset + limit]
        
        books = list(queryset)
        
        logger.info(f"Smart search: query='{query}' moods={moods} genres={genres} "
                   f"results={total_count} sort_by={sort_by}")
        
        return books, total_count
    
    @staticmethod
    def get_search_suggestions(
        query: str = "",
        category: str = "all",  # 'all', 'titles', 'authors', 'genres', 'moods'
        limit: int = 10
    ) -> Dict[str, List]:
        """
        Get search suggestions for autocomplete.
        
        Args:
            query: Partial search text
            category: Which categories to suggest
            limit: Number of suggestions per category
            
        Returns:
            Dict with suggestion categories
        """
        from accounts.models import Book, Genre
        
        suggestions = {}
        
        if category in ('all', 'titles'):
            # Book title suggestions
            titles = (Book.objects
                     .filter(title__icontains=query)
                     .values_list('title', flat=True)
                     .distinct()[:limit])
            suggestions['titles'] = list(titles)
        
        if category in ('all', 'authors'):
            # Author suggestions
            from accounts.models import Author
            authors = (Author.objects
                      .filter(full_name__icontains=query)
                      .values_list('full_name', flat=True)
                      .distinct()[:limit])
            suggestions['authors'] = list(authors)
        
        if category in ('all', 'genres'):
            # Genre suggestions
            genres = (Genre.objects
                     .filter(name__icontains=query)
                     .values_list('name', flat=True)
                     .distinct()[:limit])
            suggestions['genres'] = list(genres)
        
        if category in ('all', 'moods'):
            # Mood suggestions (from actual books)
            from django.db.models import Distinct
            moods = (Book.objects
                    .exclude(dominant_mood='')
                    .filter(description__icontains=query)
                    .values_list('dominant_mood', flat=True)
                    .distinct()[:limit])
            suggestions['moods'] = list(moods)
        
        return suggestions
    
    @staticmethod
    def get_filter_options(user=None) -> Dict:
        """
        Get available filter options for search UI.
        
        Args:
            user: Optional user for personalized genre suggestions
            
        Returns:
            Dict with available filter options
        """
        from accounts.models import Genre
        from accounts.services.preference_learner import PreferenceLearner
        
        all_genres = Genre.objects.all().values_list('name', flat=True).order_by('name')
        all_moods = [
            'happy', 'sad', 'anxious', 'relaxed', 'excited', 
            'nostalgic', 'inspired', 'curious', 'peaceful', 'angry'
        ]
        
        options = {
            'genres': list(all_genres),
            'moods': all_moods,
            'sentiments': ['positive', 'negative', 'neutral'],
            'sort_options': [
                {'value': 'relevance', 'label': 'Most Relevant'},
                {'value': 'rating', 'label': 'Highest Rated'},
                {'value': 'newest', 'label': 'Newest'},
                {'value': 'mood_match', 'label': 'Best Mood Match'},
            ],
            'rating_ranges': [
                {'min': 0, 'max': 5, 'label': 'All Ratings'},
                {'min': 4, 'max': 5, 'label': '4+ Stars'},
                {'min': 3.5, 'max': 5, 'label': '3.5+ Stars'},
            ]
        }
        
        # Add user's preferred genres if authenticated
        if user and user.is_authenticated:
            prefs = PreferenceLearner.get_user_preferences(user)
            options['user_preferred_genres'] = [
                g['name'] for g in prefs['favorite_genres']
            ]
        
        return options
