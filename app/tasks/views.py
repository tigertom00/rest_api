from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Task
from .serializers import TaskSerializer, UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter tasks by the authenticated user's Clerk ID
        clerk_user_id = self.request.headers.get('X-Clerk-User-Id')
        if clerk_user_id:
            return Task.objects.filter(clerk_user_id=clerk_user_id)
        return Task.objects.none()

    def perform_create(self, serializer):
        clerk_user_id = self.request.headers.get('X-Clerk-User-Id')
        serializer.save(clerk_user_id=clerk_user_id)

    def perform_update(self, serializer):
        # If task is being marked as completed, set completed_at
        if self.request.data.get('completed') and not self.get_object().completed:
            serializer.save(completed_at=timezone.now())
        else:
            serializer.save()

    @action(detail=True, methods=['patch'])
    def toggle_complete(self, request, pk=None):
        task = self.get_object()
        task.completed = not task.completed
        if task.completed:
            task.completed_at = timezone.now()
        else:
            task.completed_at = None
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        clerk_user_id = self.request.headers.get('X-Clerk-User-Id')
        if clerk_user_id:
            return User.objects.filter(clerk_id=clerk_user_id)
        return User.objects.none()

    def get_object(self):
        clerk_user_id = self.request.headers.get('X-Clerk-User-Id')
        if clerk_user_id:
            user = User.objects.get(clerk_id=clerk_user_id)
            return user
        return super().get_object()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info"""
        return self.retrieve(request)

    def perform_update(self, serializer):
        # Update the clerk_updated_at timestamp when user info is updated
        serializer.save(clerk_updated_at=timezone.now())