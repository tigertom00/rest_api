from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta, datetime

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_sync_containers(request):
    """Webhook endpoint for remote agents to sync container data"""

    try:
        data = request.data
        host_data = data.get('host', {})
        containers_data = data.get('containers', [])

        # Get or create host
        host, created = DockerHost.objects.get_or_create(
            name=host_data.get('name'),
            defaults={
                'hostname': host_data.get('hostname', host_data.get('name')),
                'is_local': False,
                'is_active': True,
                'last_seen': timezone.now()
            }
        )

        if not created:
            host.last_seen = timezone.now()
            host.is_active = True
            host.save(update_fields=['last_seen', 'is_active'])

        # Track container IDs from this sync
        synced_container_ids = []

        # Process each container
        for container_data in containers_data:
            # Parse timestamps
            created_at = timezone.now()
            if container_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(container_data['created_at'].replace('Z', '+00:00'))
                except:
                    pass

            started_at = None
            if container_data.get('started_at') and container_data['started_at'] != '0001-01-01T00:00:00Z':
                try:
                    started_at = datetime.fromisoformat(container_data['started_at'].replace('Z', '+00:00'))
                except:
                    pass

            finished_at = None
            if container_data.get('finished_at') and container_data['finished_at'] != '0001-01-01T00:00:00Z':
                try:
                    finished_at = datetime.fromisoformat(container_data['finished_at'].replace('Z', '+00:00'))
                except:
                    pass

            # Update or create container
            container, created = DockerContainer.objects.update_or_create(
                host=host,
                container_id=container_data['container_id'],
                defaults={
                    'name': container_data.get('name', ''),
                    'image': container_data.get('image', ''),
                    'status': container_data.get('status', 'unknown'),
                    'state': container_data.get('state', {}),
                    'ports': container_data.get('ports', []),
                    'labels': container_data.get('labels', {}),
                    'networks': container_data.get('networks', {}),
                    'mounts': container_data.get('mounts', []),
                    'created_at': created_at,
                    'started_at': started_at,
                    'finished_at': finished_at,
                }
            )

            synced_container_ids.append(container.container_id)

        # Mark containers not in this sync as potentially removed
        stale_containers = DockerContainer.objects.filter(
            host=host
        ).exclude(container_id__in=synced_container_ids)

        stale_count = stale_containers.count()
        if stale_count > 0:
            stale_containers.update(status='removed', updated_at=timezone.now())

        return Response({
            'status': 'success',
            'message': f'Synced {len(containers_data)} containers for {host.name}',
            'host': host.name,
            'synced_containers': len(containers_data),
            'marked_removed': stale_count
        })

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def agent_sync_containers(request):
    """Webhook endpoint for remote agents to sync container data"""

    try:
        data = request.data
        host_data = data.get('host', {})
        containers_data = data.get('containers', [])

        # Get or create host
        host, created = DockerHost.objects.get_or_create(
            name=host_data.get('name'),
            defaults={
                'hostname': host_data.get('hostname', host_data.get('name')),
                'is_local': False,
                'is_active': True,
                'last_seen': timezone.now()
            }
        )

        if not created:
            host.last_seen = timezone.now()
            host.is_active = True
            host.save(update_fields=['last_seen', 'is_active'])

        # Track container IDs from this sync
        synced_container_ids = []

        # Process each container
        for container_data in containers_data:
            # Parse timestamps
            created_at = timezone.now()
            if container_data.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(container_data['created_at'].replace('Z', '+00:00'))
                except:
                    pass

            started_at = None
            if container_data.get('started_at') and container_data['started_at'] != '0001-01-01T00:00:00Z':
                try:
                    started_at = datetime.fromisoformat(container_data['started_at'].replace('Z', '+00:00'))
                except:
                    pass

            finished_at = None
            if container_data.get('finished_at') and container_data['finished_at'] != '0001-01-01T00:00:00Z':
                try:
                    finished_at = datetime.fromisoformat(container_data['finished_at'].replace('Z', '+00:00'))
                except:
                    pass

            # Update or create container
            container, created = DockerContainer.objects.update_or_create(
                host=host,
                container_id=container_data['container_id'],
                defaults={
                    'name': container_data.get('name', ''),
                    'image': container_data.get('image', ''),
                    'status': container_data.get('status', 'unknown'),
                    'state': container_data.get('state', {}),
                    'ports': container_data.get('ports', []),
                    'labels': container_data.get('labels', {}),
                    'networks': container_data.get('networks', {}),
                    'mounts': container_data.get('mounts', []),
                    'created_at': created_at,
                    'started_at': started_at,
                    'finished_at': finished_at,
                }
            )

            synced_container_ids.append(container.container_id)

        # Mark containers not in this sync as potentially removed
        stale_containers = DockerContainer.objects.filter(
            host=host
        ).exclude(container_id__in=synced_container_ids)

        stale_count = stale_containers.count()
        if stale_count > 0:
            stale_containers.update(status='removed', updated_at=timezone.now())

        return Response({
            'status': 'success',
            'message': f'Synced {len(containers_data)} containers for {host.name}',
            'host': host.name,
            'synced_containers': len(containers_data),
            'marked_removed': stale_count
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)