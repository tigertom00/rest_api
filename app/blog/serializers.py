from typing import Any

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import BlogMedia, BlogPost, PostAudio, PostImage, PostYouTube, Tag

User = get_user_model()


class AuthorPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "display_name", "profile_picture")


class PostImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image", "alt_text", "caption", "order")


class PostAudioUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAudio
        fields = ("id", "audio", "title", "duration_seconds", "order")


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image", "alt_text", "caption", "order")


class PostAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostAudio
        fields = ("id", "audio", "title", "duration_seconds", "order")


class PostYouTubeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostYouTube
        fields = ("id", "url", "video_id", "title", "order")
        read_only_fields = ("video_id",)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class BlogPostSerializer(serializers.ModelSerializer):
    author = AuthorPublicSerializer(read_only=True)
    images = serializers.SerializerMethodField()
    audio_files = serializers.SerializerMethodField()
    youtube_videos = serializers.SerializerMethodField()
    tags = serializers.StringRelatedField(many=True)
    body_html = serializers.ReadOnlyField()

    class Meta:
        model = BlogPost
        fields = (
            "id",
            "author",
            "title",
            "slug",
            "excerpt",
            "body_markdown",
            "body_html",  # 👈 markdown + html
            "status",
            "tags",
            "title_nb",
            "excerpt_nb",
            "body_markdown_nb",
            "images",
            "audio_files",
            "youtube_videos",
            "meta_title",
            "meta_description",
            "published_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("slug", "published_at", "author", "body_html")

    @extend_schema_field(serializers.ListField)
    def get_images(self, obj) -> list[dict[str, Any]]:
        return [
            {"id": i.id, "url": i.image.url, "alt": i.alt_text, "caption": i.caption}
            for i in obj.images.all()
        ]

    @extend_schema_field(serializers.ListField)
    def get_audio_files(self, obj) -> list[dict[str, Any]]:
        return [
            {
                "id": a.id,
                "url": a.audio.url,
                "title": a.title,
                "duration": a.duration_seconds,
                "order": a.order,
            }
            for a in obj.audio_files.all()
        ]

    @extend_schema_field(serializers.ListField)
    def get_youtube_videos(self, obj) -> list[dict[str, Any]]:
        return [
            {"id": y.id, "url": y.url, "video_id": y.video_id, "title": y.title}
            for y in obj.youtube_videos.all()
        ]


class BlogPostWriteSerializer(serializers.ModelSerializer):
    """Used for create/update — accepts markdown input."""

    class Meta:
        model = BlogPost
        fields = (
            "id",
            "title",
            "excerpt",
            "body_markdown",
            "body_markdown_nb",
            "excerpt_nb",
            "title_nb",
            "status",
            "meta_title",
            "meta_description",
            "tags",
        )


class BlogMediaSerializer(serializers.ModelSerializer):
    url = serializers.ReadOnlyField()
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = BlogMedia
        fields = (
            "id",
            "filename",
            "original_filename",
            "file_type",
            "file_size",
            "upload_date",
            "uploaded_by",
            "url",
            "thumbnail_url",
        )
        read_only_fields = ("upload_date", "uploaded_by", "url", "thumbnail_url")


class BlogMediaUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = BlogMedia
        fields = ("file",)

    def validate_file(self, value):
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB.")

        # Validate file type
        allowed_extensions = ["jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx"]
        file_extension = value.name.split(".")[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '{file_extension}' not allowed. "
                f"Allowed types: {', '.join(allowed_extensions)}"
            )

        return value

    def create(self, validated_data):
        file = validated_data["file"]
        return BlogMedia.objects.create(
            filename=file.name,
            original_filename=file.name,
            file=file,
            file_type=file.content_type or "application/octet-stream",
            file_size=file.size,
            uploaded_by=self.context["request"].user,
        )
