from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DockerHostViewSet, DockerContainerViewSet, agent_sync_containers

router = DefaultRouter()
router.register(r'hosts', DockerHostViewSet)
router.register(r'containers', DockerContainerViewSet)

urlpatterns = [
    path('docker/', include(router.urls)),
    path('docker/agent/sync/', agent_sync_containers, name='agent_sync_containers'),
]