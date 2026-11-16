from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Any

from django.db.models import Q
from django.urls import reverse

from accounts.models import Book
from accounts.services.cover_utils import PLACEHOLDER_COVER_URL, normalize_cover

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover - exercised when optional dependency is absent
    fuzz = None


WORD_RE = re.compile(r'[a-z0-9]+')
STOPWORDS = {
    'a',
    'about',
    'after',
    'am',
    'and',
    'any',
    'are',
    'book',
    'books',
    'can',
    'for',
    'give',
    'had',
    'how',
    'i',
    'in',
    'is',
    'it',
    'me',
    'my',
    'need',
    'on',
    'or',
    'read',
    'suggest',
    'that',
    'the',
    'to',
    'want',
    'with',
}


def normalize_text(value: Any) -> str:
    return ' '.join(WORD_RE.findall(str(value or '').casefold()))


def tokenize(value: Any) -> list[str]:
    return [token for token in WORD_RE.findall(str(value or '').casefold()) if token not in STOPWORDS]


def prompt_fingerprint(prompt: str) -> str:
    tokens = tokenize(prompt)
    compact = ' '.join(tokens[:60]) or normalize_text(prompt)
    digest = hashlib.sha256(compact.encode('utf-8')).hexdigest()
    return digest[:32]


def _similarity(left: str, right: str) -> int:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0
    if fuzz is not None:
        return int(fuzz.token_set_ratio(left_norm, right_norm))
    return int(SequenceMatcher(None, left_norm, right_norm).ratio() * 100)


def _author_display(book: Book) -> str:
    authors = [author.full_name for author in book.authors.all()]
    return ', '.join(authors) if authors else 'Author unknown'


def _genre_display(book: Book) -> str:
    genres = [genre.name for genre in book.genres.all()[:3]]
    return ', '.join(genres) if genres else 'General'


def _book_url(book: Book) -> str:
    try:
        return reverse('book_detail', args=[book.slug])
    except Exception:
        return ''


def _candidate_query(title: str, author: str) -> Q:
    query = Q()
    for token in tokenize(title)[:8]:
        if len(token) >= 3:
            query |= Q(title__icontains=token)
    for token in tokenize(author)[:5]:
        if len(token) >= 3:
            query |= Q(authors__full_name__icontains=token)
    return query


def find_local_book(title: str, author: str = '', threshold: int = 82) -> tuple[Book | None, int]:
    title = (title or '').strip()
    author = (author or '').strip()
    if not title:
        return None, 0

    candidate_q = _candidate_query(title, author)
    if not candidate_q:
        return None, 0

    candidates = (
        Book.objects.filter(candidate_q)
        .distinct()
        .prefetch_related('authors', 'genres')
        .order_by('-average_rating', '-ratings_count', 'title')[:500]
    )

    best_book: Book | None = None
    best_score = 0
    best_title_score = 0
    for book in candidates:
        title_score = _similarity(title, book.title)
        author_score = 75
        if author:
            author_score = max((_similarity(author, item.full_name) for item in book.authors.all()), default=0)
        combined = int(round(title_score * 0.78 + author_score * 0.22))
        if combined > best_score:
            best_score = combined
            best_title_score = title_score
            best_book = book

    if best_book and (best_score >= threshold or best_title_score >= 91):
        return best_book, best_score
    return None, best_score


def _clamp_score(value: Any, fallback: int) -> int:
    try:
        score = int(float(value))
    except (TypeError, ValueError):
        score = fallback
    return max(0, min(score, 100))


def _normalize_suggestion(raw_item: dict[str, Any], rank: int) -> dict[str, Any]:
    title = str(raw_item.get('title') or '').strip()
    return {
        'rank': rank,
        'title': title or 'Untitled',
        'author': str(raw_item.get('author') or 'Author unknown').strip() or 'Author unknown',
        'reason': str(raw_item.get('reason') or raw_item.get('recommendation_reason') or '').strip()
        or 'This book matches the intent and mood in your request.',
        'mood_tag': str(raw_item.get('mood_tag') or raw_item.get('dominant_mood') or 'thoughtful').strip().lower()
        or 'thoughtful',
        'match_score': _clamp_score(raw_item.get('match_score'), max(70, 96 - rank * 3)),
        'genre': str(raw_item.get('genre') or 'General').strip() or 'General',
        'difficulty': str(raw_item.get('difficulty') or 'Intermediate').strip().title() or 'Intermediate',
        'source': str(raw_item.get('source') or 'llm').strip() or 'llm',
    }


