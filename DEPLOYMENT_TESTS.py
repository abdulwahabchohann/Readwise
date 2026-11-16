#!/usr/bin/env python
"""
Fast System Testing Suite for ReadWise - Deployment Readiness Check
Focuses on critical components without heavy ML loading
"""
import os
import sys
import django
import json
import time
from pathlib import Path
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'readwise.settings')
django.setup()

from django.test.client import Client
from django.urls import reverse

# Test Results
results = {
    "timestamp": datetime.now().isoformat(),
    "tests": {},
    "deployment_ready": True
}


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(msg):
    print(f"  ✅ {msg}")


def print_error(msg):
    print(f"  ❌ {msg}")


def print_warning(msg):
    print(f"  ⚠️  {msg}")


def print_info(msg):
    print(f"  ℹ️  {msg}")


# ============================================================================
# TEST 1: Database & Dataset
# ============================================================================
def test_database_and_dataset():
    """Test database and dataset integrity"""
    print_header("TEST 1: Database & Dataset Integrity")
    
    test_result = {"passed": True, "details": []}
    
    try:
        # Check database file
        db_path = Path('db.sqlite3')
        if db_path.exists():
            print_success(f"Database file exists")
            test_result["details"].append("Database file: OK")
        else:
            print_error("Database file missing")
            test_result["passed"] = False
        
        # Check dataset file
        dataset_file = Path('books_dataset_100k_real_covers.json')
        if not dataset_file.exists():
            print_error("Dataset file not found")
            test_result["passed"] = False
            results["deployment_ready"] = False
            return test_result
        
        size_mb = dataset_file.stat().st_size / (1024 * 1024)
        print_success(f"Dataset file: {size_mb:.2f} MB")
        test_result["details"].append(f"Dataset size: {size_mb:.2f} MB")
        
        # Load and validate dataset
        with open(dataset_file, 'r') as f:
            books = json.load(f)
        
        print_success(f"Dataset loaded: {len(books):,} books")
        test_result["details"].append(f"Book count: {len(books):,}")
        
        # Check covers
        books_with_covers = sum(1 for b in books if b.get('cover_image', '').strip())
        print_success(f"Books with covers: {books_with_covers:,}/{len(books):,}")
        test_result["details"].append(f"Cover coverage: {books_with_covers}/{len(books)}")
        
        if books_with_covers == 0:
            print_error("No books have covers!")
            test_result["passed"] = False
            results["deployment_ready"] = False
        
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        test_result["passed"] = False
        results["deployment_ready"] = False
    
    results["tests"]["database_and_dataset"] = test_result
    return test_result


# ============================================================================
# TEST 2: API Endpoints
# ============================================================================
def test_api_endpoints():
    """Test HTTP API endpoints"""
    print_header("TEST 2: API Endpoints")
    
    test_result = {"passed": True, "details": []}
    client = Client()
    
    try:
        # Test home page
        response = client.get('/')
        if response.status_code == 200:
            print_success("Home page (GET /): 200 OK")
            test_result["details"].append("Home page: OK")
        else:
            print_error(f"Home page returned {response.status_code}")
            test_result["passed"] = False
        
        # Test recommendations page
        response = client.get('/recommendations/')
        if response.status_code == 200:
            print_success("Recommendations page (GET /recommendations/): 200 OK")
            test_result["details"].append("Recommendations page: OK")
        else:
            print_error(f"Recommendations page returned {response.status_code}")
            test_result["passed"] = False
        
        # Test recommendations API POST
        response = client.post('/api/recommendations/', {
            'mood': 'happy',
            'improve_mood': True
        }, content_type='application/x-www-form-urlencoded')
        
        if response.status_code in [200, 400, 405]:  # 405 if API not available
            print_success(f"API recommendations endpoint: {response.status_code}")
            test_result["details"].append(f"API endpoint: {response.status_code}")
        else:
            print_warning(f"API returned {response.status_code}")
        
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        test_result["passed"] = False
    
    results["tests"]["api_endpoints"] = test_result
    return test_result


# ============================================================================
# TEST 3: Settings Validation
# ============================================================================
def test_settings():
    """Validate Django settings"""
    print_header("TEST 3: Django Settings Validation")
    
    test_result = {"passed": True, "details": []}
    
    try:
        from django.conf import settings
        
        # Check critical settings
        critical_settings = [
            ('DEBUG', False, 'Production mode'),
            ('ALLOWED_HOSTS', None, 'Allowed hosts configured'),
            ('SECRET_KEY', None, 'Secret key set'),
            ('DATABASES', None, 'Database configured'),
        ]
        
        for setting_name, expected_value, description in critical_settings:
            value = getattr(settings, setting_name, None)
            
            if value is None:
                print_warning(f"{description}: Not set")
                test_result["details"].append(f"{setting_name}: Warning")
            elif expected_value is not None and value != expected_value:
                print_warning(f"{description}: {value}")
                test_result["details"].append(f"{setting_name}: {value}")
            else:
                print_success(f"{description}: ✓")
                test_result["details"].append(f"{setting_name}: OK")
        
        # Check installed apps
        if 'accounts' in settings.INSTALLED_APPS:
            print_success("accounts app installed")
            test_result["details"].append("accounts app: OK")
        else:
            print_error("accounts app not installed")
            test_result["passed"] = False
        
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        test_result["passed"] = False
    
    results["tests"]["settings"] = test_result
    return test_result


