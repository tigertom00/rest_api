import time

from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(UserRateThrottle):
    """
    Rate limiting for login attempts.
    Stricter limits to prevent brute force attacks.
    """

    scope = "login"


class APIRateThrottle(UserRateThrottle):
    """
    General API rate limiting for authenticated users.
    Reasonable limits for normal API usage.
    """

    scope = "api"


class UploadRateThrottle(UserRateThrottle):
    """
    Rate limiting for file upload endpoints.
    More restrictive due to resource-intensive operations.
    """

    scope = "upload"


class BulkOperationRateThrottle(UserRateThrottle):
    """
    Rate limiting for bulk operations.
    Very restrictive to prevent system overload.
    """

    scope = "bulk"


class AdminRateThrottle(UserRateThrottle):
    """
    Rate limiting for admin operations.
    Moderate limits for administrative tasks.
    """

    scope = "admin"


class AnonymousRateThrottle(AnonRateThrottle):
    """
    Rate limiting for anonymous users.
    Restrictive limits for unauthenticated requests.
    """

    scope = "anon"


class SustainedRateThrottle(UserRateThrottle):
    """
    Sustained rate limiting to prevent sustained abuse.
    Tracks longer time periods (hourly/daily).
    """

    scope = "sustained"

    def get_cache_key(self, request, view):
        """
        Create cache key that includes both user and time window.
        This allows for multiple time-based rate limits.
        """
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        # Create different keys for different time windows
        current_hour = int(time.time() // 3600)
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{ident}_{current_hour}",
        }


class DatabaseOperationThrottle(UserRateThrottle):
    """
    Rate limiting specifically for database-heavy operations.
    Applied to endpoints that perform complex queries or bulk operations.
    """

    scope = "database"

    def allow_request(self, request, view):
        """
        Override to add additional checks for database operations.
        """
        # Check if user has exceeded database operation limits
        if not super().allow_request(request, view):
            return False

        # Additional check for concurrent operations
        if hasattr(request.user, "is_authenticated") and request.user.is_authenticated:
            concurrent_key = f"db_ops_concurrent_{request.user.pk}"
            concurrent_ops = cache.get(concurrent_key, 0)

            # Limit concurrent database operations per user
            if concurrent_ops >= 3:  # Max 3 concurrent operations
                return False

            # Increment concurrent operations counter
            cache.set(concurrent_key, concurrent_ops + 1, timeout=60)

        return True
