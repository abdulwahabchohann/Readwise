from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Alias for analyze_book_sentiments to make metadata backfill explicit."

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=50)
        parser.add_argument('--book-id', type=int)
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--limit', type=int)

    def handle(self, *args, **options):
        call_command(
            'analyze_book_sentiments',
            batch_size=options.get('batch_size') or 50,
            book_id=options.get('book_id'),
            force=bool(options.get('force')),
            limit=options.get('limit'),
        )
