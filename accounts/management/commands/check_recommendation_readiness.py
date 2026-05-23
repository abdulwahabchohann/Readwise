from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import Book
from accounts.services.cover_utils import PLACEHOLDER_COVER_URL, is_usable_cover_url


class Command(BaseCommand):
    help = "Validate that recommendation data and runtime settings are ready for deployment."

    def add_arguments(self, parser):
        parser.add_argument('--fail-on-issues', action='store_true', help='Raise a non-zero exit when readiness checks fail.')

    def handle(self, *args, **options):
        dataset_candidates = [
            Path(settings.BASE_DIR) / 'books_dataset_5000.json',
            Path(settings.BASE_DIR) / 'data' / 'books_dataset_5000.json',
        ]
        dataset_path = next((path for path in dataset_candidates if path.exists()), dataset_candidates[0])
        dataset_exists = dataset_path.exists()

        dataset_sample = {}
        if dataset_exists:
            with dataset_path.open('r', encoding='utf-8') as infile:
                payload = json.load(infile)
            if isinstance(payload, list) and payload:
                dataset_sample = payload[0]

        invalid_covers = 0
        usable_covers = 0
        missing_metadata = 0
        for cover_image, mood_scores, dominant_mood in Book.objects.values_list('cover_image', 'mood_scores', 'dominant_mood'):
            if is_usable_cover_url(cover_image):
                usable_covers += 1
            else:
                invalid_covers += 1
            if not dominant_mood or not mood_scores:
                missing_metadata += 1

        issues = []
        if not dataset_exists:
            issues.append(f"Dataset file missing: {dataset_path}")
        for required_key in ('cover_image', 'isbn_10', 'isbn_13'):
            if dataset_exists and required_key not in dataset_sample:
                issues.append(f"Dataset sample missing key: {required_key}")
        if PLACEHOLDER_COVER_URL.endswith('example.com/placeholder_cover.png'):
            issues.append("Placeholder cover URL still points to example.com.")
        if missing_metadata:
            issues.append(f"Books missing metadata: {missing_metadata}")
        if invalid_covers:
            issues.append(f"Books with invalid covers: {invalid_covers}")

        summary = {
            'dataset_path': str(dataset_path),
            'dataset_exists': dataset_exists,
            'placeholder_cover_url': PLACEHOLDER_COVER_URL,
            'recommender_mode': getattr(settings, 'RECOMMENDER_MODE', 'hybrid'),
            'enable_transformers': bool(getattr(settings, 'ENABLE_TRANSFORMERS', True)),
            'live_cover_lookups': bool(getattr(settings, 'LIVE_COVER_LOOKUPS', False)),
            'recommendation_cache_ttl': int(getattr(settings, 'RECOMMENDATION_CACHE_TTL', 0)),
            'recommendation_candidate_limit': int(getattr(settings, 'RECOMMENDATION_CANDIDATE_LIMIT', 0)),
            'book_count': Book.objects.count(),
            'usable_covers': usable_covers,
            'invalid_covers': invalid_covers,
            'missing_metadata': missing_metadata,
            'issues': issues,
        }

        self.stdout.write(json.dumps(summary, indent=2, default=str))
        if issues and options.get('fail_on_issues'):
            raise CommandError("Recommendation readiness check failed.")
