import docker
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from .models import DockerHost, DockerContainer, ContainerStats

logger = logging.getLogger(__name__)


class DockerMonitoringService:
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            self.client = None

    def get_or_create_host(self, hostname=None):
        if not hostname:
            try:
                hostname = self.client.info().get('Name', 'localhost')
            except:
                hostname = 'localhost'

        host, created = DockerHost.objects.get_or_create(
            name=hostname,
            defaults={
                'hostname': hostname,
                'is_local': True,
                'is_active': True,
                'last_seen': timezone.now()
            }
        )

        if not created:
            host.last_seen = timezone.now()
            host.save(update_fields=['last_seen'])

        return host

    def sync_containers(self, host=None):
        if not self.client:
            logger.error("Docker client not available")
            return

        if not host:
            host = self.get_or_create_host()

        try:
            containers = self.client.containers.list(all=True)
            container_ids = []

            for container in containers:
                container_data = self._extract_container_data(container)
                container_obj = self._update_or_create_container(host, container_data)
                container_ids.append(container_obj.container_id)

            # Mark containers not found as removed
            DockerContainer.objects.filter(host=host).exclude(
                container_id__in=container_ids
            ).update(status='removed', updated_at=timezone.now())

            logger.info(f"Synced {len(containers)} containers for host {host.name}")
            return len(containers)

        except Exception as e:
            logger.error(f"Error syncing containers: {e}")
            return 0

    def _extract_container_data(self, container):
        attrs = container.attrs

        # Parse port mappings
        ports = []
        port_bindings = attrs.get('NetworkSettings', {}).get('Ports', {})
        for container_port, host_bindings in port_bindings.items():
            if host_bindings:
                for binding in host_bindings:
                    ports.append({
                        'container_port': container_port,
                        'host_ip': binding.get('HostIp', '0.0.0.0'),
                        'host_port': binding.get('HostPort')
                    })

        # Parse created time
        created_str = attrs.get('Created')
        created_at = timezone.now()
        if created_str:
            try:
                created_at = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            except:
                pass

        # Parse started time
        started_at = None
        started_str = attrs.get('State', {}).get('StartedAt')
        if started_str and started_str != '0001-01-01T00:00:00Z':
            try:
                started_at = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
            except:
                pass

        # Parse finished time
        finished_at = None
        finished_str = attrs.get('State', {}).get('FinishedAt')
        if finished_str and finished_str != '0001-01-01T00:00:00Z':
            try:
                finished_at = datetime.fromisoformat(finished_str.replace('Z', '+00:00'))
            except:
                pass

        return {
            'container_id': container.id,
            'name': container.name,
            'image': attrs.get('Config', {}).get('Image', ''),
            'status': container.status,
            'state': attrs.get('State', {}),
            'ports': ports,
            'labels': attrs.get('Config', {}).get('Labels', {}) or {},
            'networks': attrs.get('NetworkSettings', {}).get('Networks', {}),
            'mounts': attrs.get('Mounts', []),
            'created_at': created_at,
            'started_at': started_at,
            'finished_at': finished_at,
        }

    def _update_or_create_container(self, host, container_data):
        container, created = DockerContainer.objects.update_or_create(
            host=host,
            container_id=container_data['container_id'],
            defaults=container_data
        )
        return container

    def collect_container_stats(self, container_id=None):
        if not self.client:
            logger.error("Docker client not available")
            return

        host = self.get_or_create_host()

        if container_id:
            containers = DockerContainer.objects.filter(
                host=host,
                container_id=container_id,
                status='running'
            )
        else:
            containers = DockerContainer.objects.filter(
                host=host,
                status='running'
            )

        stats_collected = 0
        for container_obj in containers:
            try:
                docker_container = self.client.containers.get(container_obj.container_id)
                stats = docker_container.stats(stream=False)

                stats_data = self._parse_container_stats(stats)

                ContainerStats.objects.create(
                    container=container_obj,
                    **stats_data
                )
                stats_collected += 1

            except Exception as e:
                logger.warning(f"Failed to collect stats for {container_obj.name}: {e}")

        logger.info(f"Collected stats for {stats_collected} containers")
        return stats_collected

    def _parse_container_stats(self, stats):
        cpu_stats = stats.get('cpu_stats', {})
        precpu_stats = stats.get('precpu_stats', {})
        memory_stats = stats.get('memory_stats', {})
        networks = stats.get('networks', {})
        blkio_stats = stats.get('blkio_stats', {})

        # Calculate CPU percentage
        cpu_percent = None
        cpu_usage = cpu_stats.get('cpu_usage', {})
        precpu_usage = precpu_stats.get('cpu_usage', {})

        if cpu_usage and precpu_usage:
            cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
            system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
            online_cpus = cpu_stats.get('online_cpus', 1)

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0

        # Memory stats
        memory_usage = memory_stats.get('usage', 0)
        memory_limit = memory_stats.get('limit', 0)
        memory_percent = None
        if memory_limit > 0:
            memory_percent = (memory_usage / memory_limit) * 100.0

        # Network stats
        network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
        network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())

        # Block IO stats
        block_read = sum(
            stat.get('value', 0)
            for stat in blkio_stats.get('io_service_bytes_recursive', [])
            if stat.get('op') == 'Read'
        )
        block_write = sum(
            stat.get('value', 0)
            for stat in blkio_stats.get('io_service_bytes_recursive', [])
            if stat.get('op') == 'Write'
        )

        return {
            'cpu_percent': cpu_percent,
            'memory_usage': memory_usage,
            'memory_limit': memory_limit,
            'memory_percent': memory_percent,
            'network_rx': network_rx,
            'network_tx': network_tx,
            'block_read': block_read,
            'block_write': block_write,
        }