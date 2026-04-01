"""
Phase 3.1: Database Optimization

Implements:
- Query optimization hints
- Database indexing strategy
- N+1 query prevention
- Connection pooling
- Query caching
"""

import logging
from functools import wraps
from typing import Dict, List, Any, Optional
from django.db.models import Prefetch, Q
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import time

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimizes database queries to reduce N+1 and improve performance."""
    
    @staticmethod
    def optimize_book_list(queryset):
        """
        Optimizes book queryset with necessary prefetches/selects.
        Reduces queries from N+1 to constant number.
        """
        return (queryset
                .select_related()  # Follow FK relationships
                .prefetch_related(
                    'authors',      # Get all authors in one query
                    'genres',       # Get all genres in one query
                    'user_ratings'  # Get all ratings in one query
                )
                .only(
                    'id', 'title', 'subtitle', 'description',
                    'cover_image', 'average_rating', 'ratings_count',
                    'sentiment_label', 'dominant_mood', 'emotional_intensity',
                    'created_at', 'updated_at'
                ))
    
    @staticmethod
    def optimize_search_results(queryset):
        """Optimize queryset for search result display."""
        return (QueryOptimizer.optimize_book_list(queryset)
                .defer(
                    'sentiment_score', 'sentiment_magnitude',
                    'mood_scores', 'sentiment_confidence'
                ))
    
    @staticmethod
    def optimize_user_profile(queryset):
        """Optimize user queryset with related data."""
        from django.contrib.auth.models import User
        return (queryset
                .select_related('profile')
                .prefetch_related(
                    'book_ratings',
                    'genre_preferences',
                    'mood_history'
                ))
    
    @staticmethod
    def optimize_recommendations(books: List) -> List:
        """
        Batch-load related data for recommendations.
        Converts N queries to 1-2 queries.
        """
        book_ids = [b.id if hasattr(b, 'id') else b.get('book_id') for b in books]
        
        if not book_ids:
            return books
        
        # Batch-load all related data
        from accounts.models import Book
        books_data = {}
        for book in Book.objects.filter(id__in=book_ids).prefetch_related('authors', 'genres'):
            books_data[book.id] = book
        
        # Enrich recommendations with prefetched data
        for rec in books:
            book_id = rec.id if hasattr(rec, 'id') else rec.get('book_id')
            if book_id in books_data:
                book = books_data[book_id]
                rec['authors_list'] = [a.full_name for a in book.authors.all()]
                rec['genres_list'] = [g.name for g in book.genres.all()]
        
        return books


class CacheStrategy:
    """Implements intelligent caching strategy for frequently accessed data."""
    
    # Cache TTLs (in seconds)
    CACHE_TTL = {
        'filter_options': 3600,      # 1 hour
        'trending_books': 1800,      # 30 minutes
        'category_books': 1800,      # 30 minutes
        'search_results': 300,       # 5 minutes
        'user_preferences': 600,     # 10 minutes
        'suggestions': 3600,         # 1 hour
    }
    
    @staticmethod
    def get_cache_key(prefix: str, identifier: str = "") -> str:
        """Generate cache key."""
        if identifier:
            return f"{prefix}:{identifier}"
        return prefix
    
    @staticmethod
    def cache_filter_options(user_id: Optional[int] = None):
        """Cache expensive filter options query."""
        cache_key = CacheStrategy.get_cache_key('filter_options', str(user_id))
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        # Generate filter options (expensive operation)
        from accounts.services.smart_search import SmartSearchFilter
        from django.contrib.auth.models import User
        
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except:
                pass
        
        options = SmartSearchFilter.get_filter_options(user=user)
        cache.set(cache_key, options, CacheStrategy.CACHE_TTL['filter_options'])
        return options
    
    @staticmethod
    def cache_trending_books(limit: int = 10):
        """Cache trending books query."""
        cache_key = CacheStrategy.get_cache_key('trending_books', str(limit))
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        from accounts.models import Book
        books = (Book.objects
                .filter(ratings_count__gte=50)
                .order_by('-average_rating', '-ratings_count')
                .prefetch_related('authors', 'genres')[:limit])
        
        result = list(books.values('id', 'title', 'average_rating', 'ratings_count'))
        cache.set(cache_key, result, CacheStrategy.CACHE_TTL['trending_books'])
        return result
    
    @staticmethod
    def invalidate_cache(pattern: str):
        """Invalidate cache entries matching pattern."""
        # Django doesn't support wildcard pattern deletion in all backends
        # This is a placeholder for cache invalidation logic
        logger.info(f"Cache invalidation triggered for pattern: {pattern}")


def query_performance_log(func):
    """Decorator to measure and log query performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from django.db import connection
        from django.db import reset_queries
        
        reset_queries()
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        elapsed = time.time() - start_time
        num_queries = len(connection.queries)
        
        logger.info(
            f"Function: {func.__name__} | "
            f"Queries: {num_queries} | "
            f"Time: {elapsed:.2f}s"
        )
        
        if num_queries > 10:
            logger.warning(
                f"⚠️ PERFORMANCE: {func.__name__} made {num_queries} queries "
                f"(expected max: 10)"
            )
        
        if elapsed > 1.0:
            logger.warning(
                f"⚠️ PERFORMANCE: {func.__name__} took {elapsed:.2f}s "
                f"(expected max: 1.0s)"
            )
        
        return result
    
    return wrapper


