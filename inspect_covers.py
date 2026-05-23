import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readwise.settings')
django.setup()

from accounts.models import Book

books = Book.objects.all().values('id', 'title', 'cover_image')[:10]
print(f"Total books: {Book.objects.count()}")
print("\nFirst 10 books:")
for book in books:
    print(f"ID: {book['id']}, Title: {book['title'][:50]}, Cover: {book['cover_image'][:50] if book['cover_image'] else 'EMPTY'}")

# Count books by cover_image status
empty_covers = Book.objects.filter(cover_image='').count()
null_covers = Book.objects.filter(cover_image__isnull=True).count()
with_covers = Book.objects.exclude(cover_image='').exclude(cover_image__isnull=True).count()

print(f"\nCover statistics:")
print(f"  Empty string: {empty_covers}")
print(f"  NULL: {null_covers}")
print(f"  With cover: {with_covers}")
