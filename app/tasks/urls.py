from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TaskViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"", TaskViewSet)
router.register(r"categories", CategoryViewSet)

router.register(r"projects", ProjectViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
