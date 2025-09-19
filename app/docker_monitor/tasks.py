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
def cleanup_old_stats(self, days=7):
    """
    Clean up old container stats older than specified days.
    """
    try:
        from datetime import timedelta
        from .models import ContainerStats

        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count, _ = ContainerStats.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()

        logger.info(f"Task {self.request.id}: Cleaned up {deleted_count} old stats records")
        return f"Cleaned up {deleted_count} old stats records"

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise