from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, TaskViewSet, ProjectViewSet

router = DefaultRouter()
router.register(r"tasks/categories", CategoryViewSet)
router.register(r"tasks", TaskViewSet)
router.register(r"projects", ProjectViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
