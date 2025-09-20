from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import List, Dict, Any
from .models import BlogPost, PostImage, PostAudio, PostYouTube, Tag, PostImage, PostAudio
from django.contrib.auth import get_user_model

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
            "id", "author", "title", "slug", "excerpt",
            "body_markdown", "body_html",  # 👈 markdown + html
            "status", "tags", "title_nb", "excerpt_nb", "body_markdown_nb",
            "images", "audio_files", "youtube_videos",
            "meta_title", "meta_description",
            "published_at", "created_at", "updated_at",
        )
        read_only_fields = ("slug", "published_at", "author", "body_html")

    @extend_schema_field(serializers.ListField)
    def get_images(self, obj) -> List[Dict[str, Any]]:
        return [{"id": i.id, "url": i.image.url, "alt": i.alt_text, "caption": i.caption} for i in obj.images.all()]

    @extend_schema_field(serializers.ListField)
    def get_audio_files(self, obj) -> List[Dict[str, Any]]:
        return [{"id": a.id, "url": a.audio.url, "title": a.title, "duration": a.duration_seconds, "order": a.order} for a in obj.audio_files.all()]

    @extend_schema_field(serializers.ListField)
    def get_youtube_videos(self, obj) -> List[Dict[str, Any]]:
        return [{"id": y.id, "url": y.url, "video_id": y.video_id, "title": y.title} for y in obj.youtube_videos.all()]


class BlogPostWriteSerializer(serializers.ModelSerializer):
    """Used for create/update — accepts markdown input."""
    class Meta:
        model = BlogPost
        fields = (
            "id", "title", "excerpt", "body_markdown", "body_markdown_nb", "excerpt_nb", "title_nb",
            "status", "meta_title", "meta_description", "tags"
        )

