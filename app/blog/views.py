# apps/blog/views.py
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from .models import BlogPost, SiteSettings, PostImage, PostAudio, PostYouTube, Tag
from .serializers import BlogPostSerializer, BlogPostWriteSerializer, PostImageUploadSerializer, PostAudioUploadSerializer, PostYouTubeSerializer, TagSerializer
from .permissions import IsOwnerOrFeaturedReadOnly


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
        q = BlogPost.objects.select_related("author").prefetch_related("tags", "images", "audio_files", "youtube_videos")
        if self.request.user.is_authenticated:
            return q.filter(author=self.request.user)
        # unauth: featured + published
        settings_row = SiteSettings.objects.first()
        if not settings_row or not settings_row.featured_author_id:
            return q.none()
        return q.filter(author_id=settings_row.featured_author_id, status=BlogPost.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return BlogPostWriteSerializer
        return BlogPostSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            if 'slug' in str(e):
                return Response(
                    {'error': 'A blog post with this title already exists. Please use a different title.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"], url_path="public", permission_classes=[])
    def public(self, request):
        #Landing page feed: always returns featured author's published posts.
        settings_row = SiteSettings.objects.first()
        qs = BlogPost.objects.none()
        if settings_row and settings_row.featured_author_id:
            qs = BlogPost.objects.filter(
                author_id=settings_row.featured_author_id,
                status=BlogPost.Status.PUBLISHED
            ).select_related("author").prefetch_related("tags", "images", "audio_files", "youtube_videos")
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
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            qs = BlogPost.objects.filter(
                author_id=settings_row.featured_author_id,
                status=BlogPost.Status.PUBLISHED,
                slug=slug
            )

        qs = qs.select_related("author").prefetch_related("tags", "images", "audio_files", "youtube_videos")
        post = qs.first()

        if not post:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = BlogPostSerializer(post)
        return Response(serializer.data)


