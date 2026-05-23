"""
Management command to remove books without cover images from the database.
"""
from django.core.management.base import BaseCommand
from accounts.models import Book


class Command(BaseCommand):
    help = 'Remove books that have no cover images from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        # Find books with no cover image
        books_without_covers = Book.objects.filter(cover_image='')
        count = books_without_covers.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ No books without cover images found.'))
            return

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(f'🔍 DRY RUN: Would delete {count} books without covers:\n')
            )
            for book in books_without_covers[:10]:
                self.stdout.write(f'  - {book.title} (ID: {book.id})')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
            return

        # Show what will be deleted
        self.stdout.write(
            self.style.WARNING(f'⚠️  Deleting {count} books without cover images...\n')
        )
        for book in books_without_covers[:5]:
            self.stdout.write(f'  - {book.title} (ID: {book.id})')
        if count > 5:
            self.stdout.write(f'  ... and {count - 5} more')

        # Delete the books
        deleted_count, _ = books_without_covers.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Successfully deleted {deleted_count} books without covers!')
        )