class DatabaseSettings:
    """Django settings for database optimization."""
    
    # Add to settings.py:
    OPTIMIZATIONS = {
        'CONN_MAX_AGE': 600,  # Connection pooling: keep connections for 10 min
        'ATOMIC_REQUESTS': False,  # Don't wrap each request in transaction
        'AUTOCOMMIT': True,  # Auto-commit mode for better concurrency
        'OPTIONS': {
            'connect_timeout': 10,
            'initialization_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
    
    @staticmethod
    def get_optimized_settings() -> Dict:
        """Return optimized database settings."""
        return DatabaseSettings.OPTIMIZATIONS


class IndexingStrategy:
    """
    Database indexing recommendations.
    Run migrations to apply these indexes.
    """
    
    INDEXES = """
    # Add to models.py Meta classes:
    
    # Book indexes
    class Meta:
        indexes = [
            models.Index(fields=['average_rating', '-ratings_count']),
            models.Index(fields=['sentiment_label']),
            models.Index(fields=['dominant_mood']),
            models.Index(fields=['created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['title']),  # For search
            models.Index(fields=['genres']),  # M2M
        ]
    
    # UserBookRating indexes (already defined in models)
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['book', 'rating']),
            models.Index(fields=['rating']),
        ]
    
    # UserProfile indexes
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['preferred_sentiment']),
        ]
    
    # UserGenrePreference indexes (already defined)
    class Meta:
        indexes = [
            models.Index(fields=['user', 'weight']),
            models.Index(fields=['genre']),
        ]
    
    # UserMoodHistory indexes (already defined)
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'dominant_mood']),
        ]
    """
    
    @staticmethod
    def get_missing_indexes() -> List[str]:
        """List recommended indexes not yet created."""
        return [
            "Book (average_rating, -ratings_count) - for trending/sorting",
            "Book (sentiment_label) - for sentiment filtering",
            "Book (dominant_mood) - for mood filtering",
            "Book (created_at) - for date filtering",
            "UserBookRating (user, created_at) - for user activity",
        ]


# Usage example in views:
"""
from accounts.services.performance import QueryOptimizer, CacheStrategy

def search_books_optimized(request):
    # 1. Check cache first
    options = CacheStrategy.cache_filter_options(user_id=request.user.id)
    
    # 2. Optimize query
    books = QueryOptimizer.optimize_search_results(
        Book.objects.filter(...)
    )
    
    # 3. Batch load related data
    books = QueryOptimizer.optimize_recommendations(books)
    
    return books
"""
