import logging
import os
import time
from datetime import datetime
from functools import wraps

import psutil
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.cache import never_cache
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

# Configure monitoring logger
monitoring_logger = logging.getLogger("monitoring")


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API performance metrics.
    """

    def process_request(self, request):
        # Start timing the request
        request._monitoring_start_time = time.time()
        request._monitoring_db_queries_start = len(connection.queries)

    def process_response(self, request, response):
        # Calculate response time
        if hasattr(request, "_monitoring_start_time"):
            response_time = time.time() - request._monitoring_start_time
            response["X-Response-Time"] = f"{response_time:.3f}s"

            # Calculate database queries
            db_queries = len(connection.queries) - getattr(
                request, "_monitoring_db_queries_start", 0
            )
            response["X-DB-Queries"] = str(db_queries)

            # Log performance metrics for API endpoints
            if request.path.startswith("/api/"):
                self.log_performance_metrics(
                    request, response, response_time, db_queries
                )

        return response

    def log_performance_metrics(self, request, response, response_time, db_queries):
        """Log performance metrics for monitoring."""
        try:
            # Prepare metrics data
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "response_time": response_time,
                "db_queries": db_queries,
                "user_id": (
                    getattr(request.user, "id", None)
                    if hasattr(request, "user")
                    else None
                ),
                "ip_address": self.get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", "")[:200],
            }

            # Log to monitoring logger
            monitoring_logger.info(
                f"API_METRICS: {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Time: {response_time:.3f}s | "
                f"DB Queries: {db_queries} | "
                f"User: {metrics['user_id']}",
                extra=metrics,
            )

            # Store in cache for real-time metrics (last 100 requests)
            cache_key = "api_performance_metrics"
            cached_metrics = cache.get(cache_key, [])
            cached_metrics.append(metrics)

            # Keep only last 100 requests
            if len(cached_metrics) > 100:
                cached_metrics = cached_metrics[-100:]

            cache.set(cache_key, cached_metrics, 3600)  # Cache for 1 hour

            # Track slow queries (> 500ms or > 10 DB queries)
            if response_time > 0.5 or db_queries > 10:
                self.log_slow_request(metrics)

        except Exception as e:
            # Don't let monitoring break the application
            monitoring_logger.error(f"Failed to log performance metrics: {e}")

    def log_slow_request(self, metrics):
        """Log slow requests for optimization."""
        monitoring_logger.warning(
            f"SLOW_REQUEST: {metrics['method']} {metrics['path']} | "
            f"Time: {metrics['response_time']:.3f}s | "
            f"DB Queries: {metrics['db_queries']}",
            extra={**metrics, "alert_type": "slow_request"},
        )

    def get_client_ip(self, request):
        """Extract client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip or ""


