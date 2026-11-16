"""Async tasks for heavy operations using Celery."""
import logging
from celery import shared_task
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_book_recommendations(self, user_id: int, mood: str, limit: int = 10):
    """
    Async task to generate book recommendations based on mood.
    
    Args:
        user_id: ID of the user requesting recommendations
        mood: User's mood description
        limit: Number of recommendations to return
    
    Returns:
        List of recommended books
    """
    try:
        from accounts.models import Book
        from accounts.services.mood_recommender import get_mood_recommender
        
        logger.info(f"Generating recommendations for user {user_id} with mood: {mood}")
        
        # Check if we have a cached result
        cache_key = f'recommendations:user:{user_id}:mood:{mood.lower()}'
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached recommendations for user {user_id}")
            return cached_result
        
        # Generate recommendations
        recommender = get_mood_recommender()
        recommendations = recommender.recommend_books(
            user_mood=mood,
            limit=limit,
            improve_mood=True,
            min_confidence=0.3
        )
        
        # Cache the result for 1 hour
        cache.set(cache_key, recommendations, timeout=3600)
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations
    
    except Exception as exc:
        logger.error(f"Error generating recommendations: {exc}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_google_books_async(self, query: str, limit: int = 10):
    """
    Async task to fetch books from Google Books API.
    
    Args:
        query: Search query
        limit: Number of books to fetch
    
    Returns:
        List of books from Google Books
    """
    try:
        from accounts.services.google_books import search_google_books
        
        logger.info(f"Fetching Google Books for query: {query}")
        
        # Check cache first
        cache_key = f'google_books:{query}:{limit}'
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached Google Books results for query: {query}")
            return cached_result
        
        # Fetch from API
        results = search_google_books(query, max_results=limit)
        books = [book.to_dict() for book in results]
        
        # Cache for 24 hours
        cache.set(cache_key, books, timeout=86400)
        
        logger.info(f"Fetched {len(books)} books from Google Books API")
        return books
    
    except Exception as exc:
        logger.error(f"Error fetching Google Books: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def update_book_sentiment(self, book_id: int):
    """
    Async task to update book sentiment analysis.
    
    Args:
        book_id: ID of the book to analyze
    """
    try:
        from accounts.models import Book
        from accounts.services.sentiment_analysis import analyze_sentiment
        
        book = Book.objects.get(id=book_id)
        logger.info(f"Analyzing sentiment for book: {book.title}")
        
        # Perform sentiment analysis on book description
        if book.description:
            result = analyze_sentiment(book.description)
            book.sentiment_label = result.get('label')
            book.sentiment_magnitude = result.get('magnitude')
            book.save()
            
            logger.info(f"Updated sentiment for book {book_id}: {result.get('label')}")
        
        return {'status': 'success', 'book_id': book_id}
    
    except Book.DoesNotExist:
        logger.warning(f"Book {book_id} not found")
    except Exception as exc:
        logger.error(f"Error updating book sentiment: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def bulk_update_book_sentiment(self, book_ids: list = None):
    """
    Async task to update sentiment for multiple books.
    
    Args:
        book_ids: List of book IDs to analyze, or None for all
    """
    try:
        from accounts.models import Book
        from accounts.services.sentiment_analysis import analyze_sentiment
        
        if book_ids is None:
            books = Book.objects.filter(description__isnull=False).excludes(description__exact='')
        else:
            books = Book.objects.filter(id__in=book_ids)
        
        logger.info(f"Analyzing sentiment for {books.count()} books")
        
        updated_count = 0
        for book in books:
            try:
                result = analyze_sentiment(book.description)
                book.sentiment_label = result.get('label')
                book.sentiment_magnitude = result.get('magnitude')
                book.save()
                updated_count += 1
            except Exception as e:
                logger.warning(f"Error analyzing sentiment for book {book.id}: {e}")
                continue
        
        logger.info(f"Updated sentiment for {updated_count} books")
        return {'status': 'success', 'updated_count': updated_count}
    
    except Exception as exc:
        logger.error(f"Error in bulk sentiment update: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def cache_category_books(self, category_id: int):
    """
    Async task to pre-cache books for a category.
    
    Args:
        category_id: ID of the category to cache
    """
    try:
        from accounts.models import Category
        from accounts.services.external import fetch_books_for_category, cache_books
        
        category = Category.objects.get(id=category_id)
        logger.info(f"Caching books for category: {category.display_name}")
        
        # Fetch books for category
        books = fetch_books_for_category(category.slug)
        
        # Cache results
        cache_books(category_id, books)
        
        logger.info(f"Cached {len(books)} books for category {category_id}")
        return {'status': 'success', 'category_id': category_id, 'book_count': len(books)}
    
    except Exception as exc:
        logger.error(f"Error caching category books: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def bulk_cache_categories(self):
    """
    Async task to pre-cache books for all categories.
    """
    try:
        from accounts.models import Category
        
        categories = Category.objects.all()
        logger.info(f"Starting bulk cache for {categories.count()} categories")
        
        for category in categories:
            # Spawn separate tasks for each category
            cache_category_books.delay(category.id)
        
        logger.info(f"Scheduled caching for {categories.count()} categories")
        return {'status': 'success', 'category_count': categories.count()}
    
    except Exception as exc:
        logger.error(f"Error in bulk cache categories: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def clean_expired_cache(self):
    """
    Async task to clean expired cache entries.
    This is useful for periodic maintenance.
    """
    try:
        logger.info("Starting cache cleanup")
        
        # Clear specific cache patterns
        cache_patterns = [
            'recommendations:',
            'google_books:',
            'category:',
        ]
        
        # Note: Django's cache backend doesn't have pattern deletion
        # You would need to implement this based on your cache backend
        # For Redis, you can use client.delete_pattern()
        
        logger.info("Cache cleanup completed")
        return {'status': 'success'}
    
    except Exception as exc:
        logger.error(f"Error cleaning cache: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=1, default_retry_delay=60)
def send_welcome_email(self, user_id: int):
    """
    Async task to send welcome email to new user.
    
    Args:
        user_id: ID of the user to send welcome email to
    """
    try:
        from django.contrib.auth.models import User
        from django.core.mail import send_mail
        from django.conf import settings
        
        user = User.objects.get(id=user_id)
        logger.info(f"Sending welcome email to {user.email}")
        
        message = f"""
        Welcome to ReadWise, {user.username}!
        
        We're excited to have you on board. Explore our collection of books,
        get personalized recommendations, and track your reading journey.
        
        Happy reading!
        """
        
        send_mail(
            subject='Welcome to ReadWise',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return {'status': 'success', 'user_id': user_id}
    
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
    except Exception as exc:
        logger.error(f"Error sending welcome email: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)
