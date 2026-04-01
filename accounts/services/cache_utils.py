"""Utilities for managing HTTP cache headers and response optimization."""
from functools import wraps
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.views.decorators.http import cache_page, condition
from django.utils.decorators import decorator_from_middleware
from django.utils.cache import add_never_cache_headers, patch_response_headers
from django.middleware.http import ConditionalGetMiddleware


def cache_api_response(timeout_seconds: int = 300):
    """
    Decorator to add cache control headers to API responses.
    
    Args:
        timeout_seconds: Cache duration in seconds
    
    Examples:
        @cache_api_response(300)  # Cache for 5 minutes
        def my_api_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            
            if isinstance(response, HttpResponse):
                # Set cache-control header
                response['Cache-Control'] = f'public, max-age={timeout_seconds}'
                response['ETag'] = f'"{hash(str(response.content))}"'
                response['Vary'] = 'Accept, Accept-Encoding'
                
                # Set expiry time
                patch_response_headers(response, cache_timeout=timeout_seconds)
            
            return response
        
        return wrapper
    
    return decorator


def no_cache(func):
    """
    Decorator to prevent caching of responses.
    Useful for dynamic or sensitive endpoints.
    
    Examples:
        @no_cache
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        
        if isinstance(response, HttpResponse):
            add_never_cache_headers(response)
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
    return wrapper


def cache_headers(max_age: int = 3600, public: bool = True):
    """
    Set explicit cache headers on response.
    
    Args:
        max_age: Cache duration in seconds
        public: Whether cache is public or private
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            response = func(request, *args, **kwargs)
            
            if isinstance(response, HttpResponse):
                cache_type = 'public' if public else 'private'
                response['Cache-Control'] = f'{cache_type}, max-age={max_age}'
                
                # Add Last-Modified header for better caching
                response['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            return response
        
        return wrapper
    
    return decorator


class CacheControlMiddleware:
    """
    Middleware to add appropriate cache headers based on response type.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Don't cache API errors or redirects
        if response.status_code in (301, 302, 304):
            add_never_cache_headers(response)
            return response
        
        # Cache JSON API responses for 5 minutes
        if response.get('Content-Type', '').startswith('application/json'):
            if response.status_code == 200:
                response['Cache-Control'] = 'public, max-age=300'
                response['Vary'] = 'Accept, Accept-Encoding'
        
        # Cache HTML pages for 1 hour
        elif response.get('Content-Type', '').startswith('text/html'):
            if response.status_code == 200:
                response['Cache-Control'] = 'public, max-age=3600'
        
        # Cache static resources for 1 month
        elif any(response.get('Content-Type', '').startswith(ct) for ct in ['image/', 'text/css', 'application/javascript', 'application/json']):
            if response.status_code == 200:
                response['Cache-Control'] = 'public, max-age=2592000'  # 30 days
        
        return response


def adaptive_cache_timeout(request, default_timeout: int = 300):
    """
    Determine cache timeout based on request parameters.
    Useful for varying cache based on user authentication or request type.
    
    Args:
        request: Django request object
        default_timeout: Default timeout in seconds
    
    Returns:
        Cache timeout in seconds
    """
    # Authenticated users get shorter cache (more fresh data)
    if request.user.is_authenticated:
        return max(60, default_timeout // 5)  # 1/5th of default, minimum 60s
    
    # Anonymous users get standard cache
    return default_timeout


def etag_response(func):
    """
    Add ETag header based on response content.
    Allows clients to cache and use conditional requests.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        
        if isinstance(response, HttpResponse) and response.status_code == 200:
            content = response.content
            # Generate ETag from content hash
            etag = f'"{hash(content)}"'
            response['ETag'] = etag
        
        return response
    
    return wrapper
