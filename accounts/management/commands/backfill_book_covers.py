from __future__ import annotations

from django.core.management.base import BaseCommand

from accounts.models import Book
from accounts.services.cover_utils import is_usable_cover_url
from accounts.services.google_books import GoogleBooksError, search_google_books


class Command(BaseCommand):
    help = "Backfill invalid or missing book covers using ISBN-first fallbacks."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Optional max number of books to process.')
        parser.add_argument('--force', action='store_true', help='Re-evaluate books even if they already have a usable cover.')
        parser.add_argument(
            '--allow-google',
            action='store_true',
            help='Use Google Books as a slower title/author fallback when no ISBN-based cover is available.',
        )
        parser.add_argument('--dry-run', action='store_true', help='Show planned updates without writing them.')

    def handle(self, *args, **options):
        queryset = Book.objects.prefetch_related('authors').order_by('id')
        limit = max(0, int(options.get('limit') or 0))
        force = bool(options.get('force'))
        allow_google = bool(options.get('allow_google'))
        dry_run = bool(options.get('dry_run'))

        processed = 0
        updated = 0
        unchanged = 0

        for book in queryset.iterator(chunk_size=100):
            if limit and processed >= limit:
                break
            processed += 1

            if not force and is_usable_cover_url(book.cover_image):
                unchanged += 1
                continue

            replacement = self._resolve_cover(book, allow_google=allow_google)
            if replacement == (book.cover_image or ''):
                unchanged += 1
                continue

            updated += 1
            self.stdout.write(f"{book.id}: {book.title} -> {replacement or '(blank)'}")
            if not dry_run:
                book.cover_image = replacement
                book.save(update_fields=['cover_image'])

        self.stdout.write(
            self.style.SUCCESS(
                f"Cover backfill complete. processed={processed} updated={updated} unchanged={unchanged} dry_run={dry_run}"
            )
        )

    def _resolve_cover(self, book: Book, *, allow_google: bool) -> str:
        for ident in (book.isbn_13, book.isbn_10):
            clean = (ident or '').replace('-', '').strip()
            if clean:
                return f"https://covers.openlibrary.org/b/isbn/{clean}-L.jpg"

        if not allow_google:
            return ''

        query = " ".join(part for part in [book.title, book.primary_author()] if part)
        if not query:
            return ''

        try:
            results = search_google_books(query, max_results=1, language='en')
        except GoogleBooksError:
            return ''

        if not results:
            return ''
        return results[0].thumbnail or ''
