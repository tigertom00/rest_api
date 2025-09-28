# API Performance Monitoring

This Django REST API includes comprehensive performance monitoring and metrics collection.

## Monitoring Features

### 1. Performance Monitoring Middleware
- **Automatic request timing**: All API requests are automatically timed
- **Database query counting**: Tracks number of DB queries per request
- **Response headers**: Adds `X-Response-Time` and `X-DB-Queries` headers
- **Slow request detection**: Logs warnings for requests > 500ms or > 10 DB queries

### 2. Metrics Collection
- **System metrics**: CPU, memory, and disk usage
- **Database metrics**: Connection count and query cache hit rate (MySQL)
- **Cache metrics**: Cache hit/miss rates and memory usage (Redis)
- **API performance**: Response times, query counts, and request patterns

### 3. Health Check Endpoint
**Endpoint**: `GET /api/health/`

Returns system health status including:
- Database connectivity
- Cache functionality
- System resource usage
- Overall health status

**Response Format**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-28T10:00:00Z",
  "checks": {
    "database": "healthy",
    "cache": "healthy",
    "cpu": "healthy",
    "memory": "healthy",
    "disk": "healthy"
  }
}
```

### 4. Admin Metrics Dashboard
**Endpoint**: `GET /api/admin/metrics/` (Admin-only)

Provides comprehensive performance metrics:
- System resource usage
- Database performance stats
- Cache performance metrics
- API performance summary
- Recent request metrics

**Response Format**:
```json
{
  "system": {
    "cpu_percent": 25.0,
    "memory_percent": 45.2,
    "disk_percent": 60.1
  },
  "database": {
    "vendor": "mysql",
    "connections": 15,
    "query_cache_hit_rate": 85.5
  },
  "cache": {
    "cache_working": true,
    "hit_rate": 92.3,
    "redis_memory_used": 12582912
  },
  "api_summary": {
    "total_requests": 100,
    "avg_response_time": 0.125,
    "max_response_time": 2.501,
    "slow_requests": 2
  }
}
```

## Performance Monitoring Decorator

Use the `@monitor_performance` decorator to monitor specific operations:

```python
from restAPI.utils.monitoring import monitor_performance

@monitor_performance('expensive_operation')
def my_expensive_function():
    # Your code here
    pass
```

## Logging Configuration

The monitoring system uses Django's logging framework:

- **Logger**: `monitoring` - Performance and metrics logs
- **Logger**: `audit` - Security and audit logs
- **Level**: INFO for normal operations, WARNING for slow requests

## Monitoring Data Storage

- **Real-time metrics**: Cached in Redis/memory for 1 hour
- **Performance logs**: Written to Django logs
- **Historical data**: Consider integrating with external monitoring services

## Integration with External Monitoring

The monitoring endpoints can be integrated with:
- **Prometheus**: Scrape `/api/admin/metrics/` endpoint
- **Grafana**: Create dashboards using the metrics data
- **Health checks**: Use `/api/health/` for load balancer health checks
- **Alerting**: Set up alerts based on slow request logs

## Security Notes

- Admin metrics endpoint requires admin authentication
- Health check endpoint is publicly accessible (as intended for load balancers)
- Monitoring logs may contain sensitive path information - review log retention policies
- Performance data is cached briefly - consider security implications in shared environments

## Performance Considerations

- Monitoring middleware adds minimal overhead (~1-2ms per request)
- Metrics are cached to avoid database queries on each request
- System metrics collection uses efficient system calls
- Health checks are optimized for frequent polling

## Usage Examples

### Check API Health
```bash
curl http://your-api.com/api/health/
```

### Get Performance Metrics (Admin only)
```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://your-api.com/api/admin/metrics/
```

### Monitor Response Times
Check response headers for timing information:
```bash
curl -I http://your-api.com/api/tasks/
```

Look for:
- `X-Response-Time: 0.125s`
- `X-DB-Queries: 3`
