from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .models import UsageSnapshot, Session, Project

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def cleanup_old_snapshots(self, hours=6):
    """
    Clean up usage snapshots older than specified hours.
    Keeps the database lean by removing old data that's no longer needed.

    Default: 6 hours (retains data for current 5-hour window + buffer)
    """
    try:
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Count before deletion
        old_snapshots = UsageSnapshot.objects.filter(timestamp__lt=cutoff_time)
        count = old_snapshots.count()

        if count > 0:
            # Delete old snapshots
            deleted, _ = old_snapshots.delete()

            # Clean up sessions with no snapshots
            empty_sessions = Session.objects.filter(usage_snapshots__isnull=True)
            sessions_deleted = empty_sessions.count()
            empty_sessions.delete()

            # Clean up projects with no sessions
            empty_projects = Project.objects.filter(sessions__isnull=True)
            projects_deleted = empty_projects.count()
            empty_projects.delete()

            logger.info(
                f"Task {self.request.id}: Cleaned up {deleted} snapshots, "
                f"{sessions_deleted} sessions, {projects_deleted} projects "
                f"older than {hours} hours"
            )

            return {
                "deleted_snapshots": deleted,
                "deleted_sessions": sessions_deleted,
                "deleted_projects": projects_deleted,
                "cutoff_time": cutoff_time.isoformat(),
            }
        else:
            logger.info(
                f"Task {self.request.id}: No snapshots older than {hours} hours to clean"
            )
            return {"message": "No old data to clean"}

    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise
