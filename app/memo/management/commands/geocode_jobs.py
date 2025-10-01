from django.core.management.base import BaseCommand
from django.utils import timezone

from app.memo.models import Jobber
from app.memo.services.geocoding import GeocodingService


class Command(BaseCommand):
    help = "Geocode all jobs with addresses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-geocode all jobs even if already geocoded",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            dest="use_async",
            help="Use Celery tasks for async processing",
        )

    def handle(self, *args, **options):
        force = options["force"]
        use_async = options["use_async"]

        # Build queryset
        if force:
            jobs = Jobber.objects.filter(adresse__isnull=False).exclude(adresse="")
        else:
            jobs = Jobber.objects.filter(
                adresse__isnull=False, latitude__isnull=True
            ).exclude(adresse="")

        total = jobs.count()
        self.stdout.write(f"Found {total} jobs to geocode...")

        if use_async:
            # Use Celery tasks for async processing
            from app.memo.tasks import geocode_job_async

            queued = 0
            for job in jobs:
                geocode_job_async.delay(job.ordre_nr)
                queued += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Queued {queued} jobs for async geocoding via Celery"
                )
            )
        else:
            # Synchronous processing
            success = 0
            failed = 0

            for job in jobs:
                result = GeocodingService.geocode_address(job.adresse)

                if result:
                    job.latitude = result["lat"]
                    job.longitude = result["lon"]
                    job.geocoded_at = timezone.now()
                    job.geocode_accuracy = result["accuracy"]
                    job.geocode_retries = 0
                    job.save()
                    success += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {job.ordre_nr}: {job.tittel} - {job.adresse}"
                        )
                    )
                else:
                    job.geocode_accuracy = "failed"
                    job.geocoded_at = timezone.now()
                    job.geocode_retries += 1
                    job.last_geocode_attempt = timezone.now()
                    job.save()
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(f"✗ {job.ordre_nr}: {job.tittel} - Failed")
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Complete: {success} succeeded, {failed} failed"
                )
            )
