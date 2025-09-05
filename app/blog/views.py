# apps/blog/views.py
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import BlogPost, SiteSettings, PostImage, PostAudio
from .serializers import BlogPostSerializer, BlogPostWriteSerializer, PostImageUploadSerializer, PostAudioUploadSerializer
from .permissions import IsOwnerOrFeaturedReadOnly


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

"""
class BlogPostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrFeaturedReadOnly]

    def get_queryset(self):
        # unchanged …
        pass  

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return BlogPostWriteSerializer
        return BlogPostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
"""



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

