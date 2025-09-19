from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from .models import DockerHost, DockerContainer, ContainerStats
from .serializers import (
    DockerHostSerializer, DockerContainerSerializer,
    DockerContainerDetailSerializer, ContainerStatsSerializer
)
from .services import DockerMonitoringService


class DockerHostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DockerHost.objects.all()
    serializer_class = DockerHostSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def sync_containers(self, request, pk=None):
        """Manually trigger container sync for a specific host"""
        host = self.get_object()

        try:
            service = DockerMonitoringService()
            if host.is_local:
                container_count = service.sync_containers(host)
                return Response({
                    'status': 'success',
                    'message': f'Synced {container_count} containers',
                    'container_count': container_count
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Remote host sync not implemented yet'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overview statistics of all hosts"""
        hosts = self.get_queryset()
        total_containers = 0
        running_containers = 0

        for host in hosts:
            total_containers += host.containers.count()
            running_containers += host.containers.filter(status='running').count()

        return Response({
            'total_hosts': hosts.count(),
            'active_hosts': hosts.filter(is_active=True).count(),
            'total_containers': total_containers,
            'running_containers': running_containers,
            'last_updated': timezone.now()
        })


class DockerContainerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DockerContainer.objects.select_related('host').prefetch_related('stats')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DockerContainerDetailSerializer
        return DockerContainerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by host
        host_id = self.request.query_params.get('host_id')
        if host_id:
            queryset = queryset.filter(host_id=host_id)

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by running containers only
        running_only = self.request.query_params.get('running_only')
        if running_only and running_only.lower() == 'true':
            queryset = queryset.filter(status='running')

        return queryset.order_by('-updated_at')

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed stats for a container"""
        container = self.get_object()

        # Get time range from query params
        hours = int(request.query_params.get('hours', 24))
        since = timezone.now() - timedelta(hours=hours)

        stats = container.stats.filter(timestamp__gte=since).order_by('-timestamp')

        # Limit results to prevent huge responses
        limit = int(request.query_params.get('limit', 1000))
        stats = stats[:limit]

        serializer = ContainerStatsSerializer(stats, many=True)
        return Response({
            'container_id': container.container_id,
            'container_name': container.name,
            'time_range_hours': hours,
            'stats_count': len(serializer.data),
            'stats': serializer.data
        })

    @action(detail=False, methods=['get'])
    def running(self, request):
        """Get all running containers across all hosts"""
        running_containers = self.get_queryset().filter(status='running')
        serializer = self.get_serializer(running_containers, many=True)

        return Response({
            'count': running_containers.count(),
            'containers': serializer.data
        })

    @action(detail=False, methods=['post'])
    def refresh_stats(self, request):
        """Manually trigger stats collection for all running containers"""
        try:
            service = DockerMonitoringService()
            stats_count = service.collect_container_stats()

            return Response({
                'status': 'success',
                'message': f'Collected stats for {stats_count} containers',
                'stats_count': stats_count
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)