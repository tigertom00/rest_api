from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from .views import TaskViewSet, UserViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', lambda request: Response({'status': 'healthy'})),
]   