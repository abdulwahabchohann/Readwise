"""
Script to remove books without cover images from the dataset JSON file.
"""
import json
import sys
from pathlib import Path


def clean_dataset(input_file, output_file=None, dry_run=False):
    """
    Remove books without cover images from dataset.
    
    Args:
        input_file: Path to input JSON dataset
        output_file: Path to save cleaned dataset (defaults to input with _cleaned suffix)
        dry_run: If True, only show what would be deleted
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    print(f"📖 Loading dataset from: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        print("❌ Dataset must be a JSON array of books")
        sys.exit(1)
    
    print(f"📊 Total books: {len(data)}")
    
    # Separate books with and without covers
    books_with_covers = []
    books_without_covers = []
    
    for book in data:
        cover = book.get('cover_image', '').strip()
        if cover and cover.lower() not in ['none', 'null', '']:
            books_with_covers.append(book)
        else:
            books_without_covers.append(book)
    
    print(f"  ✓ Books WITH covers: {len(books_with_covers)}")
    print(f"  ✗ Books WITHOUT covers: {len(books_without_covers)}")
    
    if len(books_without_covers) > 0:
        print(f"\n📋 Books to be removed:")
        for i, book in enumerate(books_without_covers[:10], 1):
            title = book.get('title', 'Unknown')
            print(f"  {i}. {title}")
        if len(books_without_covers) > 10:
            print(f"  ... and {len(books_without_covers) - 10} more")
    
    if dry_run:
        print(f"\n🔍 DRY RUN: No changes made.")
        return
    
    # Set output file
    if not output_file:
        output_file = str(input_path.parent / f"{input_path.stem}_no_blanks.json")
    
    output_path = Path(output_file)
    
    # Save cleaned dataset
    print(f"\n💾 Saving cleaned dataset to: {output_file}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(books_with_covers, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully created cleaned dataset with {len(books_with_covers)} books!")
    print(f"   Removed {len(books_without_covers)} books without cover images")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Remove books without cover images from dataset')
    parser.add_argument('input_file', help='Input JSON dataset file')
    parser.add_argument('--output', '-o', help='Output file (default: input_stem_no_blanks.json)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be removed without making changes')
    
    args = parser.parse_args()
    
    clean_dataset(args.input_file, args.output, args.dry_run)
