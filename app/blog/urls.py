from rest_framework_nested import routers
from .views import BlogPostViewSet, PostImageViewSet, PostAudioViewSet, TagViewSet

router = routers.DefaultRouter()
router.register("posts", BlogPostViewSet, basename="posts")
router.register("tags", TagViewSet, basename="tags")

posts_router = routers.NestedDefaultRouter(router, "posts", lookup="post")
posts_router.register("images", PostImageViewSet, basename="post-images")
posts_router.register("audio", PostAudioViewSet, basename="post-audio")

urlpatterns = router.urls + posts_router.urls