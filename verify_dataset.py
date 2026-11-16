import json
import time
from pathlib import Path

# Check file exists
dataset_file = Path('books_dataset_100k_with_covers.json')
if not dataset_file.exists():
    print(f"Error: {dataset_file} not found.")
    exit(1)
    
print(f"File exists: {dataset_file.exists()}")
print(f"File size: {dataset_file.stat().st_size / 1024 / 1024:.2f} MB")

# Load and test
print("\nLoading dataset...")
start = time.time()
with open(dataset_file) as f:
    books = json.load(f)
elapsed = time.time() - start

print(f"Loaded in {elapsed:.2f}s")
print(f"Total books: {len(books):,}")
print(f"\nFirst 3 books:")
for i, book in enumerate(books[:3], 1):
    cover = book.get('cover_image', '')[:50]
    print(f"  {i}. {book.get('title')[:40]}")
    print(f"     Cover: {cover}...")

# Check all have covers
books_with_covers = sum(1 for b in books if b.get('cover_image', '').strip())
print(f"\nBooks with covers: {books_with_covers:,}/{len(books):,}")
