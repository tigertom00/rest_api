"""Reusable model mixins for common functionality"""

from django.db import models


class GeocodableMixin(models.Model):
    """
    Mixin that adds geocoding fields to any model with an address field.

    To use this mixin:
    1. Include it in your model's inheritance
    2. Define an 'address_field' attribute pointing to your address field name
    3. Set up a signal handler to trigger geocoding (or use the provided tasks)

    Example:
        class MyModel(GeocodableMixin, models.Model):
            street_address = models.CharField(max_length=255)
            address_field = 'street_address'  # Tell mixin which field to geocode

            class Meta:
                indexes = [
                    models.Index(fields=['latitude', 'longitude']),
                ]
    """

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Latitude coordinate from geocoded address",
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text="Longitude coordinate from geocoded address",
    )
    geocoded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when address was last geocoded",
    )
    geocode_accuracy = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("exact", "Exact Match"),
            ("approximate", "Approximate Match"),
            ("failed", "Geocoding Failed"),
        ],
        help_text="Quality of geocoding result",
    )
    geocode_retries = models.SmallIntegerField(
        default=0, help_text="Number of geocoding retry attempts"
    )
    last_geocode_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last geocoding attempt",
    )

    class Meta:
        abstract = True

    def get_address_for_geocoding(self) -> str:
        """
        Get the address string to geocode.
        Override this method if your address is composed of multiple fields.

        Returns:
            str: The address string to geocode
        """
        if hasattr(self, "address_field"):
            return getattr(self, self.address_field, "")
        # Fallback: try common field names
        for field_name in ["address", "adresse", "street_address", "location"]:
            if hasattr(self, field_name):
                return getattr(self, field_name, "")
        return ""

    def has_coordinates(self) -> bool:
        """Check if this instance has valid geocoded coordinates"""
        return self.latitude is not None and self.longitude is not None

    def needs_geocoding(self) -> bool:
        """Check if this instance needs geocoding"""
        address = self.get_address_for_geocoding()
        if not address or not address.strip():
            return False
        return not self.has_coordinates()

    def distance_to(self, lat: float, lon: float) -> float:
        """
        Calculate distance to another coordinate

        Args:
            lat: Target latitude
            lon: Target longitude

        Returns:
            float: Distance in meters, or None if this instance has no coordinates
        """
        if not self.has_coordinates():
            return None

        from restAPI.services import GeocodingService

        return GeocodingService.calculate_distance(
            float(self.latitude), float(self.longitude), lat, lon
        )