def merge_with_library(suggestions: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    for raw_item in suggestions:
        if not isinstance(raw_item, dict):
            continue
        item = _normalize_suggestion(raw_item, rank=len(merged) + 1)
        title_key = normalize_text(item['title'])
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        local_book, local_score = find_local_book(item['title'], item['author'])
        if local_book:
            item.update(
                {
                    'book_id': local_book.pk,
                    'book_url': _book_url(local_book),
                    'cover_image': normalize_cover(local_book.cover_image or PLACEHOLDER_COVER_URL),
                    'in_library': True,
                    'library_match_score': local_score,
                    'library_title': local_book.title,
                    'library_author': _author_display(local_book),
                    'library_genre': _genre_display(local_book),
                }
            )
            if item['author'] == 'Author unknown':
                item['author'] = item['library_author']
            if item['genre'] == 'General':
                item['genre'] = item['library_genre']
        else:
            item.update(
                {
                    'book_id': None,
                    'book_url': '',
                    'cover_image': PLACEHOLDER_COVER_URL,
                    'in_library': False,
                    'library_match_score': local_score,
                    'library_title': '',
                    'library_author': '',
                    'library_genre': '',
                }
            )

        merged.append(item)
        if len(merged) >= limit:
            break

    for index, item in enumerate(merged, start=1):
        item['rank'] = index
    return merged


FALLBACK_CATALOG: dict[str, list[dict[str, str]]] = {
    'finance': [
        {'title': 'The Psychology of Money', 'author': 'Morgan Housel', 'genre': 'Finance', 'difficulty': 'Beginner'},
        {'title': 'I Will Teach You To Be Rich', 'author': 'Ramit Sethi', 'genre': 'Finance', 'difficulty': 'Beginner'},
        {'title': 'Rich Dad Poor Dad', 'author': 'Robert T. Kiyosaki', 'genre': 'Finance', 'difficulty': 'Beginner'},
        {'title': 'The Intelligent Investor', 'author': 'Benjamin Graham', 'genre': 'Finance', 'difficulty': 'Advanced'},
        {'title': 'Your Money or Your Life', 'author': 'Vicki Robin', 'genre': 'Finance', 'difficulty': 'Intermediate'},
    ],
    'crypto': [
        {'title': 'The Bitcoin Standard', 'author': 'Saifedean Ammous', 'genre': 'Crypto / Economics', 'difficulty': 'Intermediate'},
        {'title': 'Digital Gold', 'author': 'Nathaniel Popper', 'genre': 'Crypto / History', 'difficulty': 'Beginner'},
        {'title': 'Mastering Bitcoin', 'author': 'Andreas M. Antonopoulos', 'genre': 'Technology', 'difficulty': 'Advanced'},
        {'title': 'Cryptoassets', 'author': 'Chris Burniske and Jack Tatar', 'genre': 'Investing', 'difficulty': 'Intermediate'},
        {'title': 'Blockchain Basics', 'author': 'Daniel Drescher', 'genre': 'Technology', 'difficulty': 'Beginner'},
    ],
    'relationship': [
        {'title': 'Nonviolent Communication', 'author': 'Marshall B. Rosenberg', 'genre': 'Relationships', 'difficulty': 'Beginner'},
        {'title': 'The Seven Principles for Making Marriage Work', 'author': 'John M. Gottman', 'genre': 'Relationships', 'difficulty': 'Intermediate'},
        {'title': 'Hold Me Tight', 'author': 'Sue Johnson', 'genre': 'Relationships', 'difficulty': 'Intermediate'},
        {'title': 'Difficult Conversations', 'author': 'Douglas Stone, Bruce Patton, and Sheila Heen', 'genre': 'Communication', 'difficulty': 'Intermediate'},
        {'title': 'Emotional Intelligence', 'author': 'Daniel Goleman', 'genre': 'Psychology', 'difficulty': 'Intermediate'},
    ],
    'comfort': [
        {'title': 'The Comfort Book', 'author': 'Matt Haig', 'genre': 'Self-help', 'difficulty': 'Beginner'},
        {'title': 'The Midnight Library', 'author': 'Matt Haig', 'genre': 'Fiction', 'difficulty': 'Beginner'},
        {'title': 'The Little Prince', 'author': 'Antoine de Saint-Exupery', 'genre': 'Fiction', 'difficulty': 'Beginner'},
        {'title': "Man's Search for Meaning", 'author': 'Viktor E. Frankl', 'genre': 'Philosophy', 'difficulty': 'Intermediate'},
        {'title': 'The Book of Joy', 'author': 'Dalai Lama and Desmond Tutu', 'genre': 'Spirituality', 'difficulty': 'Beginner'},
    ],
    'mba': [
        {'title': 'The Personal MBA', 'author': 'Josh Kaufman', 'genre': 'Business', 'difficulty': 'Beginner'},
        {'title': 'Good Strategy Bad Strategy', 'author': 'Richard Rumelt', 'genre': 'Business', 'difficulty': 'Intermediate'},
        {'title': 'Competitive Strategy', 'author': 'Michael E. Porter', 'genre': 'Business', 'difficulty': 'Advanced'},
        {'title': 'The Lean Startup', 'author': 'Eric Ries', 'genre': 'Business', 'difficulty': 'Intermediate'},
        {'title': 'Blue Ocean Strategy', 'author': 'W. Chan Kim and Renee Mauborgne', 'genre': 'Business', 'difficulty': 'Intermediate'},
    ],
    'medicine': [
        {'title': 'Guyton and Hall Textbook of Medical Physiology', 'author': 'John E. Hall', 'genre': 'Medicine', 'difficulty': 'Advanced'},
        {'title': "Harrison's Principles of Internal Medicine", 'author': 'J. Larry Jameson', 'genre': 'Medicine', 'difficulty': 'Advanced'},
        {'title': 'Robbins Basic Pathology', 'author': 'Vinay Kumar', 'genre': 'Medicine', 'difficulty': 'Advanced'},
        {'title': "Gray's Anatomy for Students", 'author': 'Richard L. Drake', 'genre': 'Medicine', 'difficulty': 'Intermediate'},
        {'title': 'First Aid for the USMLE Step 1', 'author': 'Tao Le and Vikas Bhushan', 'genre': 'Medicine', 'difficulty': 'Advanced'},
    ],
    'software': [
        {'title': 'The Pragmatic Programmer', 'author': 'David Thomas and Andrew Hunt', 'genre': 'Software Engineering', 'difficulty': 'Intermediate'},
        {'title': 'Clean Code', 'author': 'Robert C. Martin', 'genre': 'Software Engineering', 'difficulty': 'Intermediate'},
        {'title': 'Designing Data-Intensive Applications', 'author': 'Martin Kleppmann', 'genre': 'Software Engineering', 'difficulty': 'Advanced'},
        {'title': 'Code Complete', 'author': 'Steve McConnell', 'genre': 'Software Engineering', 'difficulty': 'Intermediate'},
        {'title': 'Staff Engineer', 'author': 'Will Larson', 'genre': 'Career', 'difficulty': 'Intermediate'},
    ],
    'aeronautical': [
        {'title': 'Fundamentals of Aerodynamics', 'author': 'John D. Anderson Jr.', 'genre': 'Engineering', 'difficulty': 'Advanced'},
        {'title': 'Introduction to Flight', 'author': 'John D. Anderson Jr.', 'genre': 'Engineering', 'difficulty': 'Intermediate'},
        {'title': 'Aircraft Design', 'author': 'Daniel P. Raymer', 'genre': 'Engineering', 'difficulty': 'Advanced'},
        {'title': 'Aerodynamics for Engineers', 'author': 'John J. Bertin and Russell M. Cummings', 'genre': 'Engineering', 'difficulty': 'Advanced'},
        {'title': 'Flight Stability and Automatic Control', 'author': 'Robert C. Nelson', 'genre': 'Engineering', 'difficulty': 'Advanced'},
    ],
    'mystery': [
        {'title': 'The Thursday Murder Club', 'author': 'Richard Osman', 'genre': 'Mystery', 'difficulty': 'Beginner'},
        {'title': 'And Then There Were None', 'author': 'Agatha Christie', 'genre': 'Mystery', 'difficulty': 'Beginner'},
        {'title': 'The Girl with the Dragon Tattoo', 'author': 'Stieg Larsson', 'genre': 'Mystery', 'difficulty': 'Intermediate'},
        {'title': 'The Big Sleep', 'author': 'Raymond Chandler', 'genre': 'Mystery', 'difficulty': 'Intermediate'},
        {'title': 'Gone Girl', 'author': 'Gillian Flynn', 'genre': 'Thriller', 'difficulty': 'Intermediate'},
    ],
    'fiction': [
        {'title': 'Piranesi', 'author': 'Susanna Clarke', 'genre': 'Fiction', 'difficulty': 'Intermediate'},
        {'title': 'The Night Circus', 'author': 'Erin Morgenstern', 'genre': 'Fiction', 'difficulty': 'Intermediate'},
        {'title': 'Station Eleven', 'author': 'Emily St. John Mandel', 'genre': 'Fiction', 'difficulty': 'Intermediate'},
        {'title': 'Project Hail Mary', 'author': 'Andy Weir', 'genre': 'Science Fiction', 'difficulty': 'Beginner'},
        {'title': 'The House in the Cerulean Sea', 'author': 'TJ Klune', 'genre': 'Fiction', 'difficulty': 'Beginner'},
    ],
    'short': [
        {'title': 'Animal Farm', 'author': 'George Orwell', 'genre': 'Fiction', 'difficulty': 'Beginner'},
        {'title': 'Of Mice and Men', 'author': 'John Steinbeck', 'genre': 'Fiction', 'difficulty': 'Beginner'},
        {'title': 'The Old Man and the Sea', 'author': 'Ernest Hemingway', 'genre': 'Fiction', 'difficulty': 'Beginner'},
        {'title': 'We Should All Be Feminists', 'author': 'Chimamanda Ngozi Adichie', 'genre': 'Essays', 'difficulty': 'Beginner'},
        {'title': 'The Death of Ivan Ilyich', 'author': 'Leo Tolstoy', 'genre': 'Fiction', 'difficulty': 'Intermediate'},
    ],
    'thinking': [
        {'title': 'Thinking, Fast and Slow', 'author': 'Daniel Kahneman', 'genre': 'Psychology', 'difficulty': 'Advanced'},
        {'title': 'Meditations', 'author': 'Marcus Aurelius', 'genre': 'Philosophy', 'difficulty': 'Intermediate'},
        {'title': 'The Art of Thinking Clearly', 'author': 'Rolf Dobelli', 'genre': 'Psychology', 'difficulty': 'Beginner'},
        {'title': 'Godel, Escher, Bach', 'author': 'Douglas Hofstadter', 'genre': 'Cognitive Science', 'difficulty': 'Advanced'},
        {'title': 'The Beginning of Infinity', 'author': 'David Deutsch', 'genre': 'Science', 'difficulty': 'Advanced'},
    ],
}


def _catalog_key(prompt: str) -> str:
    text = normalize_text(prompt)
    if any(token in text for token in ('wife', 'husband', 'marriage', 'family', 'fight', 'conflict', 'relationship')):
        return 'relationship'
    if any(token in text for token in ('sad', 'lonely', 'bad', 'depressed', 'comfort', 'happy', 'uplift')):
        return 'comfort'
    if any(token in text for token in ('crypto', 'bitcoin', 'blockchain')):
        return 'crypto'
    if any(token in text for token in ('finance', 'money', 'invest', 'wealth', 'saving')):
        return 'finance'
    if any(token in text for token in ('mba', 'business school', 'management')):
        return 'mba'
    if any(token in text for token in ('mbbs', 'medicine', 'medical', 'doctor')):
        return 'medicine'
    if any(token in text for token in ('software', 'programming', 'developer', 'coding', 'engineer career')):
        return 'software'
    if any(token in text for token in ('aeronautical', 'aerospace', 'aircraft', 'flight')):
        return 'aeronautical'
    if any(token in text for token in ('mystery', 'detective', 'thriller')):
        return 'mystery'
    if any(token in text for token in ('fiction', 'fictional', 'novel', 'escape')):
        return 'fiction'
    if any(token in text for token in ('short', 'sitting', 'quick')):
        return 'short'
    if any(token in text for token in ('deep', 'thinking', 'philosophy', 'mind')):
        return 'thinking'
    return 'thinking'


def _fallback_reason(prompt: str, genre: str, difficulty: str, key: str) -> tuple[str, str]:
    if key == 'relationship':
        return (
            'empathetic',
            'This is a practical, non-judgmental match for the conflict or relationship stress in your prompt. It can help you slow the moment down, understand the other person better, and choose calmer words.',
        )
    if key == 'comfort':
        return (
            'comforting',
            'This is a gentle fit for feeling low, lonely, or emotionally tired. It offers warmth and perspective without demanding too much from you right away.',
        )
    if key in {'finance', 'crypto', 'mba', 'medicine', 'software', 'aeronautical'}:
        return (
            'educational',
            f'This is a strong {difficulty.lower()} level match for the learning goal in your prompt. It gives you a clearer path into {genre.lower()} without relying on keyword overlap alone.',
        )
    if key in {'fiction', 'mystery', 'short'}:
        return (
            'absorbing',
            'This matches the reading format or genre you asked for and gives you a focused reading experience. It is a good pick when you want the book to carry your attention quickly.',
        )
    return (
        'mind-expanding',
        'This fits a reflective, intellectually curious prompt. It should challenge your thinking while still giving you memorable ideas to sit with after reading.',
    )


def _search_local_prompt_matches(prompt: str, limit: int) -> list[dict[str, Any]]:
    tokens = [token for token in tokenize(prompt) if len(token) >= 3][:10]
    if not tokens:
        return []

    query = Q()
    for token in tokens:
        query |= Q(title__icontains=token)
        query |= Q(subtitle__icontains=token)
        query |= Q(description__icontains=token)
        query |= Q(authors__full_name__icontains=token)
        query |= Q(genres__name__icontains=token)

    candidates = (
        Book.objects.filter(query)
        .distinct()
        .prefetch_related('authors', 'genres')
        .order_by('-average_rating', '-ratings_count', 'title')[:160]
    )
    prompt_tokens = set(tokens)
    scored: list[tuple[int, Book]] = []
    for book in candidates:
        text = ' '.join(
            [
                book.title or '',
                book.subtitle or '',
                book.description or '',
                _author_display(book),
                _genre_display(book),
            ]
        )
        text_tokens = set(tokenize(text))
        overlap = len(prompt_tokens & text_tokens) * 12
        semantic = _similarity(prompt, text[:1200])
        score = min(100, int(semantic * 0.55 + overlap))
        scored.append((score, book))

    scored.sort(
        key=lambda item: (
            -item[0],
            -(float(item[1].average_rating) if item[1].average_rating else 0.0),
            -(item[1].ratings_count or 0),
            item[1].title,
        )
    )

    results: list[dict[str, Any]] = []
    for score, book in scored[:limit]:
        genre = _genre_display(book)
        results.append(
            {
                'title': book.title,
                'author': _author_display(book),
                'genre': genre,
                'difficulty': 'Intermediate',
                'mood_tag': 'relevant',
                'match_score': max(65, min(score, 95)),
                'reason': 'This local ReadWise book shares meaningful topic, author, or genre overlap with your prompt, so it is a good database-backed fallback match.',
                'source': 'local_keyword_fallback',
            }
        )
    return results


def build_keyword_fallback_suggestions(user_prompt: str, limit: int = 5) -> list[dict[str, Any]]:
    prompt = (user_prompt or '').strip()
    key = _catalog_key(prompt)
    suggestions = _search_local_prompt_matches(prompt, limit=limit)
    seen_titles = {normalize_text(item.get('title')) for item in suggestions}

    for raw_item in FALLBACK_CATALOG[key]:
        if len(suggestions) >= limit:
            break
        if normalize_text(raw_item['title']) in seen_titles:
            continue
        mood_tag, reason = _fallback_reason(prompt, raw_item['genre'], raw_item['difficulty'], key)
        suggestions.append(
            {
                **raw_item,
                'reason': reason,
                'mood_tag': mood_tag,
                'match_score': max(72, 96 - len(suggestions) * 4),
                'source': 'keyword_fallback',
            }
        )

    for index, item in enumerate(suggestions[:limit], start=1):
        item['rank'] = index
    return suggestions[:limit]
