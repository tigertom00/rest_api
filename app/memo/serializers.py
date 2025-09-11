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

    class Meta:
        model = Jobber
        fields = "__all__"

class TimelisteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeliste
        fields = "__all__"

