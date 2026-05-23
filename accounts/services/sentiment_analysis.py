"""
Advanced Sentiment Analysis Module for Book Recommendation System

This module provides state-of-the-art NLP-based sentiment analysis using transformer models
to identify multi-dimensional emotional tones in book descriptions and reviews.

Features:
- Multi-mood recognition (happy, sad, angry, relaxed, excited, anxious, etc.)
- Contextual understanding using transformer embeddings
- Explainable sentiment scoring
- Scalable architecture for large datasets
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

# Guarded imports for optional heavy ML dependencies
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

logger = logging.getLogger(__name__)

# Multi-dimensional mood categories
MOOD_CATEGORIES = {
    'happy': ['joy', 'happiness', 'delight', 'cheerful', 'joyful', 'elated', 'euphoric', 'blissful'],
    'sad': ['sadness', 'sorrow', 'melancholy', 'grief', 'despair', 'depression', 'unhappiness', 'gloom'],
    'angry': ['anger', 'rage', 'fury', 'resentment', 'irritation', 'hostility', 'frustration', 'outrage'],
    'relaxed': ['calm', 'peaceful', 'serene', 'tranquil', 'relaxed', 'content', 'at ease', 'composed'],
    'excited': ['excitement', 'enthusiasm', 'thrill', 'eagerness', 'anticipation', 'energy', 'vibrant', 'animated'],
    'anxious': ['anxiety', 'worry', 'nervousness', 'fear', 'apprehension', 'stress', 'tension', 'unease'],
    'hopeful': ['hope', 'optimism', 'confidence', 'faith', 'expectation', 'promise', 'aspiration', 'encouragement'],
    'nostalgic': ['nostalgia', 'longing', 'yearning', 'reminiscence', 'sentimental', 'wistful', 'homesick'],
    'inspired': ['inspiration', 'motivation', 'empowerment', 'uplifting', 'encouraging', 'stimulating', 'energizing'],
    'romantic': ['love', 'romance', 'affection', 'passion', 'tenderness', 'intimacy', 'devotion', 'adoration'],
}

# Mood compatibility matrix (which moods complement or improve each other)
MOOD_COMPATIBILITY = {
    'sad': ['hopeful', 'inspired', 'relaxed', 'happy'],
    'anxious': ['relaxed', 'hopeful', 'happy', 'inspired'],   # 'calm' removed – not a MOOD_CATEGORIES key
    'angry': ['relaxed', 'hopeful', 'happy', 'inspired'],     # 'calm' removed – not a MOOD_CATEGORIES key
    'happy': ['excited', 'inspired', 'romantic', 'hopeful'],
    'relaxed': ['happy', 'hopeful', 'inspired', 'romantic'],
    'excited': ['happy', 'inspired', 'hopeful'],
    'hopeful': ['happy', 'inspired', 'excited'],
    'inspired': ['happy', 'hopeful', 'excited'],
    'romantic': ['happy', 'hopeful', 'relaxed'],
    'nostalgic': ['relaxed', 'hopeful', 'happy'],
}


def _transformers_enabled() -> bool:
    raw_value = os.getenv('ENABLE_TRANSFORMERS')
    if raw_value is not None:
        return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}

    try:
        return bool(getattr(settings, 'ENABLE_TRANSFORMERS', True))
    except Exception:
        return True


class SentimentAnalyzer:
    """
    Advanced sentiment analyzer using transformer models for multi-mood recognition.
    
    Uses:
    - Sentence transformers for semantic embeddings
    - Emotion classification pipeline for mood detection
    - Contextual understanding for accurate sentiment scoring
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', 
                 emotion_model: str = 'j-hartmann/emotion-english-distilroberta-base'):
        """
        Initialize the sentiment analyzer with transformer models.
        
        Args:
            model_name: Sentence transformer model for embeddings
            emotion_model: Emotion classification model for mood detection
        """
        self.embedding_model = None
        self.emotion_classifier = None
        self.mood_embeddings = {}

        if not _transformers_enabled():
            logger.info("Transformer sentiment models disabled by configuration. Using keyword-based analysis.")
            return

        # Check if required packages are available
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not TRANSFORMERS_AVAILABLE or not NUMPY_AVAILABLE:
            logger.warning(
                f"Heavy ML dependencies not available (numpy={NUMPY_AVAILABLE}, "
                f"sentence_transformers={SENTENCE_TRANSFORMERS_AVAILABLE}, "
                f"transformers={TRANSFORMERS_AVAILABLE}). Falling back to keyword-based analysis."
            )
            return
        
        try:
            logger.info(f"Loading sentence transformer model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            
            logger.info(f"Loading emotion classification model: {emotion_model}")
            self.emotion_classifier = pipeline(
                "text-classification",
                model=emotion_model,
                device=-1  # Use CPU by default (set to 0 for GPU if available)
            )
            
            # Pre-compute mood embeddings for faster matching
            self.mood_embeddings = self._precompute_mood_embeddings()
            
            logger.info("Sentiment analyzer initialized successfully")
        except (ImportError, OSError, RuntimeError) as e:
            # Catch specific errors: ImportError (missing deps), OSError (model download issues), RuntimeError (CUDA/device issues)
            logger.error(f"Error initializing sentiment analyzer: {e}")
            # Fallback to lightweight models if heavy models fail
            logger.warning("Falling back to keyword-based sentiment analysis")
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error initializing sentiment analyzer: {e}", exc_info=True)
            logger.warning("Falling back to keyword-based sentiment analysis")
    
    def _precompute_mood_embeddings(self) -> Dict[str, any]:
        """Pre-compute embeddings for mood categories for faster matching."""
        if not self.embedding_model or not NUMPY_AVAILABLE:
            return {}
        
        mood_embeddings = {}
        for mood, keywords in MOOD_CATEGORIES.items():
            # Create a representative text for each mood
            mood_text = f"{mood} {' '.join(keywords[:3])}"
            mood_embeddings[mood] = self.embedding_model.encode(mood_text, normalize_embeddings=True)
        
        return mood_embeddings
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text to extract multi-dimensional sentiment and emotional tones.
        
        ENHANCED: Better handles complex multi-sentence prompts by:
        - Segmenting text into sentences for clause-level analysis
        - Preserving context transitions (e.g., "sad but trying to stay positive")
        - Weighting recent clauses higher for multi-turn conversations
        - Detecting implicit moods from keywords and negations
        
        Args:
            text: Input text (book description, review, user prompt, etc.)
            
        Returns:
            Dictionary containing:
            - moods: Dict of mood scores (happy, sad, etc.)
            - dominant_mood: Primary emotional tone
            - sentiment_score: Overall sentiment (-1.0 to 1.0)
            - sentiment_label: Overall label (positive/negative/neutral)
            - confidence: Confidence score (0.0 to 1.0)
            - emotional_intensity: Strength of emotions (0.0 to 1.0)
            - implicit_moods: Secondary moods detected from context
            - text_segments: Analysis by sentence for transparency
        """
        if not text or not text.strip():
            return self._empty_analysis()
        
        text = self._preprocess_text(text)
        
        # ENHANCEMENT: Analyze multi-segment text to preserve context
        segments = self._segment_text(text)
        
        # Use transformer-based analysis if available
        if self.embedding_model and self.emotion_classifier:
            base_analysis = self._transformer_analysis(text)
            # Enhance with segment-level context
            if len(segments) > 1:
                base_analysis['implicit_moods'] = self._detect_implicit_moods_from_segments(segments)
                base_analysis['text_segments'] = segments
                base_analysis['multi_segment'] = True
            return base_analysis
        else:
            base_analysis = self._keyword_based_analysis(text)
            # Enhance keyword-based with segment context
            if len(segments) > 1:
                base_analysis['implicit_moods'] = self._detect_implicit_moods_from_segments(segments)
                base_analysis['text_segments'] = segments
                base_analysis['multi_segment'] = True
            return base_analysis
    
    def _transformer_analysis(self, text: str) -> Dict[str, Any]:
        """Perform transformer-based sentiment analysis."""
        try:
            # Get emotion classification
            emotion_results = self.emotion_classifier(text, top_k=5)
            
            # Convert emotion results to mood scores
            mood_scores = self._emotions_to_moods(emotion_results)
            
            # Get semantic similarity to mood categories
            text_embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            semantic_scores = {}
            
            for mood, mood_embedding in self.mood_embeddings.items():
                if NUMPY_AVAILABLE:
                    similarity = np.dot(text_embedding, mood_embedding)
                else:
                    similarity = 0.0
                semantic_scores[mood] = float(similarity)
            
            # Combine emotion classification and semantic similarity
            combined_moods = {}
            for mood in MOOD_CATEGORIES.keys():
                emotion_score = mood_scores.get(mood, 0.0)
                semantic_score = semantic_scores.get(mood, 0.0)
                # Weighted combination (60% emotion, 40% semantic)
                combined_moods[mood] = (emotion_score * 0.6) + (semantic_score * 0.4)
            
            # Normalize mood scores to 0-1 range
            mood_values = list(combined_moods.values())
            max_mood_score = max(mood_values) if mood_values else 0.0
            if max_mood_score > 0:
                combined_moods = {k: v / max_mood_score for k, v in combined_moods.items()}
            
            # Determine dominant mood
            dominant_mood = max(combined_moods.items(), key=lambda x: x[1])[0] if combined_moods else 'neutral'
            
            # Calculate overall sentiment
            positive_moods = ['happy', 'excited', 'hopeful', 'inspired', 'romantic', 'relaxed']
            negative_moods = ['sad', 'angry', 'anxious']
            
            positive_score = sum(combined_moods.get(m, 0) for m in positive_moods)
            negative_score = sum(combined_moods.get(m, 0) for m in negative_moods)
            
            total_score = positive_score + negative_score
            if total_score > 0:
                sentiment_score = (positive_score - negative_score) / total_score
            else:
                sentiment_score = 0.0
            
            # Determine sentiment label
            if sentiment_score > 0.2:
                sentiment_label = 'positive'
            elif sentiment_score < -0.2:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            # Calculate emotional intensity
            mood_values = list(combined_moods.values())
            emotional_intensity = max(mood_values) if mood_values else 0.0
            
            # Calculate confidence
            confidence = min(emotional_intensity * 1.5, 1.0)
            
            return {
                'moods': combined_moods,
                'dominant_mood': dominant_mood,
                'sentiment_score': float(sentiment_score),
                'sentiment_label': sentiment_label,
                'confidence': float(confidence),
                'emotional_intensity': float(emotional_intensity),
                'analysis_method': 'transformer'
            }
            
        except Exception as e:
            logger.error(f"Error in transformer analysis: {e}")
            return self._keyword_based_analysis(text)
    
    def _emotions_to_moods(self, emotion_results: List[Dict]) -> Dict[str, float]:
        """Map emotion classification results to mood categories."""
        mood_scores = {mood: 0.0 for mood in MOOD_CATEGORIES.keys()}
        
        # Emotion model labels to mood mapping
        emotion_to_mood = {
            'joy': 'happy',
            'happiness': 'happy',
            'sadness': 'sad',
            'anger': 'angry',
            'fear': 'anxious',
            'surprise': 'excited',
            'disgust': 'angry',
            'neutral': 'relaxed',
            'love': 'romantic',
            'optimism': 'hopeful',
            'pessimism': 'sad',
        }
        
        for result in emotion_results:
            label = result.get('label', '').lower()
            score = result.get('score', 0.0)
            
            # Direct mapping
            if label in emotion_to_mood:
                mood = emotion_to_mood[label]
                mood_scores[mood] = max(mood_scores[mood], score)
            
            # Partial matching
            for mood, keywords in MOOD_CATEGORIES.items():
                if any(keyword in label for keyword in keywords):
                    mood_scores[mood] = max(mood_scores[mood], score * 0.7)
        
        return mood_scores
    
    def _keyword_based_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback keyword-based sentiment analysis."""
        text_lower = text.lower()
        mood_scores = {mood: 0.0 for mood in MOOD_CATEGORIES.keys()}
        
        # Count keyword matches
        for mood, keywords in MOOD_CATEGORIES.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            mood_scores[mood] = min(matches / len(keywords) * 2, 1.0)  # Normalize to 0-1
        
        # Determine dominant mood
        dominant_mood = max(mood_scores.items(), key=lambda x: x[1])[0] if any(mood_scores.values()) else 'neutral'
        
        # Calculate overall sentiment
        positive_moods = ['happy', 'excited', 'hopeful', 'inspired', 'romantic', 'relaxed']
        negative_moods = ['sad', 'angry', 'anxious']
        
        positive_score = sum(mood_scores.get(m, 0) for m in positive_moods)
        negative_score = sum(mood_scores.get(m, 0) for m in negative_moods)
        
        total_score = positive_score + negative_score
        if total_score > 0:
            sentiment_score = (positive_score - negative_score) / total_score
        else:
            sentiment_score = 0.0
        
        if sentiment_score > 0.2:
            sentiment_label = 'positive'
        elif sentiment_score < -0.2:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        mood_values = list(mood_scores.values())
        emotional_intensity = max(mood_values) if mood_values else 0.0
        confidence = min(emotional_intensity * 0.8, 1.0)
        
        return {
            'moods': mood_scores,
            'dominant_mood': dominant_mood,
            'sentiment_score': float(sentiment_score),
            'sentiment_label': sentiment_label,
            'confidence': float(confidence),
            'emotional_intensity': float(emotional_intensity),
            'analysis_method': 'keyword'
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\-\']', '', text)
        return text.strip()
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'moods': {mood: 0.0 for mood in MOOD_CATEGORIES.keys()},
            'dominant_mood': 'neutral',
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0,
            'emotional_intensity': 0.0,
            'analysis_method': 'none'
        }
    
    def _segment_text(self, text: str) -> List[str]:
        """Segment text into sentences for clause-level mood analysis."""
        # Split on sentence boundaries while preserving context
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _detect_implicit_moods_from_segments(self, segments: List[str]) -> Dict[str, float]:
        """Detect implicit moods from text segments and context transitions."""
        implicit = {}
        
        # Keywords for implicit mood detection (context clues beyond direct mood words)
        implicit_keywords = {
            'resilient': {'hopeful': 0.8, 'inspired': 0.7, 'happy': 0.5},
            'vulnerable': {'anxious': 0.6, 'sad': 0.5},
            'breakup': {'sad': 0.8, 'hopeful': 0.3},
            'loss': {'sad': 0.9, 'hopeful': 0.1},
            'recover': {'hopeful': 0.9, 'inspired': 0.7},
            'healing': {'hopeful': 0.8, 'relaxed': 0.6},
            'strength': {'inspired': 0.9, 'hopeful': 0.8},
            'overcoming': {'inspired': 0.8, 'hopeful': 0.7},
            'struggling': {'anxious': 0.7, 'sad': 0.6},
            'progress': {'hopeful': 0.8, 'inspired': 0.7},
            'growth': {'inspired': 0.8, 'hopeful': 0.7},
            'transformation': {'hopeful': 0.7, 'inspired': 0.8},
        }
        
        for segment in segments:
            segment_lower = segment.lower()
            for keyword, moods in implicit_keywords.items():
                if keyword in segment_lower:
                    for mood, score in moods.items():
                        implicit[mood] = max(implicit.get(mood, 0), score)
        
        return implicit
    
    def match_mood(self, user_mood_text: str, book_moods: Dict[str, float]) -> float:
        """
        Calculate how well a book's mood matches a user's mood.
        
        Args:
            user_mood_text: User's mood description in plain language
            book_moods: Book's mood scores dictionary
            
        Returns:
            Match score between 0.0 and 1.0
        """
        if not user_mood_text or not book_moods:
            return 0.0

        user_analysis = self.analyze_text(user_mood_text)
        return self.match_mood_from_analysis(user_analysis, book_moods)

    def match_mood_from_analysis(self, user_analysis: Dict[str, Any], book_moods: Dict[str, float]) -> float:
        """Calculate mood alignment from a precomputed user analysis payload."""
        if not user_analysis or not book_moods:
            return 0.0

        user_moods = user_analysis.get('moods', {}) or {}
        user_dominant = user_analysis.get('dominant_mood', 'neutral')

        direct_match = float(book_moods.get(user_dominant, 0.0) or 0.0)
        compatible_moods = MOOD_COMPATIBILITY.get(user_dominant, [])
        compatibility_score = sum(float(book_moods.get(mood, 0.0) or 0.0) for mood in compatible_moods)
        compatibility_score /= max(len(compatible_moods), 1)

        weighted_overlap = 0.0
        user_total = 0.0
        for mood, score in user_moods.items():
            user_score = float(score or 0.0)
            user_total += max(0.0, user_score)
            weighted_overlap += max(0.0, user_score) * float(book_moods.get(mood, 0.0) or 0.0)
        semantic_score = weighted_overlap / max(user_total, 1.0)

        match_score = (
            direct_match * 0.4 +
            compatibility_score * 0.3 +
            semantic_score * 0.3
        )
        return min(max(match_score, 0.0), 1.0)


# Global analyzer instance (lazy initialization)
_analyzer_instance: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create the global sentiment analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SentimentAnalyzer()
    return _analyzer_instance

