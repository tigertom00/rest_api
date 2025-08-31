from rest_framework import serializers
from .models import BlogPost, PostImage, PostAudio, PostYouTube, Tag, PostImage, PostAudio


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
    images = PostImageSerializer(many=True, read_only=True)
    audio_files = PostAudioSerializer(many=True, read_only=True)
    youtube_videos = PostYouTubeSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = BlogPost
        fields = (
            "id", "author", "title", "slug", "excerpt", "body",
            "status", "tags", "images", "audio_files", "youtube_videos",
            "meta_title", "meta_description",
            "published_at", "created_at", "updated_at"
        )
        read_only_fields = ("slug", "published_at", "author")

class BlogPostWriteSerializer(serializers.ModelSerializer):
    """Use for create/update; author is set from request.user in the view."""
    class Meta:
        model = BlogPost
        fields = (
            "id", "title", "excerpt", "body", "status",
            "meta_title", "meta_description", "tags"
        )
