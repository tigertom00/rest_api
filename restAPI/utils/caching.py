import hashlib
import json
import logging
from functools import wraps
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


def cache_key_generator(prefix: str, *args, **kwargs) -> str:
    """
    Generate a consistent cache key from function arguments.

    Args:
        prefix: Cache key prefix
        *args: Function positional arguments
        **kwargs: Function keyword arguments

    Returns:
        Hashed cache key string
    """
    # Create a deterministic string from arguments
    key_data = {"args": str(args), "kwargs": sorted(kwargs.items()) if kwargs else []}

    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()

    return f"{prefix}:{key_hash}"


def cached_query(timeout: int = 300, key_prefix: str = "query"):
    """
    Decorator for caching database query results.

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys

    Usage:
        @cached_query(timeout=600, key_prefix="user_tasks")
        def get_user_tasks(user_id):
            return Task.objects.filter(user_id=user_id)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_generator(
                f"{key_prefix}:{func.__name__}", *args, **kwargs
            )

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set for {cache_key}")

            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Cache key pattern to match

    Note: This requires a cache backend that supports pattern deletion
    """
    try:
        # For Redis backend, we can use pattern deletion
        if hasattr(cache, "delete_pattern"):
            cache.delete_pattern(f"*{pattern}*")
        else:
            # For other backends, we'd need to track keys separately
            logger.warning(
                f"Pattern cache invalidation not supported for pattern: {pattern}"
            )
    except Exception as e:
        logger.error(f"Cache invalidation failed for pattern {pattern}: {e}")


class CacheManager:
    """
    Centralized cache management for API responses and database queries.
    """

    # Cache timeout configurations
    TIMEOUTS = {
        "user_data": 300,  # 5 minutes
        "task_lists": 180,  # 3 minutes
        "project_data": 600,  # 10 minutes
        "blog_posts": 900,  # 15 minutes
        "media_files": 1800,  # 30 minutes
        "admin_data": 120,  # 2 minutes
        "categories": 3600,  # 1 hour (rarely changes)
    }

    @classmethod
    def get_user_cache_key(cls, user_id: int, data_type: str) -> str:
        """Generate cache key for user-specific data."""
        return f"user:{user_id}:{data_type}"

    @classmethod
    def get_list_cache_key(cls, data_type: str, filters: dict = None) -> str:
        """Generate cache key for filtered lists."""
        if filters:
            filter_hash = hashlib.md5(
                json.dumps(filters, sort_keys=True).encode()
            ).hexdigest()
            return f"list:{data_type}:{filter_hash}"
        return f"list:{data_type}:all"

    @classmethod
    def cache_user_data(
        cls, user_id: int, data_type: str, data: Any, timeout: int | None = None
    ):
        """Cache user-specific data."""
        cache_key = cls.get_user_cache_key(user_id, data_type)
        cache_timeout = timeout or cls.TIMEOUTS.get(data_type, 300)
        cache.set(cache_key, data, cache_timeout)

    @classmethod
    def get_user_data(cls, user_id: int, data_type: str) -> Any:
        """Retrieve cached user-specific data."""
        cache_key = cls.get_user_cache_key(user_id, data_type)
        return cache.get(cache_key)

    @classmethod
    def invalidate_user_cache(cls, user_id: int, data_types: list = None):
        """Invalidate all cache entries for a user."""
        if data_types:
            for data_type in data_types:
                cache_key = cls.get_user_cache_key(user_id, data_type)
                cache.delete(cache_key)
        else:
            # Invalidate all user data (requires pattern support)
            invalidate_cache_pattern(f"user:{user_id}")

    @classmethod
    def cache_list_data(
        cls,
        data_type: str,
        data: Any,
        filters: dict = None,
        timeout: int | None = None,
    ):
        """Cache list data with optional filters."""
        cache_key = cls.get_list_cache_key(data_type, filters)
        cache_timeout = timeout or cls.TIMEOUTS.get(data_type, 300)
        cache.set(cache_key, data, cache_timeout)

    @classmethod
    def get_list_data(cls, data_type: str, filters: dict = None) -> Any:
        """Retrieve cached list data."""
        cache_key = cls.get_list_cache_key(data_type, filters)
        return cache.get(cache_key)

    @classmethod
    def invalidate_list_cache(cls, data_type: str):
        """Invalidate all cached lists of a specific type."""
        invalidate_cache_pattern(f"list:{data_type}")


def cache_api_response(timeout: int = 300):
    """
    Decorator for caching API response data.

    Args:
        timeout: Cache timeout in seconds

    Usage:
        @cache_api_response(timeout=600)
        def list(self, request, *args, **kwargs):
            return super().list(request, *args, **kwargs)
    """

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            # Only cache GET requests
            if request.method != "GET":
                return view_method(self, request, *args, **kwargs)

            # Generate cache key from request parameters
            cache_key = cache_key_generator(
                f"api:{self.__class__.__name__}:{view_method.__name__}",
                request.GET.dict(),
                getattr(request.user, "id", None) if hasattr(request, "user") else None,
            )

            # Try cache first
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

            # Execute view and cache response
            response = view_method(self, request, *args, **kwargs)

            # Only cache successful responses
            if hasattr(response, "status_code") and response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


class QueryOptimizer:
    """
    Database query optimization utilities.
    """

    @staticmethod
    def optimize_queryset_for_list(
        queryset, related_fields: list = None, prefetch_fields: list = None
    ):
        """
        Optimize queryset for list views with select_related and prefetch_related.

        Args:
            queryset: Base queryset
            related_fields: Fields for select_related
            prefetch_fields: Fields for prefetch_related

        Returns:
            Optimized queryset
        """
        if related_fields:
            queryset = queryset.select_related(*related_fields)

        if prefetch_fields:
            queryset = queryset.prefetch_related(*prefetch_fields)

        return queryset

    @staticmethod
    def add_only_fields(queryset, fields: list):
        """
        Limit queryset to only specified fields for performance.

        Args:
            queryset: Base queryset
            fields: List of field names to include

        Returns:
            Optimized queryset with only() applied
        """
        return queryset.only(*fields) if fields else queryset

    @staticmethod
    def optimize_task_queryset(queryset):
        """Optimize Task queryset with common related fields."""
        return queryset.select_related("user_id", "project").prefetch_related(
            "category", "images"
        )

    @staticmethod
    def optimize_blog_queryset(queryset):
        """Optimize BlogPost queryset with common related fields."""
        return queryset.select_related("author").prefetch_related(
            "tags", "images", "audio_files", "youtube_videos"
        )

    @staticmethod
    def optimize_media_queryset(queryset):
        """Optimize BlogMedia queryset with common related fields."""
        return queryset.select_related("uploaded_by")
