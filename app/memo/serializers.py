from rest_framework import serializers
from restAPI.serializers import UserBasicSerializer

from .models import (
    ActiveTimerSession,
    ElektriskKategori,
    Jobber,
    JobberFile,
    JobberImage,
    JobberTask,
    JobbMatriell,
    Leverandorer,
    Matriell,
    Timeliste,
)


class LeverandorField(serializers.Field):
    """
    Custom field that accepts either a string (leverandor name) or dict (full leverandor data)
    """

    def to_internal_value(self, data):
        # Just return the data as-is, we'll handle it in the create/update methods
        return data

    def to_representation(self, value):
        # This shouldn't be called since it's write_only, but just in case
        return str(value)


class ElektriskKategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElektriskKategori
        fields = "__all__"


class LeverandorerSerializer(serializers.ModelSerializer):
    # Map JSON field names to model fields
    navn = serializers.CharField(source="name")

    class Meta:
        model = Leverandorer
        fields = [
            "id",
            "navn",
            "telefon",
            "hjemmeside",
            "addresse",
            "poststed",
            "postnummer",
            "epost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LeverandorerCreateSerializer(serializers.ModelSerializer):
    navn = serializers.CharField(source="name")

    class Meta:
        model = Leverandorer
        fields = [
            "navn",
            "telefon",
            "hjemmeside",
            "addresse",
            "poststed",
            "postnummer",
            "epost",
        ]

    def create(self, validated_data):
        # Use get_or_create to handle duplicates gracefully
        leverandor, created = Leverandorer.objects.get_or_create(
            name=validated_data.get("name"), defaults=validated_data
        )

        # If not created (already exists), update with new data
        if not created:
            for field, value in validated_data.items():
                if field != "name" and value:  # Don't overwrite with empty values
                    setattr(leverandor, field, value)
            leverandor.save()

        return leverandor


class MatriellSerializer(serializers.ModelSerializer):
    leverandor = LeverandorerSerializer(read_only=True)
    leverandor_id = serializers.PrimaryKeyRelatedField(
        queryset=Leverandorer.objects.all(), source="leverandor", write_only=True
    )
    kategori = ElektriskKategoriSerializer(read_only=True)
    kategori_id = serializers.PrimaryKeyRelatedField(
        queryset=ElektriskKategori.objects.all(),
        source="kategori",
        write_only=True,
        required=False,
    )

    class Meta:
        model = Matriell
        fields = "__all__"


class EFOBasenImportSerializer(serializers.ModelSerializer):
    """
    Serializer for importing data directly from EFO Basen JSON format.
    Handles foreign key lookups by name/blokknummer instead of IDs.
    Now supports embedded supplier data for automatic creation.
    """

    # Foreign key lookups - leverandor can be either string or dict
    kategori = serializers.CharField(
        write_only=True, required=False, help_text="Blokknummer (e.g., '10')"
    )
    leverandor = LeverandorField(
        write_only=True,
        help_text="Leverandor name (string) or full leverandor object (dict)",
    )

    class Meta:
        model = Matriell
        fields = [
            "el_nr",
            "tittel",
            "varemerke",
            "info",
            "varenummer",
            "gtin_number",
            "teknisk_beskrivelse",
            "varebetegnelse",
            "hoyde",
            "bredde",
            "lengde",
            "vekt",
            "bilder",
            "produktblad",
            "produkt_url",
            "fdv",
            "cpr_sertifikat",
            "miljoinformasjon",
            "kategori",
            "leverandor",
            "approved",
            "discontinued",
            "in_stock",
            "favorites",
        ]
        extra_kwargs = {
            "approved": {"default": True},
            "discontinued": {"default": False},
            "in_stock": {"default": True},
            "favorites": {"default": False},
        }

    def create(self, validated_data):
        # Handle kategori lookup by blokknummer
        kategori_blokknummer = validated_data.pop("kategori", None)
        kategori_obj = None
        if kategori_blokknummer:
            try:
                kategori_obj = ElektriskKategori.objects.get(
                    blokknummer=kategori_blokknummer
                )
            except ElektriskKategori.DoesNotExist as e:
                raise serializers.ValidationError(
                    f"ElektriskKategori with blokknummer '{kategori_blokknummer}' not found"
                ) from e

        # Handle leverandor (either embedded object or name string)
        leverandor_data = validated_data.pop("leverandor", None)
        leverandor_obj = None

        if isinstance(leverandor_data, dict):
            # Handle embedded supplier data
            supplier_serializer = LeverandorerCreateSerializer(data=leverandor_data)
            if supplier_serializer.is_valid():
                leverandor_obj = supplier_serializer.save()
            else:
                raise serializers.ValidationError(
                    f"Invalid leverandor data: {supplier_serializer.errors}"
                )
        elif isinstance(leverandor_data, str):
            # Handle string-based lookup
            try:
                leverandor_obj = Leverandorer.objects.get(name=leverandor_data)
            except Leverandorer.DoesNotExist as e:
                raise serializers.ValidationError(
                    f"Leverandoren with name '{leverandor_data}' not found"
                ) from e

        # Create the Matriell instance
        matriell = Matriell.objects.create(
            kategori=kategori_obj, leverandor=leverandor_obj, **validated_data
        )
        return matriell

    def update(self, instance, validated_data):
        # Handle kategori lookup by blokknummer
        kategori_blokknummer = validated_data.pop("kategori", None)
        if kategori_blokknummer:
            try:
                instance.kategori = ElektriskKategori.objects.get(
                    blokknummer=kategori_blokknummer
                )
            except ElektriskKategori.DoesNotExist as e:
                raise serializers.ValidationError(
                    f"ElektriskKategori with blokknummer '{kategori_blokknummer}' not found"
                ) from e

        # Handle leverandor (either embedded object or name string)
        leverandor_data = validated_data.pop("leverandor", None)
        if isinstance(leverandor_data, dict):
            # Handle embedded supplier data
            supplier_serializer = LeverandorerCreateSerializer(data=leverandor_data)
            if supplier_serializer.is_valid():
                instance.leverandor = supplier_serializer.save()
            else:
                raise serializers.ValidationError(
                    f"Invalid leverandor data: {supplier_serializer.errors}"
                )
        elif isinstance(leverandor_data, str):
            # Handle string-based lookup
            try:
                instance.leverandor = Leverandorer.objects.get(name=leverandor_data)
            except Leverandorer.DoesNotExist as e:
                raise serializers.ValidationError(
                    f"Leverandoren with name '{leverandor_data}' not found"
                ) from e

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class JobbMatriellSerializer(serializers.ModelSerializer):
    matriell = MatriellSerializer(read_only=True)
    matriell_id = serializers.PrimaryKeyRelatedField(
        queryset=Matriell.objects.all(), source="matriell", write_only=True
    )
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = JobbMatriell
        fields = "__all__"


class JobberImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobberImage
        fields = "__all__"
        read_only_fields = ["thumbnail"]


class JobberFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobberFile
        fields = "__all__"


class JobberTaskSerializer(serializers.ModelSerializer):
    jobb_tittel = serializers.CharField(source="jobb.tittel", read_only=True)
    jobb_ordre_nr = serializers.IntegerField(source="jobb.ordre_nr", read_only=True)

    class Meta:
        model = JobberTask
        fields = "__all__"
        read_only_fields = ["completed_at", "created_at", "updated_at", "thumbnail"]


class JobberSerializer(serializers.ModelSerializer):
    jobbmatriell = JobbMatriellSerializer(many=True, read_only=True)
    images = JobberImageSerializer(many=True, read_only=True)
    files = JobberFileSerializer(many=True, read_only=True)
    total_hours = serializers.ReadOnlyField()
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Jobber
        fields = "__all__"
        read_only_fields = [
            "latitude",
            "longitude",
            "geocoded_at",
            "geocode_accuracy",
            "geocode_retries",
            "last_geocode_attempt",
        ]

    def get_distance(self, obj):
        """
        Calculate distance from user's location if provided in context
        Returns distance in meters, or None if user location not provided
        """
        user_lat = self.context.get("user_lat")
        user_lon = self.context.get("user_lon")

        if user_lat and user_lon and obj.latitude and obj.longitude:
            from restAPI.services import GeocodingService

            return round(
                GeocodingService.calculate_distance(
                    user_lat, user_lon, float(obj.latitude), float(obj.longitude)
                ),
                1,
            )
        return None


class TimelisteSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    jobb_tittel = serializers.CharField(source="jobb.tittel", read_only=True)

    class Meta:
        model = Timeliste
        fields = "__all__"


class MatriellFavoriteSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for favorites list with essential fields only.
    Optimized for performance when listing many favorites.
    """

    leverandor = LeverandorerSerializer(read_only=True)
    kategori_name = serializers.CharField(source="kategori.kategori", read_only=True)

    class Meta:
        model = Matriell
        fields = [
            "id",
            "el_nr",
            "tittel",
            "varemerke",
            "varenummer",
            "leverandor",
            "kategori_name",
            "approved",
            "in_stock",
            "favorites",
            "created_at",
        ]


class ActiveTimerSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for active timer sessions.
    Includes calculated elapsed time and job details.
    """

    user = UserBasicSerializer(read_only=True)
    jobb_tittel = serializers.CharField(source="jobb.tittel", read_only=True)
    jobb_ordre_nr = serializers.IntegerField(source="jobb.ordre_nr", read_only=True)
    elapsed_seconds = serializers.ReadOnlyField()

    class Meta:
        model = ActiveTimerSession
        fields = [
            "id",
            "user",
            "jobb",
            "jobb_tittel",
            "jobb_ordre_nr",
            "start_time",
            "last_ping",
            "is_paused",
            "paused_at",
            "total_paused_seconds",
            "elapsed_seconds",
        ]
        read_only_fields = [
            "id",
            "start_time",
            "last_ping",
            "is_paused",
            "paused_at",
            "total_paused_seconds",
        ]
