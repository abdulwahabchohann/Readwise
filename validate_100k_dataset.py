"""
Comprehensive validation script for books_dataset_100k_with_covers.json
Verifies: file size, book count, and cover URL validity
"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter

def validate_dataset():
    file_path = Path('books_dataset_100k_with_covers.json')
    
    # 1. Check file exists
    print("=" * 70)
    print("VALIDATION: books_dataset_100k_with_covers.json")
    print("=" * 70)
    
    if not file_path.exists():
        print("❌ FAILED: File does not exist")
        return False
    
    print("✓ File exists")
    
    # 2. Check file size
    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    print(f"\n📊 FILE SIZE:")
    print(f"   Size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
    if 48 <= file_size_mb <= 50:
        print(f"   ✓ Within expected range (48-50 MB)")
    else:
        print(f"   ⚠ Outside expected range (48-50 MB)")
    
    # 3. Load and parse JSON
    print(f"\n📂 LOADING JSON FILE...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    print(f"   ✓ Successfully loaded JSON")
    
    # 4. Check book count
    book_count = len(books)
    print(f"\n📚 BOOK COUNT:")
    print(f"   Total books: {book_count:,}")
    if book_count == 100000:
        print(f"   ✓ Exact count: 100,000 books")
    else:
        print(f"   ⚠ Expected 100,000, got {book_count:,}")
    
    # 5. Validate cover URLs
    print(f"\n🔗 COVER URL VALIDATION:")
    
    books_with_covers = 0
    books_without_covers = 0
    invalid_cover_urls = []
    valid_cover_urls = 0
    cover_url_patterns = Counter()
    
    for idx, book in enumerate(books):
        cover_url = book.get('cover_image', '').strip()
        
        if not cover_url:
            books_without_covers += 1
            if len(invalid_cover_urls) < 5:  # Collect first 5 examples
                invalid_cover_urls.append({
                    'id': book.get('id'),
                    'title': book.get('title'),
                    'reason': 'Missing cover_image'
                })
        else:
            books_with_covers += 1
            # Validate URL format
            if cover_url.startswith('https://covers.openlibrary.org/'):
                valid_cover_urls += 1
            else:
                if len(invalid_cover_urls) < 5:
                    invalid_cover_urls.append({
                        'id': book.get('id'),
                        'title': book.get('title'),
                        'cover_url': cover_url,
                        'reason': 'Invalid URL domain'
                    })
            
            # Extract URL pattern
            parsed = urlparse(cover_url)
            domain = parsed.netloc
            cover_url_patterns[domain] += 1
    
    print(f"   Books with covers: {books_with_covers:,}/{book_count:,}")
    print(f"   Books without covers: {books_without_covers:,}")
    print(f"   Valid OpenLibrary URLs: {valid_cover_urls:,}")
    
    if books_without_covers == 0 and valid_cover_urls == book_count:
        print(f"   ✓ All books have valid cover URLs")
    else:
        print(f"   ⚠ Some books have invalid or missing URLs")
    
    # Show URL pattern distribution
    print(f"\n   Cover URL Patterns:")
    for domain, count in cover_url_patterns.most_common(5):
        print(f"     - {domain}: {count:,}")
    
    # 6. Sample books with details
    print(f"\n📖 SAMPLE BOOKS (First 5):")
    for idx, book in enumerate(books[:5], 1):
        print(f"\n   Book {idx}:")
        print(f"      ID: {book.get('id')}")
        print(f"      Title: {book.get('title')}")
        print(f"      Author: {book.get('author')}")
        print(f"      Genre: {book.get('genre')}")
        print(f"      ISBN-13: {book.get('isbn_13')}")
        print(f"      Published: {book.get('published_year')}")
        print(f"      Rating: {book.get('average_rating')}/5 ({book.get('ratings_count')} votes)")
        cover_url = book.get('cover_image', '')[:60]
        print(f"      Cover: {cover_url}...")
    
    # 7. Show examples of books without covers (if any)
    if invalid_cover_urls:
        print(f"\n⚠️  BOOKS WITH INVALID/MISSING COVERS (First 5):")
        for item in invalid_cover_urls[:5]:
            print(f"   - ID: {item.get('id')}, Title: {item.get('title')}")
            print(f"     Reason: {item.get('reason')}")
            if 'cover_url' in item:
                print(f"     URL: {item.get('cover_url')[:60]}...")
    
    # 8. Data structure validation
    print(f"\n🔍 DATA STRUCTURE VALIDATION:")
    required_fields = ['id', 'title', 'author', 'genre', 'cover_image']
    sample_book = books[0] if books else {}
    
    missing_fields = [field for field in required_fields if field not in sample_book]
    if not missing_fields:
        print(f"   ✓ All required fields present in books")
        print(f"   Fields in sample book: {list(sample_book.keys())}")
    else:
        print(f"   ⚠ Missing fields: {missing_fields}")
    
    # 9. Final Summary
    print(f"\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_valid = (
        file_size_mb >= 48 and
        book_count == 100000 and
        books_without_covers == 0 and
        valid_cover_urls == book_count
    )
    
    if all_valid:
        print("✓ ALL CHECKS PASSED - Dataset is valid!")
    else:
        print("⚠ SOME CHECKS FAILED - Review results above")
    
    print("=" * 70 + "\n")
    
    return all_valid

if __name__ == '__main__':
    validate_dataset()
