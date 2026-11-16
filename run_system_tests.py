#!/usr/bin/env python
"""
Comprehensive System Testing Script for ReadWise Recommendation Engine
Tests all components before deployment
"""
import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readwise.settings')
django.setup()

from accounts.models import Book
from accounts.services.sentiment_analysis import get_sentiment_analyzer
from accounts.services.mood_recommender import get_mood_recommender
from accounts.services.recommendation_facade import get_recommendations_for_mood

# Test Results
results = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "summary": {}
}


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(msg):
    """Print success message"""
    print(f"  ✅ {msg}")


def print_error(msg):
    """Print error message"""
    print(f"  ❌ {msg}")


def print_warning(msg):
    """Print warning message"""
    print(f"  ⚠️  {msg}")


def print_info(msg):
    """Print info message"""
    print(f"  ℹ️  {msg}")


# ============================================================================
# TEST 1: Database Connectivity
# ============================================================================
def test_database():
    """Test 1: Database connectivity and data integrity"""
    print_header("TEST 1: Database Connectivity & Data Integrity")
    
    test_result = {
        "passed": True,
        "details": []
    }
    
    try:
        # Check if database file exists
        db_path = Path('db.sqlite3')
        if db_path.exists():
            print_success(f"Database file exists: {db_path}")
            test_result["details"].append("Database file found")
        else:
            print_warning(f"Database file not found at {db_path}")
            test_result["details"].append("Database file missing")
        
        # Test connection and read
        book_count = Book.objects.count()
        print_success(f"Database connection successful - {book_count} books in DB")
        test_result["details"].append(f"Book count: {book_count}")
        
        # Check dataset file
        dataset_file = Path('books_dataset_100k_real_covers.json')
        if dataset_file.exists():
            size_mb = dataset_file.stat().st_size / (1024 * 1024)
            print_success(f"Dataset file exists: {size_mb:.2f} MB")
            test_result["details"].append(f"Dataset size: {size_mb:.2f} MB")
        else:
            print_error("Dataset file not found!")
            test_result["passed"] = False
            test_result["details"].append("Dataset file missing")
        
        # Load and validate dataset
        with open(dataset_file, 'r') as f:
            books = json.load(f)
        
        print_success(f"Dataset loaded: {len(books):,} books")
        test_result["details"].append(f"Total dataset books: {len(books):,}")
        
        # Check for covers
        books_with_covers = sum(1 for b in books if b.get('cover_image', '').strip())
        print_success(f"Books with covers: {books_with_covers:,}/{len(books):,}")
        test_result["details"].append(f"Books with covers: {books_with_covers:,}")
        
    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["database"] = test_result
    return test_result["passed"]


