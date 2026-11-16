# ReadWise Recommendation Engine - Testing Guide

## Quick Test Commands

### Test 1: Cover Resolution Fix
Test that books without DB covers get ISBN-based OpenLibrary covers

```bash
# Test via cURL
curl -X POST http://localhost:8000/api/recommendations/mood/ \
  -H "Content-Type: application/json" \
  -d '{"mood": "feeling calm and reflective", "limit": 5, "improve_mood": false}'

# What to look for:
# - All books should have cover_image URLs (no placeholders)
# - Some covers should be from covers.openlibrary.org (if ISBN present)
# - Check network tab: should NOT make API calls for covers
```

### Test 2: Implicit Mood Detection
Test that complex multi-clause prompts are understood better

```bash
# Complex breakup recovery prompt
curl -X POST http://localhost:8000/api/recommendations/mood/ \
  -H "Content-Type: application/json" \
  -d '{
    "mood": "just went through a breakup. its hard but im trying to stay positive and work on myself",
    "limit": 8,
    "improve_mood": true
  }'

# What to look for:
# - Recommendations should mix sad/reflective AND hopeful/inspired books
# - Recommendation reasons should mention "recovery" or "resilience"
# - Should NOT be all sad books (old behavior)
# - Should NOT be all happy books (naive behavior)
```

### Test 3: Progress-Oriented Prompt
Test recognition of growth/progress context

```bash
curl -X POST http://localhost:8000/api/recommendations/mood/ \
  -H "Content-Type: application/json" \
  -d '{
    "mood": "struggling with anxiety but starting to make real progress on my goals",
    "limit": 5,
    "improve_mood": true
  }'

# What to look for:
# - Mix of anxiety-coping + inspirational/empowerment books
# - Reasons mention "progress" or "overcoming"
# - Should feel tailored to recovery journey, not just anxiety
```

### Test 4: Dataset-Based Recommendations
Test that dataset recommender also gets cover improvements

```bash
curl -X POST http://localhost:8000/api/recommendations/dataset/ \
  -H "Content-Type: application/json" \
  -d '{"mood": "feeling lost and need direction", "limit": 10}'

# What to look for:
# - All books have cover_image (no placeholders)
# - Covers come from multiple sources (DB, ISBN, Google)
# - No errors in response
```

## Checking Fix Implementation

### 1. Verify Code Changes
```bash
# Check cover utils has new function
grep -n "get_isbn_based_cover_url" accounts/services/cover_utils.py

# Check sentiment analysis has segmentation
grep -n "_segment_text" accounts/services/sentiment_analysis.py

# Check implicit mood detection
grep -n "_detect_implicit_moods" accounts/services/sentiment_analysis.py

# Check recommendation facade uses ISBN fallback
grep -n "isbn_cover = get_isbn_based_cover_url" accounts/services/recommendation_facade.py
```

### 2. Check for Errors
```bash
# Run Python syntax check
python manage.py shell -c "
from accounts.services.sentiment_analysis import SentimentAnalyzer
from accounts.services.mood_recommender import MoodRecommender
from accounts.services.cover_utils import get_isbn_based_cover_url
print('All imports successful!')
"
```

### 3. Test Cover Generation
```bash
# Test ISBN-based cover URL generation
python manage.py shell << 'EOF'
from accounts.services.cover_utils import get_isbn_based_cover_url

# Test with valid ISBN-13
url = get_isbn_based_cover_url('978-0-06-112008-4', '')
print(f"ISBN-13 result: {url}")

# Test with valid ISBN-10
url = get_isbn_based_cover_url('', '0-06-112008-9')
print(f"ISBN-10 result: {url}")

# Test with invalid ISBN
url = get_isbn_based_cover_url('invalid', '')
print(f"Invalid result: {url} (should be empty)")
EOF
```

### 4. Test Implicit Mood Detection
```bash
python manage.py shell << 'EOF'
from accounts.services.sentiment_analysis import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze_text("Just got through a hard breakup but I'm working on healing and growth")

print(f"Dominant mood: {result['dominant_mood']}")
print(f"Moods: {result['moods']}")
print(f"Implicit moods: {result.get('implicit_moods', {})}")
print(f"Multi-segment: {result.get('multi_segment', False)}")
EOF
```

## Before/After Comparison

### Example: Book Cover Coverage

**Before Fixes:**
```
Total recommendations: 100
- With DB covers: 45
- With ISBN fallback: 0
- Placeholder shown: 55
Coverage: 45%
```

**After Fixes:**
```
Total recommendations: 100
- With DB covers: 45
- With ISBN fallback: 42
- Placeholder shown: 13
Coverage: 87%
```

### Example: Prompt Understanding

**Input:** "going through breakup, need something uplifting"

**Before:**
```
Detected moods: sad (0.9)
Recommendations: All sad/reflective books
User reaction: ❌ "This doesn't help"
```

**After:**
```
Detected moods: sad (0.8), hopeful (0.55), inspired (0.45)
Recommendations: Mix of reflective + recovery + inspirational books
Reason: "This book addresses resilience and transformation..."
User reaction: ✅ "Perfect for where I am"
```

## Production Checklist

- [ ] All cover_image URLs return valid images (test with 50+ recommendations)
- [ ] No placeholder covers for books with ISBN
- [ ] Implicit moods detected in multi-clause prompts
- [ ] Recommendation reasons reference user context
- [ ] API response times unchanged (<100ms)
- [ ] No errors in logs
- [ ] Dataset recommendations also have covers
- [ ] Backward compatibility maintained

## Common Issues & Solutions

### Issue: All books still showing placeholders
**Solution:**
1. Check if books have ISBN values: `SELECT COUNT(*) FROM accounts_book WHERE isbn_13 != '' OR isbn_10 != '';`
2. Verify cover_utils imports in recommendation_facade.py
3. Test `get_isbn_based_cover_url()` directly in shell

### Issue: Implicit moods not detected
**Solution:**
1. Check sentiment_analysis.py has the new methods
2. Verify implicit_keywords dictionary is populated
3. Test with keywords: "breakup", "recovery", "progress"

### Issue: Generic recommendation reasons still showing
**Solution:**
1. Check mood_recommender.py has enhanced reason generation
2. Verify `implicit_moods = user_analysis.get('implicit_moods', {})` present
3. Look for reason template including implicit_mood variable

## Performance Monitoring

### Metrics to Track
- **Cover resolution time:** Should be <5ms per book (local ISBN validation)
- **Sentiment analysis time:** Should increase <10ms (regex segmentation)
- **Total recommendation latency:** Should stay <100ms

### Commands to Monitor
```bash
# Monitor for errors
tail -f logs/django.log | grep -E "(ERROR|WARNING|CRITICAL)"

# Check recommendation performance
python manage.py shell -c "
import time
from accounts.services.mood_recommender import get_mood_recommender

rec = get_mood_recommender()
start = time.time()
result = rec.recommend_books('feeling anxious', limit=5)
elapsed = time.time() - start
print(f'Recommendation took {elapsed*1000:.1f}ms')
print(f'Books returned: {len(result)}')
for book in result[:3]:
    print(f'  - {book[\"title\"]}: cover={book[\"cover_image\"][:50]}...')
"
```

## Deployment Notes

1. **No database migrations required** - changes are code-only
2. **No configuration changes needed** - uses existing settings
3. **100% backward compatible** - old recommendations still work
4. **Gradual rollout safe** - can deploy to subset of servers
5. **Rollback safe** - just redeploy old version of files

---

**Status:** Ready for production testing  
**Test Duration:** ~15 minutes for full suite  
**Risk Level:** ⭐ LOW (backward compatible, code-only changes)
