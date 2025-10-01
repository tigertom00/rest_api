from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def geocode_job_async(self, job_id: int):
    """
    Asynchronously geocode a job's address

    Args:
        job_id: Primary key of the Jobber instance

    Returns:
        dict: Result summary with geocoding status
    """
    from .models import Jobber
    from .services.geocoding import GeocodingService

    try:
        job = Jobber.objects.get(pk=job_id)
    except Jobber.DoesNotExist:
        return {"success": False, "error": f"Job {job_id} not found"}

    # Check if address is empty
    if not job.adresse or not job.adresse.strip():
        return {"success": False, "error": "No address to geocode"}

    # Update last attempt timestamp
    job.last_geocode_attempt = timezone.now()

    try:
        result = GeocodingService.geocode_address(job.adresse)

        if result:
            job.latitude = result["lat"]
            job.longitude = result["lon"]
            job.geocoded_at = timezone.now()
            job.geocode_accuracy = result["accuracy"]
            job.geocode_retries = 0  # Reset retry counter on success
            job.save()

            return {
                "success": True,
                "job_id": job_id,
                "ordre_nr": job.ordre_nr,
                "lat": float(job.latitude),
                "lon": float(job.longitude),
                "accuracy": job.geocode_accuracy,
            }
        else:
            # Geocoding failed
            job.geocode_accuracy = "failed"
            job.geocode_retries += 1
            job.save()

            # Retry if we haven't exceeded max retries
            if job.geocode_retries < 3:
                raise self.retry(countdown=60 * job.geocode_retries)

            return {
                "success": False,
                "job_id": job_id,
                "error": "Geocoding failed after retries",
            }

    except Exception as exc:
        job.geocode_retries += 1
        job.save()

        # Retry with exponential backoff
        if job.geocode_retries < 3:
            raise self.retry(exc=exc, countdown=60 * (2**job.geocode_retries))

        return {
            "success": False,
            "job_id": job_id,
            "error": f"Exception: {str(exc)}",
        }


@shared_task
def bulk_geocode_jobs(force: bool = False):
    """
    Bulk geocode all jobs with addresses

    Args:
        force: If True, re-geocode all jobs. If False, only geocode jobs without coordinates

    Returns:
        dict: Summary of geocoding operation
    """
    from .models import Jobber

    # Build queryset
    if force:
        jobs = Jobber.objects.filter(adresse__isnull=False).exclude(adresse="")
    else:
        jobs = Jobber.objects.filter(
            adresse__isnull=False, latitude__isnull=True
        ).exclude(adresse="")

    total = jobs.count()
    queued = 0

    # Queue geocoding tasks
    for job in jobs:
        geocode_job_async.delay(job.ordre_nr)
        queued += 1

    return {
        "success": True,
        "total_jobs": total,
        "queued": queued,
        "force": force,
    }


@shared_task
def retry_failed_geocoding():
    """
    Retry geocoding for jobs that failed but haven't exceeded max retries

    Returns:
        dict: Summary of retry operation
    """
    from .models import Jobber

    # Find jobs with failed geocoding and retries < 3
    failed_jobs = Jobber.objects.filter(
        geocode_accuracy="failed", geocode_retries__lt=3
    )

    total = failed_jobs.count()
    queued = 0

    for job in failed_jobs:
        geocode_job_async.delay(job.ordre_nr)
        queued += 1

    return {
        "success": True,
        "total_failed": total,
        "queued": queued,
    }
