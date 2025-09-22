from celery import shared_task
from django.utils import timezone
import logging
from .services import DockerMonitoringService
from .models import DockerHost

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def sync_containers(self):
    """
    Sync all Docker containers from local host.
    This task runs every 2 minutes via Celery Beat.
    """
    try:
        service = DockerMonitoringService()
        container_count = service.sync_containers()

        logger.info(f"Task {self.request.id}: Synced {container_count} containers")
        return f"Synced {container_count} containers"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@shared_task(bind=True, ignore_result=True)
def collect_stats(self):
    """
    Collect performance stats for all running containers.
    This task runs every 5 minutes via Celery Beat.
    """
    try:
        service = DockerMonitoringService()
        stats_count = service.collect_container_stats()

        logger.info(f"Task {self.request.id}: Collected stats for {stats_count} containers")
        return f"Collected stats for {stats_count} containers"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@shared_task(bind=True, ignore_result=True)
def sync_remote_host(self, host_id):
    """
    Sync containers from a specific remote host.
    This would be called by remote agents.
    """
    try:
        host = DockerHost.objects.get(id=host_id)

        if host.is_local:
            # Use local Docker service
            service = DockerMonitoringService()
            container_count = service.sync_containers(host)
        else:
            # For remote hosts, this would be triggered by agent webhook
            logger.info(f"Remote host {host.name} sync triggered")
            container_count = 0

        logger.info(f"Task {self.request.id}: Synced {container_count} containers for host {host.name}")
        return f"Synced {container_count} containers for {host.name}"

    except DockerHost.DoesNotExist:
        logger.error(f"Task {self.request.id}: Host with ID {host_id} not found")
        raise
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@shared_task(bind=True, ignore_result=True)
def collect_system_stats(self):
    """
    Collect system statistics for the local host.
    This task runs every 5 minutes via Celery Beat.
    """
    try:
        service = DockerMonitoringService()

        # Update host system info (less frequently)
        host = service.update_host_system_info()

        # Collect current system stats
        system_stats = service.collect_system_stats(host)

        if system_stats:
            logger.info(f"Task {self.request.id}: Collected system stats for host {host.name}")
            return f"Collected system stats for host {host.name}"
        else:
            logger.warning(f"Task {self.request.id}: Failed to collect system stats")
            return "Failed to collect system stats"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@shared_task(bind=True, ignore_result=True)
def collect_process_stats(self, limit=10):
    """
    Collect top process statistics for the local host.
    This task runs every 10 minutes via Celery Beat.
    """
    try:
        service = DockerMonitoringService()
        host = service.get_or_create_host()

        # Collect top processes
        process_stats = service.collect_top_processes(host, limit)

        logger.info(f"Task {self.request.id}: Collected {len(process_stats)} process stats for host {host.name}")
        return f"Collected {len(process_stats)} process stats for host {host.name}"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise


@shared_task(bind=True, ignore_result=True)
def cleanup_old_stats(self, days=7):
    """
    Clean up old container and system stats older than specified days.
    """
    try:
        from datetime import timedelta
        from .models import ContainerStats, SystemStats, ProcessStats

        cutoff_date = timezone.now() - timedelta(days=days)

        # Clean up container stats
        container_deleted, _ = ContainerStats.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        # Clean up system stats
        system_deleted, _ = SystemStats.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        # Clean up process stats
        process_deleted, _ = ProcessStats.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        total_deleted = container_deleted + system_deleted + process_deleted
        logger.info(f"Task {self.request.id}: Cleaned up {total_deleted} old stats records")
        return f"Cleaned up {total_deleted} old stats records"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise