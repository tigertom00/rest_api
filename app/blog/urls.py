from rest_framework_nested import routers
from django.urls import path
from .views import BlogPostViewSet, PostImageViewSet, PostAudioViewSet, PostYouTubeViewSet, TagViewSet, BlogPostBySlugView

router = routers.DefaultRouter()
router.register("posts", BlogPostViewSet, basename="posts")
router.register("tags", TagViewSet, basename="tags")

posts_router = routers.NestedDefaultRouter(router, "posts", lookup="post")
posts_router.register("images", PostImageViewSet, basename="post-images")
posts_router.register("audio", PostAudioViewSet, basename="post-audio")
posts_router.register("youtube", PostYouTubeViewSet, basename="post-youtube")

urlpatterns = [
    path('slug/<slug:slug>/', BlogPostBySlugView.as_view(), name='post-by-slug'),
] + router.urls + posts_router.urls