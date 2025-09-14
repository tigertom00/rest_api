from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Task, Project

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, required=False
    )

    class Meta:
        model = Task
        fields = "__all__"


class ProjectSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    tasks = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), many=True, required=False
    )

    class Meta:
        model = Project
        fields = "__all__"