# ============================================================================
# TEST 2: Sentiment Analysis
# ============================================================================
def test_sentiment_analysis():
    """Test 2: Sentiment analysis engine"""
    print_header("TEST 2: Sentiment Analysis Engine")
    
    test_result = {
        "passed": True,
        "details": []
    }
    
    test_prompts = [
        ("I'm feeling happy and excited", "positive"),
        ("I'm very sad and depressed", "negative"),
        ("I'm neutral and okay", "neutral"),
        ("Feeling anxious and worried about the future", "negative"),
        ("Hopeful and inspired by new possibilities", "positive"),
    ]
    
    try:
        analyzer = get_sentiment_analyzer()
        for prompt, expected_sentiment in test_prompts:
            result = analyzer.analyze_text(prompt)
            sentiment = result.get('sentiment', {})
            label = sentiment.get('label', 'unknown') if isinstance(sentiment, dict) else result.get('sentiment_label', 'unknown')
            score = sentiment.get('score', 0) if isinstance(sentiment, dict) else result.get('sentiment_score', 0)
            
            print_info(f'Prompt: "{prompt}"')
            print_success(f"  Sentiment: {label} (score: {score:.3f})")
            test_result["details"].append(f"'{prompt}' → {label}")
            
            moods = result.get('moods', {})
            if moods:
                top_moods = sorted(moods.items(), key=lambda x: x[1], reverse=True)[:3]
                print_success(f"  Top moods: {', '.join([f'{m}({s:.2f})' for m, s in top_moods])}")
        
    except Exception as e:
        print_error(f"Sentiment analysis failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["sentiment_analysis"] = test_result
    return test_result["passed"]


# ============================================================================
# TEST 3: Recommendation API Endpoints
# ============================================================================
def test_recommendation_api():
    """Test 3: Recommendation API endpoints"""
    print_header("TEST 3: Recommendation API Endpoints")
    
    test_result = {
        "passed": True,
        "details": []
    }
    
    test_moods = [
        "I'm feeling happy and want something fun",
        "Feeling sad and need comfort",
        "Anxious and stressed, need calming",
        "Excited and want an adventure",
        "Romantic mood, want something touching",
    ]
    
    try:
        for mood in test_moods:
            print_info(f'Testing mood: "{mood}"')
            
            start_time = time.time()
            recommendations = get_recommendations_for_mood(
                user_mood=mood,
                limit=10,
                improve_mood=True,
            )
            elapsed = time.time() - start_time
            
            if recommendations and len(recommendations) > 0:
                print_success(f"  Returned {len(recommendations)} books in {elapsed:.3f}s")
                
                # Show first recommendation
                first = recommendations[0]
                print_info(f"  Top pick: {first.get('title', 'Unknown')}")
                print_info(f"    - Match: {first.get('match_percentage', 0)}%")
                print_info(f"    - Reason: {first.get('reason', 'N/A')[:60]}...")
                
                test_result["details"].append(f"{mood} → {len(recommendations)} books ({elapsed:.3f}s)")
            else:
                print_warning(f"  No recommendations returned!")
                test_result["details"].append(f"{mood} → NO RESULTS")
                test_result["passed"] = False
    
    except Exception as e:
        print_error(f"Recommendation API test failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["recommendation_api"] = test_result
    return test_result["passed"]


# ============================================================================
# TEST 4: Cover Image Validation
# ============================================================================
def test_cover_images():
    """Test 4: Cover image URLs validation"""
    print_header("TEST 4: Cover Image Validation")
    
    test_result = {
        "passed": True,
        "details": []
    }
    
    try:
        with open('books_dataset_100k_real_covers.json', 'r') as f:
            books = json.load(f)
        
        # Sample 100 random books
        import random
        sample_books = random.sample(books, min(100, len(books)))
        
        cover_stats = {
            "total": len(sample_books),
            "with_cover": 0,
            "valid_url": 0,
            "openlibrary": 0,
        }
        
        for book in sample_books:
            cover = book.get('cover_image', '').strip()
            if cover:
                cover_stats["with_cover"] += 1
                
                if cover.startswith('https://'):
                    cover_stats["valid_url"] += 1
                
                if 'covers.openlibrary.org' in cover:
                    cover_stats["openlibrary"] += 1
        
        print_success(f"Sampled {cover_stats['total']} books")
        print_success(f"Books with covers: {cover_stats['with_cover']}/{cover_stats['total']}")
        print_success(f"Valid HTTPS URLs: {cover_stats['valid_url']}/{cover_stats['total']}")
        print_success(f"OpenLibrary covers: {cover_stats['openlibrary']}/{cover_stats['total']}")
        
        test_result["details"].append(f"Cover coverage: {cover_stats['with_cover']}/{cover_stats['total']}")
        test_result["details"].append(f"Valid URLs: {cover_stats['valid_url']}/{cover_stats['total']}")
        
        if cover_stats["with_cover"] == cover_stats["total"]:
            print_success("All sampled books have covers! ✓")
        else:
            percentage = (cover_stats["with_cover"] / cover_stats["total"]) * 100
            if percentage >= 80:
                print_success(f"Cover quality good: {percentage:.1f}%")
            else:
                print_warning(f"Cover quality low: {percentage:.1f}%")
                test_result["passed"] = False
    
    except Exception as e:
        print_error(f"Cover image test failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["cover_images"] = test_result
    return test_result["passed"]


# ============================================================================
# TEST 5: Data Quality
# ============================================================================
def test_data_quality():
    """Test 5: Data quality and completeness"""
    print_header("TEST 5: Data Quality & Completeness")
    
    test_result = {
        "passed": True,
        "details": []
    }
    
    try:
        with open('books_dataset_100k_real_covers.json', 'r') as f:
            books = json.load(f)
        
        required_fields = ['id', 'title', 'author', 'isbn_13', 'cover_image']
        missing_fields = {field: 0 for field in required_fields}
        empty_values = {field: 0 for field in required_fields}
        
        for book in books:
            for field in required_fields:
                if field not in book:
                    missing_fields[field] += 1
                elif not book[field] or book[field] == '':
                    empty_values[field] += 1
        
        print_info(f"Checking {len(books):,} books for data quality...")
        
        total_missing = sum(missing_fields.values())
        total_empty = sum(empty_values.values())
        
        if total_missing > 0:
            print_warning(f"Missing fields: {total_missing}")
            for field, count in missing_fields.items():
                if count > 0:
                    print_warning(f"  - {field}: {count} books")
            test_result["passed"] = False
        else:
            print_success("All required fields present ✓")
        
        if total_empty > 0:
            print_warning(f"Empty values: {total_empty}")
            for field, count in empty_values.items():
                if count > 0:
                    percentage = (count / len(books)) * 100
                    if percentage < 1:
                        print_success(f"  - {field}: {count} books ({percentage:.2f}%)")
                    else:
                        print_warning(f"  - {field}: {count} books ({percentage:.2f}%)")
                        if field in ['title', 'cover_image']:
                            test_result["passed"] = False
        else:
            print_success("No empty required fields ✓")
        
        test_result["details"].append(f"Missing fields: {total_missing}")
        test_result["details"].append(f"Empty values: {total_empty}")
    
    except Exception as e:
        print_error(f"Data quality test failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["data_quality"] = test_result
    return test_result["passed"]


# ============================================================================
# TEST 6: Performance Testing
# ============================================================================
def test_performance():
    """Test 6: Performance metrics"""
    print_header("TEST 6: Performance Testing")
    
    test_result = {
        "passed": True,
        "details": [],
        "metrics": {}
    }
    
    try:
        # Test 1: Recommendation generation time
        print_info("Testing recommendation generation speed...")
        test_moods = [
            "happy",
            "sad and depressed",
            "anxious and stressed",
            "excited about the future"
        ]
        
        times = []
        for mood in test_moods:
            start = time.time()
            recommendations = get_recommendations_for_mood(mood, limit=5, improve_mood=True)
            elapsed = time.time() - start
            times.append(elapsed)
            print_success(f"  {mood}: {elapsed:.4f}s")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print_success(f"Average time: {avg_time:.4f}s")
        print_success(f"Min/Max: {min_time:.4f}s / {max_time:.4f}s")
        
        test_result["metrics"] = {
            "avg_recommendation_time": avg_time,
            "min_time": min_time,
            "max_time": max_time
        }
        test_result["details"].append(f"Avg recommendation time: {avg_time:.4f}s")
        
        # Check performance threshold
        if avg_time > 2.0:
            print_warning(f"Performance warning: Average time {avg_time:.4f}s is > 2.0s")
            test_result["passed"] = False
        else:
            print_success("Performance within acceptable range ✓")
    
    except Exception as e:
        print_error(f"Performance test failed: {str(e)}")
        test_result["passed"] = False
        test_result["details"].append(f"Error: {str(e)}")
    
    results["tests"]["performance"] = test_result
    return test_result["passed"]


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================
def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  READWISE RECOMMENDATION ENGINE - SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = []
    tests_failed = []
    
    # Run all tests
    if test_database():
        tests_passed.append("Database")
    else:
        tests_failed.append("Database")
    
    if test_sentiment_analysis():
        tests_passed.append("Sentiment Analysis")
    else:
        tests_failed.append("Sentiment Analysis")
    
    if test_recommendation_api():
        tests_passed.append("Recommendation API")
    else:
        tests_failed.append("Recommendation API")
    
    if test_cover_images():
        tests_passed.append("Cover Images")
    else:
        tests_failed.append("Cover Images")
    
    if test_data_quality():
        tests_passed.append("Data Quality")
    else:
        tests_failed.append("Data Quality")
    
    if test_performance():
        tests_passed.append("Performance")
    else:
        tests_failed.append("Performance")
    
    # Summary
    print_header("TEST SUMMARY")
    
    print_success(f"Passed: {len(tests_passed)}/6")
    for test in tests_passed:
        print_success(f"  ✓ {test}")
    
    if tests_failed:
        print_error(f"Failed: {len(tests_failed)}/6")
        for test in tests_failed:
            print_error(f"  ✗ {test}")
    
    overall_status = "PASSED ✅" if len(tests_failed) == 0 else "FAILED ❌"
    print(f"\nOVERALL STATUS: {overall_status}")
    
    # Save results
    results["summary"] = {
        "total_tests": 6,
        "passed": len(tests_passed),
        "failed": len(tests_failed),
        "status": overall_status,
        "timestamp": datetime.now().isoformat()
    }
    
    with open('TEST_RESULTS.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: TEST_RESULTS.json")
    print("=" * 70 + "\n")
    
    return len(tests_failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
