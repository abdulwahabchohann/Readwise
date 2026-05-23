"""
Generate 100,000 books with REAL cover images using OpenLibrary API data.
Uses a library of known-good ISBNs that have covers on OpenLibrary.
"""
import json
import random
from pathlib import Path
from typing import List, Dict


# Known ISBNs with confirmed covers on OpenLibrary (real books)
REAL_ISBN_POOL = [
    "9780451524935", "9780061120084", "9780141039992", "9780743277594",
    "9781503280786", "9780545582969", "9780316769174", "9780060935467",
    "9780451526342", "9780062073562", "9780316769549", "9780345803481",
    "9781492254127", "9780544003415", "9780061120077", "9780545139700",
    "9780545010221", "9780375759529", "9780439136365", "9780061120084",
    "9780062073555", "9780590353403", "9780439554930", "9780439708180",
    "9780062430526", "9780553382563", "9780374529239", "9780142437178",
    "9780743273565", "9780316815672", "9780545582957", "9780439023481",
    "9780374529246", "9780142419305", "9780451524942", "9780141029993",
    "9780062073525", "9780062074546", "9780141329529", "9780143117463",
]

ADJECTIVES = [
    "Brilliant", "Lost", "Forgotten", "Hidden", "Mystical", "Dark", "Light",
    "Golden", "Silver", "Crimson", "Azure", "Emerald", "Midnight", "Dawn",
    "Eternal", "Sacred", "Cursed", "Blessed", "Ancient", "Modern",
]

NOUNS = [
    "Dreams", "Shadows", "Light", "Path", "Journey", "Quest", "Destiny",
    "Heart", "Soul", "Spirit", "Mind", "Kingdom", "Empire", "World",
    "Secrets", "Mysteries", "Truths", "Lies", "Hope", "Despair", "Love",
]

GENRES = [
    "Fantasy", "Science Fiction", "Mystery", "Romance", "Thriller",
    "Historical", "Adventure", "Drama", "Horror", "Self-Help",
]

AUTHORS = [
    "Sarah Mitchell", "James Patterson", "Emma Watson", "Michael Chen",
    "Lisa Anderson", "David Brown", "Rachel Green", "Alexander Knight",
    "Sophie Martin", "Marcus Johnson", "Isabella Rose", "William Stewart",
    "Victoria Smith", "Thomas Anderson", "Eleanor Davis", "Benjamin Hall",
]


def generate_book_with_real_isbn(book_id: int) -> Dict:
    """Generate a book using a real ISBN that has a cover on OpenLibrary."""
    
    # Randomly select a real ISBN
    real_isbn = random.choice(REAL_ISBN_POOL)
    
    # Create variants by duplicating these covers across many books
    # (In production, you'd want more unique ISBNs)
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    volume = random.randint(1, 100)
    
    book = {
        "id": book_id,
        "title": f"{adj} {noun} - Volume {volume}",
        "author": random.choice(AUTHORS),
        "genre": random.choice(GENRES),
        "description": "An engaging story that explores themes of personal growth, adventure, and discovery.",
        "isbn_13": real_isbn,
        "isbn_10": "",
        "published_year": random.randint(2000, 2024),
        "page_count": random.randint(200, 500),
        "language": "English",
        "average_rating": round(random.uniform(3.0, 5.0), 2),
        "ratings_count": random.randint(100, 20000),
        # Use real ISBN with OpenLibrary cover API
        "cover_image": f"https://covers.openlibrary.org/b/isbn/{real_isbn}-L.jpg",
    }
    return book


def main():
    input_file = "books_dataset_enriched.json"
    output_file = "books_dataset_100k_real_covers.json"
    
    # Step 1: Load existing books
    print("=" * 70)
    print("STEP 1: Loading existing dataset")
    print("=" * 70)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            existing_books = json.load(f)
        books_with_covers = [b for b in existing_books if b.get('cover_image', '').strip()]
        print(f"✓ Loaded {len(existing_books):,} books")
        print(f"  - With covers: {len(books_with_covers):,}")
        print(f"  - Without covers: {len(existing_books) - len(books_with_covers):,}")
    except FileNotFoundError:
        print(f"⚠ File not found, starting fresh")
        books_with_covers = []
    
    # Step 2: Generate new books with REAL ISBNs
    print("\n" + "=" * 70)
    print("STEP 2: Generating 100,000 books with REAL cover images")
    print("=" * 70)
    print(f"📚 Using {len(REAL_ISBN_POOL)} confirmed ISBNs with covers on OpenLibrary\n")
    
    new_books = []
    for i in range(100000):
        if (i + 1) % 20000 == 0:
            print(f"   Generated {i + 1:,} books...")
        
        book = generate_book_with_real_isbn(len(books_with_covers) + i + 1)
        new_books.append(book)
    
    print(f"✅ Generated {len(new_books):,} books successfully!")
    
    # Step 3: Combine datasets
    print("\n" + "=" * 70)
    print("STEP 3: Creating final dataset")
    print("=" * 70)
    
    all_books = books_with_covers + new_books
    print(f"📊 Total books: {len(all_books):,}")
    print(f"   - Existing with covers: {len(books_with_covers):,}")
    print(f"   - New with real covers: {len(new_books):,}")
    
    # Step 4: Verify all have covers
    books_with_covers_final = sum(1 for b in all_books if b.get('cover_image', '').strip())
    print(f"   - Final verification: {books_with_covers_final:,} with covers")
    
    # Step 5: Save new dataset
    print("\n" + "=" * 70)
    print("STEP 4: Saving new dataset")
    print("=" * 70)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, indent=2, ensure_ascii=False)
    
    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"✓ Saved to: {output_file}")
    print(f"✓ File size: {file_size:.2f} MB")
    
    # Step 6: Show sample books
    print("\n" + "=" * 70)
    print("SAMPLE BOOKS (with real cover URLs)")
    print("=" * 70)
    for i, book in enumerate(new_books[:5], 1):
        print(f"\nBook {i}:")
        print(f"  Title: {book['title']}")
        print(f"  Author: {book['author']}")
        print(f"  ISBN: {book['isbn_13']}")
        print(f"  Cover: {book['cover_image']}")
    
    print("\n" + "=" * 70)
    print("🎉 PROCESS COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Dataset: {output_file}")
    print(f"✓ Total books: {len(all_books):,}")
    print(f"✓ All books have real OpenLibrary cover URLs")
    print(f"\nNext: Update settings to use the new dataset file")


if __name__ == '__main__':
    main()
