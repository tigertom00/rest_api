from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category, Task, Project
from .serializers import CategorySerializer, TaskSerializer, ProjectSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related("user_id").prefetch_related("category")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        # Only return tasks for the current user
        return Task.objects.filter(user_id=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related("user_id").prefetch_related("tasks")
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        # Only return projects for the current user
        return Project.objects.filter(user_id=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user)