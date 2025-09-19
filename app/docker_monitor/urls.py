from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DockerHostViewSet, DockerContainerViewSet

router = DefaultRouter()
router.register(r'hosts', DockerHostViewSet)
router.register(r'containers', DockerContainerViewSet)

urlpatterns = [
    path('api/docker/', include(router.urls)),
]