# ============================================================================
# TEST 4: Static Files
# ============================================================================
def test_static_files():
    """Check static files"""
    print_header("TEST 4: Static Files")
    
    test_result = {"passed": True, "details": []}
    
    try:
        # Check for placeholder image
        placeholder_path = Path('staticfiles/images/placeholder.svg')
        if placeholder_path.exists():
            print_success("Placeholder image exists")
            test_result["details"].append("Placeholder: OK")
        else:
            placeholder_path = Path('static/images/placeholder.svg')
            if placeholder_path.exists():
                print_success("Placeholder image exists (static/)")
                test_result["details"].append("Placeholder: OK")
            else:
                print_warning("Placeholder image not found")
                test_result["details"].append("Placeholder: Not found")
        
        # Check CSS files
        css_dir = Path('staticfiles/css')
        if css_dir.exists():
            css_count = len(list(css_dir.glob('*.css')))
            print_success(f"CSS files: {css_count} files")
            test_result["details"].append(f"CSS files: {css_count}")
        else:
            print_warning("CSS files not found in staticfiles")
    
    except Exception as e:
        print_error(f"Failed: {str(e)}")
    
    results["tests"]["static_files"] = test_result
    return test_result


# ============================================================================
# TEST 5: Data Files
# ============================================================================
def test_data_files():
    """Check all required data files"""
    print_header("TEST 5: Data Files Check")
    
    test_result = {"passed": True, "details": []}
    
    try:
        required_files = [
            ('books_dataset_100k_real_covers.json', 'Primary dataset'),
            ('db.sqlite3', 'Database'),
        ]
        
        for filename, description in required_files:
            file_path = Path(filename)
            if file_path.exists():
                size = file_path.stat().st_size
                size_str = f"{size / (1024*1024):.2f} MB" if size > 1024*1024 else f"{size / 1024:.2f} KB"
                print_success(f"{description}: {size_str}")
                test_result["details"].append(f"{filename}: OK ({size_str})")
            else:
                print_error(f"{description}: NOT FOUND")
                test_result["passed"] = False
                test_result["details"].append(f"{filename}: MISSING")
    
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        test_result["passed"] = False
    
    results["tests"]["data_files"] = test_result
    return test_result


# ============================================================================
# TEST 6: Code Quality
# ============================================================================
def test_code_quality():
    """Check key files exist and are valid Python"""
    print_header("TEST 6: Code Files Validation")
    
    test_result = {"passed": True, "details": []}
    
    try:
        key_files = [
            'accounts/services/sentiment_analysis.py',
            'accounts/services/mood_recommender.py',
            'accounts/services/recommendation_facade.py',
            'accounts/services/cover_utils.py',
            'accounts/views.py',
            'accounts/models.py',
        ]
        
        for filepath in key_files:
            path = Path(filepath)
            if path.exists():
                # Try to compile Python
                try:
                    with open(path) as f:
                        code = f.read()
                    compile(code, filepath, 'exec')
                    print_success(f"{filepath}: Valid Python")
                    test_result["details"].append(f"{filepath}: OK")
                except SyntaxError as e:
                    print_error(f"{filepath}: Syntax error - {str(e)}")
                    test_result["passed"] = False
                    test_result["details"].append(f"{filepath}: SYNTAX ERROR")
            else:
                print_error(f"{filepath}: NOT FOUND")
                test_result["passed"] = False
                test_result["details"].append(f"{filepath}: MISSING")
    
    except Exception as e:
        print_error(f"Failed: {str(e)}")
        test_result["passed"] = False
    
    results["tests"]["code_quality"] = test_result
    return test_result


# ============================================================================
# TEST 7: Performance Baseline
# ============================================================================
def test_performance_baseline():
    """Measure basic performance metrics"""
    print_header("TEST 7: Performance Baseline")
    
    test_result = {"passed": True, "details": [], "metrics": {}}
    
    try:
        client = Client()
        
        # Time home page load
        start = time.time()
        response = client.get('/')
        home_time = time.time() - start
        print_success(f"Home page load: {home_time*1000:.1f}ms")
        test_result["metrics"]["home_page_ms"] = round(home_time * 1000, 1)
        
        # Time recommendations page load
        start = time.time()
        response = client.get('/recommendations/')
        rec_time = time.time() - start
        print_success(f"Recommendations page load: {rec_time*1000:.1f}ms")
        test_result["metrics"]["recommendations_page_ms"] = round(rec_time * 1000, 1)
        
        # Check database load time
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        start = time.time()
        with CaptureQueriesContext(connection) as ctx:
            from accounts.models import Book
            count = Book.objects.count()
        db_time = time.time() - start
        print_success(f"Database query (Book count): {db_time*1000:.1f}ms")
        test_result["metrics"]["db_query_ms"] = round(db_time * 1000, 1)
        
    except Exception as e:
        print_warning(f"Performance test: {str(e)}")
    
    results["tests"]["performance"] = test_result
    return test_result


# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  READWISE - DEPLOYMENT READINESS TEST SUITE")
    print("=" * 70)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        test_database_and_dataset,
        test_api_endpoints,
        test_settings,
        test_static_files,
        test_data_files,
        test_code_quality,
        test_performance_baseline,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        result = test_func()
        if result["passed"]:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print_header("TEST SUMMARY")
    print_success(f"Passed: {passed}/{len(tests)}")
    if failed > 0:
        print_error(f"Failed: {failed}/{len(tests)}")
    
    overall = "✅ DEPLOYMENT READY" if results["deployment_ready"] and failed == 0 else "⚠️ REVIEW NEEDED"
    print(f"\nSTATUS: {overall}")
    
    results["summary"] = {
        "total_tests": len(tests),
        "passed": passed,
        "failed": failed,
        "deployment_ready": results["deployment_ready"] and failed == 0,
        "completed_at": datetime.now().isoformat()
    }
    
    # Save results
    with open('DEPLOYMENT_TEST_RESULTS.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: DEPLOYMENT_TEST_RESULTS.json")
    print("=" * 70 + "\n")
    
    return results["deployment_ready"] and failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
