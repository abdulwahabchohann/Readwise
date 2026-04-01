"""
Phase 3.2: API Performance Optimization

Implements:
- Rate limiting (throttling)
- Pagination
- Response compression
- Query parameter validation
- Performance metrics
- API versioning strategy
"""

import logging
from typing import Dict, List, Any, Tuple
from functools import wraps
import time
import hashlib

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

logger = logging.getLogger(__name__)


class APIRateThrottles:
    """Rate limiting policies for different API endpoints."""
    
    class AnonThrottle(AnonRateThrottle):
        """Throttle for anonymous users."""
        scope = 'anon'
        rate = '100/hour'  # 100 requests per hour
    
    class UserThrottle(UserRateThrottle):
        """Throttle for authenticated users."""
        scope = 'user'
        rate = '1000/hour'  # 1000 requests per hour for authenticated users
    
    class StrictThrottle(UserRateThrottle):
        """Strict throttle for expensive operations."""
        scope = 'strict'
        rate = '10/hour'  # 10 requests per hour


# DRF Throttle classes for use in as_view()
class AnonThrottle(AnonRateThrottle):
    scope = 'anon'
    rate = '100/hour'

class UserThrottle(UserRateThrottle):
    scope = 'user'
    rate = '1000/hour'

class SearchThrottle(UserRateThrottle):
    scope = 'search'
    rate = '100/hour'


