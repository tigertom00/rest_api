
from rest_framework_nested import routers
from .views import LlmprovidersViewSet, TagViewSet

router = routers.DefaultRouter()
router.register("providers", LlmprovidersViewSet, basename="llmproviders")
router.register("providers/tags", TagViewSet, basename="tags")
# providers_router = routers.NestedDefaultRouter(router, "providers", lookup="provider")
# providers_router.register("tags", TagViewSet, basename="tags")

urlpatterns = router.urls
