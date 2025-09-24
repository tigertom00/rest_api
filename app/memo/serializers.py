from rest_framework import serializers
from .models import Leverandorer, Matriell, Jobber, JobbMatriell, JobberImage, JobberFile, Timeliste


class LeverandorerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leverandorer
        fields = "__all__"


class MatriellSerializer(serializers.ModelSerializer):
    leverandor = LeverandorerSerializer(read_only=True)
    leverandor_id = serializers.PrimaryKeyRelatedField(
        queryset=Leverandorer.objects.all(), source="leverandor", write_only=True
    )

    class Meta:
        model = Matriell
        fields = "__all__"


class MatriellBulkCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for bulk creating Matriell objects from EFObasen data
    Accepts manufacturer name and creates/finds the manufacturer automatically
    """
    leverandor_name = serializers.CharField(write_only=True)
    leverandor = LeverandorerSerializer(read_only=True)

    class Meta:
        model = Matriell
        fields = [
            'el_nr', 'tittel', 'info', 'ean_number', 'article_number',
            'norwegian_description', 'english_description',
            'height', 'width', 'depth', 'weight',
            'etim_class', 'category', 'datasheet_url', 'image_url',
            'approved', 'discontinued', 'in_stock',
            'leverandor_name', 'leverandor'
        ]

    def create(self, validated_data):
        leverandor_name = validated_data.pop('leverandor_name')

        # Extract category (EC code) from etim_class if not provided
        etim_class = validated_data.get('etim_class', '')
        if not validated_data.get('category') and etim_class:
            import re
            ec_match = re.search(r'EC\d{6}', etim_class)
            if ec_match:
                validated_data['category'] = ec_match.group()

        # Create or get manufacturer
        leverandor, created = Leverandorer.objects.get_or_create(
            name=leverandor_name,
            defaults={
                'manufacturer_code': leverandor_name[:20].upper().replace(' ', '')
            }
        )

        validated_data['leverandor'] = leverandor
        return super().create(validated_data)


class LeverandorerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating manufacturers from EFObasen data
    """

    class Meta:
        model = Leverandorer
        fields = ['name', 'manufacturer_code', 'website_url']

    def create(self, validated_data):
        # Generate manufacturer_code if not provided
        if not validated_data.get('manufacturer_code'):
            validated_data['manufacturer_code'] = validated_data['name'][:20].upper().replace(' ', '')

        return super().create(validated_data)


class JobbMatriellSerializer(serializers.ModelSerializer):
    matriell = MatriellSerializer(read_only=True)
    matriell_id = serializers.PrimaryKeyRelatedField(
        queryset=Matriell.objects.all(), source="matriell", write_only=True
    )

    class Meta:
        model = JobbMatriell
        fields = "__all__"

class JobberImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobberImage
        fields = "__all__"


class JobberFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobberFile
        fields = "__all__"


class JobberSerializer(serializers.ModelSerializer):
    jobbmatriell = JobbMatriellSerializer(many=True, read_only=True)
    images = JobberImageSerializer(many=True, read_only=True)
    files = JobberFileSerializer(many=True, read_only=True)
    total_hours = serializers.ReadOnlyField()

    class Meta:
        model = Jobber
        fields = "__all__"

class TimelisteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeliste
        fields = "__all__"

