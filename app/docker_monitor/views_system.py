from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import DockerHost, SystemStats, ProcessStats
from .serializers import (
    DockerHostSerializer, SystemStatsSerializer, ProcessStatsSerializer
)
from .services import DockerMonitoringService


class SystemStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemStats.objects.select_related('host')
    serializer_class = SystemStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by host
        host_id = self.request.query_params.get('host_id')
        if host_id:
            queryset = queryset.filter(host_id=host_id)

        # Filter by time range
        hours = int(self.request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)
        queryset = queryset.filter(timestamp__gte=since)

        return queryset.order_by('-timestamp')

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest system stats for all hosts"""
        hosts = DockerHost.objects.filter(is_active=True)
        results = []

        for host in hosts:
            latest_stat = host.system_stats.first()
            if latest_stat:
                results.append({
                    'host': DockerHostSerializer(host).data,
                    'stats': SystemStatsSerializer(latest_stat).data
                })

        return Response({
            'count': len(results),
            'results': results
        })


class ProcessStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProcessStats.objects.select_related('host')
    serializer_class = ProcessStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by host
        host_id = self.request.query_params.get('host_id')
        if host_id:
            queryset = queryset.filter(host_id=host_id)

        # Get recent process stats only (last hour by default)
        hours = int(self.request.query_params.get('hours', 1))
        since = timezone.now() - timedelta(hours=hours)
        queryset = queryset.filter(timestamp__gte=since)

        return queryset.order_by('-timestamp', '-cpu_percent')

    @action(detail=False, methods=['get'])
    def top_cpu(self, request):
        """Get top CPU consuming processes across all hosts"""
        limit = int(request.query_params.get('limit', 10))
        host_id = request.query_params.get('host_id')

        queryset = self.get_queryset()
        if host_id:
            queryset = queryset.filter(host_id=host_id)

        # Get the most recent process stats per host
        top_processes = queryset[:limit]
        serializer = self.get_serializer(top_processes, many=True)

        return Response({
            'count': len(serializer.data),
            'processes': serializer.data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_dashboard(request, host_id=None):
    """Get comprehensive system dashboard data"""
    try:
        if host_id:
            try:
                host = DockerHost.objects.get(id=host_id)
            except DockerHost.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Host not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get the local host or first active host
            host = DockerHost.objects.filter(is_local=True).first()
            if not host:
                host = DockerHost.objects.filter(is_active=True).first()

        if not host:
            return Response({
                'status': 'error',
                'message': 'No active hosts found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get latest system stats
        current_system_stats = host.system_stats.first()

        # Get containers summary
        containers_summary = {
            'total': host.containers.count(),
            'running': host.containers.filter(status='running').count(),
            'stopped': host.containers.filter(status='exited').count(),
            'paused': host.containers.filter(status='paused').count(),
        }

        # Get top processes
        top_processes = host.process_stats.order_by('-timestamp', '-cpu_percent')[:10]

        # Get time-series data for charts (last 24 hours)
        hours_back = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours_back)
        system_stats_history = host.system_stats.filter(
            timestamp__gte=since
        ).order_by('timestamp')

        # Prepare chart data
        cpu_history = []
        memory_history = []
        disk_history = []
        network_history = []

        for stat in system_stats_history:
            timestamp = stat.timestamp.isoformat()
            cpu_history.append({
                'timestamp': timestamp,
                'cpu_percent': stat.cpu_percent,
                'load_avg_1m': stat.load_avg_1m,
                'load_avg_5m': stat.load_avg_5m,
                'load_avg_15m': stat.load_avg_15m,
            })
            memory_history.append({
                'timestamp': timestamp,
                'memory_percent': stat.memory_percent,
                'memory_used': stat.memory_used,
                'memory_available': stat.memory_available,
                'swap_percent': stat.swap_percent,
            })
            disk_history.append({
                'timestamp': timestamp,
                'disk_percent': stat.disk_percent,
                'disk_read_bytes': stat.disk_read_bytes,
                'disk_write_bytes': stat.disk_write_bytes,
            })
            network_history.append({
                'timestamp': timestamp,
                'network_bytes_sent': stat.network_bytes_sent,
                'network_bytes_recv': stat.network_bytes_recv,
            })

        dashboard_data = {
            'host': DockerHostSerializer(host).data,
            'current_system_stats': SystemStatsSerializer(current_system_stats).data if current_system_stats else None,
            'containers_summary': containers_summary,
            'top_processes': ProcessStatsSerializer(top_processes, many=True).data,
            'cpu_history': cpu_history,
            'memory_history': memory_history,
            'disk_history': disk_history,
            'network_history': network_history,
        }

        return Response(dashboard_data)

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def collect_system_metrics(request):
    """Manually trigger system metrics collection"""
    try:
        service = DockerMonitoringService()
        host = service.get_or_create_host()

        # Update system info
        service.update_host_system_info(host)

        # Collect system stats
        system_stats = service.collect_system_stats(host)

        # Collect process stats
        process_stats = service.collect_top_processes(host, limit=10)

        return Response({
            'status': 'success',
            'message': 'System metrics collected successfully',
            'host': host.name,
            'system_stats_collected': bool(system_stats),
            'process_stats_collected': len(process_stats)
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)