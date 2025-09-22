import docker
import psutil
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from .models import DockerHost, DockerContainer, ContainerStats, SystemStats, ProcessStats

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

    def update_host_system_info(self, host=None):
        """Update system specifications for a host"""
        if not host:
            host = self.get_or_create_host()

        try:
            # CPU info
            cpu_info = {}
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.strip():
                            key, value = line.split(':', 1)
                            key = key.strip()
                            if key == 'model name' and 'model_name' not in cpu_info:
                                cpu_info['model_name'] = value.strip()
                            elif key == 'processor':
                                cpu_info['cores'] = int(value.strip()) + 1
            except:
                pass

            # Memory info
            memory = psutil.virtual_memory()

            # System info
            import platform
            uname = platform.uname()

            # Update host with system info
            host.cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count()
            host.cpu_model = cpu_info.get('model_name', uname.processor)
            host.total_memory = memory.total
            host.architecture = uname.machine
            host.os_name = uname.system
            host.os_version = uname.release
            host.kernel_version = uname.version
            host.save()

            logger.info(f"Updated system info for host {host.name}")
            return host

        except Exception as e:
            logger.error(f"Error updating system info for host {host.name}: {e}")
            return host

    def collect_system_stats(self, host=None):
        """Collect current system statistics"""
        if not host:
            host = self.get_or_create_host()

        try:
            # CPU stats
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Windows doesn't have getloadavg
                load_avg = (None, None, None)

            # Memory stats
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk stats (root filesystem)
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # Network stats
            network_io = psutil.net_io_counters()

            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.get_current_timezone())

            # Process count
            process_count = len(psutil.pids())

            # CPU temperature (if available)
            cpu_temp = None
            try:
                temps = psutil.sensors_temperatures()
                if 'coretemp' in temps:
                    cpu_temp = temps['coretemp'][0].current
                elif 'cpu_thermal' in temps:
                    cpu_temp = temps['cpu_thermal'][0].current
            except:
                pass

            # Create SystemStats record
            stats_data = {
                'host': host,
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_avg_1m': load_avg[0],
                'load_avg_5m': load_avg[1],
                'load_avg_15m': load_avg[2],
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'memory_free': memory.free,
                'memory_percent': memory.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': swap.percent,
                'disk_total': disk_usage.total,
                'disk_used': disk_usage.used,
                'disk_free': disk_usage.free,
                'disk_percent': (disk_usage.used / disk_usage.total) * 100,
                'network_bytes_sent': network_io.bytes_sent,
                'network_bytes_recv': network_io.bytes_recv,
                'network_packets_sent': network_io.packets_sent,
                'network_packets_recv': network_io.packets_recv,
                'boot_time': boot_time,
                'process_count': process_count,
                'cpu_temperature': cpu_temp,
            }

            if disk_io:
                stats_data.update({
                    'disk_read_bytes': disk_io.read_bytes,
                    'disk_write_bytes': disk_io.write_bytes,
                    'disk_read_count': disk_io.read_count,
                    'disk_write_count': disk_io.write_count,
                })

            system_stats = SystemStats.objects.create(**stats_data)
            logger.info(f"Collected system stats for host {host.name}")
            return system_stats

        except Exception as e:
            logger.error(f"Error collecting system stats for host {host.name}: {e}")
            return None

    def collect_top_processes(self, host=None, limit=10):
        """Collect information about top processes by CPU usage"""
        if not host:
            host = self.get_or_create_host()

        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent',
                                           'memory_percent', 'memory_info', 'status',
                                           'create_time', 'cmdline']):
                try:
                    info = proc.info
                    if info['cpu_percent'] is None:
                        continue

                    process_data = {
                        'host': host,
                        'pid': info['pid'],
                        'name': info['name'] or '',
                        'username': info['username'] or '',
                        'cpu_percent': info['cpu_percent'],
                        'memory_percent': info['memory_percent'],
                        'status': info['status'] or '',
                        'cmdline': ' '.join(info['cmdline'] or [])[:500],  # Limit cmdline length
                    }

                    if info['memory_info']:
                        process_data.update({
                            'memory_rss': info['memory_info'].rss,
                            'memory_vms': info['memory_info'].vms,
                        })

                    if info['create_time']:
                        process_data['create_time'] = datetime.fromtimestamp(
                            info['create_time'], tz=timezone.get_current_timezone()
                        )

                    processes.append(process_data)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Sort by CPU usage and take top processes
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            top_processes = processes[:limit]

            # Create ProcessStats records
            process_stats = []
            for proc_data in top_processes:
                process_stat = ProcessStats.objects.create(**proc_data)
                process_stats.append(process_stat)

            logger.info(f"Collected top {len(process_stats)} processes for host {host.name}")
            return process_stats

        except Exception as e:
            logger.error(f"Error collecting process stats for host {host.name}: {e}")
            return []