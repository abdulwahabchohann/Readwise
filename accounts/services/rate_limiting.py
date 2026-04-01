"""Rate limiting utilities for API endpoints using django-ratelimit."""
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from functools import wraps


def get_client_ip(request):
    """Get the client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip.strip() if ip else 'unknown'


def rate_limit_api(rate_str: str):
    """
    Decorator for rate limiting API endpoints.
    
    Args:
        rate_str: Rate string (e.g., '100/h' for 100 requests per hour)
    
    Examples:
        @rate_limit_api('100/h')
        def api_view(request):
            ...
    """
    def decorator(view_func):
        # Use django-ratelimit with IP-based key
        @ratelimit(key='ip', rate=rate_str, method='POST')
        @ratelimit(key='ip', rate=rate_str, method='GET')
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def handle_rate_limit_exceeded(request):
    """Return a rate limit exceeded response."""
    return JsonResponse(
        {'error': 'Rate limit exceeded. Please try again later.'},
        status=429
    )


class APIRateLimitMixin:
    """Mixin for DRF APIView classes to add rate limiting."""
    
    # Override these in your view
    rate_limit = '100/h'  # Default: 100 requests per hour
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to apply rate limiting."""
        # Get the key function for rate limiting
        key_func = self.get_rate_limit_key
        
        # Apply rate limit check
        @ratelimit(key=key_func, rate=self.rate_limit, method=request.method)
        def check_and_proceed(*args, **kwargs):
            return super(APIRateLimitMixin, self).dispatch(request, *args, **kwargs)
        
        try:
            return check_and_proceed(*args, **kwargs)
        except Exception as e:
            # If rate limited, catch and return error
            if 'rate limit' in str(e).lower():
                return handle_rate_limit_exceeded(request)
            raise
    
    @staticmethod
    def get_rate_limit_key(group, request):
        """Get the rate limit key based on IP address."""
        return get_client_ip(request)
