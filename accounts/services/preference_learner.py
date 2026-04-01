"""
Phase 2: User Preference Learning Service

Learns user preferences from their interactions and provides personalized recommendations.
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.db.models import Q, Avg, Count, F

logger = logging.getLogger(__name__)


class PreferenceLearner:
    """Learns and updates user preferences based on behavior."""
    
    @staticmethod
    def record_book_rating(user, book, rating: int, review: str = "") -> bool:
        """
        Record a user's rating of a book and update preferences.
        
        Args:
            user: Django User object
            book: Book model instance
            rating: Rating 1-5
            review: Optional review text
            
        Returns:
            True if preference updated, False otherwise
        """
        from accounts.models import UserBookRating, UserProfile, UserGenrePreference
        
        try:
            # Save/update the rating
            rating_obj, created = UserBookRating.objects.update_or_create(
                user=user,
                book=book,
                defaults={'rating': rating, 'review': review}
            )
            
            # Update genre preferences
            PreferenceLearner._update_genre_preferences(user, book, rating)
            
            # Update user profile sentiment preferences
            PreferenceLearner._update_sentiment_preferences(user)
            
            logger.info(f"Recorded rating: {user.username} → {book.title} ({rating}★)")
            return True
            
        except Exception as e:
            logger.error(f"Error recording rating: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _update_genre_preferences(user, book, rating: int):
        """Update user's genre preferences based on rating."""
        from accounts.models import UserGenrePreference
        
        for genre in book.genres.all():
            # Higher ratings increase preference weight
            weight_change = (rating - 3) * 0.1  # -0.2 for 1★, +0.2 for 5★
            
            pref, _ = UserGenrePreference.objects.get_or_create(
                user=user,
                genre=genre,
                defaults={'weight': 0.5}
            )
            
            # Update weight (bounded between 0 and 1)
            new_weight = max(0, min(1.0, float(pref.weight) + weight_change))
            pref.weight = Decimal(str(new_weight))
            pref.interaction_count += 1
            pref.save()
            
            logger.debug(f"Updated genre preference: {genre.name} → {new_weight:.2f}")
    
    @staticmethod
    def _update_sentiment_preferences(user):
        """Update user's sentiment and mood preferences based on highly-rated books."""
        from accounts.models import UserProfile
        
        # Get user's 5-star rated books
        high_rated_books = user.book_ratings.filter(rating=5).values_list(
            'book__sentiment_score',
            'book__dominant_mood',
            'book__mood_scores',
            'book__emotional_intensity'
        )
        
        if not high_rated_books:
            return
        
        # Calculate average sentiment
        sentiments = [float(s[0]) for s in high_rated_books if s[0]]
        if sentiments:
            avg_sentiment = Decimal(str(sum(sentiments) / len(sentiments)))
        else:
            avg_sentiment = None
        
        # Calculate preferred intensity
        intensities = [float(i[3]) for i in high_rated_books if i[3]]
        if intensities:
            avg_intensity = Decimal(str(sum(intensities) / len(intensities)))
        else:
            avg_intensity = None
        
        # Update profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.preferred_sentiment = avg_sentiment
        profile.preferred_intensity = avg_intensity
        profile.save()
        
        logger.info(f"Updated sentiment preferences for {user.username}: "
                   f"sentiment={avg_sentiment}, intensity={avg_intensity}")
    
    @staticmethod
    def get_user_preferences(user) -> Dict:
        """Get complete user preference profile."""
        from accounts.models import UserProfile, UserGenrePreference
        
        try:
            profile = UserProfile.objects.get(user=user)
        except:
            profile = UserProfile.objects.create(user=user)
        
        # Get top genre preferences
        top_genres = (UserGenrePreference.objects
                     .filter(user=user)
                     .order_by('-weight')
                     .values_list('genre__name', 'weight')[:5])
        
        return {
            'preferred_sentiment': float(profile.preferred_sentiment or 0),
            'preferred_intensity': float(profile.preferred_intensity or 0),
            'preferred_moods': profile.preferred_moods or {},
            'favorite_genres': [{'name': g[0], 'weight': float(g[1])} for g in top_genres],
            'min_rating': float(profile.min_rating),
            'min_ratings_count': profile.min_ratings_count,
        }
    
    @staticmethod
    def record_mood_history(user, mood_scores: Dict, dominant_mood: str, context: str = ""):
        """Record user's mood for analytics and pattern learning."""
        from accounts.models import UserMoodHistory
        
        try:
            UserMoodHistory.objects.create(
                user=user,
                mood_scores=mood_scores,
                dominant_mood=dominant_mood,
                context=context
            )
            logger.info(f"Recorded mood: {user.username} → {dominant_mood}")
            return True
        except Exception as e:
            logger.error(f"Error recording mood: {e}", exc_info=True)
            return False


class PreferenceFilter:
    """Applies learned preferences to filter recommendations."""
    
    @staticmethod
    def apply_user_filters(user, queryset):
        """
        Apply user's learned preferences as filters.
        
        Args:
            user: Django User object
            queryset: QuerySet to filter
            
        Returns:
            Filtered QuerySet
        """
        from accounts.models import UserProfile
        
        try:
            profile = UserProfile.objects.get(user=user)
        except:
            return queryset
        
        # Apply minimum rating filter
        queryset = queryset.filter(
            average_rating__gte=profile.min_rating,
            ratings_count__gte=profile.min_ratings_count
        )
        
        # Apply genre preferences (if user has rated many books)
        genre_prefs = list(profile.genre_preferences.filter(weight__gte=0.6))
        if genre_prefs and len(genre_prefs) >= 2:
            # Only enforce if user has clear preferences
            preferred_genres = [p.genre for p in genre_prefs]
            queryset = queryset.annotate(
                genre_match_count=Count('genres', filter=Q(genres__in=preferred_genres))
            ).filter(genre_match_count__gt=0)
        
        return queryset
    
    @staticmethod
    def rank_by_preferences(user, recommendations: List[Dict]) -> List[Dict]:
        """
        Re-rank recommendations based on user's learned preferences.
        
        Args:
            user: Django User object
            recommendations: List of recommendation dicts from mood recommender
            
        Returns:
            Re-ranked recommendations
        """
        from accounts.models import UserProfile
        
        try:
            profile = UserProfile.objects.get(user=user)
            prefs = PreferenceLearner.get_user_preferences(user)
        except:
            return recommendations
        
        # Boost books matching user's preferred genres
        for rec in recommendations:
            genre_boost = 1.0
            # If book has genres matching user preferences, boost score
            if hasattr(rec, 'genres'):
                genre_pref_genres = [p.genre for p in profile.genre_preferences.filter(weight__gte=0.6)]
                match_count = len([g for g in rec.genres.all() if g in genre_pref_genres])
                genre_boost = 1.0 + (match_count * 0.1)
            
            # Adjust score based on sentiment match
            if prefs['preferred_sentiment'] != 0:
                book_sentiment = float(rec.get('sentiment_score', 0))
                sentiment_alignment = 1 - abs(book_sentiment - prefs['preferred_sentiment'])
                genre_boost *= (0.5 + sentiment_alignment * 0.5)
            
            # Apply boost to score
            rec['learning_boosted_score'] = float(rec.get('sentiment_score', 0)) * genre_boost
        
        # Re-sort by boosted score
        recommendations = sorted(
            recommendations,
            key=lambda x: x.get('learning_boosted_score', 0),
            reverse=True
        )
        
        return recommendations
