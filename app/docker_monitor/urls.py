from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DockerHostViewSet, DockerContainerViewSet, agent_sync_containers
from .views_system import SystemStatsViewSet, ProcessStatsViewSet, system_dashboard, collect_system_metrics

router = DefaultRouter()
router.register(r'hosts', DockerHostViewSet)
router.register(r'containers', DockerContainerViewSet)
router.register(r'system-stats', SystemStatsViewSet)
router.register(r'process-stats', ProcessStatsViewSet)

urlpatterns = [
    path('docker/', include(router.urls)),
    path('docker/agent/sync/', agent_sync_containers, name='agent_sync_containers'),
    path('system/dashboard/', system_dashboard, name='system_dashboard'),
    path('system/dashboard/<int:host_id>/', system_dashboard, name='system_dashboard_host'),
    path('system/collect/', collect_system_metrics, name='collect_system_metrics'),
]