class MetricsCollector:
    """
    Utility class for collecting and aggregating metrics.
    """

    @staticmethod
    def get_system_metrics():
        """Get current system performance metrics."""
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Process-specific metrics
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()

            return {
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": disk.percent,
                "process_memory_rss": process_memory.rss,
                "process_memory_vms": process_memory.vms,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            monitoring_logger.error(f"Failed to collect system metrics: {e}")
            return {}

    @staticmethod
    def get_database_metrics():
        """Get database performance metrics."""
        try:
            from django.db import connection

            # Get database connection info
            db_info = {
                "vendor": connection.vendor,
                "queries_count": len(connection.queries),
                "timestamp": datetime.now().isoformat(),
            }

            # Add MySQL-specific metrics if using MySQL
            if connection.vendor == "mysql":
                with connection.cursor() as cursor:
                    # Get connection count
                    cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                    result = cursor.fetchone()
                    if result:
                        db_info["connections"] = int(result[1])

                    # Get query cache hit rate
                    cursor.execute("SHOW STATUS LIKE 'Qcache%'")
                    cache_stats = dict(cursor.fetchall())
                    if "Qcache_hits" in cache_stats and "Qcache_inserts" in cache_stats:
                        hits = int(cache_stats["Qcache_hits"])
                        inserts = int(cache_stats["Qcache_inserts"])
                        if (hits + inserts) > 0:
                            db_info["query_cache_hit_rate"] = (
                                hits / (hits + inserts) * 100
                            )

            return db_info
        except Exception as e:
            monitoring_logger.error(f"Failed to collect database metrics: {e}")
            return {}

    @staticmethod
    def get_cache_metrics():
        """Get cache performance metrics."""
        try:
            from django.core.cache import cache

            # Try to get cache stats (works with Redis and Memcached)
            cache_stats = {}

            # Basic cache test
            test_key = "health_check_cache_test"
            cache.set(test_key, "test_value", 10)
            cache_working = cache.get(test_key) == "test_value"
            cache.delete(test_key)

            cache_stats.update(
                {
                    "cache_working": cache_working,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Try to get Redis-specific stats if available
            try:
                from django.core.cache.backends.redis import RedisCache

                if isinstance(cache._cache, RedisCache):
                    redis_client = cache._cache.get_client(None)
                    redis_info = redis_client.info()
                    cache_stats.update(
                        {
                            "redis_memory_used": redis_info.get("used_memory"),
                            "redis_connected_clients": redis_info.get(
                                "connected_clients"
                            ),
                            "redis_keyspace_hits": redis_info.get("keyspace_hits"),
                            "redis_keyspace_misses": redis_info.get("keyspace_misses"),
                        }
                    )

                    # Calculate hit rate
                    hits = redis_info.get("keyspace_hits", 0)
                    misses = redis_info.get("keyspace_misses", 0)
                    if (hits + misses) > 0:
                        cache_stats["hit_rate"] = hits / (hits + misses) * 100
            except Exception:
                pass  # Redis not available or different cache backend

            return cache_stats
        except Exception as e:
            monitoring_logger.error(f"Failed to collect cache metrics: {e}")
            return {}


@api_view(["GET"])
@permission_classes([IsAdminUser])
@never_cache
def metrics_endpoint(request):
    """
    API endpoint for retrieving performance metrics.
    Admin-only access for security.
    """
    try:
        # Collect all metrics
        metrics = {
            "system": MetricsCollector.get_system_metrics(),
            "database": MetricsCollector.get_database_metrics(),
            "cache": MetricsCollector.get_cache_metrics(),
            "api_performance": cache.get("api_performance_metrics", []),
        }

        # Calculate API performance summary
        api_metrics = metrics["api_performance"]
        if api_metrics:
            response_times = [m["response_time"] for m in api_metrics]
            db_queries = [m["db_queries"] for m in api_metrics]

            metrics["api_summary"] = {
                "total_requests": len(api_metrics),
                "avg_response_time": sum(response_times) / len(response_times),
                "max_response_time": max(response_times),
                "avg_db_queries": sum(db_queries) / len(db_queries),
                "max_db_queries": max(db_queries),
                "slow_requests": len(
                    [m for m in api_metrics if m["response_time"] > 0.5]
                ),
            }

        return Response(metrics)

    except Exception as e:
        monitoring_logger.error(f"Failed to generate metrics response: {e}")
        return Response({"error": "Failed to collect metrics"}, status=500)


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def health_check(request):
    """
    Health check endpoint for monitoring system status.
    Django view for simpler access control.
    """
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {},
        }

        # Database health check
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Cache health check
        try:
            test_key = "health_check_cache"
            cache.set(test_key, "test", 10)
            if cache.get(test_key) == "test":
                health_status["checks"]["cache"] = "healthy"
            else:
                health_status["checks"]["cache"] = "unhealthy: cache not working"
                health_status["status"] = "degraded"
            cache.delete(test_key)
        except Exception as e:
            health_status["checks"]["cache"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # System resource checks
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Check if resources are within acceptable limits
            if cpu_percent > 90:
                health_status["checks"]["cpu"] = f"warning: high usage {cpu_percent}%"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["cpu"] = "healthy"

            if memory.percent > 90:
                health_status["checks"][
                    "memory"
                ] = f"warning: high usage {memory.percent}%"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["memory"] = "healthy"

            if disk.percent > 90:
                health_status["checks"]["disk"] = f"warning: high usage {disk.percent}%"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["disk"] = "healthy"

        except Exception as e:
            health_status["checks"]["system"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

        # Return appropriate status code
        status_code = 200 if health_status["status"] == "healthy" else 503

        return JsonResponse(health_status, status=status_code)

    except Exception as e:
        monitoring_logger.error(f"Health check failed: {e}")
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
            status=503,
        )


def monitor_performance(operation_name):
    """
    Decorator for monitoring specific function performance.

    Usage:
        @monitor_performance('expensive_operation')
        def my_expensive_function():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                execution_time = time.time() - start_time

                # Log performance metrics
                monitoring_logger.info(
                    f"OPERATION_METRICS: {operation_name} | "
                    f"Time: {execution_time:.3f}s | "
                    f"Success: {success}",
                    extra={
                        "operation": operation_name,
                        "execution_time": execution_time,
                        "success": success,
                        "error": error,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return result

        return wrapper

    return decorator
