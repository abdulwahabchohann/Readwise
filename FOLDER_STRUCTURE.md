# Django ReadWise Project - Clean Folder Structure

## Before (key parts)

```text
final-year-project/
├── accounts/
│   └── tests.py
├── books_dataset_5000.json
├── books_dataset_cleaned.json
├── books_dataset_enriched.json
├── books_dataset_qacheck.json
├── dataset_recommender_metrics.json
├── dataset_recommender_test_output.json
├── check_db.py
├── check_mood_scores.py
├── check_sentiment_labels.py
├── diagnose_redirect_uri.py
├── example_usage.py
├── fix_redirect.py
├── fix_security.py
├── linkedin/
│   ├── README.md
│   ├── caption.txt
│   └── ... (other LinkedIn assets)
├── sentiment_analyzer.py
├── train_sentiment_model.py
├── test_multiple_moods.py
├── test_recommendations.py
├── test_sentiment_analyzer.py
├── tests/
│   ├── test_categories.py
│   └── test_recommendations_flow.py
└── data/
    ├── books_dataset_5000.json
    ├── books_dataset_clean.json
    └── pythonanywhere_seed.json
```

## After (key parts)

```text
final-year-project/
├── accounts/
├── data/
│   ├── books_dataset_5000.json
│   ├── books_dataset_clean.json
│   ├── books_dataset_cleaned.json
│   ├── books_dataset_enriched.json
│   ├── books_dataset_qacheck.json
│   ├── dataset_recommender_metrics.json
│   ├── dataset_recommender_test_output.json
│   └── pythonanywhere_seed.json
├── debug/
│   ├── check_db.py
│   ├── check_mood_scores.py
│   ├── check_sentiment_labels.py
│   ├── diagnose_redirect_uri.py
│   ├── example_usage.py
│   ├── fix_redirect.py
│   ├── fix_security.py
│   ├── validate_optimizations.py
│   └── verify_google_config.py
├── readwise/
│   ├── sentiment_analyzer.py
│   └── train_sentiment_model.py
├── tests/
│   ├── test_accounts.py
│   ├── test_categories.py
│   ├── test_multiple_moods.py
│   ├── test_recommendations.py
│   ├── test_recommendations_flow.py
│   └── test_sentiment_analyzer.py
└── linkedin/ (removed)
```

## Git Tracking Cleanup

- Added dataset/model ignore patterns in `.gitignore`.
- Removed tracked large dataset files from git index (kept locally in `data/`).