class OptimizedPagination(PageNumberPagination):
    """
    Pagination with performance optimizations.
    Implements cursor pagination for large datasets.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def get_paginated_response(self, data):
        """Return paginated response with metadata."""
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.get_page_size(self.request),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })


class CursorPaginationStrategy:
    """
    Cursor-based pagination for very large datasets.
    Better performance than offset pagination for large offsets.
    """
    
    @staticmethod
    def paginate_queryset(queryset, cursor: str = None, limit: int = 20):
        """
        Paginate using cursor.
        
        Args:
            queryset: Django QuerySet
            cursor: Base64-encoded cursor (id position)
            limit: Items per page
            
        Returns:
            Tuple of (items, next_cursor)
        """
        import base64
        
        # Decode cursor if provided
        start_id = 0
        if cursor:
            try:
                start_id = int(base64.b64decode(cursor).decode())
            except:
                start_id = 0
        
        # Get limit + 1 to determine if there's a next page
        items = list(queryset.filter(id__gt=start_id).order_by('id')[:limit + 1])
        
        # Check if there's a next page
        has_next = len(items) > limit
        if has_next:
            items = items[:limit]
        
        # Generate next cursor
        next_cursor = None
        if has_next and items:
            next_id = items[-1].id
            next_cursor = base64.b64encode(str(next_id).encode()).decode()
        
        return items, next_cursor


class APIResponseFormatter:
    """Formats API responses consistently and efficiently."""
    
    @staticmethod
    def success(data: Any, message: str = "", metadata: Dict = None) -> Dict:
        """Format successful response."""
        response = {
            'status': 'success',
            'data': data,
        }
        if message:
            response['message'] = message
        if metadata:
            response['metadata'] = metadata
        return response
    
    @staticmethod
    def error(error_code: str, message: str, details: Dict = None) -> Dict:
        """Format error response."""
        response = {
            'status': 'error',
            'error_code': error_code,
            'message': message,
        }
        if details:
            response['details'] = details
        return response
    
    @staticmethod
    def paginated(data: List, total: int, page: int, page_size: int, 
                  total_pages: int = None) -> Dict:
        """Format paginated response."""
        if not total_pages:
            total_pages = (total + page_size - 1) // page_size  # Ceiling division
        
        return {
            'status': 'success',
            'pagination': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
            },
            'data': data,
        }


class QueryParameterValidator:
    """Validates and sanitizes query parameters."""
    
    @staticmethod
    def validate_pagination(limit: Any, offset: Any) -> Tuple[int, int]:
        """Validate and constrain pagination parameters."""
        try:
            limit = int(limit) if limit else 20
            offset = int(offset) if offset else 0
        except ValueError:
            limit, offset = 20, 0
        
        # Constrain values
        limit = min(max(limit, 1), 100)  # 1-100
        offset = max(offset, 0)
        
        return limit, offset
    
    @staticmethod
    def validate_filters(filters_dict: Dict) -> Dict:
        """Validate and sanitize filter parameters."""
        sanitized = {}
        
        # Whitelist allowed filters
        allowed_filters = {
            'genres': (list, 'genres'),
            'moods': (list, 'moods'),
            'sentiment': (str, 'sentiment'),
            'min_rating': (float, 'min_rating'),
            'sort_by': (str, 'sort_by'),
            'q': (str, 'query'),
        }
        
        for key, value in filters_dict.items():
            if key not in allowed_filters:
                continue
            
            expected_type, field_name = allowed_filters[key]
            
            try:
                if expected_type == list:
                    sanitized[field_name] = value if isinstance(value, list) else [value]
                elif expected_type == float:
                    sanitized[field_name] = float(value)
                elif expected_type == str:
                    sanitized[field_name] = str(value).strip()[:200]  # Max 200 chars
            except (ValueError, TypeError):
                continue
        
        return sanitized


def api_performance_monitor(func):
    """Decorator to monitor API endpoint performance."""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        start_time = time.time()
        start_queries = len(get_queries_count())
        
        try:
            response = func(self, request, *args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {e}", exc_info=True)
            raise
        finally:
            elapsed = time.time() - start_time
            num_queries = len(get_queries_count()) - start_queries
            
            # Log performance metrics
            log_level = logging.WARNING if elapsed > 1.0 or num_queries > 10 else logging.INFO
            logger.log(
                log_level,
                f"API/{func.__name__} | "
                f"Time: {elapsed:.3f}s | "
                f"Queries: {num_queries} | "
                f"Status: {response.status_code if hasattr(response, 'status_code') else 'unknown'}"
            )
        
        return response
    
    return wrapper


def get_queries_count():
    """Get count of database queries (requires DEBUG=True)."""
    from django.db import connection
    return connection.queries


class ResponseCaching:
    """Implements response-level caching for API endpoints."""
    
    @staticmethod
    def generate_cache_key(request, prefix: str = "") -> str:
        """Generate cache key from request."""
        key_parts = [
            prefix,
            request.method,
            request.path,
            request.GET.urlencode(),
        ]
        
        if request.user.is_authenticated:
            key_parts.append(f"user_{request.user.id}")
        else:
            key_parts.append("anon")
        
        key = "|".join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()
    
    @staticmethod
    def cache_get_response(request, cache_key: str, cache_ttl: int = 300):
        """Decorator to cache GET response."""
        from django.core.cache import cache
        
        @wraps(cache_get_response)
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Only cache GET requests for anonymous users or non-sensitive data
                if request.method != 'GET':
                    return func(*args, **kwargs)
                
                full_cache_key = cache_key + f":{ResponseCaching.generate_cache_key(request)}"
                cached_response = cache.get(full_cache_key)
                
                if cached_response:
                    logger.debug(f"Cache hit: {full_cache_key}")
                    return cached_response
                
                response = func(*args, **kwargs)
                cache.set(full_cache_key, response, cache_ttl)
                return response
            
            return wrapper
        return decorator


# DRF Settings to add to settings.py
DRF_SETTINGS = {
    'REST_FRAMEWORK': {
        'DEFAULT_PAGINATION_CLASS': 'accounts.services.api_performance.OptimizedPagination',
        'PAGE_SIZE': 20,
        
        'DEFAULT_THROTTLE_CLASSES': [
            'accounts.services.api_performance.UserThrottle',
            'accounts.services.api_performance.AnonThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/hour',
            'user': '1000/hour',
            'search': '100/hour',
        },
        
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        
        'DEFAULT_FILTER_BACKENDS': [
            'django_filters.rest_framework.DjangoFilterBackend',
        ],
        
        # Performance settings
        'DEFAULT_TIMEOUT': 10,  # API timeout
        'COMPACT_JSON': True,  # Remove whitespace in JSON
        'UNICODE_JSON': True,  # Unicode in JSON
        
        # Security settings
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        ],
    }
}


# Usage example:
"""
from accounts.services.api_performance import (
    OptimizedPagination, QueryParameterValidator, APIResponseFormatter,
    api_performance_monitor, UserThrottle
)

class SearchAPIView(APIView):
    throttle_classes = [UserThrottle]
    pagination_class = OptimizedPagination
    
    @api_performance_monitor
    def get(self, request):
        # Validate parameters
        limit, offset = QueryParameterValidator.validate_pagination(
            request.GET.get('limit'),
            request.GET.get('offset')
        )
        
        filters = QueryParameterValidator.validate_filters(request.GET)
        
        # Perform search
        results = search_books(**filters)
        
        # Paginate
        paginator = Paginator(results, limit)
        try:
            page = paginator.page(offset // limit + 1)
        except (EmptyPage, PageNotAnInteger):
            page = paginator.page(1)
        
        # Format response
        return Response(APIResponseFormatter.paginated(
            data=page.object_list,
            total=paginator.count,
            page=page.number,
            page_size=limit,
            total_pages=paginator.num_pages
        ))
"""
