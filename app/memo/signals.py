from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Jobber


@receiver(post_save, sender=Jobber)
def geocode_job_on_address_change(sender, instance, created, **kwargs):
    """
    Automatically trigger geocoding when a job is created or its address changes
    Uses Celery for async processing to avoid blocking the save operation

    Note: This can be replaced with a generic signal handler if you have
    many models that need geocoding. See restAPI.signals for a generic version.
    """
    # Check if we should geocode
    should_geocode = False

    if created and instance.adresse and instance.adresse.strip():
        # New job with address
        should_geocode = True
    elif not created:
        # Existing job - check if address changed
        try:
            old_instance = Jobber.objects.get(pk=instance.pk)
            if old_instance.adresse != instance.adresse:
                should_geocode = True
        except Jobber.DoesNotExist:
            pass

    if should_geocode:
        # Use the global geocoding task
        from restAPI.tasks import geocode_model_instance

        geocode_model_instance.delay("memo", "Jobber", instance.ordre_nr)
