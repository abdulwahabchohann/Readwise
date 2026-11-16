from __future__ import annotations

import json
from collections import defaultdict

from django.core.management.base import BaseCommand

from accounts.models import Book


class Command(BaseCommand):
    help = "Export the current catalog into books_dataset_5000.json for the dataset recommender."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5000)
        parser.add_argument('--output', default='books_dataset_5000.json')

    def handle(self, *args, **options):
        limit = max(1, int(options.get('limit') or 5000))
        output = str(options.get('output') or 'books_dataset_5000.json')

        books = (
            Book.objects.exclude(description__isnull=True)
            .exclude(description='')
            .prefetch_related('authors', 'genres')
            .order_by('?')[:limit]
        )

        payload = []
        genre_counts = defaultdict(int)
        language_counts = defaultdict(int)
        for book in books:
            genres = [genre.name for genre in book.genres.all()[:3]] or ['General']
            for genre in genres:
                genre_counts[genre] += 1
            if book.language:
                language_counts[book.language] += 1

            payload.append(
                {
                    'book_id': str(book.id),
                    'title': book.title,
                    'author': ', '.join(author.full_name for author in book.authors.all()[:3]) or 'Unknown',
                    'genres': genres,
                    'description': book.description,
                    'published_year': book.published_year,
                    'average_rating': float(book.average_rating) if book.average_rating else None,
                    'ratings_count': book.ratings_count,
                    'language': book.language,
                    'sentiment_score': float(book.sentiment_score) if book.sentiment_score is not None else None,
                    'mood_scores': book.mood_scores or {},
                    'dominant_mood': book.dominant_mood,
                    'emotional_intensity': float(book.emotional_intensity) if book.emotional_intensity is not None else None,
                    'page_count': book.page_count,
                    'cover_image': book.cover_image or '',
                    'isbn_10': book.isbn_10 or '',
                    'isbn_13': book.isbn_13 or '',
                    'reviews': [],
                }
            )

        with open(output, 'w', encoding='utf-8') as outfile:
            json.dump(payload, outfile, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"Exported {len(payload)} books to {output}"))
        self.stdout.write(f"Top genres: {dict(sorted(genre_counts.items(), key=lambda item: item[1], reverse=True)[:5])}")
        self.stdout.write(
            f"Languages: {dict(sorted(language_counts.items(), key=lambda item: item[1], reverse=True)[:5])}"
        )
