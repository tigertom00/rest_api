# apps/blog/views.py
from datetime import datetime

from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restAPI.utils.caching import CacheManager, QueryOptimizer, cache_api_response
from restAPI.utils.throttling import APIRateThrottle, UploadRateThrottle

from .models import (
    BlogMedia,
    BlogPost,
    PostAudio,
    PostImage,
    PostYouTube,
    SiteSettings,
    Tag,
)
from .permissions import IsOwnerOrFeaturedReadOnly
from .serializers import (
    BlogMediaSerializer,
    BlogMediaUploadSerializer,
    BlogPostSerializer,
    BlogPostWriteSerializer,
    PostAudioUploadSerializer,
    PostImageUploadSerializer,
    PostYouTubeSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]


class PostImageViewSet(viewsets.ModelViewSet):
    serializer_class = PostImageUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostImage.objects.filter(post__author=self.request.user)

    def perform_create(self, serializer):
        post_id = self.kwargs["post_pk"]
        post = get_object_or_404(BlogPost, pk=post_id, author=self.request.user)
        serializer.save(post=post)


class PostAudioViewSet(viewsets.ModelViewSet):
    serializer_class = PostAudioUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostAudio.objects.filter(post__author=self.request.user)

    def perform_create(self, serializer):
        post_id = self.kwargs["post_pk"]
        post = get_object_or_404(BlogPost, pk=post_id, author=self.request.user)
        serializer.save(post=post)


class PostYouTubeViewSet(viewsets.ModelViewSet):
    serializer_class = PostYouTubeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostYouTube.objects.filter(post__author=self.request.user)

    def perform_create(self, serializer):
        post_id = self.kwargs["post_pk"]
        post = get_object_or_404(BlogPost, pk=post_id, author=self.request.user)
        serializer.save(post=post)


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    Routes:
      - /api/posts/      -> Auth users: list your posts. Unauth: list featured author's published posts.
      - /api/posts/:id/  -> Detail with the same visibility rules.
      - /api/posts/public/ -> Explicit landing-page feed (unauth friendly).
    """

    permission_classes = [IsOwnerOrFeaturedReadOnly]

    def get_queryset(self):
        q = BlogPost.objects.select_related("author").prefetch_related(
            "tags", "images", "audio_files", "youtube_videos"
        )
        if self.request.user.is_authenticated:
            # Authenticated users only see their own posts
            return q.filter(author=self.request.user)
        # unauth: featured + published
        settings_row = SiteSettings.objects.first()
        if not settings_row or not settings_row.featured_author_id:
            return q.none()
        return q.filter(
            author_id=settings_row.featured_author_id, status=BlogPost.Status.PUBLISHED
        )

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return BlogPostWriteSerializer
        return BlogPostSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if "slug" in str(e):
                return Response(
                    {
                        "error": "A blog post with this title already exists. Please use a different title."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"], url_path="public", permission_classes=[])
    def public(self, request):
        # Landing page feed: always returns featured author's published posts.
        settings_row = SiteSettings.objects.first()
        qs = BlogPost.objects.none()
        if settings_row and settings_row.featured_author_id:
            qs = (
                BlogPost.objects.filter(
                    author_id=settings_row.featured_author_id,
                    status=BlogPost.Status.PUBLISHED,
                )
                .select_related("author")
                .prefetch_related("tags", "images", "audio_files", "youtube_videos")
            )
        serializer = BlogPostSerializer(qs, many=True)
        return Response(serializer.data)


class BlogPostBySlugView(APIView):
    """Get blog post by slug. Uses same visibility rules as BlogPostViewSet."""

    permission_classes = []

    def get(self, request, slug):
        settings_row = SiteSettings.objects.first()

        if request.user and request.user.is_authenticated:
            # Authenticated users: only their own posts
            qs = BlogPost.objects.filter(author=request.user, slug=slug)
        else:
            # Unauthenticated: only featured author's published posts
            if not settings_row or not settings_row.featured_author_id:
                return Response(
                    {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
                )
            qs = BlogPost.objects.filter(
                author_id=settings_row.featured_author_id,
                status=BlogPost.Status.PUBLISHED,
                slug=slug,
            )

        qs = qs.select_related("author").prefetch_related(
            "tags", "images", "audio_files", "youtube_videos"
        )
        post = qs.first()

        if not post:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BlogPostSerializer(post)
        return Response(serializer.data)


class BlogMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing blog media files.
    Provides endpoints for upload, list, retrieve, and delete operations.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["file_type", "uploaded_by"]
    search_fields = ["filename", "original_filename"]
    throttle_classes = [UploadRateThrottle, APIRateThrottle]

    def get_queryset(self):
        queryset = BlogMedia.objects.all()

        # Date range filtering
        date_start = self.request.query_params.get("date_start")
        date_end = self.request.query_params.get("date_end")

        if date_start:
            try:
                start_date = datetime.fromisoformat(date_start.replace("Z", "+00:00"))
                queryset = queryset.filter(upload_date__gte=start_date)
            except ValueError:
                pass  # Invalid date format, ignore filter

        if date_end:
            try:
                end_date = datetime.fromisoformat(date_end.replace("Z", "+00:00"))
                queryset = queryset.filter(upload_date__lte=end_date)
            except ValueError:
                pass  # Invalid date format, ignore filter

        return QueryOptimizer.optimize_media_queryset(queryset)

    def get_serializer_class(self):
        if self.action == "create":
            return BlogMediaUploadSerializer
        return BlogMediaSerializer

    @action(detail=False, methods=["post"], url_path="upload")
    def upload(self, request):
        """
        Upload a new media file.
        Accepts multipart/form-data with 'file' field.
        """
        serializer = BlogMediaUploadSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            media_file = serializer.save()
            response_serializer = BlogMediaSerializer(media_file)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @cache_api_response(timeout=1800)  # Cache for 30 minutes
    def list(self, request, *args, **kwargs):
        """Override list method to add caching for media files."""
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a media file and its associated file storage.
        Also handles cascade deletion from blog posts if referenced.
        """
        instance = self.get_object()

        # Invalidate media cache
        CacheManager.invalidate_list_cache("media_files")

        # The model's delete method already handles file cleanup
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        """Override to invalidate cache after creation."""
        result = super().perform_create(serializer)

        # Invalidate media cache
        CacheManager.invalidate_list_cache("media_files")

        return result
