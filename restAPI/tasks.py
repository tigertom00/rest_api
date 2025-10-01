"""Global Celery tasks for restAPI app"""

from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def geocode_model_instance(self, app_label: str, model_name: str, instance_id: int):
    """
    Generic task to geocode any Django model instance that uses GeocodableMixin

    Args:
        app_label: Django app label (e.g., 'memo', 'tasks')
        model_name: Model name (e.g., 'Jobber', 'CustomUser')
        instance_id: Primary key of the instance to geocode

    Returns:
        dict: Result summary with geocoding status
    """
    from django.apps import apps

    from restAPI.services import GeocodingService

    try:
        # Get the model class
        model_class = apps.get_model(app_label, model_name)
        instance = model_class.objects.get(pk=instance_id)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load instance: {str(e)}",
            "app_label": app_label,
            "model_name": model_name,
            "instance_id": instance_id,
        }

    # Get address from instance
    if not hasattr(instance, "get_address_for_geocoding"):
        return {
            "success": False,
            "error": f"{model_name} does not use GeocodableMixin",
        }

    address = instance.get_address_for_geocoding()

    # Handle both string and dict address formats
    if not address:
        return {"success": False, "error": "No address to geocode"}

    if isinstance(address, str) and not address.strip():
        return {"success": False, "error": "No address to geocode"}

    if isinstance(address, dict) and not address.get("adresse", "").strip():
        return {"success": False, "error": "No address to geocode"}

    # Update last attempt timestamp
    instance.last_geocode_attempt = timezone.now()

    try:
        result = GeocodingService.geocode_address(address)

        if result:
            instance.latitude = result["lat"]
            instance.longitude = result["lon"]
            instance.geocoded_at = timezone.now()
            instance.geocode_accuracy = result["accuracy"]
            instance.geocode_retries = 0  # Reset retry counter on success
            instance.save()

            return {
                "success": True,
                "app_label": app_label,
                "model_name": model_name,
                "instance_id": instance_id,
                "lat": float(instance.latitude),
                "lon": float(instance.longitude),
                "accuracy": instance.geocode_accuracy,
            }
        else:
            # Geocoding failed
            instance.geocode_accuracy = "failed"
            instance.geocode_retries += 1
            instance.save()

            # Retry if we haven't exceeded max retries
            if instance.geocode_retries < 3:
                raise self.retry(countdown=60 * instance.geocode_retries)

            return {
                "success": False,
                "error": "Geocoding failed after retries",
                "instance_id": instance_id,
            }

    except Exception as exc:
        instance.geocode_retries += 1
        instance.save()

        # Retry with exponential backoff
        if instance.geocode_retries < 3:
            raise self.retry(exc=exc, countdown=60 * (2**instance.geocode_retries))

        return {
            "success": False,
            "error": f"Exception: {str(exc)}",
            "instance_id": instance_id,
        }
