from rest_framework import serializers
from .models import Llmproviders, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name_en", "name_no"]


class LlmprovidersSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True, source="tags"
    )

    class Meta:
        model = Llmproviders
        fields = [
            "id",
            "name",
            "url",
            "created_at",
            "updated_at",
            "description",
            "description_nb",
            "strengths_en",
            "strengths_no",
            "pricing",
            "pricing_nb",
            "icon",
            "tags",
            "tag_ids",
        ]
